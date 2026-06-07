# HireGraph

A LangGraph-powered hiring assistant that evaluates candidates against job descriptions end-to-end — from resume ingestion through skill scoring, human review, email drafting, and ATS logging. Built for Assignment 2: *Thinking in LangGraph*.

---

## What it demonstrates

HireGraph exercises all 13 required LangGraph patterns:

| # | Pattern | Where |
|---|---------|-------|
| 1 | `StateGraph` + `TypedDict` state | `state.py` |
| 2 | `Annotated` reducers (`operator.add`) | `skill_scores`, `critic_history`, `audit_trail` |
| 3 | Static edges (`add_edge`) | Band 1 linear chain, Band 3 fan-in |
| 4 | Dynamic routing via `Command(goto=...)` | `aggregate_scores`, `critic_loop`, `advance_path`, etc. |
| 5 | Orchestrator-worker fan-out with `Send` | `plan_required_skills` → `per_skill_worker` |
| 6 | Parallel fixed scorers (fan-out / fan-in) | `experience_scorer`, `education_scorer`, `signal_scorer` |
| 7 | `interrupt()` + resume — human scorecard review | `borderline_review` |
| 8 | `interrupt()` + resume — human email review | `human_review` |
| 9 | Evaluator-optimizer loop | `draft_email` ↔ `critic_loop` |
| 10 | LLM-recoverable loopback (`CriticFeedback.min_length`) | `critic_loop` ValidationError retry |
| 11 | Research agent (tool loop inside a node) | `signal_scorer` — Tavily + GitHub tools |
| 12 | Saga with compensating transactions | `send_email` → `update_ats` → `compensate` → `finalize` |
| 13 | `RetryPolicy` on saga nodes | `send_email` (×3), `update_ats` (×2) |

---

## Architecture

```
START
  └─► ingest ─► classify_seniority ─► plan_required_skills
                                            │
                                    Send × N skills
                                            │
                                     per_skill_worker
                                    ╱        │        ╲
                              exp_scorer  edu_scorer  sig_scorer
                                    ╲        │        ╱
                                     aggregate_scores
                                    ╱        │        ╲
                             score≥75   score<50   50-74
                                │           │         │
                           advance_path reject_path  borderline_review (interrupt)
                                │           │         │
                                └───────────┴─────────┘
                                              ▼
                                         draft_email
                                              │
                                         critic_loop ◄─── (loop if rejected)
                                         │       │
                                    approved   exhausted
                                         │       │
                                     send_email  human_review (interrupt)
                                         │
                                     update_ats
                                         │
                                       finalize ─► END
                                (compensate on any saga failure)
```

---

## Project structure

```
hiregraph/
├── src/hiregraph/
│   ├── state.py              # HireGraphState TypedDict + Pydantic models
│   ├── config.py             # Settings (env vars, mock flag)
│   ├── llm.py                # get_llm() — MockLLM or ChatOpenAI
│   ├── prompts.py            # Prompt builders for each node
│   ├── services.py           # Tavily, GitHub, email, ATS integrations
│   ├── tools.py              # LangChain @tool wrappers (search_web, lookup_github)
│   ├── graph.py              # build_graph() + compile_graph()
│   ├── api.py                # FastAPI server
│   ├── main.py               # CLI demo — three candidate scenarios
│   └── nodes/
│       ├── ingest.py
│       ├── classify_seniority.py
│       ├── plan_required_skills.py
│       ├── per_skill_worker.py
│       ├── experience_scorer.py
│       ├── education_scorer.py
│       ├── signal_scorer.py        # research agent with tool loop
│       ├── aggregate_scores.py
│       ├── advance_path.py
│       ├── reject_path.py
│       ├── borderline_review.py    # first interrupt
│       ├── draft_email.py
│       ├── critic_loop.py          # evaluator-optimizer
│       ├── human_review.py         # second interrupt
│       ├── send_email.py           # saga step 1
│       ├── update_ats.py           # saga step 2
│       ├── compensate.py           # saga rollback
│       └── finalize.py
├── tests/
│   ├── test_state.py         # Pydantic model tests
│   ├── test_nodes.py         # Unit tests for individual nodes
│   └── test_e2e.py           # End-to-end graph tests (all 3 candidates)
├── sample_data/
│   ├── resumes/              # resume_priya.md, resume_mira.md, resume_eitan.md
│   └── jds/                  # jd_senior_backend.md, jd_junior_data.md
├── ui/
│   └── index.html            # Single-page UI (dark theme, served by FastAPI)
├── graph_out/
│   ├── graph.mmd             # Mermaid source
│   └── graph.png             # Rendered graph image
├── run_test_band1.py         # Band 1: ingest → classify → plan
├── run_test_band2.py         # Band 2: per_skill_worker (operator.add fan-out)
├── run_test_band3.py         # Band 3: parallel scorers + sub-scores
├── run_test_band4.py         # Band 4: aggregate routing (Priya=advance, Mira=reject)
├── run_test_band5.py         # Band 5: borderline interrupt/resume (Eitan)
├── run_test_band6.py         # Band 6: critic loop (evaluator-optimizer, 2 rounds)
├── run_test_band7.py         # Band 7: full saga (send_email → update_ats → finalize)
├── run_signal.py             # Signal scorer in isolation (real APIs)
├── run_api.py                # Start FastAPI server
└── pyproject.toml
```

