import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.services import (
    agent_runtime,
    agent_service,
    attachment_extract_service,
    settings_service,
)
from app.services import mcp_service

router = APIRouter()


@router.post("/stream")
async def chat_stream(
    request: Request,
    message: str = Form(""),
    session_id: str | None = Form(None),
    history: str = Form("[]"),
    agent_id: str | None = Form(None),
    kb_ids: str = Form("[]"),
    rag_top_k: int = Form(5),
    files: list[UploadFile] = File(default=[]),
):
    session_key = _sanitize_path_part(session_id or "chat-session")
    llm = settings_service.load_llm()
    agent = agent_service.get_agent(agent_id) if agent_id else None
    system_prompt = None
    if agent:
        system_prompt, _ = agent_runtime.build_agent_system_prompt(agent)

    try:
        chat_history = json.loads(history)
    except Exception:
        chat_history = []

    window_size = 10
    if len(chat_history) > window_size:
        chat_history = chat_history[-window_size:]
        if chat_history and chat_history[0].get("role") != "user":
            chat_history = chat_history[1:]

    is_file_processor = agent is not None and agent.agent_mode == "file_processor"

    async def event_stream():
        node_states = _create_agent_node_states(agent)
        extraction_node_started = False
        try:
            if node_states:
                yield _sse_event({"type": "node_status", "nodes": node_states})
                node_states = _activate_agent_node(node_states, 0)
                yield _sse_event({"type": "node_status", "nodes": node_states})

            if is_file_processor and agent.require_attachments and not files:
                if node_states:
                    node_states = _fail_agent_nodes(node_states, "缺少附件")
                    yield _sse_event({"type": "node_status", "nodes": node_states})
                yield _sse_event({
                    "type": "error",
                    "error": "当前智能体必须先上传附件后再发送消息。",
                })
                return

            extracted_parts: list[str] = []

            if is_file_processor:
                total_files = len(files)
                for index, upload in enumerate(files, start=1):
                    if await request.is_disconnected():
                        break

                    filename = upload.filename or f"未命名文件-{index}"
                    yield _sse_event({
                        "type": "status",
                        "stage": "file",
                        "message": f"正在读取附件 {index}/{total_files}: {filename}",
                        "fileName": filename,
                        "index": index,
                        "total": total_files,
                    })

                    raw = await upload.read()
                    saved_path = _save_chat_upload(session_key, filename, raw)
                    yield _sse_event({
                        "type": "status",
                        "stage": "save",
                        "message": f"附件已保存: {saved_path}",
                        "fileName": filename,
                        "index": index,
                        "total": total_files,
                        "path": saved_path,
                    })
                    await asyncio.sleep(0)
                    if node_states and not extraction_node_started and len(node_states) > 1:
                        node_states = _activate_agent_node(node_states, 1)
                        extraction_node_started = True
                        yield _sse_event({"type": "node_status", "nodes": node_states})
                    if attachment_extract_service.needs_ocr(filename):
                        yield _sse_event({
                            "type": "status",
                            "stage": "ocr",
                            "message": f"正在通过 OCR 提取文件内容: {filename}",
                            "fileName": filename,
                            "index": index,
                            "total": total_files,
                        })
                        await asyncio.sleep(0)
                    yield _sse_event({
                        "type": "status",
                        "stage": "extract",
                        "message": f"正在提取文件内容: {filename}",
                        "fileName": filename,
                        "index": index,
                        "total": total_files,
                    })
                    await asyncio.sleep(0)

                    extracted = attachment_extract_service.extract_uploaded_content(filename, raw)
                    extracted_parts.append(f"[附件 {index}: {filename}]\n{extracted['text']}")

                    yield _sse_event({
                        "type": "status",
                        "stage": "extract",
                        "message": (
                            f"文件提取完成: {filename}"
                            if extracted["method"] != "ocr"
                            else f"OCR 提取完成: {filename}（共 {extracted['pages']} 页）"
                        ),
                        "fileName": filename,
                        "index": index,
                        "total": total_files,
                        "method": extracted["method"],
                        "pages": extracted["pages"],
                    })

            context = "\n\n".join(extracted_parts)
            user_content = f"{context}\n\n{message}".strip() if context else message

            # RAG: inject knowledge base context if kb_ids provided
            try:
                kb_ids_list = json.loads(kb_ids) if kb_ids else []
            except Exception:
                kb_ids_list = []
            if kb_ids_list and message:
                try:
                    from app.services import knowledge_base_service
                    emb_cfg = settings_service.load_embedding()
                    vdb_cfg = settings_service.load_vector_db()
                    rag_results = await knowledge_base_service.search(
                        query=message,
                        kb_ids=kb_ids_list,
                        top_k=rag_top_k,
                        score_threshold=0.3,
                        emb_cfg=emb_cfg,
                        vdb_cfg=vdb_cfg,
                    )
                    if rag_results:
                        rag_parts = [f"[知识库参考 {i+1} | 来源: {r.filename}]\n{r.content}" for i, r in enumerate(rag_results)]
                        rag_context = "\n\n".join(rag_parts)
                        user_content = f"{rag_context}\n\n{user_content}".strip()
                        yield _sse_event({"type": "status", "stage": "rag", "message": f"已检索到 {len(rag_results)} 条相关知识"})
                except Exception as exc:
                    yield _sse_event({"type": "status", "stage": "rag", "message": f"知识库检索失败: {exc}"})
            messages_payload = chat_history + [{"role": "user", "content": user_content}]

            if not llm.api_key:
                yield _sse_event({
                    "type": "text",
                    "text": "⚠️ 未配置 API Key，请前往「设置」页面配置大模型服务。",
                })
                return

            if node_states and not is_file_processor and len(node_states) > 1:
                node_states = _activate_agent_node(node_states, 1)
                yield _sse_event({"type": "node_status", "nodes": node_states})

            if node_states and is_file_processor and len(node_states) > 2:
                node_states = _activate_agent_node(node_states, 2)
                yield _sse_event({"type": "node_status", "nodes": node_states})

            yield _sse_event({
                "type": "status",
                "stage": "llm",
                "message": "正在生成回答..." if not is_file_processor else "文件处理完成，正在生成回答...",
            })

            async for chunk in _stream_langgraph(messages_payload, llm, system_prompt):
                if await request.is_disconnected():
                    break
                yield _sse_event(chunk)

            if node_states:
                node_states = _complete_agent_nodes(node_states)
                yield _sse_event({"type": "node_status", "nodes": node_states})

            yield _sse_event({
                "type": "status",
                "stage": "done",
                "message": "处理完成",
            })
        except Exception as exc:
            if node_states:
                node_states = _fail_agent_nodes(node_states, str(exc))
                yield _sse_event({"type": "node_status", "nodes": node_states})
            yield _sse_event({"type": "error", "error": str(exc)})
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


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _create_agent_node_states(agent) -> list[dict]:
    if not agent or not getattr(agent, "nodes", None):
        return []
    return [
        {
            "id": node.id,
            "name": node.name,
            "description": node.description,
            "status": "pending",
        }
        for node in agent.nodes
    ]


