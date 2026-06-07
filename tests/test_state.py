from hiregraph.state import (
    HireGraphState, Classification, Skill, SkillScore, CriticFeedback
)


def test_classification_fields():
    c = Classification(seniority="senior", role_family="backend", confidence=0.9)
    assert c.seniority == "senior"
    assert c.confidence == 0.9


def test_skill_optional_years():
    s = Skill(name="Python", required_years=5)
    assert s.required_years == 5
    s2 = Skill(name="Kafka")
    assert s2.required_years is None


def test_critic_feedback_min_length():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CriticFeedback(score=80, feedback="too short", approved=True)


def test_hire_graph_state_structure():
    state: HireGraphState = {
        "candidate_id": "test_001",
        "resume_text": "Sample resume",
        "jd_text": "Sample JD",
        "classification": None,
        "required_skills": None,
        "skill_scores": [],
        "experience_score": None,
        "education_score": None,
        "signal_score": None,
        "research_messages": None,
        "final_score": None,
        "recommendation": None,
        "email_draft": None,
        "critic_history": [],
        "draft_attempts": 0,
        "sent_status": None,
        "audit_trail": [],
    }
    assert state["candidate_id"] == "test_001"
    assert state["skill_scores"] == []
    assert state["draft_attempts"] == 0
