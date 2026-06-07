from typing import Literal
from pydantic import ValidationError
from langgraph.types import Command

from hiregraph.state import HireGraphState, CriticFeedback
from hiregraph.llm import get_llm
from hiregraph.prompts import build_critic_prompt

MAX_ATTEMPTS = 3
PASS_THRESHOLD = 70


def critic_loop(state: HireGraphState) -> Command[Literal["draft_email", "human_review", "send_email"]]:
    """Evaluator-optimizer: grade the email draft and loop back to draft_email or escalate to human_review."""
    attempts = state.get("draft_attempts") or 1
    llm = get_llm()
    structured = llm.with_structured_output(CriticFeedback)

    try:
        feedback: CriticFeedback = structured.invoke(build_critic_prompt(state))
    except (ValidationError, Exception) as exc:
        if attempts >= MAX_ATTEMPTS:
            return Command(
                update={"audit_trail": [f"critic_loop: parse error on attempt {attempts}, escalating â€” {exc}"]},
                goto="human_review",
            )
        return Command(
            update={"audit_trail": [f"critic_loop: parse error on attempt {attempts}, retrying â€” {exc}"]},
            goto="draft_email",
        )

    update = {
        "critic_history": [feedback],
        "audit_trail": [f"critic_loop: attempt {attempts}, score={feedback.score}, approved={feedback.approved}"],
    }

    if feedback.approved or feedback.score >= PASS_THRESHOLD:
        return Command(update=update, goto="send_email")

    if attempts >= MAX_ATTEMPTS:
        return Command(update=update, goto="human_review")

    return Command(update=update, goto="draft_email")