def _activate_agent_node(nodes: list[dict], active_index: int) -> list[dict]:
    updated = []
    last_index = len(nodes) - 1
    target_index = max(0, min(active_index, last_index))
    for index, node in enumerate(nodes):
        current = dict(node)
        if index < target_index:
            current["status"] = "completed"
        elif index == target_index:
            current["status"] = "running"
        else:
            current["status"] = "pending"
        updated.append(current)
    return updated


def _complete_agent_nodes(nodes: list[dict]) -> list[dict]:
    return [{**node, "status": "completed"} for node in nodes]


def _fail_agent_nodes(nodes: list[dict], error_message: str) -> list[dict]:
    updated = []
    failed = False
    for node in nodes:
        current = dict(node)
        if current.get("status") == "running" and not failed:
            current["status"] = "error"
            current["detail"] = error_message
            failed = True
        updated.append(current)
    if failed:
        return updated
    if updated:
        updated[0]["status"] = "error"
        updated[0]["detail"] = error_message
    return updated


def _save_chat_upload(session_key: str, filename: str, raw: bytes) -> str:
    upload_root = Path(settings_service.load_upload_dir())
    target_dir = upload_root / "chat" / session_key / datetime.now().strftime("%Y%m%d")
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_filename(filename)
    target_path = target_dir / f"{uuid4().hex}_{safe_name}"
    target_path.write_bytes(raw)
    return str(target_path)


def _sanitize_filename(filename: str) -> str:
    cleaned = Path(filename or "upload.bin").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("._")
    return cleaned or "upload.bin"


def _sanitize_path_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned or "chat-session"


