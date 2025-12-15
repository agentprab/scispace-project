# Research Gap Finder: Multi-Agent System

## Executive Summary

This document describes a multi-agent system designed to identify research gaps in scientific literature by analyzing what's **missing** from published research, rather than what exists. The system uses a hybrid approach combining LLM-powered analysis with deterministic statistical processing to systematically identify under-explored research areas.

**Key Innovation**: The system finds gaps by detecting sparse combinations in co-occurrence matrices built from MeSH terms, then uses LLM agents to validate and prioritize these gaps based on clinical significance and feasibility.

---

## 1. System Architecture Overview

### 1.1 Design Philosophy

Research gap identification requires a fundamentally different approach than traditional literature review:

1. **Gap detection is negative space analysis**: Gaps are found in what's NOT in the data, not what IS
2. **Hybrid LLM + deterministic processing**: Statistical analysis identifies sparse combinations; LLM validates clinical significance
3. **PICO framework**: Uses Population, Intervention, Comparison, Outcome framework to structure analysis
4. **MeSH-based categorization**: Leverages human-curated Medical Subject Headings for consistent categorization

### 1.2 Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RESEARCH GAP FINDER SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │    QUERY     │───▶│     DATA     │───▶│  AGGREGATOR │                   │
│  │   PLANNER    │    │   FETCHER    │    │   (Python)  │                   │
│  │   (LLM)      │    │    (API)     │    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                                       │                            │
│         │                                       ▼                            │
│         │                              ┌──────────────┐                      │
│         │                              │  LITERATURE  │                      │
│         │                              │   ANALYZER   │                      │
│         │                              │    (LLM)     │                      │
│         │                              └──────────────┘                      │
│         │                                       │                            │
│         │                                       ▼                            │
│         │                              ┌──────────────┐                      │
│         └────────────────────────────▶│     GAP     │───▶ OUTPUT           │
│                                        │ SYNTHESIZER │                      │
│                                        │    (LLM)    │                      │
│                                        └──────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pipeline Flow**: Linear (no loops) - 5 sequential agents

---

## 2. How Gap Detection Works

### 2.1 Core Insight

**Gaps are found in what's NOT in the data, not what IS.**

The system identifies research gaps by:
1. Building co-occurrence matrices from published papers
2. Finding sparse cells (< 3 papers) in these matrices
3. Validating that sparse combinations represent genuine research opportunities (not logical impossibilities)
4. Prioritizing gaps by clinical significance and feasibility

### 2.2 Technical Process

#### Step 1: MeSH Term Extraction (No LLM)

PubMed papers include human-curated MeSH (Medical Subject Headings) terms. These are extracted directly from XML:

```xml
<MeshHeading>
  <DescriptorName>Pregnant Women</DescriptorName>
</MeshHeading>
<MeshHeading>
  <DescriptorName>Smoking Cessation</DescriptorName>
</MeshHeading>
```

**Why MeSH?**: 
- Human-curated, standardized terminology
- Consistent across papers
- No LLM interpretation needed
- Reliable categorization

#### Step 2: PICO Mapping (No LLM)

MeSH terms are mapped to standardized PICO categories using a predefined dictionary:

```python
MESH_TO_PICO = {
    "Pregnant Women": ("population", "pregnant"),
    "Homeless Persons": ("population", "homeless"),
    "Nicotine Replacement Therapy": ("intervention", "nrt"),
    "Text Messaging": ("intervention", "mobile_sms"),
    "Counseling": ("intervention", "counseling"),
    ...
}
```

**PICO Framework**:
- **Population**: Who is being studied (e.g., pregnant women, low-income adults)
- **Intervention**: What is being tested (e.g., NRT, mobile apps, counseling)
- **Comparison**: Control conditions (often implicit)
- **Outcome**: What is measured (e.g., quit rates, abstinence)

#### Step 3: Co-occurrence Matrix Construction (No LLM)

The system counts how often each (population, intervention) pair appears together:

```
                  │ NRT │ Counseling │ Mobile App │
──────────────────┼─────┼────────────┼────────────│
Adults            │ 134 │    167     │     10     │
Pregnant          │   8 │     10     │      0     │  ← GAP
Low-income        │  34 │     41     │      2     │  ← GAP
Homeless          │   2 │      3     │      0     │  ← GAP
Adolescents       │  45 │     52     │     15     │
```

**Sparse Cell Detection**: Cells with < 3 papers are flagged as potential research gaps.

#### Step 4: LLM Validation and Analysis

