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
}, {"configurable": {"thread_id": "test-band3"}})


print(result["classification"])

print("\n=== REQUIRED SKILLS ===")
for s in result["required_skills"] or []:
    print(f"  - {s.name} (required_years={s.required_years})")
   

print("\n=== SKILL SCORES (operator.add reducer merges all 4 workers) ===")
for s in result.get("skill_scores", []):
    print(f"  {s.skill}: {s.score}/100")
    print(f"  Skill: {s.skill}")
    print(f"  Score: {s.score}")
    print(f"  Evidence: {s.evidence}")  

print("\n=== FIXED SCORERS ===")
print(f"  experience_score : {result.get('experience_score')}/100")
print(f"  education_score  : {result.get('education_score')}/100")
print(f"  signal_score     : {result.get('signal_score')}/100")

print("\n=== AUDIT TRAIL ===")
for line in result["audit_trail"]:
    print(f"  {line}")
