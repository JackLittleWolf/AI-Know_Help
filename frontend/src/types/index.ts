export interface TextBlock {
  type: 'text' | 'table'
  label: string
  value: string | Record<string, unknown>[]
}

export interface PageContent {
  page: number
  text_blocks: TextBlock[]
  preview_b64?: string
}

export interface OCRData {
  filename: string
  total_pages: number
  processed_pages: number
  content: PageContent[]
}

export interface OCRResponse {
  code: number
  message: string
  data: OCRData | null
}

export interface PromptRequest {
  content: string
  type?: string
  skills?: string[]
  agent_id?: string
}

export interface TestPromptRequest {
  prompt: string
  user_input: string
}

export interface TestPromptData {
  result: string
}

export interface TestPromptResponse {
  code: number
  message: string
  data: TestPromptData | null
}

export interface PromptData {
  original_content: string
  generated_prompt: string
  explanation: string
}

export interface PromptResponse {
  code: number
  message: string
  data: PromptData | null
}

// ── LLM Settings ──────────────────────────────────────────────────────────────

export type LLMProvider = 'anthropic' | 'openai' | 'custom'

export interface LLMSettings {
  provider: LLMProvider
  api_key: string
  base_url: string
  model: string
  max_tokens: number
  temperature: number
  enable_thinking: boolean
  thinking_budget_tokens: number
}

// ── OCR Settings ──────────────────────────────────────────────────────────────

export type OCRProvider = 'local' | 'external'
export type LocalEngine = 'rapidocr' | 'paddleocr'

export interface OCRSettings {
  provider: OCRProvider
  local_engine: LocalEngine
  dpi: number
  lang: string
  external_url: string
  external_api_key: string
  external_timeout: number
}

export interface SecuritySettings {
  settings_password: string
}

export interface StorageSettings {
  upload_dir: string
}

// ── MCP Settings ──────────────────────────────────────────────────────────────

export interface MCPServerSettings {
  name: string
  url: string
  api_key: string
  enabled: boolean
}

export interface MCPSettings {
  servers: MCPServerSettings[]
}

// ── Embedding Settings ────────────────────────────────────────────────────────

export type EmbeddingProvider = 'ollama' | 'openai' | 'huggingface'

export interface EmbeddingSettings {
  provider: EmbeddingProvider
  ollama_base_url: string
  ollama_model: string
  openai_api_key: string
  openai_base_url: string
  openai_model: string
  hf_model_name: string
  chunk_size: number
  chunk_overlap: number
}

// ── Vector DB Settings ────────────────────────────────────────────────────────

export type VectorDBProvider = 'chroma' | 'qdrant' | 'milvus' | 'pgvector'

export interface VectorDBSettings {
  provider: VectorDBProvider
  chroma_persist_dir: string
  qdrant_url: string
  qdrant_api_key: string
  milvus_uri: string
  milvus_token: string
  pgvector_dsn: string
}

// ── Knowledge Base ────────────────────────────────────────────────────────────

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  created_at: string
  doc_count: number
  chunk_count: number
}

export interface KnowledgeDocument {
  id: string
  kb_id: string
  filename: string
  file_type: string
  file_size: number
  chunk_count: number
  created_at: string
}

export interface SearchResult {
  content: string
  score: number
  doc_id: string
  filename: string
  kb_id: string
  chunk_index: number
}

// ── Combined ──────────────────────────────────────────────────────────────────

export interface AppSettings {
  llm: LLMSettings
  ocr: OCRSettings
  security?: SecuritySettings
  storage?: StorageSettings
  mcp?: MCPSettings
  embedding?: EmbeddingSettings
  vector_db?: VectorDBSettings
}

export interface AppSettingsResponse {
  code: number
  message: string
  data: AppSettings | null
}

// kept for prompt API usage
export interface LLMSettingsResponse {
  code: number
  message: string
  data: LLMSettings | null
}

// ── Skills ────────────────────────────────────────────────────────────────────

export interface SkillMeta {
  id: string
  name: string
  skill_md: string
  has_scripts: boolean
  has_assets: boolean
}
