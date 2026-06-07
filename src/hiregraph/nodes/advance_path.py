from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def advance_path(state: HireGraphState) -> Command[Literal["draft_email"]]:
    """Route a high-scoring candidate (>=75) to email drafting."""
    return Command(
        update={"audit_trail": ["advance_path: candidate advancing â€” drafting email"]},
        goto="draft_email",
    )
