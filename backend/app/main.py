from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ocr, prompt, settings, skills, chat, agents, knowledge
from app.core.config import settings as env_settings

app = FastAPI(
    title="OCR & AI Prompt Tool",
    description="OCR内容提取与AI提示词生成工具",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=env_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(prompt.router, prefix="/api/prompt", tags=["Prompt"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
