from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def reject_path(state: HireGraphState) -> Command[Literal["draft_email"]]:
    """Route a low-scoring candidate (<50) to rejection email drafting."""
    # Rejected candidates still receive a polite rejection email.
    # The recommendation field ("reject") controls the tone in draft_email.
    return Command(
        update={"audit_trail": ["reject_path: candidate rejected â€” drafting rejection email"]},
        goto="draft_email",
    )
