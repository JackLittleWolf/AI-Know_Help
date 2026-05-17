import logging
from langchain_core.embeddings import Embeddings
from app.models.schemas import EmbeddingSettings

logger = logging.getLogger(__name__)


def get_embeddings(cfg: EmbeddingSettings) -> Embeddings:
    """Factory: returns a LangChain Embeddings instance for the configured provider."""
    if cfg.provider == "ollama":
        from langchain_community.embeddings import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=cfg.ollama_base_url,
            model=cfg.ollama_model,
        )

    if cfg.provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        kwargs: dict = {
            "model": cfg.openai_model,
            "api_key": cfg.openai_api_key,
        }
        if cfg.openai_base_url:
            kwargs["base_url"] = cfg.openai_base_url
        return OpenAIEmbeddings(**kwargs)

    if cfg.provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=cfg.hf_model_name)

    raise ValueError(f"Unknown embedding provider: {cfg.provider}")
