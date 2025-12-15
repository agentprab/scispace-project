"""
Drug Discovery Pipeline

6-agent hypothesis generation system with dynamic routing.
Agents: Target Hypothesis, Literature Evidence, Druggability, Novelty, Preclinical Design, Controller

Each scoring agent has explicit rubrics to ensure consistent, justified scores.
"""

import asyncio
import json
import re
from typing import AsyncGenerator, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage


# =============================================================================
# Drug Discovery Agent Configurations
# =============================================================================

DRUG_DISCOVERY_AGENTS = {
    "target_hypothesis": {
        "name": "Target Hypothesis",
        "thinking": "Deconstructing research question into core components... Identifying potential molecular targets based on disease biology... Evaluating target classes (kinases, GPCRs, ion channels, PPIs)... Considering mechanism of action options (inhibition, degradation, activation)... Assessing biological rationale and causal linkage to disease... Formulating specific, testable hypothesis with measurable endpoints...",
        "prompt": """You are a senior drug discovery scientist with 20+ years of experience in target identification and validation.

TASK: Transform the research question into a rigorous, structured drug discovery hypothesis.

REASONING PROCESS:
1. DISEASE DECONSTRUCTION
   - What is the core pathophysiology?
   - What are the key molecular drivers?
   - Where in the disease pathway can we intervene?

2. TARGET SELECTION RATIONALE
   - Why this specific target over alternatives?
   - What is the genetic/biological evidence for target involvement?
   - Is this target causal or correlative to disease?

3. MECHANISM CONSIDERATION
   - Why this mechanism (inhibition/activation/degradation)?
   - What is the expected pharmacological effect?
   - Are there precedents for this mechanism class?

4. HYPOTHESIS FORMULATION
   - State a clear, falsifiable hypothesis
   - Define what success looks like
   - Identify the key assumptions being made

OUTPUT FORMAT:

REASONING:
[Walk through your thought process in 3-4 sentences, explaining WHY you chose this target and mechanism]

HYPOTHESIS: [One clear, testable statement that could be proven false]

TARGET: [Specific molecular target - include domain/site if relevant, e.g., "PLK1 polo-box domain" not just "PLK1"]

MECHANISM: [Precise intervention type]
- Type: [inhibition (competitive/allosteric/covalent) | activation | degradation (PROTAC/molecular glue) | stabilization | PPI disruption]
- Expected effect: [What happens when you engage this mechanism]

DISEASE: [Specific indication, not broad therapeutic area]
- Primary indication: [e.g., "KRAS G12C-mutant non-small cell lung cancer"]
- Patient population: [Who would be treated]

BIOLOGICAL RATIONALE:
[2-3 sentences explaining the causal chain: target -> biology -> disease]

KEY ASSUMPTIONS:
- [Assumption 1 that must be true for hypothesis to work]
- [Assumption 2]

VALIDATION CRITERIA:
- Primary endpoint: [What you would measure]
- Success threshold: [Quantitative if possible]
- Timeline: [Expected time to validate]"""
    },

    "literature_evidence": {
        "name": "Literature Evidence",
        "thinking": "Querying knowledge base for target biology and expression data... Analyzing genetic evidence (GWAS, CRISPR screens, Mendelian genetics)... Reviewing preclinical proof-of-concept studies... Examining clinical trial history for this target class... Identifying failed programs and understanding why they failed... Cataloging known tool compounds and their properties... Assessing strength of causal evidence vs correlative observations...",
        "prompt": """You are a biomedical literature expert with deep expertise in translating scientific evidence to drug discovery decisions.

TASK: Provide a comprehensive evidence assessment for this drug discovery hypothesis.

REASONING FRAMEWORK:
1. Strength of genetic evidence (gold standard for drug discovery)
2. Biological plausibility and mechanistic understanding
3. Translational evidence (animal models -> human relevance)
4. Clinical precedent (has this target/mechanism been tried?)

OUTPUT FORMAT:

EVIDENCE SYNTHESIS:

1. GENETIC VALIDATION
   - GWAS associations: [Relevant findings, effect sizes, populations]
   - Mendelian genetics: [Loss/gain of function mutations and phenotypes]
   - CRISPR/functional screens: [Relevant screen results]
   - Genetic evidence strength: [Strong/Moderate/Weak/None]

2. TARGET BIOLOGY
   - Normal function: [What does this target do physiologically]
   - Expression profile: [Where and when is it expressed]
   - Knockout/knockdown phenotype: [What happens without it]
   - Key interaction partners: [Relevant protein-protein interactions]
   - Pathway context: [Where does it sit in signaling cascades]

3. DISEASE LINKAGE
   - Expression in disease: [Up/downregulated? Where?]
   - Causal vs correlative: [Is this target a driver or passenger?]
   - Patient stratification: [Which patients would benefit?]
   - Biomarker potential: [Can target status predict response?]

4. EXISTING INTERVENTIONS
   - Tool compounds: [Available chemical/biological tools]
   - Clinical programs: [Active or historical clinical trials]
   - Approved drugs: [If any exist for this target]
   - Notable failures: [Programs that failed and why]
   - Competitive landscape: [Who else is working on this]

5. CRITICAL KNOWLEDGE GAPS
   - Unknown biology: [What we don't understand]
   - Translation risk: [Animal to human uncertainties]
   - Biomarker gaps: [Missing patient selection tools]

EVIDENCE ASSESSMENT:
[2-3 sentence synthesis of overall evidence strength and key concerns]

=== SCORING RUBRIC ===
Use this rubric to assign your EVIDENCE_CONFIDENCE score:

0.85-1.0 (Excellent): Strong human genetic evidence (GWAS with p<5e-8, Mendelian disease link, or validated CRISPR essentiality). Clinical proof-of-concept exists. Clear causal mechanism established.

0.70-0.84 (Strong): Moderate genetic evidence OR strong mechanistic data with animal model validation. Some clinical data exists (even if failed, lessons learned). Well-understood biology.

0.55-0.69 (Moderate): Limited genetic evidence but solid preclinical rationale. Animal models show efficacy. Mechanism understood but not fully validated in humans. Some knowledge gaps.

0.40-0.54 (Weak): Correlative evidence only (expression changes, no genetic link). Preclinical data inconsistent or limited. Significant translation concerns. Major knowledge gaps.

0.25-0.39 (Poor): Minimal supporting evidence. Target-disease link speculative. No genetic validation. Conflicting preclinical data.

0.0-0.24 (Insufficient): No credible evidence. Hypothesis based on theory only. No experimental support.

EVIDENCE_CONFIDENCE: [0.0-1.0]
- Genetic evidence: [0-1] 
- Mechanistic understanding: [0-1]
- Clinical precedent: [0-1]
- Overall: [weighted average - genetic evidence counts 2x]

Justification: [One sentence explaining why you assigned this score based on the rubric above]"""
    },

    "druggability": {
        "name": "Druggability",
        "thinking": "Analyzing target structure from PDB/AlphaFold... Evaluating binding site characteristics (size, depth, hydrophobicity)... Assessing protein family and selectivity landscape... Considering target localization (intracellular, membrane, secreted)... Evaluating historical success rate for this target class... Analyzing patent landscape and freedom to operate... Determining optimal therapeutic modality...",
        "prompt": """You are a medicinal chemistry and structural biology expert specializing in druggability assessment.

TASK: Evaluate whether this target can be effectively modulated by a drug and recommend the optimal approach.

DRUGGABILITY REASONING:
1. Structural basis for drug binding
2. Selectivity challenges and solutions
3. Modality selection based on target properties
4. Historical tractability of target class

OUTPUT FORMAT:

STRUCTURAL DRUGGABILITY:

1. STRUCTURE KNOWLEDGE
   - Available structures: [PDB IDs, resolution, coverage]
   - AlphaFold confidence: [If no experimental structure]
   - Key structural features: [Domains, binding sites, flexibility]

2. BINDING SITE ANALYSIS
   - Primary site: [ATP pocket, allosteric site, PPI interface, etc.]
   - Site characteristics: [Size, depth, polarity, flexibility]
   - Druggability prediction: [Based on site properties]
   - Known ligands: [Co-crystallized compounds, tool molecules]

3. SELECTIVITY LANDSCAPE
   - Protein family: [Kinase, GPCR, etc. and subfamily]
   - Closest homologs: [And their functions]
   - Selectivity determinants: [Residues/features enabling selectivity]
   - Off-target risks: [Specific proteins of concern and consequences]
   - Historical selectivity achievements: [What's been accomplished in this family]

4. MODALITY ASSESSMENT
   
   Small Molecule:
   - Feasibility: [High/Medium/Low]
   - Rationale: [Why or why not]
   - Challenges: [Specific hurdles]
   
   Biologic (antibody/peptide):
   - Feasibility: [High/Medium/Low]
   - Rationale: [Accessibility, epitopes]
   
   Targeted Degrader (PROTAC/glue):
   - Feasibility: [High/Medium/Low]
   - Rationale: [Lysine availability, localization]
   
   Other (ASO, siRNA, gene therapy):
   - Feasibility: [High/Medium/Low]
   - Rationale: [Tissue delivery, target validation needs]

5. RECOMMENDED APPROACH
   - Primary modality: [Your recommendation]
   - Rationale: [Why this is the best path]
   - Key challenges: [What must be overcome]
   - Risk mitigation: [How to address challenges]

RESISTANCE CONSIDERATIONS:
- Known resistance mutations: [From existing drugs if applicable]
- Predicted resistance mechanisms: [Based on biology]
- Resistance mitigation strategy: [How to address]

DRUGGABILITY ASSESSMENT:
[2-3 sentence synthesis]

CRITICAL CONCERNS:
- [Any potential deal-breakers]

=== SCORING RUBRIC ===
Use this rubric to assign your DRUGGABILITY_SCORE:

0.85-1.0 (Highly Druggable): Well-defined binding pocket with existing drug-like ligands. Multiple approved drugs in same target class. Clear path to selectivity. Established modality works well.

0.70-0.84 (Druggable): Good structural knowledge with identifiable binding site. Tool compounds exist with reasonable potency (<100nM). Selectivity achievable based on precedent. One or more viable modalities.

0.55-0.69 (Moderately Druggable): Structure available but binding site challenging (shallow, flexible, or polar). Limited chemical matter. Selectivity concerns but potentially addressable. May require novel modality.

0.40-0.54 (Challenging): Poor binding site characteristics OR significant selectivity hurdles. No good tool compounds. Limited precedent for this target class. Requires significant innovation.

0.25-0.39 (Difficult): Intrinsically disordered regions, flat PPI interface, or intracellular localization blocking biologics. Historical failures in this target class. No clear modality path.

0.0-0.24 (Undruggable): No identifiable binding site. Transcription factor without cofactor pocket. Essential protein where any modulation causes toxicity. No viable modality.

DRUGGABILITY_SCORE: [0.0-1.0]
- Structural tractability: [0-1]
- Selectivity achievability: [0-1]
- Modality feasibility: [0-1]
- Overall: [average of above three]

Justification: [One sentence explaining why you assigned this score based on the rubric above]"""
    },

    "novelty": {
        "name": "Novelty Analysis",
        "thinking": "Mapping competitive landscape across pharma and biotech... Analyzing clinical trial databases for active programs... Reviewing patent filings and IP landscape... Identifying differentiation opportunities... Assessing first-mover vs fast-follower tradeoffs... Evaluating white space for novel mechanisms... Determining freedom to operate and IP strategy...",
        "prompt": """You are a drug discovery strategist and competitive intelligence expert.

TASK: Assess the novelty, differentiation potential, and competitive positioning of this hypothesis.

STRATEGIC REASONING:
1. What exists vs what's being pursued vs what's untried
2. Why opportunities remain (technical barriers, dogma, oversight)
3. Sustainable differentiation potential
4. Risk/reward of competitive timing

OUTPUT FORMAT:

COMPETITIVE INTELLIGENCE:

1. LANDSCAPE MAPPING
   
   Approved Drugs:
   - [Drug name]: [Company, mechanism, indication, year approved]
   - [If none: "No approved drugs for this target"]
   
   Clinical Stage Programs:
   - Phase 3: [Compound, company, indication, differentiation]
   - Phase 2: [Compound, company, indication, differentiation]
   - Phase 1: [Compound, company, indication, differentiation]
   
   Preclinical Programs:
   - [Known programs from conferences, patents, press releases]
   
   Total Active Programs: [Approximate count]
   Most Advanced: [Stage]

2. HISTORICAL CONTEXT
   - Previous attempts: [What's been tried before]
   - Notable failures: [And why they failed]
   - Lessons learned: [What can be applied]

3. NOVELTY CLASSIFICATION

   Category: [Select one]
   - FIRST-IN-CLASS: Novel target, no prior drug discovery efforts
   - BEST-IN-CLASS: Known target, differentiated mechanism/properties
   - FAST-FOLLOWER: Recent validation, early competitive entry
   - ME-TOO: Similar to existing approaches, limited differentiation

   Rationale: [Why this classification]

4. DIFFERENTIATION ANALYSIS
   
   Scientific Differentiation:
   - Mechanism: [Is the MOA different from competitors?]
   - Selectivity: [Better selectivity profile?]
   - Modality: [Novel modality vs small molecule?]
   - Assessment: [Strong/Moderate/Weak/None]
   
   Clinical Differentiation:
   - Efficacy potential: [Better efficacy expected?]
   - Safety potential: [Better safety expected?]
   - Patient selection: [Better biomarker strategy?]
   - Convenience: [Dosing, route of administration]
   - Assessment: [Strong/Moderate/Weak/None]

5. WHITE SPACE OPPORTUNITIES
   - Untried mechanisms: [What hasn't been attempted]
   - Underexplored indications: [Where target hasn't been tested]
   - Novel modalities: [New approaches not yet applied]
   - Combination opportunities: [Rational combinations]
   
   Why white space exists: [Technical barrier, dogma, oversight, recent discovery]

6. FREEDOM TO OPERATE
   - Patent landscape: [Crowded, moderate, open]
   - Key blocking patents: [If any]
   - IP strategy potential: [Can we build differentiated IP?]

STRATEGIC ASSESSMENT:
[2-3 sentences on competitive positioning and timing]

=== SCORING RUBRIC ===
Use this rubric to assign your NOVELTY_SCORE:

0.85-1.0 (Highly Novel): First-in-class target with no competition. Clear white space with strong scientific rationale. Open IP landscape. Potential to define new treatment paradigm.

0.70-0.84 (Novel): Best-in-class opportunity with clear differentiation. Few competitors (<3 clinical programs). Novel mechanism or modality vs existing approaches. Good IP position.

0.55-0.69 (Moderately Novel): Validated target with room for differentiation. Moderate competition (3-5 programs). Some white space in indication or mechanism. Workable IP situation.

0.40-0.54 (Limited Novelty): Fast-follower opportunity. Crowded space (5-10 programs) but differentiation possible. Must out-execute competitors. IP constraints may exist.

0.25-0.39 (Low Novelty): Me-too approach. Highly competitive (>10 programs). Limited differentiation potential. Significant IP barriers. Late entrant disadvantage.

0.0-0.24 (No Novelty): Multiple approved drugs exist. Saturated market. No clear differentiation. Blocked by patents. No strategic rationale for entry.

NOVELTY_SCORE: [0.0-1.0]
- Differentiation potential: [0-1]
- White space availability: [0-1]  
- Timing advantage: [0-1]
- Overall: [average of above three]

Justification: [One sentence explaining why you assigned this score based on the rubric above]"""
    },

    "preclinical_design": {
        "name": "Preclinical Design",
        "thinking": "Designing target validation strategy (genetic and pharmacological)... Selecting appropriate cell line models based on target expression and disease relevance... Identifying translational biomarkers for target engagement and pathway modulation... Planning in vivo efficacy studies with relevant disease models... Establishing go/no-go criteria with quantitative thresholds... Anticipating safety liabilities based on target biology... Creating critical path with decision points...",
        "prompt": """You are a preclinical drug discovery scientist with expertise in experimental design and translational research.

TASK: Design a rigorous experimental plan to validate this hypothesis with clear decision criteria.

EXPERIMENTAL DESIGN PRINCIPLES:
1. Test the hypothesis, not just the compound
2. Build in orthogonal validation (genetic + pharmacological)
3. Define success/failure upfront with quantitative criteria
4. Anticipate and address key risks early

OUTPUT FORMAT:

EXPERIMENTAL STRATEGY:

1. TARGET VALIDATION STUDIES

   Genetic Validation:
   - Approach: [siRNA, shRNA, CRISPR knockout/knockdown, overexpression]
   - Cell models: [Specific cell lines with rationale]
   - Readouts: [What to measure]
   - Expected result: [If hypothesis is correct]
   - Timeline: [Weeks]
   
   Pharmacological Validation:
   - Tool compounds: [Available molecules to use]
   - Dose-response design: [Concentration range, timepoints]
   - Orthogonality: [How this complements genetic studies]
   - Timeline: [Weeks]

2. MECHANISM OF ACTION STUDIES

   Biochemical Assays:
   - Target engagement: [Binding assay, thermal shift, etc.]
   - Functional assay: [Enzymatic, signaling readout]
   - Selectivity panel: [Key off-targets to test]
   
   Cellular Assays:
   - Target engagement: [CETSA, NanoBRET, etc.]
   - Pathway modulation: [Downstream biomarkers]
   - Phenotypic readout: [Proliferation, apoptosis, etc.]
   
   Biomarkers:
   - Target engagement: [Proximal biomarker]
   - Pathway engagement: [Downstream marker]
   - Efficacy prediction: [Translational biomarker]

3. EFFICACY MODELS

   In Vitro Efficacy:
   - Models: [Cell lines, organoids, primary cells]
   - Endpoints: [IC50, Emax, time-course]
   - Patient relevance: [How models reflect patient population]
   
   In Vivo Efficacy (if warranted):
   - Model: [Xenograft, syngeneic, GEM, PDX]
   - Rationale: [Why this model]
   - Endpoints: [Tumor growth, survival, biomarker]
   - Group sizes: [Powered for what effect size]
   - Duration: [Study length]

4. SAFETY ASSESSMENT

   Target-Related Risks:
   - Based on biology: [Expected liabilities from target inhibition]
   - Based on expression: [Tissues at risk]
   - Mitigation: [How to monitor/address]
   
   Selectivity-Related Risks:
   - Key off-targets: [And their consequences]
   - Required selectivity: [Fold-selectivity needed]
   - Testing strategy: [Panel, counter-screens]

5. GO/NO-GO DECISION FRAMEWORK

   GO Criteria (must achieve ALL):
   - [Criterion 1 with quantitative threshold]
   - [Criterion 2 with quantitative threshold]
   - [Criterion 3 with quantitative threshold]
   
   NO-GO Criteria (any one kills program):
   - [Criterion 1 - what would indicate hypothesis is wrong]
   - [Criterion 2 - what would indicate undruggable]
   - [Criterion 3 - what would indicate safety issue]

6. CRITICAL PATH

   Phase 1 - Target Validation: [X weeks]
   Decision point 1: [What must be true to continue]
   
   Phase 2 - Lead Identification: [X weeks]  
   Decision point 2: [What must be true to continue]
   
   Phase 3 - Lead Optimization: [X weeks]
   Decision point 3: [What must be true to continue]

RESOURCE REQUIREMENTS:
- Timeline: [Total months to IND-enabling]
- Complexity: [Low/Medium/High]
- Key dependencies: [Reagents, models, expertise needed]

FEASIBILITY ASSESSMENT:
[2-3 sentences on overall feasibility and key risks]

=== SCORING RUBRIC ===
Use this rubric to assign your FEASIBILITY_SCORE:

0.85-1.0 (Highly Feasible): Standard assays and models readily available. Tool compounds exist. Clear biomarkers identified. Straightforward path with <12 months to key decision. Low technical risk.

0.70-0.84 (Feasible): Most assays established, some optimization needed. Relevant models available. Reasonable biomarker strategy. 12-18 month timeline. Moderate technical risk.

0.55-0.69 (Moderately Feasible): Some assays need development. Animal models imperfect but usable. Biomarker strategy needs work. 18-24 month timeline. Notable technical hurdles.

0.40-0.54 (Challenging): Significant assay development required. Limited model options. Biomarker gaps. >24 month timeline. High technical risk. Requires specialized expertise.

0.25-0.39 (Difficult): Major technical barriers. No good disease models. No validated biomarkers. Unclear timeline. Very high risk. May require technology breakthrough.

0.0-0.24 (Not Feasible): No path to validation with current technology. Models don't exist. Cannot measure relevant endpoints. Prohibitive resource requirements.

FEASIBILITY_SCORE: [0.0-1.0]
- Technical feasibility: [0-1]
- Resource availability: [0-1]
- Timeline realism: [0-1]
- Overall: [average of above three]

Justification: [One sentence explaining why you assigned this score based on the rubric above]"""
    },

    "controller": {
        "name": "Controller",
        "thinking": "Aggregating scores across all dimensions... Identifying weakest link in the hypothesis chain... Evaluating whether deficiencies are addressable through iteration... Weighing evidence strength against druggability and novelty... Determining if hypothesis merits resource investment... Making portfolio-level go/no-go recommendation...",
        "prompt": """You are a drug discovery portfolio manager responsible for resource allocation decisions.

TASK: Evaluate all evidence and make a go/no-go decision or request refinement.

SCORES FROM EVALUATION:
- Evidence Confidence: {evidence_score}
- Druggability Score: {druggability_score}
- Novelty Score: {novelty_score}
- Feasibility Score: {feasibility_score}

Loops used: {loops_used} of {max_loops}
Remaining loops: {remaining_loops}

DECISION FRAMEWORK:
{loop_rules}

SCORE INTERPRETATION:
- 0.70+: Strong - no concerns
- 0.55-0.69: Adequate - acceptable with awareness of limitations  
- 0.40-0.54: Weak - needs improvement or strong justification
- Below 0.40: Critical weakness - likely NO_GO unless addressable

OUTPUT FORMAT:

PORTFOLIO ANALYSIS:

Score Summary:
- Evidence: {evidence_score} [Strong >=0.70, Adequate >=0.55, Weak >=0.40, Critical <0.40]
- Druggability: {druggability_score} [Strong >=0.70, Adequate >=0.55, Weak >=0.40, Critical <0.40]
- Novelty: {novelty_score} [Strong >=0.70, Adequate >=0.55, Weak >=0.40, Critical <0.40]
- Feasibility: {feasibility_score} [Strong >=0.70, Adequate >=0.55, Weak >=0.40, Critical <0.40]

Composite Score: [Average of all four scores]

Weakest Link: [Which dimension is most limiting and why]

Risk Assessment:
- Scientific risk: [High/Medium/Low] - [One sentence why]
- Technical risk: [High/Medium/Low] - [One sentence why]  
- Competitive risk: [High/Medium/Low] - [One sentence why]

DECISION: [GO / NO_GO / LOOP]
LOOP_TARGET: [target_hypothesis / literature_evidence / preclinical_design / none]

REASONING:
[2-3 sentences explaining the decision, referencing specific scores and the rubric thresholds]

NEXT STEPS:
[If GO: Key milestones and success criteria]
[If NO_GO: What would need to change to reconsider]
[If LOOP: Specific guidance for the target agent on what to improve]"""
    }
}

