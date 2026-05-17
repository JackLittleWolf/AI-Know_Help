import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document

from app.models.knowledge_schemas import KnowledgeBase, KnowledgeDocument, SearchResult
from app.models.schemas import EmbeddingSettings, VectorDBSettings
from app.services import document_parser_service, embedding_service

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent / "data" / "knowledge_bases.json"


# ── Metadata helpers ──────────────────────────────────────────────────────────

def _load_data() -> dict:
    if _DATA_FILE.exists():
        try:
            return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"knowledge_bases": [], "documents": []}


def _save_data(data: dict) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Knowledge Base CRUD ───────────────────────────────────────────────────────

def list_kbs() -> list[KnowledgeBase]:
    return [KnowledgeBase(**kb) for kb in _load_data()["knowledge_bases"]]


def get_kb(kb_id: str) -> KnowledgeBase | None:
    for kb in _load_data()["knowledge_bases"]:
        if kb["id"] == kb_id:
            return KnowledgeBase(**kb)
    return None


def create_kb(name: str, description: str = "") -> KnowledgeBase:
    data = _load_data()
    kb = KnowledgeBase(
        id=uuid4().hex,
        name=name,
        description=description,
        created_at=datetime.now().isoformat(),
    )
    data["knowledge_bases"].append(kb.model_dump())
    _save_data(data)
    return kb


def delete_kb(kb_id: str, emb_cfg: EmbeddingSettings | None = None, vdb_cfg: VectorDBSettings | None = None) -> None:
    data = _load_data()
    data["knowledge_bases"] = [kb for kb in data["knowledge_bases"] if kb["id"] != kb_id]
    data["documents"] = [d for d in data["documents"] if d["kb_id"] != kb_id]
    _save_data(data)
    if emb_cfg and vdb_cfg:
        try:
            _delete_collection(kb_id, emb_cfg, vdb_cfg)
        except Exception as exc:
            logger.warning("Failed to delete vector collection for kb %s: %s", kb_id, exc)


# ── Document CRUD ─────────────────────────────────────────────────────────────

def list_docs(kb_id: str) -> list[KnowledgeDocument]:
    return [KnowledgeDocument(**d) for d in _load_data()["documents"] if d["kb_id"] == kb_id]


def delete_doc(kb_id: str, doc_id: str, emb_cfg: EmbeddingSettings | None = None, vdb_cfg: VectorDBSettings | None = None) -> None:
    data = _load_data()
    doc = next((d for d in data["documents"] if d["id"] == doc_id and d["kb_id"] == kb_id), None)
    if not doc:
        return
    data["documents"] = [d for d in data["documents"] if not (d["id"] == doc_id and d["kb_id"] == kb_id)]

    # Update kb doc/chunk counts
    for kb in data["knowledge_bases"]:
        if kb["id"] == kb_id:
            kb["doc_count"] = max(0, kb.get("doc_count", 1) - 1)
            kb["chunk_count"] = max(0, kb.get("chunk_count", doc.get("chunk_count", 0)) - doc.get("chunk_count", 0))
            break
    _save_data(data)

    if emb_cfg and vdb_cfg:
        try:
            vs = _get_vectorstore(kb_id, emb_cfg, vdb_cfg)
            # Delete by metadata filter where available
            _delete_doc_from_vectorstore(vs, doc_id, vdb_cfg)
        except Exception as exc:
            logger.warning("Failed to delete doc vectors %s: %s", doc_id, exc)


# ── Ingestion ─────────────────────────────────────────────────────────────────

async def ingest_file(
    kb_id: str,
    filename: str,
    raw: bytes,
    emb_cfg: EmbeddingSettings,
    vdb_cfg: VectorDBSettings,
) -> KnowledgeDocument:
    ext = Path(filename).suffix.lower().lstrip(".")
    doc_id = uuid4().hex

    chunks = document_parser_service.parse_file(filename, raw, emb_cfg.chunk_size, emb_cfg.chunk_overlap)

    lc_docs = [
        Document(
            page_content=c["text"],
            metadata={
                "kb_id": kb_id,
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": c["chunk_index"],
                "page": c["page"],
            },
        )
        for c in chunks
        if c["text"].strip()
    ]

    if lc_docs:
        vs = _get_vectorstore(kb_id, emb_cfg, vdb_cfg)
        await vs.aadd_documents(lc_docs)

    doc = KnowledgeDocument(
        id=doc_id,
        kb_id=kb_id,
        filename=filename,
        file_type=ext,
        file_size=len(raw),
        chunk_count=len(lc_docs),
        created_at=datetime.now().isoformat(),
    )

    data = _load_data()
    data["documents"].append(doc.model_dump())
    for kb in data["knowledge_bases"]:
        if kb["id"] == kb_id:
            kb["doc_count"] = kb.get("doc_count", 0) + 1
            kb["chunk_count"] = kb.get("chunk_count", 0) + len(lc_docs)
            break
    _save_data(data)
    return doc


