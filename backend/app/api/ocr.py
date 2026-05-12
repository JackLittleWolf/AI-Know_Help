import os
import tempfile
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import OCRResponse, OCRData
from app.services import ocr_service
from app.core.config import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif",
    ".pdf", ".docx", ".xlsx", ".pptx",
}


@router.post("/process", response_model=OCRResponse)
async def process_ocr(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {suffix}")

    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制（最大50MB）")

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename or f"upload{suffix}")
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        if suffix in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}:
            pages = ocr_service.process_image(tmp_path)
        elif suffix == ".pdf":
            pages = ocr_service.process_pdf(tmp_path)
        else:
            pages = ocr_service.process_office(tmp_path, suffix)

        data = OCRData(
            filename=file.filename or "",
            total_pages=len(pages),
            processed_pages=len(pages),
            content=pages,
        )
        return OCRResponse(data=data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
