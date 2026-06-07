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
}, {"configurable": {"thread_id": "priya-band7"}})

print("=== SAGA RESULTS ===")
print(f"  sent_status    : {result.get('sent_status')}")
print(f"  recommendation : {result.get('recommendation')}")
print(f"  final_score    : {result.get('final_score')}")

print("\n=== AUDIT TRAIL (saga nodes) ===")
for line in result.get("audit_trail", []):
    if any(k in line for k in ["send_email", "update_ats", "compensate", "finalize"]):
        print(f"  {line}")

print("\n=== FULL AUDIT TRAIL ===")
for line in result.get("audit_trail", []):
    print(f"  {line}")
