# Drug Discovery Hypothesis Generation: Multi-Agent System

## Executive Summary

This document describes a multi-agent system designed to generate novel, testable hypotheses for drug discovery. The architecture is informed by real-world drug discovery reasoning patterns observed in scientific literature (e.g., PLK1 kinase inhibitor research) and addresses the unique requirements of pharmaceutical hypothesis generation.

**Key Feature**: Each scoring agent uses explicit rubrics to ensure consistent, justified scores across evaluations.

---

## 1. System Architecture Overview

### 1.1 Design Philosophy

Drug discovery hypothesis generation differs from general scientific reasoning in several key ways:

1. **Target-centric thinking**: Hypotheses revolve around molecular targets with specific structural and functional properties
2. **Druggability constraints**: Not all biological insights translate to therapeutic opportunities
3. **Novelty is paramount**: Redundant hypotheses waste significant R&D resources
4. **Iterative refinement**: Hypotheses evolve based on evidence quality and feasibility assessments

### 1.2 Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DRUG DISCOVERY HYPOTHESIS SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   TARGET     │───▶│  LITERATURE  │───▶│ DRUGGABILITY │                   │
│  │  HYPOTHESIS  │    │   EVIDENCE   │    │  ASSESSMENT  │                   │
│  │    AGENT     │    │    AGENT     │    │    AGENT     │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         ▲                                       │                            │
│         │                                       ▼                            │
│         │                              ┌──────────────┐                      │
│         │                              │   NOVELTY    │                      │
│         │                              │   ANALYSIS   │                      │
│         │                              │    AGENT     │                      │
│         │                              └──────────────┘                      │
│         │                                       │                            │
│         │            ┌──────────────┐           ▼                            │
│         │            │  CONTROLLER  │◀──────────┤                            │
│         │            │    AGENT     │           │                            │
│         │            └──────────────┘           │                            │
│         │                   │                   ▼                            │
│         │                   │          ┌──────────────┐                      │
│         └───────────────────┼─────────▶│  PRECLINICAL │───▶ OUTPUT          │
│              (re-scope)     │          │    DESIGN    │                      │
│                             │          │    AGENT     │                      │
│                             │          └──────────────┘                      │
│                             │                   ▲                            │
│                             └───────────────────┘                            │
│                              (redesign experiment)                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scoring Framework

### 2.1 Unified Score Interpretation

All agents use a consistent scoring scale with explicit thresholds:

| Score Range | Classification | Interpretation |
|-------------|----------------|----------------|
| 0.85 - 1.00 | Excellent | No concerns, strong foundation |
| 0.70 - 0.84 | Strong | Minor concerns, proceed with confidence |
| 0.55 - 0.69 | Adequate | Acceptable with awareness of limitations |
| 0.40 - 0.54 | Weak | Needs improvement or strong justification |
| 0.25 - 0.39 | Poor | Significant concerns, likely requires pivot |
| 0.00 - 0.24 | Critical | Fundamental issues, reconsider approach |

### 2.2 Controller Decision Thresholds

| Threshold | Action |
|-----------|--------|
| All scores ≥ 0.55 | **GO** - Proceed to validation |
| Any score < 0.40 | **LOOP** or **NO_GO** - Critical weakness |
| Scores 0.40-0.54 | Use judgment based on context |
| Max 3 iterations | Force terminal decision |

---

## 3. Agent Definitions with Scoring Rubrics

### 3.1 Target Hypothesis Agent

**Role**: Transform research questions into structured, target-specific drug discovery hypotheses.

**Why this agent?**: Drug discovery begins with target identification. Unlike general scientific hypotheses, drug discovery hypotheses must specify:
- The molecular target (protein, pathway, etc.)
- The proposed intervention mechanism
- The expected therapeutic outcome
- The disease context

**Output Components**:
- REASONING: Thought process explaining target and mechanism choice
- HYPOTHESIS: Clear, testable statement
- TARGET: Specific molecular target with domain/site
- MECHANISM: Intervention type (inhibition/activation/degradation/etc.)
- DISEASE: Specific indication and patient population
- BIOLOGICAL RATIONALE: Causal chain from target to disease
- KEY ASSUMPTIONS: What must be true for hypothesis to work
- VALIDATION CRITERIA: Measurable success endpoints

*Note: This agent does not produce a score; it generates the hypothesis for downstream evaluation.*

---

### 3.2 Literature Evidence Agent

**Role**: Retrieve and synthesize existing scientific evidence relevant to the hypothesis.

**Why this agent?**: Evidence grounding prevents:
- Proposing already-disproven hypotheses
- Missing critical known mechanisms
- Overlooking existing drugs (competitive landscape)
- Ignoring known safety signals

#### Scoring Rubric: EVIDENCE_CONFIDENCE

