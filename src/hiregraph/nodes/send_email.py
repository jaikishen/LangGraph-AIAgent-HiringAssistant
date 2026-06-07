from __future__ import annotations
from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState
import hiregraph.services as svc


def send_email(state: HireGraphState) -> Command[Literal["update_ats", "compensate"]]:
    candidate_id = state.get("candidate_id", "unknown")
    recommendation = state.get("recommendation") or "advance"
    draft = state.get("email_draft") or "(no draft)"

    subject = (
        "Your Application — Next Steps"
        if recommendation == "advance"
        else "Thank you for applying"
    )

    # candidate_email: use a placeholder since we don't collect it from resumes
    to = f"{candidate_id}@candidates.example.com"

    try:
        svc.send_email(to=to, subject=subject, body=draft)
        return Command(
            update={
                "sent_status": "sent",
                "audit_trail": [f"send_email: sent to {to}, subject={subject!r}"],
            },
            goto="update_ats",
        )
    except svc.EmailSendError as exc:
        return Command(
            update={
                "sent_status": "failed",
                "audit_trail": [f"send_email: FAILED — {exc}"],
            },
            goto="compensate",
        )
