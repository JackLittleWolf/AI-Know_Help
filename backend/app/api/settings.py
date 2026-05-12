import io
from fastapi import APIRouter, HTTPException
from app.models.schemas import AppSettings, AppSettingsResponse, OCRSettings
from app.services import settings_service

router = APIRouter()


@router.get("", response_model=AppSettingsResponse)
async def get_settings():
    data = settings_service.load()
    return AppSettingsResponse(data=_mask(data))


@router.put("", response_model=AppSettingsResponse)
async def update_settings(body: AppSettings):
    stored = settings_service.load()
    # Restore masked API keys if client echoed them back unchanged
    if body.llm.api_key == _mask_key(stored.llm.api_key):
        body.llm.api_key = stored.llm.api_key
    if body.ocr.external_api_key == _mask_key(stored.ocr.external_api_key):
        body.ocr.external_api_key = stored.ocr.external_api_key
    settings_service.save(body)
    return AppSettingsResponse(data=_mask(body))


@router.post("/ocr/test", response_model=dict)
async def test_ocr(ocr: OCRSettings):
    """Quick connectivity check for external OCR endpoints."""
    if ocr.provider != "external":
        return {"code": 200, "message": "本地引擎无需测试连接"}
    if not ocr.external_url:
        raise HTTPException(status_code=400, detail="external_url 不能为空")
    try:
        import httpx
        from PIL import Image
        import numpy as np

        # Send a tiny 1×1 white PNG as a smoke test
        img = Image.new("RGB", (32, 32), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        headers = {}
        if ocr.external_api_key:
            headers["Authorization"] = f"Bearer {ocr.external_api_key}"

        async with httpx.AsyncClient(timeout=ocr.external_timeout) as client:
            resp = await client.post(
                ocr.external_url,
                files={"file": ("test.png", buf, "image/png")},
                headers=headers,
            )
        if resp.status_code < 500:
            return {"code": 200, "message": f"连接成功（HTTP {resp.status_code}）"}
        raise HTTPException(status_code=502, detail=f"服务返回 {resp.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _mask(s: AppSettings) -> AppSettings:
    return s.model_copy(deep=True, update={
        "llm": s.llm.model_copy(update={"api_key": _mask_key(s.llm.api_key)}),
        "ocr": s.ocr.model_copy(update={"external_api_key": _mask_key(s.ocr.external_api_key)}),
    })


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
