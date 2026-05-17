import type { KnowledgeBase, KnowledgeDocument, SearchResult } from '@/types'

const BASE = '/api/knowledge'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, options)
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText)
    throw new Error(text || `HTTP ${resp.status}`)
  }
  const json = await resp.json()
  return json.data as T
}

// ── Knowledge Base CRUD ───────────────────────────────────────────────────────

export async function listKBs(): Promise<KnowledgeBase[]> {
  return request<KnowledgeBase[]>(`${BASE}/bases`)
}

export async function createKB(name: string, description: string): Promise<KnowledgeBase> {
  return request<KnowledgeBase>(`${BASE}/bases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  })
}

export async function deleteKB(kbId: string): Promise<void> {
  await fetch(`${BASE}/bases/${kbId}`, { method: 'DELETE' })
}

// ── Documents ─────────────────────────────────────────────────────────────────

export async function listDocs(kbId: string): Promise<KnowledgeDocument[]> {
  return request<KnowledgeDocument[]>(`${BASE}/bases/${kbId}/docs`)
}

export async function uploadDoc(kbId: string, file: File): Promise<KnowledgeDocument> {
  const form = new FormData()
  form.append('file', file)
  return request<KnowledgeDocument>(`${BASE}/bases/${kbId}/docs`, {
    method: 'POST',
    body: form,
  })
}

export async function deleteDoc(kbId: string, docId: string): Promise<void> {
  await fetch(`${BASE}/bases/${kbId}/docs/${docId}`, { method: 'DELETE' })
}

// ── Search ────────────────────────────────────────────────────────────────────

export async function searchKB(
  query: string,
  kbIds: string[],
  topK = 5,
  scoreThreshold = 0.0,
): Promise<SearchResult[]> {
  return request<SearchResult[]>(`${BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, kb_ids: kbIds, top_k: topK, score_threshold: scoreThreshold }),
  })
}

// ── Test connection ───────────────────────────────────────────────────────────

export async function testConnection(): Promise<{ code: number; message: string }> {
  const resp = await fetch(`${BASE}/test-connection`, { method: 'POST' })
  return resp.json()
}
