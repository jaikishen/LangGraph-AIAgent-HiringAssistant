"""HireGraph demo -- three candidate scenarios."""
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("HIREGRAPH_USE_MOCKS", "true")
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure stdout can handle Unicode on Windows (cp1252 consoles reject arrows/dashes)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from hiregraph.graph import compile_graph
from hiregraph.state import HireGraphState
from langgraph.types import Command
try:
    from langgraph.errors import GraphInterrupt
except ImportError:
    GraphInterrupt = None


RESUMES = Path(__file__).parent.parent.parent / "sample_data" / "resumes"
JDS     = Path(__file__).parent.parent.parent / "sample_data" / "jds"


def _blank_state(candidate_id: str, resume_file: str, jd_file: str) -> dict:
    return {
        "candidate_id":    candidate_id,
        "resume_text":     (RESUMES / resume_file).read_text(encoding="utf-8"),
        "jd_text":         (JDS / jd_file).read_text(encoding="utf-8"),
        "classification":  None,
        "required_skills": None,
        "skill_scores":    [],
        "experience_score": None,
        "education_score":  None,
        "signal_score":     None,
        "research_messages": None,
        "final_score":      None,
        "recommendation":   None,
        "email_draft":      None,
        "critic_history":   [],
        "draft_attempts":   0,
        "sent_status":      None,
        "audit_trail":      [],
    }


def _print_scoreboard(label: str, result: dict) -> None:
    rec   = result.get("recommendation", "?")
    score = result.get("final_score", "?")
    sent  = result.get("sent_status", "?")
    skill_scores = result.get("skill_scores") or []
    critic_rounds = len(result.get("critic_history") or [])

    rec_tag = {"advance": "[ADVANCE]", "reject": "[REJECT]", "borderline": "[BORDERLINE]"}.get(rec, "[?]")

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Final score    : {score}/100")
    print(f"  Recommendation : {rec_tag} {rec}")
    print(f"  Email status   : {sent}")
    print(f"  Critic rounds  : {critic_rounds}")

    if skill_scores:
        print(f"\n  Skill Scores:")
        for s in skill_scores:
            print(f"    {s.skill:<22} {s.score:>3}/100")

    exp = result.get("experience_score")
    edu = result.get("education_score")
    sig = result.get("signal_score")
    if any(v is not None for v in [exp, edu, sig]):
        print(f"\n  Component Scores:")
        print(f"    Experience  : {exp}")
        print(f"    Education   : {edu}")
        print(f"    Signal      : {sig}")

    print(f"\n  Audit trail ({len(result.get('audit_trail') or [])} entries):")
    for line in (result.get("audit_trail") or []):
        print(f"    - {line}")


def run_priya(app) -> None:
    """Scenario 1: Strong candidate -- advance."""
    print("\n>>> SCENARIO 1: Priya (senior backend -- expect ADVANCE)")
    config = {"configurable": {"thread_id": "priya-main-demo"}}
    state  = _blank_state("priya_001", "resume_priya.md", "jd_senior_backend.md")
    result = app.invoke(state, config)
    _print_scoreboard("Priya Ramachandran - Senior Backend Engineer", result)


def run_mira(app) -> None:
    """Scenario 2: Weak/mismatched candidate -- reject."""
    print("\n>>> SCENARIO 2: Mira (frontend/UX -- expect REJECT)")
    config = {"configurable": {"thread_id": "mira-main-demo"}}
    state  = _blank_state("mira_001", "resume_mira.md", "jd_junior_data.md")
    result = app.invoke(state, config)
    _print_scoreboard("Mira Cohen - Frontend / UX Designer", result)


def run_eitan(app) -> None:
    """Scenario 3: Borderline candidate -- human interrupt -- resume."""
    print("\n>>> SCENARIO 3: Eitan (mid-level -- expect BORDERLINE + human interrupt)")
    config = {"configurable": {"thread_id": "eitan-main-demo"}}
    state  = _blank_state("eitan_001", "resume_eitan.md", "jd_senior_backend.md")

    result = None

    # Run until interrupt
    interrupted = False
    interrupt_value = {}

    if GraphInterrupt is not None:
        try:
            result = app.invoke(state, config)
        except GraphInterrupt as gi:
            interrupted = True
            interrupt_value = gi.args[0][0].value if gi.args else {}
    else:
        result = app.invoke(state, config)

    # Check for interrupt in result dict (LangGraph >= 0.2 style)
    if result is not None and isinstance(result, dict) and "__interrupt__" in result:
        interrupted = True
        interrupts = result["__interrupt__"]
        if interrupts:
            interrupt_value = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]

    if interrupted:
        score = interrupt_value.get("final_score", "?")
        print(f"\n  [** INTERRUPT **] borderline_review fired -- score={score}")
        print(f"  Human decision: APPROVE (override recommendation -> advance)")
        result = app.invoke(
            Command(resume={"approved": True, "recommendation_override": "advance"}),
            config,
        )

    # critic_loop may also interrupt (human_review) -- auto-approve for demo
    if result is not None and isinstance(result, dict) and "__interrupt__" in result:
        print(f"\n  [** INTERRUPT **] human_review fired after critic exhaustion -- auto-approving")
        result = app.invoke(Command(resume={"approved": True}), config)

    if result:
        _print_scoreboard("Eitan Schreiber - Mid-Level Backend Developer", result)


def main() -> None:
    print("=" * 52)
    print("          HireGraph -- Hiring Assistant")
    print("    LangGraph - All 13 patterns demonstrated")
    print("=" * 52)

    app = compile_graph()

    run_priya(app)
    run_mira(app)
    run_eitan(app)

    print("\n" + "="*60)
    print("  All three scenarios complete.")
    print("="*60)


if __name__ == "__main__":
    main()
