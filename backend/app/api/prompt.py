from fastapi import APIRouter, HTTPException
from app.models.schemas import PromptRequest, PromptResponse, TestPromptRequest, TestPromptResponse, TestPromptData
from app.services import prompt_service

router = APIRouter()


@router.get("/skills")
async def list_skills():
    return prompt_service.SKILL_DESCRIPTIONS


@router.post("/generate", response_model=PromptResponse)
async def generate_prompt(request: PromptRequest):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    data = await prompt_service.generate_prompt(request.content, request.type or "general", request.skills)
    return PromptResponse(data=data)


@router.post("/test", response_model=TestPromptResponse)
async def test_prompt(request: TestPromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")
    if not request.user_input.strip():
        raise HTTPException(status_code=400, detail="测试输入不能为空")
    result = await prompt_service.test_prompt(request.prompt, request.user_input)
    return TestPromptResponse(data=TestPromptData(result=result))
