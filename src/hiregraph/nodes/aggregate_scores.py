from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState


def aggregate_scores(state: HireGraphState) -> Command[Literal["advance_path", "reject_path", "borderline_review"]]:
    """Compute weighted final score and route to advance_path, reject_path, or borderline_review."""
    skill_scores = state.get("skill_scores") or []
    skill_avg = (
        sum(s.score for s in skill_scores) / len(skill_scores)
        if skill_scores else 50
    )
    exp = state.get("experience_score") or 50
    edu = state.get("education_score") or 50
    sig = state.get("signal_score") or 50

    final_score = round(
        (skill_avg * 0.40) + (exp * 0.30) + (edu * 0.15) + (sig * 0.15)
    )

    if final_score >= 75:
        recommendation = "advance"
        goto = "advance_path"
    elif final_score < 50:
        recommendation = "reject"
        goto = "reject_path"
    else:
        recommendation = "borderline"
        goto = "borderline_review"

    return Command(
        update={
            "final_score": final_score,
            "recommendation": recommendation,
            "audit_trail": [
                f"aggregate: skill_avg={skill_avg:.0f}, exp={exp}, edu={edu}, sig={sig} "
                f"-> final={final_score}, recommendation={recommendation}"
            ],
        },
        goto=goto,
    )
