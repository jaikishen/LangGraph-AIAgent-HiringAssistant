from hiregraph.state import HireGraphState


def ingest(state: HireGraphState) -> dict:
    """Validate and log input sizes; first node in the linear ingestion chain."""
    resume_len = len(state.get("resume_text") or "")
    jd_len = len(state.get("jd_text") or "")
    print("=== CLASSIFICATION ===")
    # print("[Ingest] Resume length:", resume_len)
    # print("[Ingest] JD length:", jd_len)

    return {
        "audit_trail": [
            f"ingest: candidate={state['candidate_id']}, "
            f"resume={resume_len}chars, jd={jd_len}chars"
        ]
    }
