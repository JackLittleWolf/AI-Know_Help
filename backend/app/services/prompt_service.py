import json
from typing import List
from app.models.schemas import PromptData
from app.services import settings_service, skills_service

PROMPT_TEMPLATES = {
    "general": "通用问答",
    "code": "代码生成",
    "summary": "文档总结",
    "analysis": "数据分析",
    "translation": "翻译",
}

BASE_SYSTEM_PROMPT = """你是一位专业的AI提示词工程师。请根据用户提供的原始需求，生成一个高质量、结构清晰、可直接使用的AI提示词。

要求：
1. 提示词应包含明确的角色定义、任务描述、输出格式要求
2. 语言简洁、逻辑清晰
3. 避免歧义，确保AI能准确理解意图
4. 根据需求类型调整提示词风格

请以JSON格式返回，包含以下字段：
- generated_prompt: 优化后的提示词
- explanation: 优化说明（简要说明做了哪些优化）"""


def _build_system_prompt(skills: List[str]) -> str:
    """Inject selected SKILL.md contents into the system prompt."""
    skill_sections = []
    for skill_id in skills:
        content = skills_service.get_skill_md(skill_id)
        if content:
            skill_sections.append(content.strip())

    if not skill_sections:
        return BASE_SYSTEM_PROMPT

    injected = "\n\n---\n\n".join(skill_sections)
    return BASE_SYSTEM_PROMPT + f"\n\n以下是你需要遵循的 Skill SOP，请在生成提示词时严格参考：\n\n{injected}"


async def generate_prompt(content: str, prompt_type: str = "general", skills: List[str] = None) -> PromptData:
    type_label = PROMPT_TEMPLATES.get(prompt_type, "通用问答")
    skills = skills or []
    llm = settings_service.load_llm()

    if llm.api_key:
        if llm.provider == "anthropic":
            return await _call_anthropic(content, type_label, skills, llm)
        else:
            return await _call_openai_compat(content, type_label, skills, llm)
    return _generate_local(content, type_label, skills)


async def _call_anthropic(content: str, type_label: str, skills: List[str], llm) -> PromptData:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=llm.api_key)
    message = await client.messages.create(
        model=llm.model,
        max_tokens=llm.max_tokens,
        system=_build_system_prompt(skills),
        messages=[{"role": "user", "content": f"需求类型：{type_label}\n\n原始需求：\n{content}"}],
    )
    return _parse_llm_text(message.content[0].text, content)


async def _call_openai_compat(content: str, type_label: str, skills: List[str], llm) -> PromptData:
    import httpx

    base = llm.base_url.rstrip("/") or "https://api.openai.com/v1"
    payload = {
        "model": llm.model,
        "max_tokens": llm.max_tokens,
        "temperature": llm.temperature,
        "messages": [
            {"role": "system", "content": _build_system_prompt(skills)},
            {"role": "user", "content": f"需求类型：{type_label}\n\n原始需求：\n{content}"},
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


def _generate_local(content: str, type_label: str, skills: List[str]) -> PromptData:
    skill_names = []
    skill_sop_blocks = []
    for skill_id in skills:
        skill = skills_service.get_skill(skill_id)
        if skill:
            skill_names.append(skill.name)
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
        f"已为「{type_label}」类型需求添加角色定义、任务描述、要求说明和输出格式规范。{skill_note}"
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
