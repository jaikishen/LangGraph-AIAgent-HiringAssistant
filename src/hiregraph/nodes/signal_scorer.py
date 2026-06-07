from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from hiregraph.state import HireGraphState
from hiregraph.llm import get_llm
from hiregraph.tools import search_web, lookup_github
from hiregraph.prompts import build_signal_prompt

TOOLS = [search_web, lookup_github]
MAX_TOOL_ROUNDS = 5


def signal_scorer(state: HireGraphState) -> dict:
    """Research agent: call Tavily and GitHub tools to score public signals; runs in parallel."""
    llm = get_llm()
    bound_llm = llm.bind_tools(TOOLS)
    tool_map = {t.name: t for t in TOOLS}

    messages = [HumanMessage(content=build_signal_prompt(state))]

    response = None
    for _ in range(MAX_TOOL_ROUNDS):
        response = bound_llm.invoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", []) or []
        if not tool_calls:
            break

        for tc in tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn is None:
                result = f"Unknown tool: {tc['name']}"
            else:
                try:
                    result = tool_fn.invoke(tc["args"])
                except Exception as exc:
                    result = f"Tool returned no data: {type(exc).__name__}"
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    final_content = getattr(response, "content", "") or "" if response else ""
    try:
        score = int(str(final_content).strip().split()[0])
        score = max(0, min(100, score))
    except (ValueError, IndexError):
        score = 65

    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]

    # Serialise messages as dicts for state (checkpointer-safe)
    serialised = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serialised.append({"role": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serialised.append({"role": "ai", "content": m.content or ""})
        elif isinstance(m, ToolMessage):
            serialised.append({"role": "tool", "content": m.content})

    # Audit: summary + one line per tool result
    audit = [f"signal_scorer: score={score}/100, tool_calls={len(tool_messages)}"]
    for tm in tool_messages:
        audit.append(f"  signal_scorer tool result: {tm.content[:100]}")

    return {
        "signal_score": score,
        "research_messages": serialised,
        "audit_trail": audit,
    }
