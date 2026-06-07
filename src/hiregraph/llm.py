from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from hiregraph.config import get_settings
from hiregraph.state import Classification, CriticFeedback, Skill


@dataclass
class _MockResponse:
    content: str
    tool_calls: list = field(default_factory=list)


class _MockClassificationLLM:
    def invoke(self, prompt: Any) -> Classification:
        text = str(prompt).lower()
        if any(k in text for k in ["8 years", "staff", "senior backend", "pelican"]):
            return Classification(seniority="senior", role_family="backend", confidence=0.92)
        if any(k in text for k in ["3 years", "mid", "eitan", "intermediate"]):
            return Classification(seniority="mid", role_family="backend", confidence=0.71)
        if any(k in text for k in ["frontend", "react", "mira", "css"]):
            return Classification(seniority="senior", role_family="frontend", confidence=0.88)
        return Classification(seniority="mid", role_family="backend", confidence=0.60)


class _MockCriticLLM:
    _instances: dict = {}

    def __init__(self, key: str = "default"):
        self._key = key
        if key not in _MockCriticLLM._instances:
            _MockCriticLLM._instances[key] = 0

    def invoke(self, prompt: Any) -> CriticFeedback:
        _MockCriticLLM._instances[self._key] += 1
        count = _MockCriticLLM._instances[self._key]
        if count == 1:
            return CriticFeedback(
                score=58,
                feedback="Opening paragraph is too generic. Mention the candidate's specific project achievements.",
                approved=False,
            )
        return CriticFeedback(
            score=86,
            feedback="Well-personalised and professional. Clearly references specific experience from the resume.",
            approved=True,
        )


class _MockSkillPlanLLM:
    def invoke(self, prompt: Any):
        class _SkillPlanResponse:
            skills = [
                Skill(name="Python", required_years=5),
                Skill(name="Kafka", required_years=None),
                Skill(name="PostgreSQL", required_years=None),
                Skill(name="distributed systems", required_years=None),
            ]
        return _SkillPlanResponse()


class _MockBoundAgentLLM:
    """Returns a score without calling any tools (mock mode)."""

    def invoke(self, messages: Any) -> _MockResponse:
        return _MockResponse(content="78")


class MockLLM:
    """Deterministic stand-in for ChatOpenAI. Runs end to end with no API key."""

    def invoke(self, prompt: Any) -> _MockResponse:
        text = str(prompt).lower()

        # Detect candidate from resume content in prompt
        is_mira  = any(k in text for k in ["ui/ux", "css", "figma", "react native", "sketch", "mira"])
        is_eitan = any(k in text for k in ["eitan", "3 years", "entry-level"])
        is_priya = any(k in text for k in ["pelican", "8 years", "staff backend", "priya"])

        if any(k in text for k in ["draft", "write an email", "compose"]):
            return _MockResponse(content=(
                "Dear Candidate,\n\n"
                "Thank you for your application. After carefully reviewing your background "
                "in distributed systems and your contributions to open-source Python projects, "
                "we are pleased to move forward with your application.\n\n"
                "Best regards,\nHiring Team"
            ))
        if "educational background" in text:
            return _MockResponse(content="30" if is_mira else "65" if is_eitan else "70")
        if "experience" in text and "score" in text:
            return _MockResponse(content="25" if is_mira else "60" if is_eitan else "82")
        if "signal" in text or "github" in text:
            return _MockResponse(content="20" if is_mira else "55" if is_eitan else "80")
        # Default — skill scoring
        return _MockResponse(content="20" if is_mira else "58" if is_eitan else "82")

    def with_structured_output(self, schema):
        name = getattr(schema, "__name__", "")
        if name == "Classification":
            return _MockClassificationLLM()
        if name == "CriticFeedback":
            return _MockCriticLLM()
        if name == "SkillPlan":
            return _MockSkillPlanLLM()
        return _MockClassificationLLM()

    def bind_tools(self, tools):
        return _MockBoundAgentLLM()


def get_llm():
    settings = get_settings()
    if settings.use_mocks or not settings.openai_api_key:
        return MockLLM()
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=settings.model_name)
