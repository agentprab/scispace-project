# Multi-Agent Research Pipeline Backend

A unified FastAPI backend supporting multiple research pipelines using LangGraph and LangChain.

## Supported Pipelines

1. **Drug Discovery Pipeline** - 6-agent hypothesis generation with dynamic routing
2. **Research Gap Finder Pipeline** - 5-agent system to identify under-explored areas in scientific literature

## Architecture

```
backend/
├── backend.py              # FastAPI server - unified router for all pipelines
├── drug_discovery.py       # Drug discovery pipeline orchestrator (6 agents)
├── gap_finder.py           # LangGraph orchestrator for research gap pipeline
├── config.py               # Shared configuration
├── requirements.txt        # Dependencies
│
├── api_clients/            # External API integrations (No LLM)
│   ├── pubmed.py           # PubMed E-utilities client
│   └── openalex.py         # OpenAlex enrichment client
│
├── processors/             # Data processing (No LLM)
│   ├── mesh_mapper.py      # MeSH term → PICO category mapping
│   ├── xml_parser.py       # PubMed XML parsing
│   └── aggregator.py       # Statistics, matrices, sparse cells
│
└── agents/                 # LLM-powered agents (research gap pipeline)
    ├── query_planner.py    # Generates search queries
    ├── literature_analyzer.py  # Analyzes patterns & gaps
    └── gap_synthesizer.py  # Generates hypotheses
```

## Pipeline 1: Drug Discovery

### Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. TARGET HYPOTHESIS (LLM)         │
│     - Formulate structured hypothesis│
│     - Identify molecular targets     │
│     - Define mechanism of action     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  2. LITERATURE EVIDENCE (LLM)       │
│     - Synthesize scientific evidence │
│     - Assess target-disease linkage │
│     - Review competitive landscape  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  3. DRUGGABILITY (LLM)              │
│     - Assess structural druggability│
│     - Evaluate selectivity risks    │
│     - Recommend modality           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  4. NOVELTY ANALYSIS (LLM)         │
│     - Map competitive landscape     │
│     - Assess differentiation        │
│     - Identify white space          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  5. PRECLINICAL DESIGN (LLM)        │
│     - Design validation experiments │
│     - Select models                 │
│     - Define GO/NO-GO criteria     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  6. CONTROLLER (LLM)                │
│     - Evaluate scores               │
│     - Decide: GO / NO-GO / LOOP    │
│     - Route back if needed (max 3) │
└─────────────────────────────────────┘
    │
    ▼
Final Decision + Scores
```

### Features
- **Dynamic Routing**: Controller can loop back to refine earlier agents (max 3 iterations)
- **Score-based Decisions**: Evidence, Druggability, Novelty, Feasibility scores
- **Iterative Refinement**: Automatically refines low-scoring areas

## Pipeline 2: Research Gap Finder

### Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. QUERY PLANNER (LLM)             │
│     - Decomposes domain into        │
│       optimized PubMed queries      │
│     - Identifies PICO dimensions    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  2. DATA FETCHER (API)              │
│     - PubMed E-utilities search     │
│     - Fetch paper records (XML)     │
│     - OpenAlex enrichment           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  3. AGGREGATOR (Python)             │
│     - Parse XML, extract MeSH       │
│     - Map MeSH → PICO categories    │
│     - Build co-occurrence matrix    │
│     - Find sparse cells (gaps)      │
│     - Sample abstracts              │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  4. LITERATURE ANALYZER (LLM)       │
│     - Interpret distributions       │
│     - Analyze sparse combinations   │
│     - Identify temporal trends      │
│     - Detect contradictions         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  5. GAP SYNTHESIZER (LLM)           │
│     - Prioritize gaps               │
│     - Generate hypotheses           │
│     - Suggest study designs         │
└─────────────────────────────────────┘
    │
    ▼
Structured Research Gaps + Hypotheses
```

### How Gap Detection Works

The key insight: **Gaps are found in what's NOT in the data, not what IS.**

#### 1. MeSH Term Extraction (No LLM)
PubMed papers come with human-curated MeSH (Medical Subject Headings) terms. We extract these directly from the XML:

```xml
<MeshHeading>
  <DescriptorName>Pregnant Women</DescriptorName>
</MeshHeading>
<MeshHeading>
  <DescriptorName>Smoking Cessation</DescriptorName>
</MeshHeading>
```

#### 2. PICO Mapping (No LLM)
MeSH terms are mapped to standardized PICO categories using a predefined dictionary:

```python
MESH_TO_PICO = {
    "Pregnant Women": ("population", "pregnant"),
    "Homeless Persons": ("population", "homeless"),
    "Nicotine Replacement Therapy": ("intervention", "nrt"),
    "Text Messaging": ("intervention", "mobile_sms"),
    ...
}
```

#### 3. Co-occurrence Matrix (No LLM)
Count how often each (population, intervention) pair appears together:

