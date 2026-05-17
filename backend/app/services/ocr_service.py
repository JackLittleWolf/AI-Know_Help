import os
import io
import base64
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
from PIL import Image
from pdf2image import convert_from_path
from app.models.schemas import PageContent, TextBlock, OCRSettings

_PREVIEW_MAX = 1200  # max dimension for preview thumbnail


def _image_to_b64(image: Image.Image) -> str:
    thumb = image.copy()
    thumb.thumbnail((_PREVIEW_MAX, _PREVIEW_MAX), Image.LANCZOS)
    buf = io.BytesIO()
    thumb.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ── engine dispatch ────────────────────────────────────────────────────────────

def _ocr_image(image: Image.Image, ocr_cfg: OCRSettings) -> List[TextBlock]:
    if ocr_cfg.provider == "external":
        return _ocr_image_external(image, ocr_cfg)
    if ocr_cfg.local_engine == "paddleocr":
        return _ocr_paddleocr(image, ocr_cfg)
    return _ocr_rapidocr(image, ocr_cfg)


# ── local: RapidOCR ────────────────────────────────────────────────────────────

def _ocr_rapidocr(image: Image.Image, ocr_cfg: OCRSettings) -> List[TextBlock]:
    import numpy as np
    from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR, LangRec
    engine = RapidOCR(params={
        "Det.ocr_version": OCRVersion.PPOCRV4,
        "Det.engine_type": EngineType.PADDLE,
        "Det.model_type": ModelType.MOBILE,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Rec.engine_type": EngineType.PADDLE,
        "Rec.model_type": ModelType.MOBILE,
        "Rec.lang_type": LangRec.CH,
        "Cls.ocr_version": OCRVersion.PPOCRV4,
        "Cls.engine_type": EngineType.PADDLE,
        "Cls.model_type": ModelType.MOBILE,
    })
    result = engine(np.array(image))
    return _parse_lines(_rapidocr_text_lines(result))


def _rapidocr_text_lines(result: object) -> List[str]:
    # rapidocr 3.x returns RapidOCROutput, which stores recognized text in txts.
    txts = getattr(result, "txts", None)
    if txts is not None:
        return [text for text in txts if isinstance(text, str) and text.strip()]

    # Older rapidocr_onnxruntime style returns (result, elapse).
    if isinstance(result, tuple) and result:
        return _rapidocr_text_lines(result[0])

    try:
        items = iter(result) if result is not None else iter(())
    except TypeError:
        return []

    lines: List[str] = []
    for item in items:
        text = ""
        if isinstance(item, str):
            text = item
        elif isinstance(item, dict):
            text = str(item.get("text") or item.get("txt") or "")
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            text = str(item[1])
        if text.strip():
            lines.append(text)
    return lines


# ── local: PaddleOCR ───────────────────────────────────────────────────────────

def _ocr_paddleocr(image: Image.Image, ocr_cfg: OCRSettings) -> List[TextBlock]:
    import numpy as np
    from paddleocr import PaddleOCR
    engine = PaddleOCR(use_angle_cls=True, lang=ocr_cfg.lang, show_log=False)
    result = engine.ocr(np.array(image), cls=True)
    lines: List[str] = []
    for page in (result or []):
        for item in (page or []):
            text = item[1][0] if item and len(item) > 1 else ""
            if text.strip():
                lines.append(text)
    return _parse_lines(lines)


# ── external HTTP OCR ──────────────────────────────────────────────────────────

def _ocr_image_external(image: Image.Image, ocr_cfg: OCRSettings) -> List[TextBlock]:
    import io
    import httpx

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    headers = {}
    if ocr_cfg.external_api_key:
        headers["Authorization"] = f"Bearer {ocr_cfg.external_api_key}"

    with httpx.Client(timeout=ocr_cfg.external_timeout) as client:
        resp = client.post(
            ocr_cfg.external_url,
            files={"file": ("image.png", buf, "image/png")},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    # Support two response shapes:
    # 1. {"text": "..."} — plain text
    # 2. {"blocks": [{"type": ..., "label": ..., "value": ...}]} — structured
    if "blocks" in data:
        return [TextBlock(**b) for b in data["blocks"]]
    text = data.get("text") or data.get("result") or str(data)
    return _parse_lines(text.splitlines())


# ── shared helpers ─────────────────────────────────────────────────────────────

def _parse_lines(lines: List[str]) -> List[TextBlock]:
    table_rows: List[List[str]] = []
    text_lines: List[str] = []
    for line in lines:
        parts = [p.strip() for p in line.split("  ") if p.strip()]
        if len(parts) >= 3:
            table_rows.append(parts)
        else:
            text_lines.append(line)

    blocks: List[TextBlock] = []
    if text_lines:
        blocks.append(TextBlock(type="text", label="文本内容", value="\n".join(text_lines)))
    if table_rows:
        headers = [f"列{i+1}" for i in range(len(table_rows[0]))]
        blocks.append(TextBlock(
            type="table",
            label="表格内容",
            value=[dict(zip(headers, row)) for row in table_rows],
        ))
    return blocks


# ── public API ─────────────────────────────────────────────────────────────────

def _get_ocr_cfg() -> OCRSettings:
    from app.services import settings_service
    return settings_service.load_ocr()


def process_image(file_path: str) -> List[PageContent]:
    cfg = _get_ocr_cfg()
    image = Image.open(file_path).convert("RGB")
    return [PageContent(page=1, text_blocks=_ocr_image(image, cfg), preview_b64=_image_to_b64(image))]


def process_pdf(file_path: str) -> List[PageContent]:
    cfg = _get_ocr_cfg()
    # images = convert_from_path(poppler_path = r'D:\Project\AI\AI_Know_Help_20260511\AI_Know_Help_20260511\backend\app\plugin\poppler\Library\bin', pdf_path = file_path, dpi=cfg.dpi)
    images = convert_from_path(pdf_path = file_path, dpi=cfg.dpi)
    return [
        PageContent(page=i, text_blocks=_ocr_image(img, cfg), preview_b64=_image_to_b64(img))
        for i, img in enumerate(images, start=1)
    ]


def process_office(file_path: str, suffix: str) -> List[PageContent]:
    pdf_path = _convert_office_to_pdf(file_path)
    try:
        return process_pdf(pdf_path)
    finally:
        shutil.rmtree(os.path.dirname(pdf_path), ignore_errors=True)


def _convert_office_to_pdf(file_path: str) -> str:
    from app.services import settings_service

    upload_root = settings_service.load_upload_dir()
    os.makedirs(upload_root, exist_ok=True)
    out_dir = tempfile.mkdtemp(dir=upload_root)
    os.system(f'libreoffice --headless --convert-to pdf --outdir "{out_dir}" "{file_path}"')
    pdf_path = os.path.join(out_dir, f"{Path(file_path).stem}.pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"LibreOffice failed to convert {file_path} to PDF")
    return pdf_path
