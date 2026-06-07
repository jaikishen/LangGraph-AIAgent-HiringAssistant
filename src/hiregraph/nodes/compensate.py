from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def compensate(state: HireGraphState) -> Command[Literal["finalize"]]:
    candidate_id = state.get("candidate_id", "unknown")
    sent_status = state.get("sent_status") or "failed"

    return Command(
        update={
            "sent_status": "compensated",
            "audit_trail": [
                f"compensate: saga rolled back for {candidate_id} (was: {sent_status})"
            ],
        },
        goto="finalize",
    )
