from typing import Literal
from langgraph.types import Command

from hiregraph.state import HireGraphState, Classification
from hiregraph.llm import get_llm
from hiregraph.prompts import build_classify_prompt


def classify_seniority(state: HireGraphState) -> Command[Literal["plan_required_skills"]]:
    llm = get_llm()
    structured = llm.with_structured_output(Classification)
    classification: Classification = structured.invoke(build_classify_prompt(state))

    return Command(
        update={
            "classification": classification,
            "audit_trail": [
                f"classify: seniority={classification.seniority}, "
                f"role={classification.role_family}, "
                f"confidence={classification.confidence:.2f}"
            ],
        },
        goto="plan_required_skills",
    )