| Score | Criteria |
|-------|----------|
| **0.85-1.0** (Excellent) | Strong human genetic evidence (GWAS with p<5e-8, Mendelian disease link, or validated CRISPR essentiality). Clinical proof-of-concept exists. Clear causal mechanism established. |
| **0.70-0.84** (Strong) | Moderate genetic evidence OR strong mechanistic data with animal model validation. Some clinical data exists (even if failed, lessons learned). Well-understood biology. |
| **0.55-0.69** (Adequate) | Limited genetic evidence but solid preclinical rationale. Animal models show efficacy. Mechanism understood but not fully validated in humans. Some knowledge gaps. |
| **0.40-0.54** (Weak) | Correlative evidence only (expression changes, no genetic link). Preclinical data inconsistent or limited. Significant translation concerns. Major knowledge gaps. |
| **0.25-0.39** (Poor) | Minimal supporting evidence. Target-disease link speculative. No genetic validation. Conflicting preclinical data. |
| **0.0-0.24** (Critical) | No credible evidence. Hypothesis based on theory only. No experimental support. |

**Composite Score Calculation**:
- Genetic evidence: 0-1 (weighted 2x)
- Mechanistic understanding: 0-1
- Clinical precedent: 0-1
- Overall = (2×Genetic + Mechanistic + Clinical) / 4

**Required**: One-sentence justification explaining score based on rubric.

---

### 3.3 Druggability Assessment Agent

**Role**: Evaluate whether the target and proposed mechanism are amenable to drug intervention.

**Why this agent?**: This is the critical gap in generic hypothesis systems. Many biologically valid targets fail as drug targets due to:
- Lack of suitable binding pockets
- Selectivity challenges (off-target toxicity risk)
- Resistance mechanisms
- Tissue penetration requirements

#### Scoring Rubric: DRUGGABILITY_SCORE

| Score | Criteria |
|-------|----------|
| **0.85-1.0** (Highly Druggable) | Well-defined binding pocket with existing drug-like ligands. Multiple approved drugs in same target class. Clear path to selectivity. Established modality works well. |
| **0.70-0.84** (Druggable) | Good structural knowledge with identifiable binding site. Tool compounds exist with reasonable potency (<100nM). Selectivity achievable based on precedent. One or more viable modalities. |
| **0.55-0.69** (Moderately Druggable) | Structure available but binding site challenging (shallow, flexible, or polar). Limited chemical matter. Selectivity concerns but potentially addressable. May require novel modality. |
| **0.40-0.54** (Challenging) | Poor binding site characteristics OR significant selectivity hurdles. No good tool compounds. Limited precedent for this target class. Requires significant innovation. |
| **0.25-0.39** (Difficult) | Intrinsically disordered regions, flat PPI interface, or intracellular localization blocking biologics. Historical failures in this target class. No clear modality path. |
| **0.0-0.24** (Undruggable) | No identifiable binding site. Transcription factor without cofactor pocket. Essential protein where any modulation causes toxicity. No viable modality. |

**Composite Score Calculation**:
- Structural tractability: 0-1
- Selectivity achievability: 0-1
- Modality feasibility: 0-1
- Overall = Average of above three

**Required**: One-sentence justification explaining score based on rubric.

---

### 3.4 Novelty Analysis Agent

**Role**: Assess the novelty of the hypothesis and identify underexplored opportunities.

**Why this agent?**: This is the KEY DIFFERENTIATOR for drug discovery. The PLK1 example illustrates this perfectly:
- ATP-competitive PLK1 inhibitors: heavily explored, selectivity issues
- PBD-targeting inhibitors: underexplored, potentially more selective
- The "gap" (PBD targeting) is where the novel hypothesis lies

#### Scoring Rubric: NOVELTY_SCORE

| Score | Criteria |
|-------|----------|
| **0.85-1.0** (Highly Novel) | First-in-class target with no competition. Clear white space with strong scientific rationale. Open IP landscape. Potential to define new treatment paradigm. |
| **0.70-0.84** (Novel) | Best-in-class opportunity with clear differentiation. Few competitors (<3 clinical programs). Novel mechanism or modality vs existing approaches. Good IP position. |
| **0.55-0.69** (Moderately Novel) | Validated target with room for differentiation. Moderate competition (3-5 programs). Some white space in indication or mechanism. Workable IP situation. |
| **0.40-0.54** (Limited Novelty) | Fast-follower opportunity. Crowded space (5-10 programs) but differentiation possible. Must out-execute competitors. IP constraints may exist. |
| **0.25-0.39** (Low Novelty) | Me-too approach. Highly competitive (>10 programs). Limited differentiation potential. Significant IP barriers. Late entrant disadvantage. |
| **0.0-0.24** (No Novelty) | Multiple approved drugs exist. Saturated market. No clear differentiation. Blocked by patents. No strategic rationale for entry. |

**Composite Score Calculation**:
- Differentiation potential: 0-1
- White space availability: 0-1
- Timing advantage: 0-1
- Overall = Average of above three

**Required**: One-sentence justification explaining score based on rubric.

---

### 3.5 Preclinical Design Agent

**Role**: Design a minimal experimental plan to test the hypothesis.

**Why this agent?**: A hypothesis is only valuable if it's testable. This agent ensures:
- Experiments are feasible and appropriately scoped
- The right models and assays are proposed
- Success criteria are defined upfront

#### Scoring Rubric: FEASIBILITY_SCORE

