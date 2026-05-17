import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.knowledge_schemas import (
    DocListResponse,
    DocResponse,
    KBListResponse,
    KBResponse,
    KnowledgeBaseCreate,
    SearchRequest,
    SearchResponse,
)
from app.services import knowledge_base_service, settings_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Knowledge Base CRUD ───────────────────────────────────────────────────────

@router.get("/bases", response_model=KBListResponse)
async def list_bases():
    return KBListResponse(data=knowledge_base_service.list_kbs())


@router.post("/bases", response_model=KBResponse)
async def create_base(body: KnowledgeBaseCreate):
    kb = knowledge_base_service.create_kb(body.name, body.description)
    return KBResponse(data=kb)


@router.delete("/bases/{kb_id}")
async def delete_base(kb_id: str):
    if not knowledge_base_service.get_kb(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    emb_cfg = settings_service.load_embedding()
    vdb_cfg = settings_service.load_vector_db()
    knowledge_base_service.delete_kb(kb_id, emb_cfg, vdb_cfg)
    return {"code": 200, "message": "deleted"}


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get("/bases/{kb_id}/docs", response_model=DocListResponse)
async def list_docs(kb_id: str):
    if not knowledge_base_service.get_kb(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return DocListResponse(data=knowledge_base_service.list_docs(kb_id))


@router.post("/bases/{kb_id}/docs", response_model=DocResponse)
async def upload_doc(kb_id: str, file: UploadFile = File(...)):
    if not knowledge_base_service.get_kb(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    raw = await file.read()
    emb_cfg = settings_service.load_embedding()
    vdb_cfg = settings_service.load_vector_db()
    try:
        doc = await knowledge_base_service.ingest_file(
            kb_id, file.filename or "upload", raw, emb_cfg, vdb_cfg
        )
    except Exception as exc:
        logger.exception("Ingest failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=str(exc))
    return DocResponse(data=doc)


@router.delete("/bases/{kb_id}/docs/{doc_id}")
async def delete_doc(kb_id: str, doc_id: str):
    emb_cfg = settings_service.load_embedding()
    vdb_cfg = settings_service.load_vector_db()
    knowledge_base_service.delete_doc(kb_id, doc_id, emb_cfg, vdb_cfg)
    return {"code": 200, "message": "deleted"}


# ── Search ────────────────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search(body: SearchRequest):
    emb_cfg = settings_service.load_embedding()
    vdb_cfg = settings_service.load_vector_db()
    results = await knowledge_base_service.search(
        query=body.query,
        kb_ids=body.kb_ids,
        top_k=body.top_k,
        score_threshold=body.score_threshold,
        emb_cfg=emb_cfg,
        vdb_cfg=vdb_cfg,
    )
    return SearchResponse(data=results)


# ── Test connection ───────────────────────────────────────────────────────────

@router.post("/test-connection")
async def test_connection():
    emb_cfg = settings_service.load_embedding()
    vdb_cfg = settings_service.load_vector_db()
    try:
        from app.services import embedding_service
        embeddings = embedding_service.get_embeddings(emb_cfg)
        embeddings.embed_query("test")
    except Exception as exc:
        return {"code": 500, "message": f"Embedding error: {exc}"}
    try:
        knowledge_base_service._get_vectorstore("__test__", emb_cfg, vdb_cfg)
    except Exception as exc:
        return {"code": 500, "message": f"Vector DB error: {exc}"}
    return {"code": 200, "message": "Connection OK"}
