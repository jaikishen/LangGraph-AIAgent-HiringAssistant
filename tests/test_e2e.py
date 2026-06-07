"""End-to-end graph tests — all three candidate scenarios."""
from __future__ import annotations
import os
os.environ["HIREGRAPH_USE_MOCKS"] = "true"

import pytest
from pathlib import Path
from hiregraph.graph import compile_graph
from hiregraph.llm import _MockCriticLLM
from langgraph.types import Command

RESUMES = Path("sample_data/resumes")
JDS     = Path("sample_data/jds")


def _blank(candidate_id, resume_file, jd_file):
    return {
        "candidate_id":    candidate_id,
        "resume_text":     (RESUMES / resume_file).read_text(encoding="utf-8"),
        "jd_text":         (JDS / jd_file).read_text(encoding="utf-8"),
        "classification":  None, "required_skills": None,
        "skill_scores":    [], "experience_score": None,
        "education_score": None, "signal_score": None,
        "research_messages": None, "final_score": None,
        "recommendation":  None, "email_draft": None,
        "critic_history":  [], "draft_attempts": 0,
        "sent_status":     None, "audit_trail": [],
    }


@pytest.fixture
def app():
    _MockCriticLLM._instances.clear()
    return compile_graph()


# --- Priya: advance path ---

def test_e2e_priya_advance(app):
    config = {"configurable": {"thread_id": "priya-e2e"}}
    result = app.invoke(_blank("priya_e2e", "resume_priya.md", "jd_senior_backend.md"), config)
    assert result["recommendation"] == "advance"
    assert result["final_score"] >= 75
    assert result["sent_status"] == "sent"
    assert len(result["skill_scores"]) > 0
    assert len(result["audit_trail"]) > 0


# --- Mira: reject path ---

def test_e2e_mira_reject(app):
    config = {"configurable": {"thread_id": "mira-e2e"}}
    result = app.invoke(_blank("mira_e2e", "resume_mira.md", "jd_junior_data.md"), config)
    assert result["recommendation"] == "reject"
    assert result["final_score"] < 50
    assert result["sent_status"] == "sent"


# --- Eitan: borderline interrupt/resume ---

def test_e2e_eitan_borderline_interrupt_resume(app):
    config = {"configurable": {"thread_id": "eitan-e2e"}}
    state  = _blank("eitan_e2e", "resume_eitan.md", "jd_senior_backend.md")

    interrupted = False
    result = None

    try:
        from langgraph.errors import GraphInterrupt
        try:
            result = app.invoke(state, config)
        except GraphInterrupt:
            interrupted = True
    except ImportError:
        result = app.invoke(state, config)

    if result and "__interrupt__" in result:
        interrupted = True

    assert interrupted, "Expected borderline_review interrupt for Eitan"

    # Resume with approval
    result = app.invoke(Command(resume={"approved": True, "recommendation_override": "advance"}), config)

    # Handle possible second interrupt (human_review after critic exhaustion)
    if result and "__interrupt__" in result:
        result = app.invoke(Command(resume={"approved": True}), config)

    assert result["sent_status"] == "sent"
    assert result["final_score"] is not None
    # After human approved with override, recommendation should be advance
    assert result["recommendation"] == "advance"


# --- Audit trail completeness ---

def test_e2e_audit_trail_populated(app):
    _MockCriticLLM._instances.clear()
    config = {"configurable": {"thread_id": "priya-audit-e2e"}}
    result = app.invoke(_blank("priya_audit", "resume_priya.md", "jd_senior_backend.md"), config)
    trail = result.get("audit_trail", [])
    assert len(trail) >= 5, f"Expected >=5 audit entries, got {len(trail)}: {trail}"
    node_names = {"ingest", "classify", "plan", "aggregate", "draft_email", "critic_loop", "send_email", "finalize"}
    found = {entry.split(":")[0] for entry in trail}
    assert found & node_names, f"No expected node names in audit trail: {found}"
