# Multi-Agent Research Pipelines

Unified project with:
- **Frontend (React + Vite + Tailwind)**: pipeline selector UI, agent run console, live SSE output.
- **Backend (FastAPI + LangGraph/LangChain)**: two pipelines (Drug Discovery + Research Gap Finder) with SSE streaming.

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.13 (venv recommended)
- An OpenAI API key in `.env` at the repo root:
  ```
  OPENAI_API_KEY=your-key
  MODEL_NAME=gpt-4o-mini
  ```

### Backend
```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
uvicorn backend:app --reload --port 8000
```

Key files:
- `backend.py` — FastAPI entrypoint/router
- `drug_discovery.py` — 6-agent drug discovery pipeline (dynamic routing, loops)
- `gap_finder.py` — LangGraph research-gap pipeline orchestrator
- `agents/` — LLM agents for research-gap flow
- `api_clients/` — PubMed/OpenAlex clients (no LLM)
- `processors/` — MeSH/PICO mapping, XML parsing, aggregation

### Frontend
```bash
cd frontend
npm install
npm run dev
```

UI basics:
- Pipeline selection page → pick Drug Discovery or Research Gap
- Execution view with input, agent list/status, streaming output, scores (drug discovery), and loop notifications
- Back button to return to pipeline selection

## Pipelines

### Drug Discovery Pipeline
- Agents: target_hypothesis → literature_evidence → druggability → novelty → preclinical_design → controller
- Features: dynamic routing with loops (max 3), scoring (evidence/druggability/novelty/feasibility), GO/NO-GO/LOOP decisions
- Implemented in `backend/drug_discovery.py`

### Research Gap Finder
- Agents: query_planner → data_fetcher → aggregator → literature_analyzer → gap_synthesizer
- Features: linear flow, uses LangGraph in `backend/gap_finder.py`
- Non-LLM steps handled by processors + API clients; LLM steps in agents

## API (Backend)
- `POST /api/pipeline/stream` — body: `{"question": "...", "pipeline_type": "drug_discovery" | "research_gap"}`; streams SSE events
- `GET /api/health` — health check
- `GET /api/pipelines` — lists available pipelines and agents

## Dev Notes
- Frontend uses SSE; keep backend on `:8000` (default) unless you update the frontend proxy/Vite config.
- Drug discovery prompts and flow live in `drug_discovery.py`; research gap flow in `gap_finder.py` + `agents/`.
- Environment variables are loaded from both `.env` (root) and `backend/.env` if present.

## Scripts (common)
```bash
# Backend (from backend/)
uvicorn backend:app --reload --port 8000

# Frontend (from frontend/)
npm run dev
```

## Repo Layout
```
backend/               # FastAPI + pipelines
frontend/              # React UI (Vite)
drug_discovery_multi_agent_system.md  # reference notes
README.md              # this file
```


