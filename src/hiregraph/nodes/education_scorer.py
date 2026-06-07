from hiregraph.state import HireGraphState
from hiregraph.llm import get_llm
from hiregraph.prompts import build_education_prompt


def education_scorer(state: HireGraphState) -> dict:
    """Score educational background; runs in parallel with experience and signal scorers."""
    llm = get_llm()
    response = llm.invoke(build_education_prompt(state))
    try:
        score = int(str(response.content).strip().split()[0])
        score = max(0, min(100, score))
    except (ValueError, IndexError):
        score = 60
    return {
        "education_score": score,
        "audit_trail": [f"education_scorer: {score}/100"],
    }
