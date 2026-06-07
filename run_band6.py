import os, sys
os.environ["HIREGRAPH_USE_MOCKS"] = "true"
sys.path.insert(0, "src")

from pathlib import Path
from hiregraph.graph import compile_graph

app = compile_graph()

result = app.invoke({
    "candidate_id": "priya_001",
    "resume_text": Path("sample_data/resumes/resume_priya.md").read_text(),
    "jd_text": Path("sample_data/jds/jd_senior_backend.md").read_text(),
    "classification": None, "required_skills": None, "skill_scores": [],
    "experience_score": None, "education_score": None, "signal_score": None,
    "research_messages": None, "final_score": None, "recommendation": None,
    "email_draft": None, "critic_history": [], "draft_attempts": 0,
    "sent_status": None, "audit_trail": [],
}, {"configurable": {"thread_id": "priya-band6"}})

print("=== DRAFT EMAIL ===")
print(result.get("email_draft", "(none)")[:300])

print("\n=== CRITIC HISTORY ===")
for i, f in enumerate(result.get("critic_history", []), 1):
    print(f"  Round {i}: score={f.score}, approved={f.approved}")
    print(f"    feedback: {f.feedback[:80]}")

print(f"\n=== SUMMARY ===")
print(f"  draft_attempts : {result.get('draft_attempts')}")
print(f"  recommendation : {result.get('recommendation')}")
print(f"  final_score    : {result.get('final_score')}")

print("\n=== AUDIT TRAIL (critic-related) ===")
for line in result.get("audit_trail", []):
    if any(k in line for k in ["draft_email", "critic_loop"]):
        print(f"  {line}")
