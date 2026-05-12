import yaml
import uuid
from pathlib import Path
from typing import List
from app.models.schemas import Agent

_AGENTS_FILE = Path(__file__).parent.parent / "data" / "agents.yml"

def _ensure_dir() -> None:
    _AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_agents() -> List[Agent]:
    _ensure_dir()
    if not _AGENTS_FILE.exists():
        # Default agent
        default_agent = Agent(
            id="default",
            name="默认助手",
            description="通用智能助手",
            system_prompt="你是一个有用的 AI 助手。",
            icon="robot"
        )
        save_agents([default_agent])
        return [default_agent]
    
    try:
        raw = yaml.safe_load(_AGENTS_FILE.read_text(encoding="utf-8")) or []
        return [Agent(**agent_data) for agent_data in raw]
    except Exception:
        return []

def save_agents(agents: List[Agent]) -> None:
    _ensure_dir()
    _AGENTS_FILE.write_text(
        yaml.dump([a.model_dump() for a in agents], allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

def get_agent(agent_id: str) -> Agent | None:
    agents = load_agents()
    for a in agents:
        if a.id == agent_id:
            return a
    return None

def add_agent(agent: Agent) -> Agent:
    agents = load_agents()
    if not agent.id:
        agent.id = str(uuid.uuid4())
    agents.append(agent)
    save_agents(agents)
    return agent

def update_agent(agent: Agent) -> Agent | None:
    agents = load_agents()
    for i, a in enumerate(agents):
        if a.id == agent.id:
            agents[i] = agent
            save_agents(agents)
            return agent
    return None

def delete_agent(agent_id: str) -> bool:
    agents = load_agents()
    filtered = [a for a in agents if a.id != agent_id]
    if len(filtered) != len(agents):
        save_agents(filtered)
        return True
    return False