| Score | Criteria |
|-------|----------|
| **0.85-1.0** (Highly Feasible) | Standard assays and models readily available. Tool compounds exist. Clear biomarkers identified. Straightforward path with <12 months to key decision. Low technical risk. |
| **0.70-0.84** (Feasible) | Most assays established, some optimization needed. Relevant models available. Reasonable biomarker strategy. 12-18 month timeline. Moderate technical risk. |
| **0.55-0.69** (Moderately Feasible) | Some assays need development. Animal models imperfect but usable. Biomarker strategy needs work. 18-24 month timeline. Notable technical hurdles. |
| **0.40-0.54** (Challenging) | Significant assay development required. Limited model options. Biomarker gaps. >24 month timeline. High technical risk. Requires specialized expertise. |
| **0.25-0.39** (Difficult) | Major technical barriers. No good disease models. No validated biomarkers. Unclear timeline. Very high risk. May require technology breakthrough. |
| **0.0-0.24** (Not Feasible) | No path to validation with current technology. Models don't exist. Cannot measure relevant endpoints. Prohibitive resource requirements. |

**Composite Score Calculation**:
- Technical feasibility: 0-1
- Resource availability: 0-1
- Timeline realism: 0-1
- Overall = Average of above three

**Required**: One-sentence justification explaining score based on rubric.

---

### 3.6 Controller Agent

**Role**: Orchestrate the workflow and make routing decisions based on agent outputs.

**Why this agent?**: Drug discovery is inherently iterative. The controller enables:
- Dynamic re-routing based on quality scores
- Hypothesis refinement when needed
- Early termination of non-viable hypotheses
- Final go/no-go decisions

#### Decision Logic

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROLLER DECISION TREE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  All scores ≥ 0.55?                                         │
│       │                                                      │
│       ├── YES ──▶ GO (proceed to experimental validation)   │
│       │                                                      │
│       └── NO ───▶ Any score < 0.40?                         │
│                       │                                      │
│                       ├── YES & loops remaining ──▶ LOOP    │
│                       │       │                              │
│                       │       ├── Low evidence ──▶          │
│                       │       │     literature_evidence      │
│                       │       │                              │
│                       │       ├── Low druggability/novelty ─▶│
│                       │       │     target_hypothesis        │
│                       │       │                              │
│                       │       └── Low feasibility ──▶        │
│                       │             preclinical_design       │
│                       │                                      │
│                       ├── YES & no loops ──▶ NO_GO          │
│                       │                                      │
│                       └── NO (scores 0.40-0.54) ──▶         │
│                             Use judgment, may GO or LOOP     │
│                                                              │
│  Max iterations: 3 (forces terminal GO/NO_GO decision)      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Loop Targets

| Weak Dimension | Loop Target | Rationale |
|----------------|-------------|-----------|
| Evidence | literature_evidence | Re-evaluate with different framing |
| Druggability | target_hypothesis | Consider different target or mechanism |
| Novelty | target_hypothesis | Pivot to more differentiated approach |
| Feasibility | preclinical_design | Simplify experimental plan |

---

## 4. Memory Architecture

### 4.1 Memory Types

The system employs three types of memory to support hypothesis generation and refinement:

| Memory Type | Scope | Purpose | Implementation |
|-------------|-------|---------|----------------|
| **Working Memory** | Single pipeline run | Store intermediate outputs, scores, and feedback | State dictionary passed between agents |
| **Episodic Memory** | Within iteration | Track what was tried and why it failed/succeeded | Feedback field with controller reasoning |
| **Semantic Memory** | Cross-session (future) | Store successful hypothesis patterns for learning | Database of GO decisions with features |

### 4.2 Current Implementation: Working Memory

```python
state = {
    # Hypothesis context (persists through iterations)
    "question": str,
    "hypothesis": str,
    
    # Agent outputs (updated each pass)
    "evidence": str,
    "druggability": str,
    "novelty": str,
    "preclinical": str,
    
    # Scores (numerical summaries)
    "evidence_score": float,
    "druggability_score": float,
    "novelty_score": float,
    "feasibility_score": float,
    
    # Control memory
    "loops_used": int,
    "feedback": str,  # Why we looped - episodic memory
}
```

### 4.3 Memory Flow

```
Iteration 1:
  hypothesis_v1 → scores → feedback: "low novelty, pivot to PBD"
                                          ↓
Iteration 2:                         [feedback informs]
  hypothesis_v2 → scores → feedback: "all adequate"
                                          ↓
                                    GO decision
```

**Key Design Decision**: Feedback is passed as natural language rather than structured data. This allows the controller to provide nuanced guidance ("consider PBD instead of ATP site") rather than just numeric signals.

### 4.4 Memory Limitations (Current Design)

| Limitation | Impact | Future Enhancement |
|------------|--------|-------------------|
| No cross-session memory | Cannot learn from past runs | Add hypothesis database |
| No retrieval mechanism | Cannot find similar past hypotheses | Add vector similarity search |
| Linear feedback only | Cannot branch into parallel hypotheses | Add hypothesis tree structure |

---

## 5. Tools and External Integrations

### 5.1 Current Tool Design

The current implementation uses **LLM knowledge only** - no external API calls. This is a deliberate design choice for the initial version.

| Tool Category | Status | Rationale |
|---------------|--------|-----------|
| Literature Search (PubMed) | 🔮 Planned | Would ground evidence in real citations |
| Structure Database (PDB) | 🔮 Planned | Would improve druggability assessment |
| Clinical Trials (ClinicalTrials.gov) | 🔮 Planned | Would improve competitive landscape |
| Patent Search | 🔮 Planned | Would improve freedom-to-operate analysis |
| LLM Reasoning | ✅ Active | Primary tool for all agents |

