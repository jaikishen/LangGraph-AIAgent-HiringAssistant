from __future__ import annotations
from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def advance_path(state: HireGraphState) -> Command[Literal["draft_email"]]:
    return Command(
        update={"audit_trail": ["advance_path: candidate advancing — drafting email"]},
        goto="draft_email",
    )
