from typing import Literal
from langgraph.types import Command, interrupt

from hiregraph.state import HireGraphState


def human_review(state: HireGraphState) -> Command[Literal["send_email", "draft_email"]]:
    decision = interrupt({
        "candidate_id": state.get("candidate_id"),
        "email_draft": state.get("email_draft"),
        "critic_history": [
            {"score": f.score, "feedback": f.feedback, "approved": f.approved}
            for f in (state.get("critic_history") or [])
        ],
        "draft_attempts": state.get("draft_attempts"),
        "action": "Critic loop exhausted. Review draft and approve to send, or reject to redraft.",
    })

    if decision.get("approved"):
        edited = decision.get("edited_draft") or state.get("email_draft", "")
        return Command(
            update={
                "email_draft": edited,
                "audit_trail": ["human_review: human approved email draft"],
            },
            goto="send_email",
        )

    return Command(
        update={"audit_trail": ["human_review: human rejected draft â€” redrafting"]},
        goto="draft_email",
    )