### 5.2 Tool Integration Architecture (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Target    Literature   Druggability   Novelty   Preclinical│
│  Hypoth.   Evidence     Assessment     Analysis  Design     │
└─────┬──────────┬────────────┬────────────┬──────────┬───────┘
      │          │            │            │          │
      ▼          ▼            ▼            ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                      TOOL LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  PubMed    ChEMBL    PDB/AlphaFold   ClinicalTrials  Patent │
│  Search    Search    Structure       Search          Search │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Tool Assignment by Agent

| Agent | Primary Tools | Purpose |
|-------|--------------|---------|
| Target Hypothesis | Disease ontology, Gene databases | Identify valid targets |
| Literature Evidence | **PubMed**, **ChEMBL** | Ground claims in real papers |
| Druggability | **PDB**, **AlphaFold**, ChEMBL | Assess structural tractability |
| Novelty | **ClinicalTrials.gov**, Patent DBs | Map competitive landscape |
| Preclinical Design | Assay databases, Model catalogs | Identify available resources |
| Controller | None (reasoning only) | Orchestration |

### 5.4 Why No Tools in Current Version?

| Reason | Explanation |
|--------|-------------|
| Scope control | Focus on architecture, not API integration |
| LLM knowledge sufficient | GPT-4/Claude have substantial biomedical knowledge |
| Reproducibility | External APIs introduce variability |
| Cost | API calls add latency and cost |
| Demonstration | Core value is in reasoning flow, not data retrieval |

**Recommendation for production**: Add PubMed and ClinicalTrials.gov first - these provide highest value for evidence grounding and competitive intelligence.

---

## 6. State Management

### 4.1 State Schema

```python
state = {
    # Input
    "question": str,           # Original research question
    
    # Hypothesis (from Target Hypothesis Agent)
    "hypothesis": str,         # Full hypothesis output
    
    # Evidence (from Literature Evidence Agent)
    "evidence": str,           # Full evidence synthesis
    "evidence_score": float,   # 0.0-1.0, None until computed
    
    # Druggability (from Druggability Agent)
    "druggability": str,       # Full druggability assessment
    "druggability_score": float,
    
    # Novelty (from Novelty Agent)
    "novelty": str,            # Full novelty analysis
    "novelty_score": float,
    
    # Preclinical (from Preclinical Design Agent)
    "preclinical": str,        # Full experimental plan
    "feasibility_score": float,
    
    # Control
    "loops_used": int,         # Number of refinement loops (max 3)
    "feedback": str,           # Controller feedback for refinement
}
```

### 4.2 Score Propagation

Scores are computed incrementally as each agent completes:

1. **After Literature Evidence**: `evidence_score` available
2. **After Druggability**: `druggability_score` available
3. **After Novelty**: `novelty_score` available
4. **After Preclinical Design**: `feasibility_score` available
5. **Controller**: All scores available for decision

---

## 5. Routing Logic

### 5.1 Flow Diagram

```
                    ┌─────────────────┐
                    │  START (Entry)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
        ┌──────────│    TARGET       │◀─────────────┐
        │          │   HYPOTHESIS    │              │
        │          └────────┬────────┘              │
        │                   │                       │
        │                   ▼                       │
        │          ┌─────────────────┐              │
        │    ┌────▶│   LITERATURE    │              │
        │    │     │    EVIDENCE     │              │
        │    │     │ [SCORE: 0-1]    │              │
        │    │     └────────┬────────┘              │
        │    │              │                       │
        │    │              ▼                       │
        │    │     ┌─────────────────┐              │
        │    │     │  DRUGGABILITY   │              │
        │    │     │ [SCORE: 0-1]    │              │
        │    │     └────────┬────────┘              │
        │    │              │                       │
        │    │              ▼                       │
        │    │     ┌─────────────────┐              │
        │    │     │    NOVELTY      │              │
        │    │     │ [SCORE: 0-1]    │              │
        │    │     └────────┬────────┘              │
        │    │              │                       │
        │    │              ▼                       │
        │    │     ┌─────────────────┐              │
        │    └─────│   PRECLINICAL   │◀────────┐    │
        │          │     DESIGN      │         │    │
        │          │ [SCORE: 0-1]    │         │    │
        │          └────────┬────────┘         │    │
        │                   │                  │    │
        │                   ▼                  │    │
        │          ┌─────────────────┐         │    │
        │          │   CONTROLLER    │─────────┴────┘
        │          │  (max 3 loops)  │    (re-route)
        │          └────────┬────────┘
        │                   │
        │         ┌─────────┴─────────┐
        │         ▼                   ▼
        │   ┌──────────┐        ┌──────────┐
        │   │    GO    │        │  NO_GO   │
        │   │ (success)│        │ (reject) │
        │   └──────────┘        └──────────┘
        │
        └──── (re_scope feedback loop)
```

---

## 6. Decision Rationale Summary

### 6.1 Why These Specific Agents?

