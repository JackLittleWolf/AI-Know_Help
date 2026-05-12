export interface Agent {
  id: string
  name: string
  description: string
  system_prompt: string
  icon?: string
}

export async function getAgents(): Promise<Agent[]> {
  const resp = await fetch('/api/agents')
  if (!resp.ok) throw new Error('Failed to fetch agents')
  const data = await resp.json()
  return data.data || []
}

export async function createAgent(agent: Omit<Agent, 'id'>): Promise<Agent> {
  const resp = await fetch('/api/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agent)
  })
  if (!resp.ok) throw new Error('Failed to create agent')
  const data = await resp.json()
  return data.data[0]
}

export async function updateAgent(agent: Agent): Promise<Agent> {
  const resp = await fetch(`/api/agents/${agent.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agent)
  })
  if (!resp.ok) throw new Error('Failed to update agent')
  const data = await resp.json()
  return data.data[0]
}

export async function deleteAgent(id: string): Promise<void> {
  const resp = await fetch(`/api/agents/${id}`, {
    method: 'DELETE'
  })
  if (!resp.ok) throw new Error('Failed to delete agent')
}