from __future__ import annotations
from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState
import hiregraph.services as svc


def update_ats(state: HireGraphState) -> Command[Literal["finalize", "compensate"]]:
    candidate_id = state.get("candidate_id", "unknown")
    recommendation = state.get("recommendation") or "advance"

    try:
        record_id = svc.update_ats(candidate_id=candidate_id, recommendation=recommendation)
        return Command(
            update={"audit_trail": [f"update_ats: logged {candidate_id} -> {recommendation} as {record_id}"]},
            goto="finalize",
        )
    except svc.ATSUpdateError as exc:
        return Command(
            update={
                "sent_status": "compensated",
                "audit_trail": [f"update_ats: FAILED — {exc}"],
            },
            goto="compensate",
        )