| Agent | Rationale |
|-------|-----------|
| Target Hypothesis | Drug discovery is target-centric; need structured hypothesis format |
| Literature Evidence | Evidence grounding prevents redundant/disproven hypotheses |
| Druggability | **Critical gap** in generic systems; many valid targets aren't druggable |
| Novelty | **Key differentiator**; drug discovery requires novel angles |
| Preclinical Design | Hypothesis value depends on testability |
| Controller | Enables iterative refinement characteristic of real drug discovery |

### 6.2 Why Explicit Scoring Rubrics?

| Problem | Solution |
|---------|----------|
| Inconsistent scoring across runs | Explicit criteria anchor scores to observable evidence |
| Generous/optimistic bias | Rubric forces acknowledgment of weaknesses |
| Unclear score meaning | Thresholds define what each range means |
| No accountability | Required justification links score to specific evidence |

### 6.3 Why Dynamic vs Sequential Routing?

| Aspect | Sequential | Dynamic (Chosen) |
|--------|------------|------------------|
| Reflects real drug discovery? | No | Yes |
| Handles poor-quality intermediate outputs? | No | Yes |
| Enables hypothesis refinement? | No | Yes |
| Allows early termination? | No | Yes |
| Complexity | Lower | Higher |
| Token usage | Predictable | Variable |

**Conclusion**: Dynamic routing better models real drug discovery reasoning despite higher complexity.

### 6.4 Why These Routing Thresholds?

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| Strong score | ≥ 0.70 | High confidence, no concerns |
| Adequate score | ≥ 0.55 | Acceptable for proceeding |
| Weak score | ≥ 0.40 | Needs attention but not fatal |
| Critical weakness | < 0.40 | Requires intervention or rejection |
| Max iterations | 3 | Prevents infinite loops; forces decision |

---

## 7. Example Walkthrough

### Input
```
Question: "Can we develop a more selective PLK1 inhibitor for cancer treatment?"
```

### Iteration 1

**Target Hypothesis Agent**:
```
REASONING: PLK1 is a validated oncology target with proven clinical efficacy 
but selectivity issues. The ATP site is highly conserved, making selectivity 
challenging. I'll start with the conventional ATP-competitive approach.

TARGET: PLK1 kinase domain ATP-binding site
MECHANISM: ATP-competitive inhibition
DISEASE: Solid tumors with PLK1 overexpression
RATIONALE: PLK1 is overexpressed in many cancers and drives proliferation
OUTCOME: >90% PLK1 inhibition in tumor xenografts with minimal PLK2/3 activity
```

**Literature Evidence Agent**:
```
EVIDENCE SYNTHESIS:
- GENETIC VALIDATION: Strong (essential gene in cancer, CRISPR screens)
- EXISTING INTERVENTIONS: Multiple ATP-competitive inhibitors (BI2536, Volasertib)
  in clinical trials; selectivity issues limit therapeutic window
- CLINICAL PRECEDENT: Volasertib reached Phase 3 but failed to show OS benefit

EVIDENCE_CONFIDENCE: 0.72
- Genetic evidence: 0.85
- Mechanistic understanding: 0.80
- Clinical precedent: 0.50 (failures inform limitations)
- Overall: 0.72

Justification: Strong genetic and biological validation, but clinical 
precedent shows ATP-competitive approach has hit ceiling.
```

**Druggability Agent**:
```
STRUCTURAL DRUGGABILITY: Well-characterized kinase domain, multiple structures
SELECTIVITY ASSESSMENT: ATP-binding site highly conserved across PLK family
  - High risk of PLK2/3 inhibition → hematological toxicity
  - Therapeutic window severely limited

DRUGGABILITY_SCORE: 0.45
- Structural tractability: 0.85
- Selectivity achievability: 0.25
- Modality feasibility: 0.75
- Overall: 0.45

Justification: Excellent structure but selectivity in ATP pocket is the 
known limiting factor causing clinical failures.

CRITICAL CONCERNS: ["Selectivity challenge in ATP pocket is fundamental"]
```

**Novelty Agent**:
```
COMPETITIVE LANDSCAPE: >10 clinical programs targeting ATP site
NOVELTY_CLASSIFICATION: ME_TOO
WHITE_SPACE: PBD-targeting approach is underexplored

NOVELTY_SCORE: 0.25
- Differentiation: 0.20
- White space: 0.30
- Timing advantage: 0.25
- Overall: 0.25

Justification: Highly crowded space with no clear differentiation from 
existing ATP-competitive approaches.

RECOMMENDATION: pivot
```

**Controller Decision**:
```
PORTFOLIO ANALYSIS:
- Evidence: 0.72 [Strong]
- Druggability: 0.45 [Weak - selectivity limiting]
- Novelty: 0.25 [Poor - crowded, undifferentiated]
- Feasibility: (not evaluated due to early intervention)

Weakest Link: Novelty (0.25) - hypothesis is not differentiated

DECISION: LOOP
LOOP_TARGET: target_hypothesis

REASONING: While evidence is strong, both druggability (0.45) and 
novelty (0.25) are below adequate thresholds. The selectivity challenge 
in the ATP pocket is well-documented in the literature. Need to pivot 
to a differentiated approach.

NEXT STEPS: Consider targeting polo-box domain (PBD) instead of ATP 
site for improved selectivity. PBD is unique to PLK family.
```