async def _stream_langgraph(messages: list[dict], llm, system: str | None = None):
    from typing import Annotated
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

    app_settings = settings_service.load()
    mcp_servers = app_settings.mcp.servers

    # MCP tool discovery — failures are non-fatal; fall back to no tools
    try:
        lc_tools, tool_index = await mcp_service.gather_all_tools(mcp_servers)
    except Exception as exc:
        lc_tools, tool_index = [], {}

    chat_model = _build_chat_model(llm)
    if lc_tools:
        chat_model = chat_model.bind_tools(lc_tools)

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

    # Agentic loop: keep invoking until no more tool calls
    MAX_TOOL_ROUNDS = 5
    for _round in range(MAX_TOOL_ROUNDS):
        accumulated_msg = None

        async for msg, metadata in app.astream({"messages": lc_messages}, stream_mode="messages"):
            if metadata.get("langgraph_node") != "chatbot":
                continue

            # Accumulate chunks so tool_calls are preserved in the final aggregate.
            # In streaming mode tool_calls arrive in an intermediate chunk, not the
            # last one, so we cannot rely on the last chunk alone.
            if accumulated_msg is None:
                accumulated_msg = msg
            else:
                try:
                    accumulated_msg = accumulated_msg + msg
                except Exception:
                    accumulated_msg = msg

            # Skip chunks that carry tool call data — stream text/reasoning only
            raw_calls = getattr(msg, "tool_calls", None) or []
            if raw_calls:
                continue

            reasoning_text, answer_text = _extract_message_parts(msg)
            if reasoning_text:
                yield {"type": "reasoning", "text": reasoning_text}
            if answer_text:
                yield {"type": "text", "text": answer_text}

        # Read complete tool_calls from the accumulated message
        tool_calls_in_round: list[dict] = []
        if accumulated_msg is not None:
            raw_calls = getattr(accumulated_msg, "tool_calls", None) or []
            tool_calls_in_round = list(raw_calls)

        if not tool_calls_in_round:
            break

        lc_messages.append(accumulated_msg)

        for tc in tool_calls_in_round:
            fn_name: str = tc.get("name", "")
            fn_args: dict = tc.get("args", {})
            tc_id: str = tc.get("id", fn_name)

            yield {
                "type": "tool_call",
                "tool_name": fn_name,
                "arguments": fn_args,
                "status": "running",
            }

            routing = tool_index.get(fn_name)
            if routing:
                srv = mcp_service.find_server(mcp_servers, routing["server_name"])
                if srv:
                    try:
                        tool_result = await mcp_service.call_tool(
                            srv, routing["original_tool"], fn_args
                        )
                    except Exception as exc:
                        # Tool call failed — tell the LLM so it can answer from
                        # its own knowledge instead of silently returning nothing
                        tool_result = (
                            f"[工具调用失败: {exc}] "
                            "无法从外部服务获取数据，请根据你自身的知识直接回答用户问题。"
                        )
                else:
                    tool_result = (
                        f"[MCP Error] 找不到服务器: {routing['server_name']}。"
                        "请根据你自身的知识直接回答用户问题。"
                    )
            else:
                tool_result = (
                    f"[Error] 未知工具: {fn_name}。"
                    "请根据你自身的知识直接回答用户问题。"
                )

            yield {
                "type": "tool_call",
                "tool_name": fn_name,
                "arguments": fn_args,
                "result": tool_result,
                "status": "done",
            }

            lc_messages.append(ToolMessage(content=tool_result, tool_call_id=tc_id))


def _build_chat_model(llm):
    if llm.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model_name": llm.model,
            "anthropic_api_key": llm.api_key,
            "max_tokens": llm.max_tokens,
            "temperature": llm.temperature,
            "streaming": True,
        }
        if llm.enable_thinking:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": max(1024, llm.thinking_budget_tokens),
            }
        return ChatAnthropic(**kwargs)

    from langchain_openai import ChatOpenAI

    base = llm.base_url.rstrip("/") or "https://api.openai.com/v1"
    model_kwargs = _build_openai_model_kwargs(llm)
    kwargs = {
        "model": llm.model,
        "openai_api_key": llm.api_key,
        "openai_api_base": base,
        "max_tokens": llm.max_tokens,
        "temperature": llm.temperature,
        "streaming": True,
    }
    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs
    return ChatOpenAI(**kwargs)


def _build_openai_model_kwargs(llm) -> dict:
    if not llm.enable_thinking:
        return {}

    model_name = (llm.model or "").lower()
    model_kwargs: dict = {}

    if llm.provider == "custom":
        # Ollama and many OpenAI-compatible services use `think`.
        model_kwargs["extra_body"] = {"think": True}
        return model_kwargs

    if model_name.startswith(("o1", "o3", "o4", "gpt-5")):
        model_kwargs["reasoning"] = {"effort": "medium"}
    return model_kwargs


def _extract_message_parts(msg) -> tuple[str, str]:
    reasoning_parts: list[str] = []
    text_parts: list[str] = []

    def append_value(value, kind: str) -> None:
        if value is None:
            return
        if isinstance(value, str):
            target = reasoning_parts if kind == "reasoning" else text_parts
            if value:
                target.append(value)
            return
        if isinstance(value, list):
            for item in value:
                append_value(item, kind)
            return
        if isinstance(value, dict):
            block_type = str(value.get("type", "")).lower()
            if block_type in {"thinking", "reasoning", "reasoning_content", "redacted_thinking"}:
                append_value(
                    value.get("thinking")
                    or value.get("text")
                    or value.get("content")
                    or value.get("reasoning"),
                    "reasoning",
                )
            elif block_type in {"text", "output_text"}:
                append_value(value.get("text") or value.get("content"), "text")
            else:
                append_value(
                    value.get("text")
                    or value.get("content")
                    or value.get("value"),
                    kind,
                )

    append_value(getattr(msg, "content", None), "text")

    additional_kwargs = getattr(msg, "additional_kwargs", {}) or {}
    append_value(additional_kwargs.get("reasoning_content"), "reasoning")
    append_value(additional_kwargs.get("reasoning"), "reasoning")
    append_value(additional_kwargs.get("thinking"), "reasoning")

    return "".join(reasoning_parts), "".join(text_parts)
