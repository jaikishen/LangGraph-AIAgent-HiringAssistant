from __future__ import annotations
from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState
from hiregraph.llm import get_llm
from hiregraph.prompts import build_draft_prompt


def draft_email(state: HireGraphState) -> Command[Literal["critic_loop"]]:
    llm = get_llm()
    response = llm.invoke(build_draft_prompt(state))
    attempts = (state.get("draft_attempts") or 0) + 1

    return Command(
        update={
            "email_draft": response.content,
            "draft_attempts": attempts,
            "audit_trail": [f"draft_email: attempt {attempts}"],
        },
        goto="critic_loop",
    )