DRUG_DISCOVERY_SEQUENCE = [
    "target_hypothesis",
    "literature_evidence",
    "druggability",
    "novelty",
    "preclinical_design",
    "controller"
]


# =============================================================================
# Helper Functions
# =============================================================================

def parse_score(text: str, key: str) -> float:
    """Extract a score from text with improved parsing."""
    search_keys = [key, key.replace("_", " "), key.replace("_SCORE", ""), key.replace("_CONFIDENCE", "")]
    
    # Try exact pattern match first
    for search_key in search_keys:
        pattern = rf'{re.escape(search_key)}[:\s]+([0-1]\.?\d*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                return min(1.0, max(0.0, val))
            except ValueError:
                continue
    
    # Try finding "Overall: X.XX" pattern near the key
    for search_key in search_keys:
        pos = text.lower().find(search_key.lower())
        if pos != -1:
            # Look for "Overall:" within 200 chars after the key
            snippet = text[pos:pos+200]
            overall_match = re.search(r'Overall[:\s]+([0-1]\.\d+)', snippet, re.IGNORECASE)
            if overall_match:
                try:
                    val = float(overall_match.group(1))
                    return min(1.0, max(0.0, val))
                except ValueError:
                    pass
    
    # Fallback: find any decimal near the key
    text_lower = text.lower()
    for search_key in search_keys:
        pos = text_lower.find(search_key.lower())
        if pos != -1:
            snippet = text[pos:pos+50]
            decimals = re.findall(r'(\d+\.\d+)', snippet)
            if decimals:
                val = float(decimals[0])
                if val <= 1.0:
                    return val
    
    return 0.55  # Default to middle of "adequate" range


