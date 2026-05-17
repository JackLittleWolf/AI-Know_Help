import os
import shutil
import tempfile
from typing import TypedDict

from app.models.schemas import PageContent
from app.services import ocr_service, settings_service

DIRECT_TEXT_SUFFIXES = {
    ".txt", ".text", ".md", ".csv", ".json",
    ".yaml", ".yml", ".xml", ".log", ".ini", ".conf",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
PDF_SUFFIXES = {".pdf"}
OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}
OCR_SUFFIXES = IMAGE_SUFFIXES | PDF_SUFFIXES | OFFICE_SUFFIXES


class ExtractResult(TypedDict):
    text: str
    method: str
    pages: int


def needs_ocr(filename: str) -> bool:
    return _suffix(filename) in OCR_SUFFIXES


def extract_uploaded_content(filename: str, raw: bytes) -> ExtractResult:
    suffix = _suffix(filename)

    if suffix in DIRECT_TEXT_SUFFIXES:
        return _extract_text_bytes(filename, raw, method="native_text")

    if suffix in OCR_SUFFIXES:
        return _extract_via_ocr(filename, raw, suffix)

    auto_text = _try_extract_plain_text(filename, raw)
    if auto_text is not None:
        return {
            "text": auto_text,
            "method": "native_text_auto",
            "pages": 1,
        }

    return {
        "text": filename,
        "method": "filename_only",
        "pages": 1,
    }


def _extract_via_ocr(filename: str, raw: bytes, suffix: str) -> ExtractResult:
    upload_root = settings_service.load_upload_dir()
    os.makedirs(upload_root, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(dir=upload_root)
    tmp_path = os.path.join(tmp_dir, filename or f"upload{suffix}")
    try:
        with open(tmp_path, "wb") as file_obj:
            file_obj.write(raw)

        if suffix in IMAGE_SUFFIXES:
            pages = ocr_service.process_image(tmp_path)
        elif suffix in PDF_SUFFIXES:
            pages = ocr_service.process_pdf(tmp_path)
        else:
            pages = ocr_service.process_office(tmp_path, suffix)

        text = _render_pages(filename, pages)
        return {
            "text": text,
            "method": "ocr",
            "pages": len(pages),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _extract_text_bytes(filename: str, raw: bytes, method: str) -> ExtractResult:
    return {
        "text": f"{filename}\n{raw.decode('utf-8', errors='replace')}",
        "method": method,
        "pages": 1,
    }


def _try_extract_plain_text(filename: str, raw: bytes) -> str | None:
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return f"{filename}\n{decoded}"


def _render_pages(filename: str, pages: list[PageContent]) -> str:
    chunks: list[str] = [filename]
    for page in pages:
        page_lines: list[str] = []
        for block in page.text_blocks:
            if block.type == "text" and isinstance(block.value, str):
                if block.value.strip():
                    page_lines.append(block.value.strip())
            elif block.type == "table" and isinstance(block.value, list):
                for row in block.value:
                    if isinstance(row, dict):
                        pairs = [f"{key}: {value}" for key, value in row.items()]
                        if pairs:
                            page_lines.append(" | ".join(pairs))

        page_text = "\n".join(page_lines).strip()
        if page_text:
            chunks.append(f"[第 {page.page} 页]\n{page_text}")

    return "\n\n".join(chunks)


def _suffix(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()
