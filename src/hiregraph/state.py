import operator
from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field


class Skill(BaseModel):
    name: str
    required_years: int | None = None


class Classification(BaseModel):
    seniority: Literal["junior", "mid", "senior", "executive"]
    role_family: str
    confidence: float


class SkillScore(BaseModel):
    skill: str
    score: int
    evidence: str


class CriticFeedback(BaseModel):
    score: int
    feedback: str = Field(min_length=20)
    approved: bool


class HireGraphState(TypedDict):
    # Inputs
    candidate_id:      str
    resume_text:       str
    jd_text:           str

    # Classification
    classification:    Classification | None

    # Orchestrator plan
    required_skills:   list[Skill] | None

    # Skill workers â€” reducer merges parallel writes
    skill_scores:      Annotated[list[SkillScore], operator.add]

    # Fixed parallel scorers
    experience_score:  int | None
    education_score:   int | None
    signal_score:      int | None

    # Research agent short-term memory
    research_messages: list[dict] | None

    # Aggregate
    final_score:       int | None
    recommendation:    Literal["advance", "reject", "borderline"] | None

    # Drafting + critic
    email_draft:       str | None
    critic_history:    Annotated[list[CriticFeedback], operator.add]
    draft_attempts:    int

    # Saga
    sent_status:       Literal["sent", "failed", "compensated", "pending"] | None

    # Audit â€” every node appends one line
    audit_trail:       Annotated[list[str], operator.add]
