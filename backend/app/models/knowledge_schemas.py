from pydantic import BaseModel, Field
from typing import Optional, List


class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str = ""
    created_at: str
    doc_count: int = 0
    chunk_count: int = 0


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeDocument(BaseModel):
    id: str
    kb_id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int = 0
    created_at: str


class SearchRequest(BaseModel):
    query: str
    kb_ids: List[str]
    top_k: int = 5
    score_threshold: float = 0.0


class SearchResult(BaseModel):
    content: str
    score: float
    doc_id: str
    filename: str
    kb_id: str
    chunk_index: int


class KBListResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[KnowledgeBase]] = None


class KBResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[KnowledgeBase] = None


class DocListResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[KnowledgeDocument]] = None


class DocResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[KnowledgeDocument] = None


class SearchResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[SearchResult]] = None
