from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import RetryPolicy

from hiregraph.state import HireGraphState
from hiregraph.services import EmailSendError, ATSUpdateError
from hiregraph.nodes import (
    ingest, classify_seniority, plan_required_skills, per_skill_worker,
    experience_scorer, education_scorer, signal_scorer,
    aggregate_scores, advance_path, reject_path, borderline_review,
    draft_email, critic_loop, human_review,
    send_email, update_ats, compensate, finalize,
)


def build_graph() -> StateGraph:
    workflow = StateGraph(HireGraphState)

    workflow.add_node("ingest", ingest)
    workflow.add_node("classify_seniority", classify_seniority)
    workflow.add_node("plan_required_skills", plan_required_skills)
    workflow.add_node("per_skill_worker", per_skill_worker)
    workflow.add_node("experience_scorer", experience_scorer)
    workflow.add_node("education_scorer", education_scorer)
    workflow.add_node("signal_scorer", signal_scorer)
    workflow.add_node("aggregate_scores", aggregate_scores)
    workflow.add_node("advance_path", advance_path)
    workflow.add_node("reject_path", reject_path)
    workflow.add_node("borderline_review", borderline_review)
    workflow.add_node("draft_email", draft_email)
    workflow.add_node("critic_loop", critic_loop)
    workflow.add_node("human_review", human_review)
    workflow.add_node("send_email", send_email, retry_policy=RetryPolicy(max_attempts=3, retry_on=(EmailSendError,)))
    workflow.add_node("update_ats", update_ats, retry_policy=RetryPolicy(max_attempts=2, retry_on=(ATSUpdateError,)))
    workflow.add_node("compensate", compensate)
    workflow.add_node("finalize", finalize)

    # Band 1 - linear
    workflow.add_edge(START, "ingest")
    workflow.add_edge("ingest", "classify_seniority")
    workflow.add_edge("classify_seniority", "plan_required_skills")

    # Band 2->3: per_skill_worker fans out to all three parallel scorers
    workflow.add_edge("per_skill_worker", "experience_scorer")
    workflow.add_edge("per_skill_worker", "education_scorer")
    workflow.add_edge("per_skill_worker", "signal_scorer")

    # Band 3 fan-in to aggregate
    workflow.add_edge("experience_scorer", "aggregate_scores")
    workflow.add_edge("education_scorer", "aggregate_scores")
    workflow.add_edge("signal_scorer", "aggregate_scores")

    # Band 5 static edges
    # NOTE: draft_email uses Command(goto="critic_loop") - no static edge needed
    workflow.add_edge("finalize", END)

    return workflow


def compile_graph(checkpointer=None):
    workflow = build_graph()
    return workflow.compile(
        checkpointer=checkpointer or MemorySaver(serde=JsonPlusSerializer())
    )
