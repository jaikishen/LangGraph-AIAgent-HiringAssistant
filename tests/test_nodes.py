"""Unit tests for individual HireGraph nodes."""
from __future__ import annotations
import os
os.environ["HIREGRAPH_USE_MOCKS"] = "true"

import pytest
from pathlib import Path
from hiregraph.state import Classification, SkillScore, CriticFeedback
from hiregraph.llm import _MockCriticLLM

RESUMES = Path("sample_data/resumes")
JDS     = Path("sample_data/jds")


def _base_state(**overrides):
    state = {
        "candidate_id": "test_001",
        "resume_text": (RESUMES / "resume_priya.md").read_text(encoding="utf-8"),
        "jd_text": (JDS / "jd_senior_backend.md").read_text(encoding="utf-8"),
        "classification": Classification(seniority="senior", role_family="backend", confidence=0.92),
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
    state.update(overrides)
    return state


# --- ingest ---

def test_ingest_preserves_inputs():
    from hiregraph.nodes.ingest import ingest
    state = _base_state()
    result = ingest(state)
    # ingest returns a plain dict with audit_trail; original text already in state
    assert any("ingest" in line for line in result["audit_trail"])


def test_ingest_returns_audit_trail():
    from hiregraph.nodes.ingest import ingest
    state = _base_state()
    result = ingest(state)
    assert "audit_trail" in result
    assert len(result["audit_trail"]) >= 1


# --- classify_seniority ---

def test_classify_seniority_priya():
    from hiregraph.nodes.classify_seniority import classify_seniority
    state = _base_state()
    cmd = classify_seniority(state)
    # classify_seniority returns a Command
    classification = cmd.update["classification"]
    assert classification.seniority == "senior"
    assert classification.role_family == "backend"
    assert 0 < classification.confidence <= 1.0


# --- draft_email ---

def test_draft_email_increments_attempts():
    from hiregraph.nodes.draft_email import draft_email
    state = _base_state(draft_attempts=0, email_draft=None,
                        recommendation="advance", final_score=80)
    cmd = draft_email(state)
    assert cmd.update["draft_attempts"] == 1
    assert cmd.update["email_draft"] is not None
    assert cmd.goto == "critic_loop"


def test_draft_email_increments_on_retry():
    from hiregraph.nodes.draft_email import draft_email
    state = _base_state(draft_attempts=1, email_draft="old draft",
                        recommendation="advance", final_score=80)
    cmd = draft_email(state)
    assert cmd.update["draft_attempts"] == 2


# --- critic_loop ---

def test_critic_loop_first_call_rejects():
    _MockCriticLLM._instances.clear()
    from hiregraph.nodes.critic_loop import critic_loop
    state = _base_state(
        email_draft="Dear Candidate, we'd like to proceed with your application.",
        draft_attempts=1,
        recommendation="advance",
    )
    cmd = critic_loop(state)
    feedback_list = cmd.update.get("critic_history", [])
    assert len(feedback_list) == 1
    assert feedback_list[0].approved is False
    assert cmd.goto == "draft_email"


def test_critic_loop_second_call_approves():
    _MockCriticLLM._instances.clear()
    _MockCriticLLM._instances["default"] = 1  # simulate one call already done
    from hiregraph.nodes.critic_loop import critic_loop
    state = _base_state(
        email_draft="Dear Candidate, we'd like to proceed with your application.",
        draft_attempts=2,
        recommendation="advance",
    )
    cmd = critic_loop(state)
    feedback_list = cmd.update.get("critic_history", [])
    assert len(feedback_list) == 1
    assert feedback_list[0].approved is True
    assert cmd.goto == "send_email"


# --- aggregate_scores ---

def test_aggregate_advance_path():
    from hiregraph.nodes.aggregate_scores import aggregate_scores
    state = _base_state(
        skill_scores=[SkillScore(skill="Python", score=90, evidence="10 yrs")],
        experience_score=85, education_score=80, signal_score=78,
    )
    cmd = aggregate_scores(state)
    assert cmd.update["final_score"] >= 75
    assert cmd.update["recommendation"] == "advance"
    assert cmd.goto == "advance_path"


def test_aggregate_reject_path():
    from hiregraph.nodes.aggregate_scores import aggregate_scores
    state = _base_state(
        skill_scores=[SkillScore(skill="Python", score=20, evidence="no match")],
        experience_score=25, education_score=30, signal_score=20,
    )
    cmd = aggregate_scores(state)
    assert cmd.update["final_score"] < 50
    assert cmd.update["recommendation"] == "reject"
    assert cmd.goto == "reject_path"


def test_aggregate_borderline_path():
    from hiregraph.nodes.aggregate_scores import aggregate_scores
    state = _base_state(
        skill_scores=[SkillScore(skill="Python", score=60, evidence="ok")],
        experience_score=60, education_score=65, signal_score=55,
    )
    cmd = aggregate_scores(state)
    score = cmd.update["final_score"]
    assert 50 <= score < 75
    assert cmd.goto == "borderline_review"


# --- send_email node ---

def test_send_email_node_success():
    from hiregraph.nodes.send_email import send_email
    state = _base_state(
        email_draft="Dear Candidate, congratulations!",
        recommendation="advance",
        final_score=80,
    )
    cmd = send_email(state)
    assert cmd.update["sent_status"] == "sent"
    assert cmd.goto == "update_ats"


# --- compensate ---

def test_compensate_sets_status():
    from hiregraph.nodes.compensate import compensate
    state = _base_state(sent_status="failed")
    cmd = compensate(state)
    assert cmd.update["sent_status"] == "compensated"
    assert cmd.goto == "finalize"
