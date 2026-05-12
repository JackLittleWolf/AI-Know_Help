import json
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from app.models.schemas import SkillMeta

_SKILLS_DIR = Path(__file__).parent.parent / "data" / "skills"


def _ensure_dir() -> None:
    _SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _read_name(skill_dir: Path, content: str) -> str:
    """Return custom name from meta.json if present, else extract from SKILL.md heading."""
    meta_file = skill_dir / "meta.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if meta.get("name"):
                return meta["name"]
        except Exception:
            pass
    return _extract_name(content, skill_dir.name)


def _save_name(skill_dir: Path, name: str) -> None:
    (skill_dir / "meta.json").write_text(
        json.dumps({"name": name}, ensure_ascii=False), encoding="utf-8"
    )


def list_skills() -> List[SkillMeta]:
    _ensure_dir()
    result = []
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8")
        result.append(SkillMeta(
            id=skill_dir.name,
            name=_read_name(skill_dir, content),
            skill_md=content,
            has_scripts=(skill_dir / "scripts").exists(),
            has_assets=(skill_dir / "assets").exists(),
        ))
    return result


def get_skill(skill_id: str) -> Optional[SkillMeta]:
    skill_dir = _SKILLS_DIR / skill_id
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    content = skill_md.read_text(encoding="utf-8")
    return SkillMeta(
        id=skill_id,
        name=_read_name(skill_dir, content),
        skill_md=content,
        has_scripts=(skill_dir / "scripts").exists(),
        has_assets=(skill_dir / "assets").exists(),
    )


def create_from_text(skill_md_content: str, name: Optional[str] = None) -> SkillMeta:
    """Create a skill from raw SKILL.md text."""
    _ensure_dir()
    skill_id = str(uuid.uuid4())
    skill_dir = _SKILLS_DIR / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
    resolved_name = name.strip() if name and name.strip() else _extract_name(skill_md_content, skill_id)
    _save_name(skill_dir, resolved_name)
    return SkillMeta(id=skill_id, name=resolved_name, skill_md=skill_md_content)


def create_from_zip(zip_bytes: bytes, name: Optional[str] = None) -> SkillMeta:
    """Create a skill from a zip archive containing SKILL.md."""
    import zipfile
    import io

    _ensure_dir()
    skill_id = str(uuid.uuid4())
    skill_dir = _SKILLS_DIR / skill_id
    skill_dir.mkdir(parents=True)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        entries = zf.namelist()
        skill_md_path = _find_skill_md(entries)
        if not skill_md_path:
            shutil.rmtree(skill_dir)
            raise ValueError("zip 包中未找到 SKILL.md 文件")

        prefix = skill_md_path[: -len("SKILL.md")]

        for entry in entries:
            if not entry.startswith(prefix):
                continue
            rel = entry[len(prefix):]
            if not rel or rel.endswith("/"):
                continue
            dest = skill_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(entry))

    skill_md_content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    resolved_name = name.strip() if name and name.strip() else _extract_name(skill_md_content, skill_id)
    _save_name(skill_dir, resolved_name)
    return SkillMeta(
        id=skill_id,
        name=resolved_name,
        skill_md=skill_md_content,
        has_scripts=(skill_dir / "scripts").exists(),
        has_assets=(skill_dir / "assets").exists(),
    )


def delete_skill(skill_id: str) -> None:
    skill_dir = _SKILLS_DIR / skill_id
    if skill_dir.exists():
        shutil.rmtree(skill_dir)


def get_skill_md(skill_id: str) -> Optional[str]:
    skill_md = _SKILLS_DIR / skill_id / "SKILL.md"
    if skill_md.exists():
        return skill_md.read_text(encoding="utf-8")
    return None


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_name(content: str, fallback: str) -> str:
    """Extract skill name from first # heading in SKILL.md."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _find_skill_md(names: List[str]) -> Optional[str]:
    for name in names:
        if name == "SKILL.md":
            return name
    for name in names:
        parts = name.split("/")
        if len(parts) == 2 and parts[1] == "SKILL.md":
            return name
    return None
