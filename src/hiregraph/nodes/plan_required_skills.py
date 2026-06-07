from typing import Literal
from langgraph.types import Command, Send
from pydantic import BaseModel

from hiregraph.state import HireGraphState, Skill
from hiregraph.llm import get_llm
from hiregraph.prompts import build_skill_plan_prompt


class SkillPlan(BaseModel):
    skills: list[Skill]


def plan_required_skills(state: HireGraphState) -> Command:
    llm = get_llm()
    structured = llm.with_structured_output(SkillPlan)
    plan: SkillPlan = structured.invoke(build_skill_plan_prompt(state))
    skills = plan.skills or []

    audit = [f"plan: extracted {len(skills)} skills â€” {[s.name for s in skills]}"]

    if not skills:
        return Command(
            update={"required_skills": [], "audit_trail": audit},
            goto=["experience_scorer", "education_scorer", "signal_scorer"],
        )

    return Command(
        update={"required_skills": skills, "audit_trail": audit},
        goto=[
            Send("per_skill_worker", {
                "skill": skill,
                "resume_text": state["resume_text"],
                "jd_text": state["jd_text"],
                "candidate_id": state["candidate_id"],
            })
            for skill in skills
        ],
    )