### Iteration 2

**Target Hypothesis Agent** (with feedback):
```
REASONING: Based on controller feedback, I'm pivoting to the polo-box 
domain which offers structural uniqueness within the PLK family. The PBD 
is essential for substrate recognition and localization, providing a 
mechanistically distinct approach to PLK1 inhibition.

TARGET: PLK1 polo-box domain (PBD)
MECHANISM: PBD inhibition disrupting substrate recognition and localization
DISEASE: Solid tumors with PLK1 overexpression
RATIONALE: PBD is unique to PLK family, enabling selective inhibition 
without affecting related kinases
OUTCOME: Selective PLK1 inhibition with >100x selectivity over PLK2/3
```

**Literature Evidence Agent**:
```
EVIDENCE SYNTHESIS:
- GENETIC VALIDATION: Same strong evidence (PLK1 essentiality)
- EXISTING INTERVENTIONS: Few PBD inhibitors (Poloxin, early stage)
- KEY UNCERTAINTIES: PBD inhibitor efficacy in vivo less validated

EVIDENCE_CONFIDENCE: 0.62
- Genetic evidence: 0.85
- Mechanistic understanding: 0.60
- Clinical precedent: 0.30 (no clinical data for PBD approach)
- Overall: 0.62

Justification: Genetic validation still strong but PBD mechanism less 
proven than ATP-competitive approach. Reasonable preclinical data exists.
```

**Druggability Agent**:
```
STRUCTURAL DRUGGABILITY: PBD structure known (multiple crystal structures)
  - Defined binding pocket at phosphopeptide recognition site
  - Less conserved than ATP site
  
SELECTIVITY ASSESSMENT: PBD sequence diverges between PLK1/2/3
  - Selectivity achievable based on structural analysis

DRUGGABILITY_SCORE: 0.68
- Structural tractability: 0.70
- Selectivity achievability: 0.75
- Modality feasibility: 0.60
- Overall: 0.68

Justification: Good structural basis for selectivity but smaller pocket 
may limit chemical space; feasible with medicinal chemistry optimization.
```

**Novelty Agent**:
```
COMPETITIVE LANDSCAPE: <3 programs targeting PBD
NOVELTY_CLASSIFICATION: BEST_IN_CLASS
WHITE_SPACE: PBD targeting underexplored despite structural rationale

NOVELTY_SCORE: 0.75
- Differentiation: 0.80
- White space: 0.75
- Timing advantage: 0.70
- Overall: 0.75

Justification: Clear differentiation from crowded ATP-competitive space 
with scientific rationale for improved selectivity.
```

**Preclinical Design Agent**:
```
TARGET VALIDATION: 
- CRISPR PLK1 knockin with PBD mutations (selectivity-defining residues)
- siRNA validation in panel of cancer cell lines

MECHANISM STUDIES: 
- FP assay for PBD binding
- Cellular PLK1 localization (PBD disruption should mislocalize)
- Phospho-substrate biomarkers

FEASIBILITY_SCORE: 0.72
- Technical feasibility: 0.75
- Resource availability: 0.70
- Timeline realism: 0.70
- Overall: 0.72

Justification: Standard assays applicable, PBD binding assays exist, 
in vivo models same as ATP-competitive programs.
```

**Controller Decision**:
```
PORTFOLIO ANALYSIS:
- Evidence: 0.62 [Adequate]
- Druggability: 0.68 [Adequate]
- Novelty: 0.75 [Strong]
- Feasibility: 0.72 [Strong]

Composite Score: 0.69 (Adequate overall)

Weakest Link: Evidence (0.62) - less clinical validation for PBD approach

DECISION: GO

REASONING: All scores are ≥0.55 (adequate threshold). The pivot to PBD 
targeting has resolved the critical novelty and selectivity concerns. 
While evidence confidence is lower than the ATP approach, the improved 
druggability and strong novelty scores justify proceeding.

NEXT STEPS:
1. Develop PBD binding assay (FP-based)
2. Validate selectivity hypothesis with PLK1/2/3 panel
3. Demonstrate cellular target engagement
4. GO/NO-GO decision at 6 months based on selectivity data
```

---

## 8. Alternative Approaches Analysis

This section analyzes major design alternatives that were considered, with explicit pros and cons for each decision.

### 8.1 Agent Architecture Alternatives

#### Option A: Monolithic Single-Agent (Rejected)

One powerful LLM handles the entire hypothesis generation in a single prompt.

```
┌─────────────────────────────────────┐
│         SINGLE MEGA-AGENT           │
│  (hypothesis + evidence + drugs +   │
│   novelty + design in one prompt)   │
└─────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Simpler implementation | No iterative refinement possible |
| Lower latency (one LLM call) | Context window limits depth |
| No state management needed | Cannot specialize prompts |
| Cheaper (fewer tokens total) | All-or-nothing output |
| | No intermediate checkpoints |
| | Harder to debug failures |

**Why rejected**: Drug discovery requires deep reasoning in multiple dimensions. A single prompt cannot adequately cover evidence synthesis, structural biology, competitive intelligence, and experimental design with sufficient depth.

#### Option B: Parallel Multi-Agent (Considered)

All evaluation agents run simultaneously, then a synthesizer combines results.

```
                    ┌──────────────┐
                    │   Hypothesis │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Evidence │    │ Druggab. │    │ Novelty  │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         └───────────────┼───────────────┘
                         ▼
                  ┌──────────────┐
                  │  Synthesizer │
                  └──────────────┘
