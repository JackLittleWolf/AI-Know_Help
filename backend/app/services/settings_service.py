import yaml
from pathlib import Path
from app.models.schemas import AppSettings, LLMSettings, OCRSettings, StorageSettings, EmbeddingSettings, VectorDBSettings

_SETTINGS_FILE = Path(__file__).parent.parent / "data" / "settings.yml"
_LEGACY_JSON = Path(__file__).parent.parent / "data" / "settings.json"
_LEGACY_LLM_JSON = Path(__file__).parent.parent / "data" / "llm_settings.json"


def _ensure_dir() -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load() -> AppSettings:
    _ensure_dir()
    if _SETTINGS_FILE.exists():
        try:
            raw = yaml.safe_load(_SETTINGS_FILE.read_text(encoding="utf-8")) or {}
            return AppSettings(**raw)
        except Exception:
            pass
    # Migrate from legacy JSON files
    for legacy in (_LEGACY_JSON, _LEGACY_LLM_JSON):
        if legacy.exists():
            try:
                import json
                data = json.loads(legacy.read_text())
                app = AppSettings(**data) if "llm" in data else AppSettings(llm=LLMSettings(**data))
                save(app)
                return app
            except Exception:
                pass
    # Fall back to env var
    from app.core.config import settings as env
    return AppSettings(
        llm=LLMSettings(api_key=env.ANTHROPIC_API_KEY),
        storage=StorageSettings(upload_dir=env.UPLOAD_DIR),
    )


def save(s: AppSettings) -> None:
    _ensure_dir()
    _SETTINGS_FILE.write_text(
        yaml.dump(s.model_dump(), allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def load_llm() -> LLMSettings:
    return load().llm


def load_ocr() -> OCRSettings:
    return load().ocr


def load_upload_dir() -> str:
    settings = load()
    return settings.storage.upload_dir


def load_embedding() -> EmbeddingSettings:
    return load().embedding


def load_vector_db() -> VectorDBSettings:
    return load().vector_db
