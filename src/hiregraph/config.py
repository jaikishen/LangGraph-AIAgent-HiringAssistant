from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model_name: str
    use_mocks: bool
    tavily_api_key: str | None
    github_token: str | None


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        model_name=os.environ.get("HIREGRAPH_MODEL", "gpt-4o-mini"),
        use_mocks=_as_bool(os.environ.get("HIREGRAPH_USE_MOCKS"), default=False),
        tavily_api_key=os.environ.get("TAVILY_API_KEY"),
        github_token=os.environ.get("GITHUB_TOKEN"),
    )