```

| Pros | Cons |
|------|------|
| Faster (parallel execution) | Agents can't inform each other |
| Independent agent failures | Druggability can't use evidence context |
| Easier to scale | No iterative refinement |
| Deterministic execution time | Synthesizer becomes bottleneck |

**Why not chosen**: Sequential flow allows upstream context to inform downstream agents. For example, the Druggability agent benefits from seeing the Evidence synthesis, and the Novelty agent needs Druggability scores to assess true differentiation.

#### Option C: Sequential with Dynamic Routing (Chosen) ✓

Agents run in sequence with controller-mediated feedback loops.

| Pros | Cons |
|------|------|
| Context flows between agents | Higher latency |
| Iterative refinement possible | More complex state management |
| Early termination on failure | Variable execution time |
| Mimics real drug discovery | Higher token usage |
| Intermediate checkpoints | Requires careful routing logic |

**Why chosen**: Best matches the iterative, context-dependent nature of real drug discovery reasoning.

---

### 8.2 Routing Strategy Alternatives

#### Option A: Fixed Sequential (Rejected)

All agents always run in fixed order, no loops.

```
Hypothesis → Evidence → Druggability → Novelty → Design → Output
```

| Pros | Cons |
|------|------|
| Predictable | No refinement on weak hypotheses |
| Simple implementation | Wasted compute on bad paths |
| Consistent latency | Cannot pivot mid-stream |

**Why rejected**: A hypothesis with low novelty score (0.25) would still go through full evaluation. Real drug discovery pivots early when critical issues emerge.

#### Option B: Score-Threshold Gating (Considered)

Stop immediately when any score falls below threshold.

```
Hypothesis → Evidence (0.72) ✓ → Druggability (0.35) ✗ → STOP
```

| Pros | Cons |
|------|------|
| Fast failure | No chance to recover |
| Resource efficient | May reject salvageable hypotheses |
| Clear decision points | Binary (no nuance) |

**Why not chosen**: A low druggability score might be fixed by pivoting to a different mechanism, which requires looping back to Target Hypothesis rather than stopping entirely.

#### Option C: Controller-Mediated Dynamic Routing (Chosen) ✓

Controller agent decides: GO, NO_GO, or LOOP with target.

| Pros | Cons |
|------|------|
| Nuanced decisions | Controller adds latency |
| Can specify what to fix | Controller could make errors |
| Natural language feedback | More complex |
| Mimics human expert | Requires prompt engineering |

**Why chosen**: Allows sophisticated decisions like "novelty is low but fixable by targeting a different domain" rather than binary stop/continue.

---

### 8.3 Scoring Approach Alternatives

#### Option A: No Explicit Scores (Rejected)

Agents provide qualitative assessments only; controller interprets free text.

| Pros | Cons |
|------|------|
| More natural output | Inconsistent interpretation |
| No arbitrary thresholds | Hard to compare across runs |
| Flexible | Controller may miss issues |

**Why rejected**: Quantitative scores enable consistent decision thresholds and tracking across iterations.

#### Option B: Binary Scores (Considered)

Each dimension is simply PASS or FAIL.

| Pros | Cons |
|------|------|
| Simple decisions | Loses nuance |
| Clear thresholds | No differentiation within pass/fail |
| Easy to aggregate | Harder to prioritize improvements |

**Why not chosen**: A 0.55 vs 0.85 score carries important information for prioritization and risk assessment.

#### Option C: Continuous Scores with Rubrics (Chosen) ✓

0.0-1.0 scores with explicit criteria for each range.

| Pros | Cons |
|------|------|
| Nuanced assessment | Requires careful rubric design |
| Consistent via rubrics | LLM may not follow exactly |
| Enables thresholds | Arbitrary boundaries |
| Trackable over iterations | More complex prompts |

**Why chosen**: Rubrics anchor scores to observable evidence, improving consistency and interpretability.

---

### 8.4 Number of Agents Alternatives

#### Option A: Fewer Agents (3-4)

Combine related functions (e.g., Evidence + Druggability + Novelty → "Target Assessment")

| Pros | Cons |
|------|------|
| Less coordination overhead | Each agent does too much |
| Fewer handoffs | Harder to iterate on specific aspects |
| Simpler state | Less specialized prompts |

#### Option B: More Agents (8-10)

Split further (e.g., separate Genetic Evidence, Clinical Evidence, Safety Assessment, IP Analysis)

| Pros | Cons |
|------|------|
| Highly specialized | Coordination complexity |
| Deep expertise per agent | More state to manage |
| Parallel potential | Higher latency if sequential |

#### Option C: Six Agents (Chosen) ✓

Current design: Hypothesis, Evidence, Druggability, Novelty, Design, Controller

| Pros | Cons |
|------|------|
| Matches drug discovery stages | Some agents do multiple things |
| Manageable complexity | Could be split further |
| Clear separation of concerns | - |

**Why chosen**: Maps to natural phases of drug discovery decision-making without excessive fragmentation.

---

### 8.5 Iteration Limit Alternatives

| Max Loops | Pros | Cons |
|-----------|------|------|
| 1 (no loops) | Fast, deterministic | No refinement |
| 2 | Some refinement | May not converge |
| **3 (chosen)** | Good refinement potential | Reasonable compute |
| 5 | More chances to fix | Diminishing returns |
| Unlimited | Maximum flexibility | Risk of infinite loops |

**Why 3 chosen**: Empirically, most hypotheses either succeed in 1-2 iterations or have fundamental issues that more loops won't fix. Three iterations balances refinement opportunity with resource efficiency.

---

### 8.6 Summary: Design Decision Matrix

| Decision | Chosen | Primary Alternative | Key Differentiator |
|----------|--------|--------------------|--------------------|
| Architecture | Sequential + Dynamic | Parallel | Context flow between agents |
| Routing | Controller-mediated | Score-threshold gating | Nuanced pivot decisions |
| Scoring | Continuous + Rubrics | Binary pass/fail | Preserves nuance |
| Agent count | 6 | 3-4 combined | Maps to drug discovery stages |
| Max iterations | 3 | Unlimited | Prevents infinite loops |
| Memory | Working (state dict) | Full episodic | Scope appropriate |
| Tools | LLM-only (v1) | Full API integration | Development focus |

- [x] Define State schema with all agent outputs
- [x] Implement each agent with detailed prompts
- [x] Add explicit scoring rubrics to each scoring agent
- [x] Require score justifications
- [x] Configure routing with nodes and edges
- [x] Implement conditional routing from controller
- [x] Add iteration counter and max iteration logic (3 loops)
- [x] Implement feedback propagation for re-routing
- [ ] Add logging for decision history
- [ ] Test with diverse drug discovery questions
- [ ] Tune routing thresholds based on output quality

---

## 9. Future Enhancements

1. **Real Literature Integration**: Connect to PubMed, ChEMBL, ClinicalTrials.gov APIs
2. **Structure-Aware Reasoning**: Integrate AlphaFold/PDB for structural druggability
3. **Patent Landscape**: Add Freedom-to-Operate analysis with patent databases
4. **Multi-Hypothesis Generation**: Generate and compare multiple hypotheses
5. **Human-in-the-Loop**: Add checkpoints for expert review before terminal decisions
6. **Score Calibration**: Analyze score distributions across many runs to calibrate rubrics

---

## Appendix A: Complete Scoring Rubrics

### Evidence Confidence Rubric (Literature Evidence Agent)

| Score | Genetic Evidence | Mechanistic Data | Clinical Precedent |
|-------|------------------|------------------|-------------------|
| 0.85-1.0 | GWAS p<5e-8, Mendelian link, CRISPR essential | Complete pathway understanding | Clinical PoC demonstrated |
| 0.70-0.84 | Moderate genetic signal | Strong animal model data | Some clinical data exists |
| 0.55-0.69 | Limited but present | Preclinical rationale solid | No clinical data but analogous targets tried |
| 0.40-0.54 | Only correlative | Inconsistent preclinical | Concerning failures in class |
| 0.25-0.39 | None | Speculative | Multiple class failures |
| 0.0-0.24 | Contradictory | None | Definitively disproven |

### Druggability Score Rubric (Druggability Agent)

| Score | Structure | Selectivity | Modality |
|-------|-----------|-------------|----------|
| 0.85-1.0 | Drug-like ligands bound | Approved selective drugs exist | Multiple options work |
| 0.70-0.84 | Tool compounds <100nM | Precedent for selectivity | Clear best modality |
| 0.55-0.69 | Challenging pocket | Addressable concerns | Requires optimization |
| 0.40-0.54 | Poor characteristics | Significant hurdles | Limited options |
| 0.25-0.39 | Disordered/flat | Historical failures | No clear path |
| 0.0-0.24 | No site | Impossible | None viable |

### Novelty Score Rubric (Novelty Agent)

| Score | Competition | Differentiation | IP Landscape |
|-------|-------------|-----------------|--------------|
| 0.85-1.0 | None | First-in-class | Open |
| 0.70-0.84 | <3 programs | Clear best-in-class | Favorable |
| 0.55-0.69 | 3-5 programs | Moderate differentiation | Workable |
| 0.40-0.54 | 5-10 programs | Must out-execute | Constrained |
| 0.25-0.39 | >10 programs | Limited | Crowded |
| 0.0-0.24 | Approved drugs | None | Blocked |

### Feasibility Score Rubric (Preclinical Design Agent)

| Score | Assays | Models | Timeline |
|-------|--------|--------|----------|
| 0.85-1.0 | Standard, available | Validated, predictive | <12 months |
| 0.70-0.84 | Minor optimization | Good options | 12-18 months |
| 0.55-0.69 | Development needed | Imperfect but usable | 18-24 months |
| 0.40-0.54 | Significant development | Limited | >24 months |
| 0.25-0.39 | Major barriers | None good | Unclear |
| 0.0-0.24 | Not possible | Don't exist | Prohibitive |

---

## Appendix B: Prompt Templates

See the `drug_discovery.py` implementation file for complete prompt templates for each agent.
