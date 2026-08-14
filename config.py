import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    llm_mode: str
    search_mode: str
    openai_key: str | None
    anthropic_key: str | None
    tavily_key: str | None


def load_config() -> AgentConfig:
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if openai_key:
        llm_mode = "openai"
    elif anthropic_key:
        llm_mode = "anthropic"
    else:
        llm_mode = "demo"

    search_mode = "tavily" if tavily_key else "wikipedia"

    return AgentConfig(
        llm_mode=llm_mode,
        search_mode=search_mode,
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        tavily_key=tavily_key,
    )


def print_mode_banner(cfg: AgentConfig) -> None:
    print("=" * 60)
    print("RESEARCH AGENT HARNESS -- startup configuration")
    print(f"  LLM reasoning mode : {cfg.llm_mode.upper()}")
    print(f"  Search mode        : {cfg.search_mode.upper()}")
    print("=" * 60)