# ── Search ────────────────────────────────────────────────────────────────────

async def search(
    query: str,
    kb_ids: list[str],
    top_k: int,
    score_threshold: float,
    emb_cfg: EmbeddingSettings,
    vdb_cfg: VectorDBSettings,
) -> list[SearchResult]:
    all_results: list[SearchResult] = []
    for kb_id in kb_ids:
        try:
            vs = _get_vectorstore(kb_id, emb_cfg, vdb_cfg)
            hits = await vs.asimilarity_search_with_relevance_scores(query, k=top_k)
            for doc, score in hits:
                if score < score_threshold:
                    continue
                meta = doc.metadata
                all_results.append(SearchResult(
                    content=doc.page_content,
                    score=round(score, 4),
                    doc_id=meta.get("doc_id", ""),
                    filename=meta.get("filename", ""),
                    kb_id=meta.get("kb_id", kb_id),
                    chunk_index=meta.get("chunk_index", 0),
                ))
        except Exception as exc:
            logger.warning("Search failed for kb %s: %s", kb_id, exc)

    all_results.sort(key=lambda r: r.score, reverse=True)
    return all_results[:top_k]


# ── Vectorstore factory ───────────────────────────────────────────────────────

def _get_vectorstore(kb_id: str, emb_cfg: EmbeddingSettings, vdb_cfg: VectorDBSettings):
    embeddings = embedding_service.get_embeddings(emb_cfg)
    collection = f"kb_{kb_id}"

    if vdb_cfg.provider == "chroma":
        from langchain_chroma import Chroma
        persist_dir = str(Path(vdb_cfg.chroma_persist_dir).resolve())
        return Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

    if vdb_cfg.provider == "qdrant":
        from langchain_qdrant import QdrantVectorStore
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        client = QdrantClient(url=vdb_cfg.qdrant_url, api_key=vdb_cfg.qdrant_api_key or None)
        # Ensure collection exists
        try:
            client.get_collection(collection)
        except Exception:
            sample = embeddings.embed_query("test")
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=len(sample), distance=Distance.COSINE),
            )
        return QdrantVectorStore(client=client, collection_name=collection, embedding=embeddings)

    if vdb_cfg.provider == "milvus":
        from langchain_community.vectorstores import Milvus
        return Milvus(
            embedding_function=embeddings,
            collection_name=collection,
            connection_args={"uri": vdb_cfg.milvus_uri, "token": vdb_cfg.milvus_token or ""},
        )

    if vdb_cfg.provider == "pgvector":
        from langchain_community.vectorstores import PGVector
        return PGVector(
            embeddings=embeddings,
            collection_name=collection,
            connection=vdb_cfg.pgvector_dsn,
        )

    raise ValueError(f"Unknown vector DB provider: {vdb_cfg.provider}")


def _delete_collection(kb_id: str, emb_cfg: EmbeddingSettings, vdb_cfg: VectorDBSettings) -> None:
    collection = f"kb_{kb_id}"
    if vdb_cfg.provider == "chroma":
        from chromadb import PersistentClient
        persist_dir = str(Path(vdb_cfg.chroma_persist_dir).resolve())
        client = PersistentClient(path=persist_dir)
        try:
            client.delete_collection(collection)
        except Exception:
            pass

    elif vdb_cfg.provider == "qdrant":
        from qdrant_client import QdrantClient
        client = QdrantClient(url=vdb_cfg.qdrant_url, api_key=vdb_cfg.qdrant_api_key or None)
        try:
            client.delete_collection(collection)
        except Exception:
            pass


def _delete_doc_from_vectorstore(vs, doc_id: str, vdb_cfg: VectorDBSettings) -> None:
    """Best-effort deletion of all chunks belonging to doc_id."""
    if vdb_cfg.provider == "chroma":
        try:
            vs._collection.delete(where={"doc_id": doc_id})
        except Exception:
            pass
    elif vdb_cfg.provider == "qdrant":
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        try:
            vs.client.delete(
                collection_name=vs.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="metadata.doc_id", match=MatchValue(value=doc_id))]
                ),
            )
        except Exception:
            pass