The LLM receives **aggregated statistics** (not raw papers):
- Distribution percentages (e.g., "5% of papers study pregnant populations")
- Sparse combinations list (population-intervention pairs with < 3 papers)
- Sample abstracts (15-20 representative papers)
- Temporal trends (publication counts over time)

The LLM then:
1. Validates logical coherence (e.g., "Can pregnant women receive this intervention?")
2. Assesses clinical significance ("Why does this gap matter?")
3. Filters false positives ("Is this combination logically impossible?")
4. Prioritizes gaps by impact and feasibility

---

## 3. Agent Definitions

### 3.1 Query Planner Agent

**Role**: Decompose research domain into optimized PubMed search queries.

**Why this agent?**: Effective gap analysis requires comprehensive literature coverage. The Query Planner ensures we capture all relevant papers by generating multiple search strategies.

**Key Responsibilities**:
- Identify key concepts and MeSH terms
- Generate 4-6 distinct PubMed queries
- Balance sensitivity (finding all papers) with specificity (avoiding noise)
- Identify PICO dimensions (populations, interventions, outcomes)

**Output Format**:
```json
{
    "domain_summary": "Brief summary of research domain",
    "search_queries": [
        "'Smoking Cessation'[MeSH] AND 'Hispanic Americans'[MeSH]",
        "tobacco cessation AND (Hispanic OR Latino) AND low-income"
    ],
    "key_populations": ["population1", "population2"],
    "key_interventions": ["intervention1", "intervention2"],
    "key_outcomes": ["outcome1", "outcome2"],
    "time_range_suggestion": "2018-2024",
    "search_rationale": "Explanation of search strategy"
}
```

**Technical Details**:
- Uses `gpt-4o-mini` with temperature 0.3
- Outputs structured JSON (with repair logic for parsing errors)
- Fallback: Simple query if JSON parsing fails

---

### 3.2 Data Fetcher Agent

**Role**: Execute PubMed searches and retrieve paper metadata.

**Why this agent?**: Non-LLM step that handles API calls efficiently.

**Key Responsibilities**:
- Execute multiple PubMed queries in parallel
- Fetch full paper records (XML format with MeSH terms)
- Enrich with citation data from OpenAlex (optional)
- Deduplicate papers across queries

**Technical Implementation**:
- Uses PubMed E-utilities API (free, no key required)
- Batch fetching (50 papers per batch)
- OpenAlex enrichment for citation counts (polite pool)
- Handles API failures gracefully

**Output**: List of paper objects with:
- Title, abstract, authors
- MeSH terms (critical for gap detection)
- DOI, PMID, publication date
- Citation counts (if available)

---

### 3.3 Aggregator Agent

**Role**: Compute statistics from paper corpus.

**Why this agent?**: Deterministic statistical processing is more reliable than LLM for counting and categorization.

**Key Responsibilities**:
- Parse MeSH terms from XML
- Map MeSH → PICO categories
- Build frequency distributions (populations, interventions, outcomes)
- Construct co-occurrence matrices
- Identify sparse cells (< 3 papers)
- Sample abstracts for LLM analysis

**Output Format**:
```json
{
    "total_papers": 500,
    "population_distribution": {
        "adults": {"count": 350, "percentage": 70.0},
        "pregnant": {"count": 25, "percentage": 5.0},
        ...
    },
    "intervention_distribution": {...},
    "sparse_combinations": [
        {"population": "pregnant", "intervention": "mobile_app", "count": 0},
        ...
    ],
    "sample_abstracts": [...],
    "temporal_trends": {...}
}
```

**Technical Details**:
- Pure Python processing (no LLM)
- Handles MeSH term variations and synonyms
- Filters out irrelevant MeSH terms
- Samples abstracts strategically (diverse, representative)

---

### 3.4 Literature Analyzer Agent

**Role**: Interpret statistics and identify preliminary gap patterns.

**Why this agent?**: Statistical patterns need interpretation. The Literature Analyzer applies domain knowledge to distinguish genuine gaps from false positives.

**Key Responsibilities**:
1. **Interpret Distributions**
   - Identify understudied populations (< 5% of papers)
   - Identify understudied interventions (< 5% of papers)
   - Flag missing study designs (e.g., few RCTs)

2. **Analyze Sparse Combinations**
   - Assess clinical significance of sparse pairs
   - Distinguish "not studied because not relevant" vs "genuine gap"
   - Apply domain logic filters

3. **Review Temporal Trends**
   - Identify emerging areas (growing publications)
   - Identify declining areas needing revival

4. **Validate Logical Coherence**
   - Filter false positives (e.g., "Can infants use mobile apps?")
   - Check intervention-target appropriateness
   - Verify ethical feasibility

