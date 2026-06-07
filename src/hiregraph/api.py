"""FastAPI server for HireGraph."""
from __future__ import annotations
import os, uuid
from pathlib import Path
from typing import Any

# os.environ.setdefault("HIREGRAPH_USE_MOCKS", "true")

from fastapi import FastAPI, HTTPException, BackgroundTasks, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langgraph.types import Command

from hiregraph.parser import extract_text

from hiregraph.graph import compile_graph

app_state: dict[str, Any] = {}   # in-memory store for thread results / interrupt state

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = compile_graph()
    return _graph


app = FastAPI(title="HireGraph API", version="1.0")

STATIC_DIR = Path(__file__).parent.parent.parent / "ui"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR)), name="ui")

@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


class EvaluateRequest(BaseModel):
    candidate_id: str
    resume_text: str
    jd_text: str


class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool
    recommendation_override: str | None = None
    edited_draft: str | None = None


def _blank_state(req: EvaluateRequest) -> dict:
    return {
        "candidate_id":    req.candidate_id,
        "resume_text":     req.resume_text,
        "jd_text":         req.jd_text,
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


def _serialize_result(result: dict) -> dict:
    """Convert Pydantic models in result to plain dicts for JSON."""
    out = dict(result)
    # skill_scores: list[SkillScore]
    if "skill_scores" in out and out["skill_scores"]:
        out["skill_scores"] = [
            {"skill": s.skill, "score": s.score, "evidence": s.evidence}
            for s in out["skill_scores"]
        ]
    # critic_history: list[CriticFeedback]
    if "critic_history" in out and out["critic_history"]:
        out["critic_history"] = [
            {"score": f.score, "feedback": f.feedback, "approved": f.approved}
            for f in out["critic_history"]
        ]
    # classification: Classification pydantic model
    if "classification" in out and out["classification"] is not None:
        c = out["classification"]
        out["classification"] = {"seniority": c.seniority, "role_family": c.role_family, "confidence": c.confidence}
    # required_skills
    if "required_skills" in out and out["required_skills"]:
        out["required_skills"] = [
            {"name": s.name, "required_years": s.required_years}
            for s in out["required_skills"]
        ]
    # drop large fields not useful in API response
    out.pop("resume_text", None)
    out.pop("jd_text", None)
    out.pop("research_messages", None)
    return out


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    """Start a new evaluation. Returns thread_id and result (or interrupt info)."""
    thread_id = f"{req.candidate_id}-{uuid.uuid4().hex[:6]}"
    config    = {"configurable": {"thread_id": thread_id}}
    graph     = get_graph()

    try:
        from langgraph.errors import GraphInterrupt
        has_interrupt_exc = True
    except ImportError:
        has_interrupt_exc = False
        GraphInterrupt = None

    interrupted = False
    interrupt_value = {}
    result = None

    if has_interrupt_exc:
        try:
            result = graph.invoke(_blank_state(req), config)
        except GraphInterrupt as gi:
            interrupted = True
            interrupt_value = gi.args[0][0].value if gi.args else {}
    else:
        result = graph.invoke(_blank_state(req), config)

    if result and "__interrupt__" in result:
        interrupted = True
        iv = result["__interrupt__"]
        interrupt_value = iv[0].value if iv and hasattr(iv[0], "value") else (iv[0] if iv else {})

    app_state[thread_id] = {"interrupted": interrupted, "result": result}

    if interrupted:
        return {
            "thread_id": thread_id,
            "status": "interrupted",
            "interrupt_type": interrupt_value.get("action", "human review required"),
            "interrupt_data": interrupt_value,
        }

    return {
        "thread_id": thread_id,
        "status": "complete",
        "result": _serialize_result(result),
    }


@app.post("/resume")
def resume(req: ResumeRequest):
    """Resume a paused (interrupted) evaluation."""
    graph  = get_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    resume_payload: dict = {"approved": req.approved}
    if req.recommendation_override:
        resume_payload["recommendation_override"] = req.recommendation_override
    if req.edited_draft:
        resume_payload["edited_draft"] = req.edited_draft

    try:
        from langgraph.errors import GraphInterrupt
        has_interrupt_exc = True
    except ImportError:
        has_interrupt_exc = False
        GraphInterrupt = None

    interrupted = False
    interrupt_value = {}
    result = None

    if has_interrupt_exc:
        try:
            result = graph.invoke(Command(resume=resume_payload), config)
        except GraphInterrupt as gi:
            interrupted = True
            interrupt_value = gi.args[0][0].value if gi.args else {}
    else:
        result = graph.invoke(Command(resume=resume_payload), config)

    if result and "__interrupt__" in result:
        interrupted = True
        iv = result["__interrupt__"]
        interrupt_value = iv[0].value if iv and hasattr(iv[0], "value") else (iv[0] if iv else {})

    if interrupted:
        return {
            "thread_id": req.thread_id,
            "status": "interrupted",
            "interrupt_type": interrupt_value.get("action", "human review required"),
            "interrupt_data": interrupt_value,
        }

    return {
        "thread_id": req.thread_id,
        "status": "complete",
        "result": _serialize_result(result),
    }


@app.get("/status/{thread_id}")
def status(thread_id: str):
    """Check the stored state for a thread."""
    if thread_id not in app_state:
        raise HTTPException(status_code=404, detail="Thread not found")
    entry = app_state[thread_id]
    if entry["interrupted"]:
        return {"thread_id": thread_id, "status": "interrupted"}
    result = entry.get("result") or {}
    return {
        "thread_id": thread_id,
        "status": "complete",
        "recommendation": result.get("recommendation"),
        "final_score": result.get("final_score"),
        "sent_status": result.get("sent_status"),
    }


@app.post("/evaluate-file")
async def evaluate_file(
    candidate_id: str = Form(...),
    resume_file: UploadFile = File(None),
    resume_text: str = Form(""),
    jd_file: UploadFile = File(None),
    jd_text: str = Form(""),
):
    """Start evaluation from uploaded files and/or pasted text."""
    resume_str = (
        extract_text(await resume_file.read(), resume_file.filename)
        if resume_file and resume_file.filename
        else resume_text
    )
    jd_str = (
        extract_text(await jd_file.read(), jd_file.filename)
        if jd_file and jd_file.filename
        else jd_text
    )
    if not resume_str.strip() or not jd_str.strip():
        raise HTTPException(400, "Resume and JD are required (upload a file or paste text)")

    req = EvaluateRequest(candidate_id=candidate_id, resume_text=resume_str, jd_text=jd_str)
    return evaluate(req)


@app.get("/health")
def health():
    return {"status": "ok", "service": "hiregraph"}
