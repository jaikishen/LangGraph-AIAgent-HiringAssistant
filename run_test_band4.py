import os, sys
os.environ["HIREGRAPH_USE_MOCKS"] = "true"
sys.path.insert(0, "src")

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from hiregraph.graph import compile_graph

app = compile_graph()

def run(label, resume_file, jd_file, thread_id):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = app.invoke({
        "candidate_id": thread_id,
        "resume_text": Path(f"sample_data/resumes/{resume_file}").read_text(),
        "jd_text": Path(f"sample_data/jds/{jd_file}").read_text(),
        "classification": None, "required_skills": None, "skill_scores": [],
        "experience_score": None, "education_score": None, "signal_score": None,
        "research_messages": None, "final_score": None, "recommendation": None,
        "email_draft": None, "critic_history": [], "draft_attempts": 0,
        "sent_status": None, "audit_trail": [],
    }, {"configurable": {"thread_id": thread_id}})

    print(f"  final_score    : {result.get('final_score')}/100")
    print(f"  recommendation : {result.get('recommendation')}")
    print(f"  interrupted    : {'yes' if result.get('__interrupt__') else 'no'}")
    print("\n  Audit trail:")
    for line in result.get("audit_trail", []):
        print(f"    {line}")
    return result

run("Priya — strong candidate (expect: advance)", "resume_priya.md", "jd_senior_backend.md", "priya-band4")
run("Mira — weak candidate (expect: reject)",    "resume_mira.md",  "jd_senior_backend.md", "mira-band4")
