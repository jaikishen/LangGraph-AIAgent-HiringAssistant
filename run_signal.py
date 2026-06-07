"""
Test the signal_scorer research agent in isolation.
Uses real OpenAI + Tavily APIs (HIREGRAPH_USE_MOCKS must be false/unset).
"""
import sys
sys.path.insert(0, "src")

from pathlib import Path
from hiregraph.nodes.signal_scorer import signal_scorer
from hiregraph.state import Classification

state = {
    "candidate_id": "priya_001",
    "resume_text": Path("sample_data/resumes/resume_priya.md").read_text(),
    "jd_text": Path("sample_data/jds/jd_senior_backend.md").read_text(),
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


print("Running signal_scorer (real APIs)...\n")
result = signal_scorer(state)

print(f"\n=== SIGNAL SCORE: {result['signal_score']}/100 ===")

print("\n=== AUDIT TRAIL ===")
for line in result["audit_trail"]:
    print(f"  {line}")

print("\n=== RESEARCH MESSAGES ===")
for msg in result.get("research_messages", []):
    role = msg["role"].upper()
    content = msg["content"][:200]
    print(f"  [{role}] {content}")
    print()
