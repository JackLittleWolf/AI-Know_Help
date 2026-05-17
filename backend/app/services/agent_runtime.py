from typing import Iterable, List, Optional

from app.models.schemas import Agent, AgentNode
from app.services import agent_service, skills_service


PROMPT_ENGINEER_AGENT_ID = "prompt-engineer"
CODE_GENERATOR_AGENT_ID = "code-generator"
FILE_PROCESSOR_AGENT_ID = "file-processor"

PROMPT_ENGINEER_SYSTEM_PROMPT = """你是一位专业的 AI 提示词工程师智能体。你的任务是根据用户原始需求，生成高质量、结构清晰、可直接使用的 AI 提示词。

工作要求：
1. 主动理解用户目标、约束、上下文和期望输出
2. 根据需求类型选择合适的角色定义、任务拆解、输入说明、输出格式和质量标准
3. 如果可用 Skills 中包含适合当前任务的 SOP，必须把它转化为提示词中的可执行要求
4. 避免空泛表达，输出应能直接复制给另一个 AI 使用
5. 只返回 JSON，不要输出 Markdown 代码块

JSON 字段：
- generated_prompt: 优化后的提示词
- explanation: 简要说明本次优化策略，以及使用了哪些 Skill"""

CODE_GENERATOR_SYSTEM_PROMPT = """你是一位资深代码生成智能体。你的任务是根据用户需求生成可运行、可维护、贴合现有工程风格的代码。

工作要求：
1. 先理解用户目标、运行环境、输入输出、边界条件和约束
2. 优先给出完整可用的实现；如果上下文不足，明确列出关键假设
3. 代码应结构清晰、命名准确、避免无意义复杂度
4. 如用户提供项目上下文，遵循现有框架、目录结构、编码风格和依赖选择
5. 如果可用 Skills 中包含适合当前任务的 SOP、模板、约束或领域知识，必须在方案和代码中落实
6. 对关键实现点给出简洁说明，并指出必要的运行或验证命令
7. 不要编造不存在的 API；不确定时说明需要确认的点"""

FILE_PROCESSOR_SYSTEM_PROMPT = """你是一位文件处理智能体，基于上传附件帮助用户提取和整理文件内容。

工作要求：
1. 必须优先基于附件内容回答，禁止脱离文件内容臆测
2. 先忠实提取文件中的正文、表格、标题和关键信息，再根据用户要求进行整理
3. 如果用户没有额外要求，默认给出：
   - 文件内容概览
   - 关键字段/章节
   - 可直接引用的原文片段
4. 如果上传多个文件，按文件分别整理，并说明文件名
5. 当文件内容为空、识别失败或信息不足时，要明确说明
6. 输出尽量结构化，便于用户继续追问"""

BUILTIN_AGENT_IDS = {"default", PROMPT_ENGINEER_AGENT_ID, CODE_GENERATOR_AGENT_ID, FILE_PROCESSOR_AGENT_ID}

DEFAULT_AGENT_NODES = [
    AgentNode(id="understand-request", name="用户需求解析", description="理解用户问题、上下文和目标"),
    AgentNode(id="generate-answer", name="开始生成回答", description="根据需求组织答案内容"),
    AgentNode(id="answer-ready", name="回答生成完成", description="输出最终结果"),
]

PROMPT_ENGINEER_NODES = [
    AgentNode(id="analyze-request", name="用户需求解析", description="分析原始需求、目标和约束"),
    AgentNode(id="build-prompt", name="开始生成提示词", description="构建适合当前任务的提示词"),
    AgentNode(id="prompt-ready", name="提示词生成完成", description="输出最终提示词"),
]

CODE_GENERATOR_NODES = [
    AgentNode(id="parse-requirement", name="用户需求解析", description="分析用户需求、约束和工程上下文"),
    AgentNode(id="generate-code", name="需求收集完成，开始生成代码", description="根据需求生成代码实现"),
    AgentNode(id="code-ready", name="代码生成完成", description="输出最终代码和说明"),
]

FILE_PROCESSOR_NODES = [
    AgentNode(id="collect-file", name="读取上传附件", description="接收并保存用户上传的文件"),
    AgentNode(id="extract-content", name="提取文件内容", description="通过 OCR 或文本提取获取文件内容"),
    AgentNode(id="file-answer-ready", name="文件内容整理完成", description="基于附件内容生成最终回答"),
]


