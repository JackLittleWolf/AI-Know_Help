from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Agent, AgentResponse
from app.services import agent_service

router = APIRouter()

@router.get("", response_model=AgentResponse)
async def list_agents():
    agents = agent_service.load_agents()
    return AgentResponse(data=agents)

@router.post("", response_model=AgentResponse)
async def create_agent(agent: Agent):
    new_agent = agent_service.add_agent(agent)
    return AgentResponse(data=[new_agent])

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent: Agent):
    agent.id = agent_id
    updated = agent_service.update_agent(agent)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(data=[updated])

@router.delete("/{agent_id}", response_model=AgentResponse)
async def delete_agent(agent_id: str):
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(data=[])
