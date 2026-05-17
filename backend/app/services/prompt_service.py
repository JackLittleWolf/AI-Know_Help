import json
from typing import List
from app.models.schemas import Agent, PromptData
from app.services import agent_runtime, settings_service, skills_service

PROMPT_TEMPLATES = {
    "general": "通用问答",
    "code": "代码生成",
    "summary": "文档总结",
    "analysis": "数据分析",
    "translation": "翻译",
}

SKILL_DESCRIPTIONS = PROMPT_TEMPLATES


async def generate_prompt(
    content: str,
    prompt_type: str = "general",
    skills: List[str] = None,
    agent_id: str | None = None,
) -> PromptData:
    type_label = PROMPT_TEMPLATES.get(prompt_type, "通用问答")
    skills = skills or []
    llm = settings_service.load_llm()
    agent = agent_runtime.get_agent_or_prompt_engineer(agent_id)
    system_prompt, skill_names = agent_runtime.build_agent_system_prompt(agent, skills)

    if llm.api_key:
        if llm.provider == "anthropic":
            return await _call_anthropic(content, type_label, llm, system_prompt)
        else:
            return await _call_openai_compat(content, type_label, llm, system_prompt)
    return _generate_local(content, type_label, agent, skills, skill_names)


async def _call_anthropic(content: str, type_label: str, llm, system_prompt: str) -> PromptData:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=llm.api_key)
    message = await client.messages.create(
        model=llm.model,
        max_tokens=llm.max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": _build_prompt_generation_task(content, type_label)}],
    )
    return _parse_llm_text(message.content[0].text, content)


async def _call_openai_compat(content: str, type_label: str, llm, system_prompt: str) -> PromptData:
    import httpx

    base = llm.base_url.rstrip("/") or "https://api.openai.com/v1"
    payload = {
        "model": llm.model,
        "max_tokens": llm.max_tokens,
        "temperature": llm.temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _build_prompt_generation_task(content, type_label)},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {llm.api_key}"},
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    return _parse_llm_text(text, content)


def _build_prompt_generation_task(content: str, type_label: str) -> str:
    return (
        f"需求类型：{type_label}\n\n"
        "请以当前智能体身份完成提示词生成任务。若系统提示词中提供了 Skills，请先判断适用性，再把适用 Skill 的流程和标准融入生成结果。\n\n"
        f"原始需求：\n{content}"
    )


def _parse_llm_text(text: str, original: str) -> PromptData:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])
        return PromptData(
            original_content=original,
            generated_prompt=data.get("generated_prompt", text),
            explanation=data.get("explanation", ""),
        )
    except Exception:
        return PromptData(original_content=original, generated_prompt=text, explanation="")


def _generate_local(
    content: str,
    type_label: str,
    agent: Agent,
    request_skills: List[str],
    skill_names: List[str],
) -> PromptData:
    skill_sop_blocks = []
    for skill_id in agent_runtime.merge_skill_ids(agent.skills, request_skills):
        skill = skills_service.get_skill(skill_id)
        if skill:
            skill_sop_blocks.append(f"### {skill.name}\n{skill.skill_md[:300]}{'...' if len(skill.skill_md) > 300 else ''}")

    sop_note = ("\n\n# 参考 Skill SOP\n" + "\n\n".join(skill_sop_blocks)) if skill_sop_blocks else ""

    generated = (
        f"# 角色\n你是一位专业的{type_label}助手。\n\n"
        f"# 任务\n{content.strip()}\n\n"
        f"# 要求\n"
        f"1. 回答应准确、完整、有条理\n"
        f"2. 使用清晰的结构和格式\n"
        f"3. 如有必要，提供示例说明\n\n"
        f"# 输出格式\n请以结构化方式输出，使用标题和列表组织内容。"
        f"{sop_note}"
    )

    skill_note = f"并参考了以下 Skill：{', '.join(skill_names)}。" if skill_names else ""
    explanation = (
        f"已通过「{agent.name}」智能体为「{type_label}」类型需求添加角色定义、任务描述、要求说明和输出格式规范。{skill_note}"
        f"（当前未配置 API Key，使用本地规则生成。请前往「设置」页面配置大模型服务。）"
    )
    return PromptData(original_content=content, generated_prompt=generated, explanation=explanation)


async def test_prompt(prompt: str, user_input: str) -> str:
    llm = settings_service.load_llm()

    if llm.api_key:
        if llm.provider == "anthropic":
            return await _test_call_anthropic(prompt, user_input, llm)
        else:
            return await _test_call_openai_compat(prompt, user_input, llm)
    return _test_local(prompt, user_input)


async def _test_call_anthropic(prompt: str, user_input: str, llm) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=llm.api_key)
    message = await client.messages.create(
        model=llm.model,
        max_tokens=llm.max_tokens,
        system=prompt,
        messages=[{"role": "user", "content": user_input}],
    )
    return message.content[0].text


async def _test_call_openai_compat(prompt: str, user_input: str, llm) -> str:
    import httpx

    base = llm.base_url.rstrip("/") or "https://api.openai.com/v1"
    payload = {
        "model": llm.model,
        "max_tokens": llm.max_tokens,
        "temperature": llm.temperature,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {llm.api_key}"},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _test_local(prompt: str, user_input: str) -> str:
    return (
        "⚠️ 当前未配置 API Key，无法真实调用 LLM 测试提示词效果。\n\n"
        "请前往「设置」页面配置大模型服务后再使用测试功能。\n\n"
        f"---\n将使用以下提示词：\n{prompt[:200]}{'...' if len(prompt) > 200 else ''}\n\n"
        f"测试输入：\n{user_input}"
    )