---

## Setup

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
# Install dependencies
uv sync

# Copy and fill in API keys (only needed for real mode)
cp .env.example .env
```

**.env**
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
GITHUB_TOKEN=ghp-...          # classic token, no scopes needed
HIREGRAPH_USE_MOCKS=true      # set false to use real APIs
```

---

## Running

### CLI demo — all three scenarios

```bash
uv run python src/hiregraph/main.py
```

Runs Priya (advance), Mira (reject), and Eitan (borderline + human interrupt/resume) in sequence and prints a scoreboard for each.

### Band-by-band scripts (incremental milestones)

```bash
uv run python run_test_band1.py
uv run python run_test_band2.py
uv run python run_test_band3.py
uv run python run_test_band4.py
uv run python run_test_band5.py
uv run python run_test_band6.py
uv run python run_test_band7.py
```

- **`run_test_band1.py`** — Priya through the linear chain only: prints classification, required skills, and audit trail. Confirms ingest → classify → plan wiring.
- **`run_test_band2.py`** — Adds the skill worker fan-out: prints every `SkillScore` (skill, score, evidence) produced by the `operator.add` reducer across 4 parallel workers.
- **`run_test_band3.py`** — Deepest view for Priya: classification + required skills + every skill score with evidence + sub-scores (experience / education / signal) + audit trail.
- **`run_test_band4.py`** — Side-by-side Priya vs Mira: final score, recommendation, and full audit trail for both in one run. Confirms advance/reject routing.
- **`run_test_band5.py`** — Eitan: shows the interrupt firing, the scorecard payload, and the resume-with-approval flow.
- **`run_test_band6.py`** — Critic loop (evaluator-optimizer): prints the email draft, both critic rounds (rejected → approved), and the draft/critic audit lines.
- **`run_test_band7.py`** — Full saga: `send_email` → `update_ats` → `finalize`. Prints `sent_status`, saga-node audit lines, and the complete audit trail.

Start with **band3** to see the full evaluation detail, then **band4** for the Priya/Mira contrast, then **band5** for Eitan's interrupt.

### API server

```bash
uv run python run_api.py
# or
uv run uvicorn hiregraph.api:app --app-dir src --port 8000 --reload
```

Endpoints:
- `POST /evaluate` — `{candidate_id, resume_text, jd_text}` → starts evaluation
- `POST /resume` — `{thread_id, approved, recommendation_override?}` → resumes an interrupt
- `GET  /status/{thread_id}` — check thread state
- `GET  /health` — health check
- `GET  /` — serves the HTML UI

### HTML UI

Start the API server, then open `http://localhost:8000` in a browser.

### Tests

```bash
uv run pytest tests/ -v
```

20 tests: 4 state, 12 node unit tests, 4 end-to-end graph tests.

---

## Three candidate scenarios

| Candidate | Resume | JD | Expected score | Path |
|-----------|--------|----|---------------|------|
| **Priya** | Senior backend, 8 yrs, Python/Kafka/Postgres | Senior backend | ~80 | advance → email sent |
| **Mira** | Frontend/UX, CSS/Figma | Junior data | ~34 | reject → rejection email sent |
| **Eitan** | Mid-level backend, 3 yrs | Senior backend | ~63 | borderline → **human interrupt** → resume → email sent |

---

## Scoring formula

```
final_score = round(skill_avg × 0.40 + experience × 0.30 + education × 0.15 + signal × 0.15)

Routing:  ≥ 75  →  advance_path
          < 50  →  reject_path
          50-74 →  borderline_review (human interrupt)
```

---

## Mock vs real mode

`HIREGRAPH_USE_MOCKS=true` (default) uses `MockLLM` and mock service calls — no API keys needed, fully deterministic, runs offline.

`HIREGRAPH_USE_MOCKS=false` uses `ChatOpenAI` (gpt-4o-mini), real Tavily web search, and real GitHub profile lookups.

The signal scorer research agent runs a live tool loop (Tavily + GitHub) even in partial-real mode — set `HIREGRAPH_USE_MOCKS=false` with both keys configured to see it call tools against real data.