**Critical Validation Logic**:

The agent applies domain logic to filter invalid combinations:

1. **Intervention Target vs Secondary Population**
   - Example: In parenting interventions, children are affected but parents receive intervention
   - Only flag gaps where population directly receives intervention

2. **Age/Developmental Appropriateness**
   - Consider if intervention is designed for population's developmental stage
   - Consider regulatory/ethical constraints

3. **Capacity to Participate**
   - Can population physically/cognitively/legally participate?
   - Consider consent capacity, communication ability

4. **Logical Coherence**
   - Does the combination make sense?
   - Would a researcher actually design this study?

**Output Format**:
```json
{
    "distribution_insights": {
        "understudied_populations": [...],
        "understudied_interventions": [...],
        "filtered_out": [...]
    },
    "sparse_combination_analysis": [
        {
            "combination": "Population + Intervention",
            "paper_count": 0,
            "is_genuine_gap": true,
            "gap_type": "genuine_gap | false_positive | unclear",
            "reasoning": "Why this is/isn't a valid gap"
        }
    ],
    "temporal_insights": {...},
    "contradictions": [...]
}
```

**Technical Details**:
- Uses `gpt-4o-mini` with temperature 0.3
- Receives aggregated statistics (not raw papers)
- JSON output with repair logic for parsing errors

---

### 3.5 Gap Synthesizer Agent

**Role**: Synthesize analysis into prioritized, actionable research gaps with hypotheses.

**Why this agent?**: Final agent transforms gap analysis into concrete research opportunities.

**Key Responsibilities**:
1. **Prioritize Gaps**
   - Rank by research impact potential
   - Consider: clinical significance, feasibility, novelty, urgency

2. **Generate Hypotheses**
   - Formulate specific, testable hypotheses
   - Hypotheses should be falsifiable and measurable

3. **Suggest Study Designs**
   - Recommend appropriate study designs (RCT, cohort, etc.)
   - Note key challenges and solutions
   - Identify resource requirements

4. **Final Validity Check**
   - Re-validate all gaps using same logic as Literature Analyzer
   - Exclude any gaps marked as false positives

**Output Format**:
```json
{
    "research_gaps": [
        {
            "rank": 1,
            "title": "Mobile interventions for pregnant ED patients",
            "category": "missing_combination",
            "description": "2-3 sentence description",
            "validity_check": {
                "population_is_intervention_target": true,
                "intervention_is_appropriate_for_population": true,
                "study_would_be_ethically_feasible": true
            },
            "evidence_summary": {
                "papers_found": 0,
                "related_papers": 34,
                "key_statistic": "Only 0% of studies examined this combination"
            },
            "clinical_significance": "Why this gap matters",
            "hypothesis": {
                "statement": "A text-message-based smoking cessation program...",
                "primary_outcome": "30-day quit rate",
                "expected_direction": "increase"
            },
            "suggested_study_design": {
                "design": "RCT",
                "setting": "Emergency departments",
                "population": "Pregnant women presenting to ED",
                "sample_size_estimate": "200 participants",
                "duration": "6 months"
            },
            "challenges": ["challenge1", "challenge2"],
            "feasibility_rating": "medium",
            "impact_rating": "high"
        }
    ]
}
```

**Technical Details**:
- Uses `gpt-4o-mini` with temperature 0.7 (creative mode)
- Receives Literature Analyzer output
- Generates actionable research recommendations

---

## 4. Technical Implementation

### 4.1 LangGraph Orchestration

The pipeline uses LangGraph for workflow orchestration:

```python
graph = StateGraph(GapFinderState)

graph.add_node("query_planner", query_planner_node)
graph.add_node("data_fetcher", data_fetcher_node)
graph.add_node("aggregator", aggregator_node)
graph.add_node("literature_analyzer", literature_analyzer_node)
graph.add_node("gap_synthesizer", gap_synthesizer_node)

graph.set_entry_point("query_planner")
graph.add_edge("query_planner", "data_fetcher")
graph.add_edge("data_fetcher", "aggregator")
graph.add_edge("aggregator", "literature_analyzer")
graph.add_edge("literature_analyzer", "gap_synthesizer")
graph.add_edge("gap_synthesizer", END)
```

**State Management**: TypedDict tracks:
- User query
- Search queries
- Raw papers
- Statistics
- Analysis results
- Final gaps

### 4.2 Streaming Support

The system supports Server-Sent Events (SSE) for real-time frontend updates:

