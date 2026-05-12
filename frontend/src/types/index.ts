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

// ── Combined ──────────────────────────────────────────────────────────────────

export interface AppSettings {
  llm: LLMSettings
  ocr: OCRSettings
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