def parse_controller_decision(text: str) -> tuple:
    """Parse controller output."""
    text_upper = text.upper()
    
    decision = "GO"
    decision_match = re.search(r'DECISION:\s*(GO|NO_GO|NO-GO|LOOP)', text_upper)
    if decision_match:
        d = decision_match.group(1)
        if d == "LOOP":
            decision = "LOOP"
        elif "NO" in d:
            decision = "NO_GO"
        else:
            decision = "GO"
    
    loop_target = None
    if decision == "LOOP":
        target_match = re.search(r'LOOP_TARGET:\s*(\w+)', text, re.IGNORECASE)
        if target_match:
            target = target_match.group(1).lower()
            if "hypothesis" in target or "target" in target:
                loop_target = "target_hypothesis"
            elif "evidence" in target or "literature" in target:
                loop_target = "literature_evidence"
            elif "preclinical" in target or "design" in target or "feasibility" in target:
                loop_target = "preclinical_design"
            elif "druggability" in target:
                loop_target = "target_hypothesis"  # Re-think target if druggability is the issue
            elif "novelty" in target:
                loop_target = "target_hypothesis"  # Re-think target if novelty is the issue
        if not loop_target:
            loop_target = "target_hypothesis"
    
    return decision, loop_target


def build_drug_discovery_input(agent_id: str, state: Dict[str, Any]) -> str:
    """Build input for drug discovery agents."""
    if agent_id == "target_hypothesis":
        inp = f"Research Question: {state['question']}"
        if state.get("feedback") and state["loops_used"] > 0:
            inp += f"\n\n[REFINEMENT REQUEST - Iteration {state['loops_used']+1}]\n{state['feedback']}\n\nPrevious hypothesis had weaknesses. Please refine with a stronger, more differentiated approach."
        return inp
    
    elif agent_id == "literature_evidence":
        return f"Evaluate this drug discovery hypothesis:\n\n{state['hypothesis']}"
    
    elif agent_id == "druggability":
        return f"HYPOTHESIS:\n{state['hypothesis']}\n\nEVIDENCE CONTEXT:\n{state['evidence'][:2000]}"
    
    elif agent_id == "novelty":
        ev_score = state['evidence_score'] if state['evidence_score'] is not None else 0.5
        dr_score = state['druggability_score'] if state['druggability_score'] is not None else 0.5
        return f"HYPOTHESIS:\n{state['hypothesis']}\n\nCONTEXT:\n- Evidence confidence: {ev_score:.2f}\n- Druggability score: {dr_score:.2f}"
    
    elif agent_id == "preclinical_design":
        ev_score = state['evidence_score'] if state['evidence_score'] is not None else 0.5
        dr_score = state['druggability_score'] if state['druggability_score'] is not None else 0.5
        nv_score = state['novelty_score'] if state['novelty_score'] is not None else 0.5
        inp = f"""HYPOTHESIS:
{state['hypothesis']}

CONTEXT:
- Evidence confidence: {ev_score:.2f}
- Druggability score: {dr_score:.2f}
- Novelty score: {nv_score:.2f}

DRUGGABILITY ASSESSMENT:
{state['druggability'][:1500]}"""
        if state.get("feedback") and state["loops_used"] > 0:
            inp += f"\n\n[REFINEMENT REQUEST]\nPrevious experimental plan had feasibility concerns. Please design a more practical, resource-efficient approach with clearer go/no-go criteria."
        return inp
    
    elif agent_id == "controller":
        return "Review all scores and make your portfolio decision."
    
    return state["question"]