```python
async def run_gap_finder_streaming(query: str):
    async for event in graph.astream({"user_query": query}):
        yield {
            "type": "agent_event",
            "agent": event["current_node"],
            "phase": "thinking" | "output" | "complete",
            "content": "..."
        }
```

**Event Types**:
- `agent_event`: Progress updates from each agent
- `pipeline_complete`: Final results
- `pipeline_error`: Error handling

### 4.3 API Integration

#### PubMed E-utilities (Free, No Key)

- **esearch.fcgi**: Search for PMIDs
- **efetch.fcgi**: Fetch full records with MeSH terms
- Rate limiting: Polite delays between requests
- Batch fetching: 50 papers per request

#### OpenAlex (Free, No Key)

- **Works API**: Citation counts, concepts
- Polite pool: Requires `mailto` header
- Optional enrichment: Falls back gracefully if unavailable

---

## 5. Gap Detection Algorithm

### 5.1 Sparse Cell Detection

**Threshold**: < 3 papers = potential gap

**Rationale**:
- Too few papers to draw conclusions
- May indicate genuine research gap
- Needs validation by LLM (could be false positive)

### 5.2 False Positive Filtering

The system filters invalid gaps using domain logic:

| Filter | Example | Action |
|--------|---------|--------|
| Intervention target mismatch | Children affected by parental intervention | Exclude (children not direct targets) |
| Developmental mismatch | Mobile apps for infants | Exclude (not developmentally appropriate) |
| Capacity mismatch | Text messaging for non-verbal patients | Exclude (cannot participate) |
| Logical incoherence | Intervention that doesn't apply to population | Exclude (doesn't make sense) |

### 5.3 Gap Prioritization

Gaps are ranked by:

1. **Clinical Significance**: Impact on patient outcomes/public health
2. **Feasibility**: Can this study realistically be conducted?
3. **Novelty**: Is this a genuinely new research direction?
4. **Urgency**: Does this address an unmet need?

---

## 6. Output Format

### 6.1 Final Research Gaps Structure

```json
{
    "research_gaps": [
        {
            "rank": 1,
            "title": "Short descriptive title",
            "category": "missing_combination | understudied_population | ...",
            "description": "2-3 sentence description",
            "evidence_summary": {
                "papers_found": 0,
                "related_papers": 34,
                "key_statistic": "Only 0% of studies..."
            },
            "hypothesis": {
                "statement": "Testable hypothesis",
                "primary_outcome": "What to measure",
                "expected_direction": "increase | decrease"
            },
            "suggested_study_design": {
                "design": "RCT | Cohort | ...",
                "setting": "Where",
                "population": "Who",
                "sample_size_estimate": "N participants",
                "duration": "Timeframe"
            },
            "feasibility_rating": "high | medium | low",
            "impact_rating": "high | medium | low"
        }
    ]
}
```

### 6.2 Gap Categories

- **missing_combination**: Population-intervention pair with no/few papers
- **understudied_population**: Population appears in < 5% of papers
- **understudied_intervention**: Intervention appears in < 5% of papers
- **methodological**: Missing study designs (e.g., few RCTs)
- **outcome_measurement**: Rarely measured outcomes
- **emerging_opportunity**: New area with growing interest

---

## 7. Key Design Decisions

### 7.1 Why Hybrid LLM + Deterministic?

**Deterministic Processing** (Aggregator):
- More reliable for counting and categorization
- Consistent results across runs
- No token costs for statistical operations

**LLM Processing** (Query Planner, Literature Analyzer, Gap Synthesizer):
- Domain knowledge for query generation
- Clinical reasoning for gap validation
- Creative hypothesis generation

### 7.2 Why MeSH Terms?

- **Human-curated**: More reliable than LLM extraction
- **Standardized**: Consistent terminology across papers
- **Structured**: Easy to map to PICO framework
- **Comprehensive**: Covers populations, interventions, outcomes

### 7.3 Why PICO Framework?

- **Standard**: Widely used in systematic reviews
- **Structured**: Enables systematic gap analysis
- **Comprehensive**: Covers all aspects of research design
- **Actionable**: Maps directly to study design decisions

---

## 8. Limitations and Considerations

### 8.1 Known Limitations

1. **MeSH Coverage**: Not all papers have MeSH terms (especially older papers)
2. **PICO Mapping**: Dictionary-based mapping may miss novel terms
3. **False Positives**: Some sparse combinations are logically impossible (filtered by LLM)
4. **Temporal Bias**: Recent papers may be overrepresented
5. **Language**: Primarily English-language papers from PubMed

### 8.2 Validation Challenges

