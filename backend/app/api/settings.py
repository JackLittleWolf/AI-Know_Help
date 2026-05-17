import io
from fastapi import APIRouter, HTTPException
from app.models.schemas import AppSettings, AppSettingsResponse, MCPServerSettings, OCRSettings, SettingsPasswordRequest
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
    # Restore masked MCP server API keys
    stored_servers = {srv.name: srv for srv in stored.mcp.servers}
    for srv in body.mcp.servers:
        stored_srv = stored_servers.get(srv.name)
        if stored_srv and srv.api_key == _mask_key(stored_srv.api_key):
            srv.api_key = stored_srv.api_key
    # Restore masked embedding / vector DB secrets
    if body.embedding.openai_api_key == _mask_key(stored.embedding.openai_api_key):
        body.embedding.openai_api_key = stored.embedding.openai_api_key
    if body.vector_db.qdrant_api_key == _mask_key(stored.vector_db.qdrant_api_key):
        body.vector_db.qdrant_api_key = stored.vector_db.qdrant_api_key
    if body.vector_db.milvus_token == _mask_key(stored.vector_db.milvus_token):
        body.vector_db.milvus_token = stored.vector_db.milvus_token
    if body.vector_db.pgvector_dsn == _mask_key(stored.vector_db.pgvector_dsn):
        body.vector_db.pgvector_dsn = stored.vector_db.pgvector_dsn
    body.security = stored.security
    settings_service.save(body)
    return AppSettingsResponse(data=_mask(body))


@router.post("/verify-password", response_model=dict)
async def verify_settings_password(body: SettingsPasswordRequest):
    stored = settings_service.load()
    if body.password == stored.security.settings_password:
        return {"code": 200, "message": "success"}
    raise HTTPException(status_code=401, detail="密码错误")


@router.post("/mcp/test", response_model=dict)
async def test_mcp_server(srv: MCPServerSettings):
    """Quick connectivity check: fetch tools/list from an MCP server."""
    if not srv.url:
        raise HTTPException(status_code=400, detail="url 不能为空")
    try:
        from app.services import mcp_service
        tools = await mcp_service.list_tools(srv)
        return {"code": 200, "message": f"连接成功，发现 {len(tools)} 个工具"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))



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
    masked_servers = [
        srv.model_copy(update={"api_key": _mask_key(srv.api_key)})
        for srv in s.mcp.servers
    ]
    return s.model_copy(deep=True, update={
        "llm": s.llm.model_copy(update={"api_key": _mask_key(s.llm.api_key)}),
        "ocr": s.ocr.model_copy(update={"external_api_key": _mask_key(s.ocr.external_api_key)}),
        "security": s.security.model_copy(update={"settings_password": _mask_key(s.security.settings_password)}),
        "mcp": s.mcp.model_copy(update={"servers": masked_servers}),
        "embedding": s.embedding.model_copy(update={"openai_api_key": _mask_key(s.embedding.openai_api_key)}),
        "vector_db": s.vector_db.model_copy(update={
            "qdrant_api_key": _mask_key(s.vector_db.qdrant_api_key),
            "milvus_token": _mask_key(s.vector_db.milvus_token),
            "pgvector_dsn": _mask_key(s.vector_db.pgvector_dsn),
        }),
    })


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