def update_drug_discovery_state(agent_id: str, output: str, state: Dict[str, Any]):
    """Update state after drug discovery agent runs."""
    if agent_id == "target_hypothesis":
        state["hypothesis"] = output
    elif agent_id == "literature_evidence":
        state["evidence"] = output
        state["evidence_score"] = parse_score(output, "EVIDENCE_CONFIDENCE")
    elif agent_id == "druggability":
        state["druggability"] = output
        state["druggability_score"] = parse_score(output, "DRUGGABILITY_SCORE")
    elif agent_id == "novelty":
        state["novelty"] = output
        state["novelty_score"] = parse_score(output, "NOVELTY_SCORE")
    elif agent_id == "preclinical_design":
        state["preclinical"] = output
        state["feasibility_score"] = parse_score(output, "FEASIBILITY_SCORE")


def get_drug_discovery_scores(state: Dict[str, Any]) -> Dict[str, float]:
    """Return only scores that have been computed."""
    scores = {}
    if state["evidence_score"] is not None:
        scores["evidence"] = state["evidence_score"]
    if state["druggability_score"] is not None:
        scores["druggability"] = state["druggability_score"]
    if state["novelty_score"] is not None:
        scores["novelty"] = state["novelty_score"]
    if state["feasibility_score"] is not None:
        scores["feasibility"] = state["feasibility_score"]
    return scores