def get_default_agent() -> Agent:
    return _get_or_create_builtin_agent(Agent(
        id="default",
        name="默认助手",
        description="通用智能助手",
        system_prompt="你是一个有用的 AI 助手。",
        icon="robot",
        skills=[],
        nodes=DEFAULT_AGENT_NODES,
    ))


def get_prompt_engineer_agent() -> Agent:
    return _get_or_create_builtin_agent(Agent(
        id=PROMPT_ENGINEER_AGENT_ID,
        name="Prompt Engineer",
        description="用于提示词生成的内置智能体，可结合 Skills 生成高质量提示词。",
        system_prompt=PROMPT_ENGINEER_SYSTEM_PROMPT,
        icon="robot",
        skills=[],
        nodes=PROMPT_ENGINEER_NODES,
    ))


def get_code_generator_agent() -> Agent:
    return _get_or_create_builtin_agent(Agent(
        id=CODE_GENERATOR_AGENT_ID,
        name="代码生成智能体",
        description="面向代码生成、重构和工程实现的内置智能体，可结合 Skills 输出更贴合场景的代码。",
        system_prompt=CODE_GENERATOR_SYSTEM_PROMPT,
        icon="robot",
        skills=[],
        nodes=CODE_GENERATOR_NODES,
    ))


def get_file_processor_agent() -> Agent:
    return _get_or_create_builtin_agent(Agent(
        id=FILE_PROCESSOR_AGENT_ID,
        name="文件处理智能体",
        description="用于提取、整理和总结上传文件内容的内置智能体，选择后必须上传附件。",
        system_prompt=FILE_PROCESSOR_SYSTEM_PROMPT,
        icon="ocr",
        skills=[],
        agent_mode="file_processor",
        require_attachments=True,
        nodes=FILE_PROCESSOR_NODES,
    ))


def ensure_builtin_agents() -> List[Agent]:
    get_default_agent()
    get_prompt_engineer_agent()
    get_code_generator_agent()
    get_file_processor_agent()
    return agent_service.load_agents()


def _get_or_create_builtin_agent(default_agent: Agent) -> Agent:
    if default_agent.id:
        agent = agent_service.get_agent(default_agent.id)
        if agent:
            if not agent.nodes and default_agent.nodes:
                agent.nodes = default_agent.nodes
                updated = agent_service.update_agent(agent)
                if updated:
                    return updated
            return agent
    return agent_service.add_agent(default_agent)


def get_agent_or_prompt_engineer(agent_id: Optional[str]) -> Agent:
    if agent_id:
        agent = agent_service.get_agent(agent_id)
        if agent:
            return agent
    return get_prompt_engineer_agent()


def merge_skill_ids(*groups: Optional[Iterable[str]]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for group in groups:
        for skill_id in group or []:
            if skill_id and skill_id not in seen:
                seen.add(skill_id)
                merged.append(skill_id)
    return merged


def build_skill_sections(skill_ids: Iterable[str]) -> tuple[str, List[str]]:
    sections = []
    names = []
    for skill_id in skill_ids:
        skill = skills_service.get_skill(skill_id)
        if not skill:
            continue
        names.append(skill.name)
        sections.append(f"## {skill.name}\nSkill ID: {skill.id}\n\n{skill.skill_md.strip()}")
    return "\n\n---\n\n".join(sections), names


def build_agent_system_prompt(agent: Agent, extra_skill_ids: Optional[Iterable[str]] = None) -> tuple[str, List[str]]:
    skill_ids = merge_skill_ids(agent.skills, extra_skill_ids)
    skill_context, skill_names = build_skill_sections(skill_ids)
    system_prompt = agent.system_prompt.strip()

    if not skill_context:
        return system_prompt, []

    return (
        f"{system_prompt}\n\n"
        "# 可用 Skills\n"
        "下面的 Skills 是当前智能体可使用的能力和 SOP。执行任务时，请判断哪些 Skill 适用，并将其流程、约束和产出标准落实到最终结果中。\n\n"
        f"{skill_context}"
    ), skill_names
