from __future__ import annotations
from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def reject_path(state: HireGraphState) -> Command[Literal["draft_email"]]:
    # Rejected candidates still receive a polite rejection email.
    # The recommendation field ("reject") controls the tone in draft_email.
    return Command(
        update={"audit_trail": ["reject_path: candidate rejected — drafting rejection email"]},
        goto="draft_email",
    )