- **Domain Logic**: Requires domain expertise to validate filters
- **Clinical Significance**: Subjective assessment of gap importance
- **Feasibility**: Resource requirements may vary by institution

### 8.3 Future Enhancements

- Expand MeSH → PICO mapping dictionary
- Add more outcome categories
- Support multiple languages
- Integrate additional databases (e.g., Embase, PsycINFO)
- Add citation network analysis

---

## 9. Usage Examples

### 9.1 Basic Usage

```python
from gap_finder import run_gap_finder_pipeline

result = await run_gap_finder_pipeline(
    "smoking cessation interventions in emergency departments"
)

print(f"Found {len(result['research_gaps'])} research gaps")
for gap in result['research_gaps']:
    print(f"{gap['rank']}. {gap['title']}")
```

### 9.2 Streaming Usage

```python
from gap_finder import run_gap_finder_streaming

async for event in run_gap_finder_streaming("smoking cessation in ED"):
    if event['type'] == 'agent_event':
        print(f"{event['agent']}: {event['phase']}")
    elif event['type'] == 'pipeline_complete':
        gaps = event['result']['research_gaps']
        print(f"Found {len(gaps)} gaps")
```

### 9.3 API Endpoint

```bash
curl -X POST http://localhost:8000/api/pipeline/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "smoking cessation in emergency departments",
    "pipeline_type": "research_gap"
  }'
```

---

## 10. Comparison with Drug Discovery Pipeline

| Aspect | Drug Discovery | Research Gap Finder |
|--------|---------------|---------------------|
| **Flow** | Dynamic routing with loops | Linear (no loops) |
| **Orchestration** | Manual async generators | LangGraph |
| **Scoring** | Yes (4 scores) | No |
| **Iterations** | Max 3 loops | Single pass |
| **LLM Agents** | 6 agents | 3 agents |
| **Non-LLM Steps** | None | 2 steps (Data Fetcher, Aggregator) |
| **Output** | GO/NO-GO decision | Ranked research gaps |

---

## 11. File Structure

```
backend/
├── gap_finder.py              # Main LangGraph orchestrator
├── agents/
│   ├── query_planner.py      # Query generation agent
│   ├── literature_analyzer.py # Pattern analysis agent
│   └── gap_synthesizer.py     # Gap synthesis agent
├── api_clients/
│   ├── pubmed.py              # PubMed E-utilities client
│   └── openalex.py            # OpenAlex enrichment client
└── processors/
    ├── mesh_mapper.py          # MeSH → PICO mapping
    ├── xml_parser.py           # PubMed XML parsing
    └── aggregator.py           # Statistical aggregation
```

---

## 12. References

- **MeSH**: Medical Subject Headings - https://www.nlm.nih.gov/mesh/
- **PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **OpenAlex**: https://openalex.org/
- **PICO Framework**: Richardson WS, et al. (1995). "The well-built clinical question: a key to evidence-based decisions"
- **LangGraph**: https://langchain-ai.github.io/langgraph/

---

## Appendix: Example Output

```json
{
    "research_gaps": [
        {
            "rank": 1,
            "title": "Mobile text-message interventions for pregnant women in emergency departments",
            "category": "missing_combination",
            "description": "While mobile interventions show promise for smoking cessation, and emergency departments serve many pregnant smokers, no studies have tested text-message programs specifically for pregnant ED patients.",
            "evidence_summary": {
                "papers_found": 0,
                "related_papers": 34,
                "key_statistic": "0% of studies examined mobile interventions for pregnant ED patients, despite 34 papers on related topics"
            },
            "clinical_significance": "Pregnant smokers face unique barriers and ED visits represent a critical intervention opportunity. Mobile interventions could reach this hard-to-reach population.",
            "hypothesis": {
                "statement": "A text-message-based smoking cessation program delivered to pregnant women during ED visits will increase 30-day quit rates compared to standard care.",
                "primary_outcome": "30-day biochemically verified quit rate",
                "expected_direction": "increase"
            },
            "suggested_study_design": {
                "design": "RCT",
                "setting": "Urban emergency departments",
                "population": "Pregnant women (18+) presenting to ED who smoke",
                "sample_size_estimate": "200 participants (100 per arm) for 80% power",
                "duration": "6 months (3 months intervention + 3 months follow-up)"
            },
            "challenges": [
                "Recruitment in busy ED setting",
                "Retention of hard-to-reach population",
                "Ensuring intervention is developmentally appropriate"
            ],
            "feasibility_rating": "medium",
            "impact_rating": "high"
        }
    ]
}
```

