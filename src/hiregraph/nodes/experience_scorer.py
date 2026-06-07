from hiregraph.state import HireGraphState
from hiregraph.llm import get_llm
from hiregraph.prompts import build_experience_prompt


def experience_scorer(state: HireGraphState) -> dict:
    llm = get_llm()
    response = llm.invoke(build_experience_prompt(state))
    try:
        score = int(str(response.content).strip().split()[0])
        score = max(0, min(100, score))
    except (ValueError, IndexError):
        score = 60
    return {
        "experience_score": score,
        "audit_trail": [f"experience_scorer: {score}/100"],
    }
