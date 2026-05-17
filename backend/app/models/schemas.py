from pydantic import BaseModel, Field
from typing import List, Union, Any, Optional, Literal


# ── Embedding Settings ────────────────────────────────────────────────────────

class EmbeddingSettings(BaseModel):
    provider: Literal["ollama", "openai", "huggingface"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "text-embedding-3-small"
    hf_model_name: str = "BAAI/bge-small-zh-v1.5"
    chunk_size: int = 500
    chunk_overlap: int = 50


# ── Vector DB Settings ────────────────────────────────────────────────────────

class VectorDBSettings(BaseModel):
    provider: Literal["chroma", "qdrant", "milvus", "pgvector"] = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""
    pgvector_dsn: str = ""


# ── MCP Settings ──────────────────────────────────────────────────────────────

class MCPServerSettings(BaseModel):
    name: str = ""
    url: str = ""
    api_key: str = ""
    enabled: bool = True


class MCPSettings(BaseModel):
    servers: List[MCPServerSettings] = Field(default_factory=list)


# ── LLM Settings ──────────────────────────────────────────────────────────────

class LLMSettings(BaseModel):
    provider: Literal["anthropic", "openai", "custom"] = "anthropic"
    api_key: str = ""
    base_url: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024
    temperature: float = 0.7
    enable_thinking: bool = False
    thinking_budget_tokens: int = 10000


# ── OCR Settings ──────────────────────────────────────────────────────────────

class OCRSettings(BaseModel):
    provider: Literal["local", "external"] = "local"
    # local engine: rapidocr or paddleocr
    local_engine: Literal["rapidocr", "paddleocr"] = "rapidocr"
    # image pre-processing
    dpi: int = 150
    lang: str = "ch"          # rapidocr/paddleocr language hint
    # external HTTP OCR service
    external_url: str = ""    # POST endpoint, receives multipart file, returns {text: str} or {blocks: [...]}
    external_api_key: str = ""
    external_timeout: int = 30


# ── Security Settings ────────────────────────────────────────────────────────

class SecuritySettings(BaseModel):
    settings_password: str = "admin"


# ── Storage Settings ──────────────────────────────────────────────────────────

class StorageSettings(BaseModel):
    upload_dir: str = "/tmp/ocr_uploads"


# ── Combined Settings ─────────────────────────────────────────────────────────

class AppSettings(BaseModel):
    llm: LLMSettings = LLMSettings()
    ocr: OCRSettings = OCRSettings()
    security: SecuritySettings = SecuritySettings()
    storage: StorageSettings = StorageSettings()
    mcp: MCPSettings = MCPSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    vector_db: VectorDBSettings = VectorDBSettings()


class SettingsPasswordRequest(BaseModel):
    password: str


class AppSettingsResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[AppSettings] = None


# kept for backwards compat with existing prompt API
class LLMSettingsResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[LLMSettings] = None


# ── OCR ───────────────────────────────────────────────────────────────────────

class TextBlock(BaseModel):
    type: str  # "text" | "table"
    label: str
    value: Union[str, List[dict]]


class PageContent(BaseModel):
    page: int
    text_blocks: List[TextBlock]
    preview_b64: Optional[str] = None  # base64 PNG thumbnail for preview


class OCRData(BaseModel):
    filename: str
    total_pages: int
    processed_pages: int
    content: List[PageContent]


class OCRResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[OCRData] = None


class PromptRequest(BaseModel):
    content: str
    type: Optional[str] = "general"
    skills: List[str] = Field(default_factory=list)
    agent_id: Optional[str] = None


class SkillMeta(BaseModel):
    id: str
    name: str
    skill_md: str
    has_scripts: bool = False
    has_assets: bool = False


class PromptData(BaseModel):
    original_content: str
    generated_prompt: str
    explanation: str


class PromptResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[PromptData] = None


class TestPromptRequest(BaseModel):
    prompt: str
    user_input: str


class TestPromptData(BaseModel):
    result: str


class TestPromptResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[TestPromptData] = None


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentNode(BaseModel):
    id: str
    name: str
    description: str = ""


class Agent(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    system_prompt: str
    icon: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    kb_ids: List[str] = Field(default_factory=list)
    agent_mode: Literal["general", "file_processor"] = "general"
    require_attachments: bool = False
    nodes: List[AgentNode] = Field(default_factory=list)


class AgentResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[Agent]] = None