# =============================================================================
# Pipeline Runner
# =============================================================================

async def run_drug_discovery_pipeline(
    question: str,
    llm,
    max_loops: int = 3
) -> AsyncGenerator[str, None]:
    """Run the 6-agent drug discovery pipeline with dynamic routing."""
    
    state: Dict[str, Any] = {
        "question": question,
        "hypothesis": "",
        "evidence": "",
        "evidence_score": None,
        "druggability": "",
        "druggability_score": None,
        "novelty": "",
        "novelty_score": None,
        "preclinical": "",
        "feasibility_score": None,
        "loops_used": 0,
        "feedback": "",
    }
    
    agent_idx = 0
    iteration_num = 1
    
    yield f"data: {json.dumps({'type': 'iteration_start', 'iteration': iteration_num})}\n\n"
    
    async def stream_llm(system: str, user: str) -> AsyncGenerator[str, None]:
        """Stream LLM response."""
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    while agent_idx < len(DRUG_DISCOVERY_SEQUENCE):
        agent_id = DRUG_DISCOVERY_SEQUENCE[agent_idx]
        config = DRUG_DISCOVERY_AGENTS[agent_id]
        
        # Thinking phase
        yield f"data: {json.dumps({'agent': agent_id, 'phase': 'thinking', 'content': config['thinking']})}\n\n"
        await asyncio.sleep(0.8)
        
        # Build prompts
        user_input = build_drug_discovery_input(agent_id, state)
        system_prompt = config["prompt"]
        
        if agent_id == "controller":
            remaining = max_loops - state["loops_used"]
            
            ev_score = state["evidence_score"] if state["evidence_score"] is not None else 0.5
            dr_score = state["druggability_score"] if state["druggability_score"] is not None else 0.5
            nv_score = state["novelty_score"] if state["novelty_score"] is not None else 0.5
            fe_score = state["feasibility_score"] if state["feasibility_score"] is not None else 0.5
            
            if remaining <= 0:
                loop_rules = "You have NO remaining loops. You MUST choose GO or NO_GO only."
            else:
                loop_rules = f"""You have {remaining} loop(s) remaining.

Decision Guidelines:
- All scores >= 0.55: Consider GO (adequate across all dimensions)
- Any score < 0.40: Critical weakness - LOOP to improve or NO_GO if unfixable
- Scores 0.40-0.54: Weak but potentially acceptable - use judgment

LOOP targets:
- Low evidence -> LOOP to literature_evidence (re-evaluate with different framing)
- Low druggability or novelty -> LOOP to target_hypothesis (consider different target/mechanism)
- Low feasibility -> LOOP to preclinical_design (simplify experimental plan)

Choose NO_GO only if the hypothesis is fundamentally flawed and cannot be salvaged."""
            
            system_prompt = system_prompt.format(
                evidence_score=f"{ev_score:.2f}",
                druggability_score=f"{dr_score:.2f}",
                novelty_score=f"{nv_score:.2f}",
                feasibility_score=f"{fe_score:.2f}",
                loops_used=state["loops_used"],
                max_loops=max_loops,
                remaining_loops=remaining,
                loop_rules=loop_rules
            )
        
        # Stream output
        full_output = ""
        async for token in stream_llm(system_prompt, user_input):
            full_output += token
            yield f"data: {json.dumps({'agent': agent_id, 'phase': 'output', 'content': token})}\n\n"
        
        # Update state
        update_drug_discovery_state(agent_id, full_output, state)
        scores = get_drug_discovery_scores(state)
        
        # Complete phase
        yield f"data: {json.dumps({'agent': agent_id, 'phase': 'complete', 'full_output': full_output, 'scores': scores})}\n\n"
        await asyncio.sleep(0.2)
        
        # Controller routing
        if agent_id == "controller":
            decision, loop_target = parse_controller_decision(full_output)
            remaining = max_loops - state["loops_used"]
            
            if decision == "LOOP" and loop_target and remaining > 0:
                state["loops_used"] += 1
                iteration_num += 1
                
                try:
                    loop_idx = DRUG_DISCOVERY_SEQUENCE.index(loop_target)
                    state["feedback"] = f"Iteration {iteration_num}: Controller requested refinement due to low scores. Focus on improving the weakest aspects."
                    
                    yield f"data: {json.dumps({'type': 'loop', 'from': 'controller', 'to': loop_target, 'iteration': iteration_num})}\n\n"
                    yield f"data: {json.dumps({'type': 'iteration_end', 'iteration': iteration_num-1, 'action': 'loop', 'scores': scores})}\n\n"
                    yield f"data: {json.dumps({'type': 'iteration_start', 'iteration': iteration_num})}\n\n"
                    
                    agent_idx = loop_idx
                    await asyncio.sleep(0.5)
                    continue
                except ValueError:
                    pass
            
            if decision == "LOOP" and remaining <= 0:
                ev = state["evidence_score"] if state["evidence_score"] is not None else 0.5
                dr = state["druggability_score"] if state["druggability_score"] is not None else 0.5
                nv = state["novelty_score"] if state["novelty_score"] is not None else 0.5
                fe = state["feasibility_score"] if state["feasibility_score"] is not None else 0.5
                avg_score = (ev + dr + nv + fe) / 4
                decision = "GO" if avg_score >= 0.50 else "NO_GO"
            
            yield f"data: {json.dumps({'type': 'iteration_end', 'iteration': iteration_num, 'action': decision.lower(), 'scores': scores})}\n\n"
            yield f"data: {json.dumps({'type': 'pipeline_complete', 'decision': decision, 'scores': scores, 'iterations': iteration_num})}\n\n"
            break
        
        agent_idx += 1