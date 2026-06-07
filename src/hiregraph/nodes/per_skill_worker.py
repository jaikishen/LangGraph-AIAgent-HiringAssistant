from hiregraph.state import HireGraphState, SkillScore
from hiregraph.llm import get_llm
from hiregraph.prompts import build_skill_score_prompt


def per_skill_worker(state: HireGraphState) -> dict:
    skill = state.get("skill")
    if skill is None:
        return {"audit_trail": ["per_skill_worker: no skill in payload, skipping"]}

    skill_name = skill.name if hasattr(skill, "name") else str(skill)
    llm = get_llm()
    response = llm.invoke(build_skill_score_prompt(state, skill_name))

    try:
        score = int(str(response.content).strip().split()[0])
        score = max(0, min(100, score))
    except (ValueError, IndexError):
        score = 50

    skill_score = SkillScore(
        skill=skill_name,
        score=score,
        evidence=f"Assessed from resume. Score: {score}/100.",
    )

    return {
        "skill_scores": [skill_score],
        "audit_trail": [f"worker: scored '{skill_name}' = {score}/100"],
    }
