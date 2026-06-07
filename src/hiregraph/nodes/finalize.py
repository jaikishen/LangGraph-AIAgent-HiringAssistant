from hiregraph.state import HireGraphState


def finalize(state: HireGraphState) -> dict:
    """Terminal node: append a final summary line to the audit trail before END."""
    candidate_id = state.get("candidate_id", "unknown")
    final_score = state.get("final_score")
    recommendation = state.get("recommendation")
    sent_status = state.get("sent_status")

    return {
        "audit_trail": [
            f"finalize: {candidate_id} | score={final_score} | rec={recommendation} | sent={sent_status}"
        ]
    }
