from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import SkillMeta
from app.services import skills_service

router = APIRouter()


class SkillTextBody(BaseModel):
    skill_md: str
    name: str | None = None


@router.get("", response_model=list[SkillMeta])
async def list_skills():
    return skills_service.list_skills()


@router.get("/{skill_id}", response_model=SkillMeta)
async def get_skill(skill_id: str):
    skill = skills_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/from-text", response_model=SkillMeta, status_code=201)
async def create_from_text(body: SkillTextBody):
    if not body.skill_md.strip():
        raise HTTPException(status_code=400, detail="skill_md 不能为空")
    try:
        return skills_service.create_from_text(body.skill_md.strip(), name=body.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-zip", response_model=SkillMeta, status_code=201)
async def create_from_zip(file: UploadFile = File(...), name: Optional[str] = Form(None)):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 .zip 文件")
    data = await file.read()
    try:
        return skills_service.create_from_zip(data, name=name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(skill_id: str):
    skills_service.delete_skill(skill_id)
