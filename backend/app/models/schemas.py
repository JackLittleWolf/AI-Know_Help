from pydantic import BaseModel
from typing import List, Union, Any, Optional, Literal


# ── LLM Settings ──────────────────────────────────────────────────────────────

class LLMSettings(BaseModel):
    provider: Literal["anthropic", "openai", "custom"] = "anthropic"
    api_key: str = ""
    base_url: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024
    temperature: float = 0.7


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


# ── Combined Settings ─────────────────────────────────────────────────────────

class AppSettings(BaseModel):
    llm: LLMSettings = LLMSettings()
    ocr: OCRSettings = OCRSettings()


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
    skills: List[str] = []


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

class Agent(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    system_prompt: str
    icon: Optional[str] = None


class AgentResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[Agent]] = None

