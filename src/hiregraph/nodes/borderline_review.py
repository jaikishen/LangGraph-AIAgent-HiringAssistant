from __future__ import annotations
from typing import Literal
from langgraph.types import Command, interrupt

from hiregraph.state import HireGraphState


def borderline_review(state: HireGraphState) -> Command[Literal["draft_email"]]:
    decision = interrupt({
        "candidate_id": state.get("candidate_id"),
        "final_score": state.get("final_score"),
        "recommendation": state.get("recommendation"),
        "skill_scores": [
            {"skill": s.skill, "score": s.score, "evidence": s.evidence}
            for s in (state.get("skill_scores") or [])
        ],
        "audit_trail": state.get("audit_trail") or [],
        "action": "Review candidate scorecard. Approve to advance, reject to send rejection email.",
    })

    if decision.get("approved"):
        update = {"audit_trail": ["borderline_review: human approved — drafting advance email"]}
        override = decision.get("recommendation_override")
        if override:
            update["recommendation"] = override
    else:
        update = {
            "recommendation": "reject",
            "audit_trail": ["borderline_review: human rejected — drafting rejection email"],
        }

    return Command(update=update, goto="draft_email")
