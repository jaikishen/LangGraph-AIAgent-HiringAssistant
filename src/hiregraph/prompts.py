from __future__ import annotations
from hiregraph.state import HireGraphState


def build_classify_prompt(state: HireGraphState) -> str:
    return (
        "Classify this candidate against the job description.\n\n"
        f"Resume:\n{state['resume_text']}\n\n"
        f"Job Description:\n{state['jd_text']}\n\n"
        "Return seniority (junior/mid/senior/executive), role_family (e.g. backend, frontend, data), "
        "and confidence (0.0 to 1.0)."
    )


def build_skill_plan_prompt(state: HireGraphState) -> str:
    role = state["classification"].role_family if state.get("classification") else "unknown"
    return (
        f"Extract the required skills from this job description for a {role} role.\n\n"
        f"Job Description:\n{state['jd_text']}\n\n"
        "Return a list of skills. For each skill include the name and required_years if stated."
    )


def build_skill_score_prompt(state: HireGraphState, skill_name: str) -> str:
    return (
        f"Score the candidate's proficiency in '{skill_name}' from 0 to 100.\n\n"
        f"Resume:\n{state['resume_text']}\n\n"
        "Return a score (int 0-100) and a one-sentence evidence string."
    )


def build_experience_prompt(state: HireGraphState) -> str:
    seniority = state["classification"].seniority if state.get("classification") else "unknown"
    return (
        f"Score the candidate's overall years and quality of experience for a {seniority} role.\n\n"
        f"Resume:\n{state['resume_text']}\n\n"
        "Return a single integer score from 0 to 100."
    )


def build_education_prompt(state: HireGraphState) -> str:
    return (
        "Score the candidate's educational background from 0 to 100.\n\n"
        f"Resume:\n{state['resume_text']}\n\n"
        "Return a single integer score from 0 to 100. "
        "No degree is not a penalty — relevant bootcamps and self-study count."
    )


def build_signal_prompt(state: HireGraphState) -> str:
    return (
        "Research this candidate's public signals (GitHub, writing, talks) and score from 0 to 100.\n\n"
        f"Resume summary:\n{state['resume_text'][:500]}\n\n"
        "Use the available tools to look up their GitHub profile and any public writing. "
        "Return a score from 0 to 100 based on what you find."
    )


def build_draft_prompt(state: HireGraphState) -> str:
    rec = state.get("recommendation") or "unknown"
    score = state.get("final_score") or 0
    skills = state.get("skill_scores") or []
    skill_lines = "\n".join(
        f"  - {s.skill}: {s.score}/100 ({s.evidence})" for s in skills
    ) or "  (none)"

    return (
        f"Draft a professional email to this candidate.\n\n"
        f"Recommendation: {rec}\n"
        f"Overall score: {score}/100\n"
        f"Skill scores:\n{skill_lines}\n\n"
        f"Resume snippet:\n{state['resume_text'][:400]}\n\n"
        "Guidelines: be warm and specific. Reference at least one detail from the resume. "
        "If advancing: express enthusiasm and next steps. "
        "If rejecting: be respectful and encouraging. "
        "If borderline: thank them and explain the decision is pending review."
    )


def build_critic_prompt(state: HireGraphState) -> str:
    return (
        f"Review this candidate email draft and score it from 0 to 100.\n\n"
        f"Draft:\n{state.get('email_draft', '')}\n\n"
        f"Recommendation context: {state.get('recommendation')}\n\n"
        "Criteria: personalisation (does it mention specific resume details?), "
        "tone (professional and warm?), clarity (clear next steps?). "
        "Return score (int), detailed feedback (min 20 chars), and approved (bool, True if score >= 70)."
    )
