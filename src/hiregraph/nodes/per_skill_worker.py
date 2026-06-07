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

    lines = str(response.content).strip().splitlines()
    try:
        score = max(0, min(100, int(lines[0].strip())))
    except (ValueError, IndexError):
        score = 50
    evidence = lines[1].strip() if len(lines) > 1 else f"Score: {score}/100"

    skill_score = SkillScore(
        skill=skill_name,
        score=score,
        evidence=evidence,
    )

    return {
        "skill_scores": [skill_score],
        "audit_trail": [f"worker: scored '{skill_name}' = {score}/100"],
    }