```
                  │ NRT │ Counseling │ Mobile App │
──────────────────┼─────┼────────────┼────────────│
Adults            │ 134 │    167     │     10     │
Pregnant          │   8 │     10     │      0     │  ← GAP
Low-income        │  34 │     41     │      2     │  ← GAP
Homeless          │   2 │      3     │      0     │  ← GAP
```

#### 4. Sparse Cell Detection (No LLM)
Cells with < 3 papers = potential research gaps.

#### 5. LLM Interpretation
The LLM receives **aggregated statistics** (not raw papers):
- Distribution percentages
- Sparse combinations list
- Sample abstracts (15-20)
- Temporal trends

The LLM interprets patterns and generates hypotheses.

## APIs Used

### PubMed E-utilities (Free, No Key)
- `esearch.fcgi` - Search for PMIDs
- `efetch.fcgi` - Fetch full records with MeSH terms

### OpenAlex (Free, No Key)
- Works API - Citation counts, concepts
- Polite pool with `mailto` header

## Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export MODEL_NAME="gpt-4o-mini"  # optional, defaults to gpt-4o-mini

# Or create .env file in project root
echo "OPENAI_API_KEY=your-key" > ../.env
echo "MODEL_NAME=gpt-4o-mini" >> ../.env

# Run server
uvicorn backend:app --reload --port 8000
```

## API Endpoints

### POST /api/pipeline/stream
Stream pipeline execution with Server-Sent Events (SSE).

**Request:**
```json
{
    "question": "Can we develop a selective PLK1 inhibitor targeting the polo-box domain?",
    "pipeline_type": "drug_discovery"
}
```

or

```json
{
    "question": "smoking cessation interventions in emergency departments",
    "pipeline_type": "research_gap"
}
```

**Response:** Server-Sent Events stream with format:
```json
{"agent": "target_hypothesis", "phase": "thinking", "content": "..."}
{"agent": "target_hypothesis", "phase": "output", "content": "..."}
{"agent": "target_hypothesis", "phase": "complete", "full_output": "...", "scores": {...}}
{"type": "pipeline_complete", "decision": "GO", "scores": {...}, "iterations": 1}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy"
}
```

### GET /api/pipelines
List available pipelines and their agents.

**Response:**
```json
{
    "pipelines": [
        {
            "id": "drug_discovery",
            "name": "Drug Discovery Pipeline",
            "agents": ["target_hypothesis", "literature_evidence", ...]
        },
        {
            "id": "research_gap",
            "name": "Research Gap Finder",
            "agents": ["query_planner", "data_fetcher", ...]
        }
    ]
}
```

## Example Outputs

### Drug Discovery Pipeline

```json
{
    "decision": "GO",
    "scores": {
        "evidence": 0.75,
        "druggability": 0.70,
        "novelty": 0.85,
        "feasibility": 0.80
    },
    "iterations": 1
}
```

### Research Gap Pipeline

```json
{
    "research_gaps": [
        {
            "rank": 1,
            "title": "Mobile interventions for pregnant ED patients",
            "category": "missing_combination",
            "evidence_summary": {
                "papers_found": 0,
                "related_papers": 34
            },
            "hypothesis": {
                "statement": "A text-message-based smoking cessation program...",
                "primary_outcome": "30-day quit rate",
                "expected_direction": "increase"
            },
            "impact_rating": "high",
            "feasibility_rating": "medium"
        }
    ]
}
```

## Frontend Integration

The backend streams Server-Sent Events (SSE) compatible with React frontends. Events match the format:

```json
{"agent": "query_planner", "phase": "thinking", "content": "..."}
{"agent": "query_planner", "phase": "output", "content": "..."}
{"agent": "query_planner", "phase": "complete", "full_output": "..."}
{"type": "pipeline_complete", "result": {...}}
```

The frontend (`frontend/src/App.jsx`) supports both pipelines with pipeline selection and agent visualization.

## Dependencies

- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **LangGraph** - Multi-agent workflows
- **LangChain OpenAI** - OpenAI integration
- **httpx** - HTTP client for API calls
- **pydantic** - Data validation
- **python-dotenv** - Environment variable management

See `requirements.txt` for specific versions.

## Development

```bash
# Run with auto-reload
uvicorn backend:app --reload --port 8000

# Run production server
uvicorn backend:app --host 0.0.0.0 --port 8000
```

## Code Organization

- **Drug Discovery Pipeline**: Implemented in `drug_discovery.py` with all 6 agents, helper functions, and the main pipeline orchestrator
- **Research Gap Pipeline**: Implemented in `gap_finder.py` using LangGraph for workflow orchestration
- **Backend Router**: `backend.py` serves as the unified FastAPI server that routes requests to the appropriate pipeline

## Notes

- Both pipelines use the same OpenAI API key from environment variables
- Drug Discovery pipeline supports dynamic routing with max 3 loop iterations
- Research Gap pipeline is linear (no loops)
- All pipelines stream results via SSE for real-time frontend updates
