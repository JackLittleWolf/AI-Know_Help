import json
from fastapi import APIRouter, File, Form, UploadFile, Request
from fastapi.responses import StreamingResponse
from app.services import settings_service, agent_service

router = APIRouter()

@router.post("/stream")
async def chat_stream(
    request: Request,
    message: str = Form(...),
    session_id: str = Form(...),
    history: str = Form("[]"),
    agent_id: str = Form(None),
    files: list[UploadFile] = File(default=[]),
):
    llm = settings_service.load_llm()
    
    system_prompt = None
    if agent_id:
        agent = agent_service.get_agent(agent_id)
        if agent:
            system_prompt = agent.system_prompt

    file_texts = []
    for f in files:
        raw = await f.read()
        file_texts.append(_extract_text(f.filename or "", raw))

    context = "\n\n".join(f"[附件: {t}]" for t in file_texts if t)
    user_content = f"{context}\n\n{message}".strip() if context else message

    try:
        chat_history = json.loads(history)
    except Exception:
        chat_history = []
        
    # Sliding window: keep max 10 messages from history (5 pairs)
    WINDOW_SIZE = 10
    if len(chat_history) > WINDOW_SIZE:
        chat_history = chat_history[-WINDOW_SIZE:]
        # Ensure we always start with a user message for compatibility (Anthropic requires this)
        if chat_history and chat_history[0].get("role") != "user":
            chat_history = chat_history[1:]

    messages_payload = chat_history + [{"role": "user", "content": user_content}]

    async def event_stream():
        try:
            if llm.api_key:
                async for chunk in _stream_langgraph(messages_payload, llm, system_prompt):
                    if await request.is_disconnected():
                        break
                    yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'text': '⚠️ 未配置 API Key，请前往「设置」页面配置大模型服务。'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _extract_text(filename: str, raw: bytes) -> str:
    name = filename.lower()
    try:
        if name.endswith((".txt", ".md", ".csv")):
            return f"{filename}\n{raw.decode('utf-8', errors='replace')}"
        if name.endswith(".pdf"):
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            return f"{filename}\n{text}"
        if name.endswith(".docx"):
            import docx, io
            doc = docx.Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
            return f"{filename}\n{text}"
        if name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
            import numpy as np
            from PIL import Image
            import io as _io
            from rapidocr_onnxruntime import RapidOCR
            img = Image.open(_io.BytesIO(raw)).convert("RGB")
            arr = np.array(img)
            ocr = RapidOCR()
            result, _ = ocr(arr)
            text = "\n".join(r[1] for r in result) if result else ""
            return f"{filename}\n{text}"
    except Exception:
        pass
    return filename


async def _stream_langgraph(messages: list[dict], llm, system: str = None):
    from typing import Annotated
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    if llm.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        chat_model = ChatAnthropic(
            model_name=llm.model,
            anthropic_api_key=llm.api_key,
            max_tokens=llm.max_tokens,
            temperature=llm.temperature,
            streaming=True
        )
    else:
        from langchain_openai import ChatOpenAI
        base = llm.base_url.rstrip("/") or "https://api.openai.com/v1"
        chat_model = ChatOpenAI(
            model=llm.model,
            openai_api_key=llm.api_key,
            openai_api_base=base,
            max_tokens=llm.max_tokens,
            temperature=llm.temperature,
            streaming=True
        )

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    async def chatbot(state: State):
        msgs = state["messages"]
        if system:
            msgs = [SystemMessage(content=system)] + msgs
        response = await chat_model.ainvoke(msgs)
        return {"messages": [response]}

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    app = graph_builder.compile()

    lc_messages = []
    for m in messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))

    async for msg, metadata in app.astream({"messages": lc_messages}, stream_mode="messages"):
        if msg.content and metadata.get("langgraph_node") == "chatbot":
            yield msg.content
