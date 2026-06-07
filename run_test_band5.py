import os, sys
os.environ["HIREGRAPH_USE_MOCKS"] = "true"
sys.path.insert(0, "src")

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from langgraph.types import Command
from hiregraph.graph import compile_graph

app = compile_graph()
config = {"configurable": {"thread_id": "eitan-interrupt-test"}}

initial_state = {
    "candidate_id": "eitan_001",
    "resume_text": Path("sample_data/resumes/resume_eitan.md").read_text(),
    "jd_text": Path("sample_data/jds/jd_senior_backend.md").read_text(),
    "classification": None, "required_skills": None, "skill_scores": [],
    "experience_score": None, "education_score": None, "signal_score": None,
    "research_messages": None, "final_score": None, "recommendation": None,
    "email_draft": None, "critic_history": [], "draft_attempts": 0,
    "sent_status": None, "audit_trail": [],
}

print("=== INVOKING GRAPH (expect pause at borderline_review) ===")
result = app.invoke(initial_state, config)

interrupts = result.get("__interrupt__") or []
if interrupts:
    payload = interrupts[0].value
    print(f"\nGRAPH PAUSED at borderline_review")
    print(f"  candidate_id : {payload.get('candidate_id')}")
    print(f"  final_score  : {payload.get('final_score')}")
    print(f"  action       : {payload.get('action')}")
    print(f"\n  Scorecard:")
    for s in payload.get("skill_scores", []):
        print(f"    {s['skill']}: {s['score']}/100")

    print("\n=== RESUMING WITH APPROVAL ===")
    result2 = app.invoke(Command(resume={"approved": True}), config)
    print(f"  recommendation : {result2.get('recommendation')}")
    print(f"  audit_trail (last 3):")
    for line in result2.get("audit_trail", [])[-3:]:
        print(f"    {line}")
else:
    print(f"No interrupt — final_score={result.get('final_score')}, recommendation={result.get('recommendation')}")
    print("(Eitan may have scored outside the borderline range with current mock values)")
    print("\n  Audit trail:")
    for line in result.get("audit_trail", []):
        print(f"    {line}")
