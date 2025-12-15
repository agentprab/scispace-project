"""
Gap Synthesizer Agent.

LLM-powered agent that synthesizes analysis findings into structured research gaps
and generates actionable hypotheses.
"""

import json
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, MODEL_NAME, LLM_TEMPERATURE_CREATIVE


SYSTEM_PROMPT = """You are a senior research strategist helping identify high-impact research opportunities in public health, behavioral science, and social science domains.

Given the literature analysis findings, your task is to:

1. PRIORITIZE GAPS
   - Rank gaps by research impact potential
   - Consider: clinical significance, feasibility, novelty, and urgency
   - Focus on gaps that are both important AND addressable

2. GENERATE HYPOTHESES
   - For each top gap, formulate a specific, testable hypothesis
   - Hypotheses should be falsifiable and measurable
   - Consider what study design would test the hypothesis

3. PROVIDE ACTIONABLE GUIDANCE
   - Suggest appropriate study designs
   - Note key challenges and how to address them
   - Identify what resources/collaborations would be needed

*** CRITICAL: VALIDATE CLINICAL/LOGICAL COHERENCE ***

Before including ANY gap in your final output, apply this validity test:

1. INTERVENTION TARGETABILITY
   - Is this population the direct recipient of the intervention, or merely affected by it?
   - If the population is a SECONDARY subject (e.g., children affected by parental behavior), they are not the intervention target
   - Only include gaps where the population would directly receive/participate in the intervention

2. FEASIBILITY CHECK
   - Could this population realistically participate in this intervention?
   - Consider: consent capacity, developmental stage, physical/cognitive ability, legal constraints
   - Would an ethics board (IRB) approve this study?

3. LOGICAL COHERENCE
   - Does the population-intervention pair make sense given the domain?
   - Ask yourself: "Would a real researcher design a study with this exact combination?"
   - If the answer is "no" or "that doesn't make sense," exclude it

4. DISTINGUISH TARGETS FROM AFFECTED PARTIES
   - In many health interventions, there are direct targets and indirect beneficiaries
   - Example: Caregiver interventions target caregivers, not patients
   - Example: Parenting programs target parents, not children
   - Example: Workplace wellness targets employees, not their families
   - Only the direct targets should be considered for intervention gaps

If the Literature Analyzer marked a gap as "false_positive" or "excluded," do NOT include it in your research gaps.

OUTPUT FORMAT - Respond with valid JSON only:
{
    "research_gaps": [
        {
            "rank": 1,
            "title": "Short descriptive title of the gap",
            "category": "understudied_population | understudied_intervention | missing_combination | methodological | outcome_measurement | emerging_opportunity",
            "description": "2-3 sentence description of what's missing and why it matters",
            "validity_check": {
                "population_is_intervention_target": true,
                "intervention_is_appropriate_for_population": true,
                "study_would_be_ethically_feasible": true
            },
            "evidence_summary": {
                "papers_found": X,
                "related_papers": Y,
                "key_statistic": "e.g., 'Only 3% of studies examined this population'"
            },
            "clinical_significance": "Why addressing this gap matters for patients/public health",
            "hypothesis": {
                "statement": "Clear, testable hypothesis statement",
                "primary_outcome": "What you would measure",
                "expected_direction": "e.g., 'increase in X' or 'reduction in Y'"
            },
            "suggested_study_design": {
                "design": "RCT | Quasi-experimental | Cohort | Qualitative | Mixed methods",
                "setting": "Where the study would be conducted",
                "population": "Who would be enrolled",
                "sample_size_estimate": "Rough estimate with rationale",
                "duration": "Expected study duration"
            },
            "challenges": ["challenge1", "challenge2"],
            "feasibility_rating": "high | medium | low",
            "impact_rating": "high | medium | low",
            "novelty_rating": "high | medium | low"
        }
    ],
    "excluded_gaps": [
        {
            "gap": "Description of excluded gap",
            "reason": "Why it was excluded - explain the logical/clinical issue"
        }
    ],
    "synthesis_summary": "3-4 sentence executive summary of the most important findings and recommendations",
    "field_observations": "Brief comment on the overall state of research in this domain",
    "methodological_recommendations": ["recommendation1", "recommendation2"]
}

GUIDELINES:
- Identify 3-5 high-priority VALID gaps (quality over quantity)
- Each hypothesis should be specific enough to design a study around
- Be realistic about feasibility - don't suggest gaps that can't be addressed
- Consider your audience: researchers looking for impactful, fundable projects
- Ground recommendations in the evidence provided
- Always explain your reasoning for including or excluding gaps
- When in doubt about validity, exclude the gap and explain why in "excluded_gaps\""""


THINKING_TEXT = "Prioritizing research gaps by impact and feasibility... Formulating testable hypotheses... Designing study approaches... Assessing resource requirements... Generating actionable recommendations..."


def get_llm():
    """Get configured LLM instance with creative temperature."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=LLM_TEMPERATURE_CREATIVE,  # Slightly higher for creative hypothesis generation
        api_key=OPENAI_API_KEY
    )


def format_analysis_for_prompt(analysis: dict, stats: dict, domain: str) -> str:
    """
    Format analysis results for synthesis prompt.
    
    Args:
        analysis: Results from literature_analyzer
        stats: Original statistics
        domain: Research domain string
        
    Returns:
        Formatted string for LLM prompt
    """
    lines = []
    
    lines.append(f"RESEARCH DOMAIN: {domain}")
    lines.append(f"PAPERS ANALYZED: {stats.get('total_papers', 'Unknown')}")
    lines.append("")
    
    # Distribution insights
    dist_insights = analysis.get('distribution_insights', {})
    
    lines.append("UNDERSTUDIED POPULATIONS:")
    for pop in dist_insights.get('understudied_populations', []):
        lines.append(f"  - {pop.get('category')}: {pop.get('percentage')}% - {pop.get('significance', '')}")
    lines.append("")
    
    lines.append("UNDERSTUDIED INTERVENTIONS:")
    for interv in dist_insights.get('understudied_interventions', []):
        lines.append(f"  - {interv.get('category')}: {interv.get('percentage')}% - {interv.get('significance', '')}")
    lines.append("")
    
    lines.append("UNDERSTUDIED OUTCOMES:")
    for out in dist_insights.get('understudied_outcomes', []):
        lines.append(f"  - {out.get('category')}: {out.get('percentage')}% - {out.get('significance', '')}")
    lines.append("")
    
    if dist_insights.get('methodological_observations'):
        lines.append(f"METHODOLOGICAL OBSERVATIONS: {dist_insights['methodological_observations']}")
        lines.append("")
    
    # Sparse combinations
    lines.append("HIGH-PRIORITY SPARSE COMBINATIONS:")
    sparse_analysis = analysis.get('sparse_combination_analysis', [])
    high_priority = [s for s in sparse_analysis if s.get('priority') == 'high' or s.get('is_genuine_gap')]
    for combo in high_priority[:10]:
        lines.append(f"  - {combo.get('combination')}: {combo.get('paper_count')} papers")
        lines.append(f"    Significance: {combo.get('clinical_significance', 'N/A')}")
    lines.append("")
    
    # Temporal insights
    temporal = analysis.get('temporal_insights', {})
    lines.append("TEMPORAL INSIGHTS:")
    lines.append(f"  Overall trend: {temporal.get('overall_trend', 'unknown')}")
    if temporal.get('emerging_topics'):
        lines.append(f"  Emerging topics: {', '.join(temporal['emerging_topics'])}")
    if temporal.get('declining_topics'):
        lines.append(f"  Declining topics: {', '.join(temporal['declining_topics'])}")
    lines.append("")
    
    # Contradictions
    contradictions = analysis.get('contradictions_and_debates', [])
    if contradictions:
        lines.append("ACTIVE DEBATES/CONTRADICTIONS:")
        for debate in contradictions:
            lines.append(f"  - {debate.get('topic')}: {debate.get('summary', '')}")
    lines.append("")
    
    # Key findings
    if analysis.get('key_findings_summary'):
        lines.append(f"ANALYZER SUMMARY: {analysis['key_findings_summary']}")
    
    return "\n".join(lines)


async def synthesize_gaps(analysis: dict, stats: dict, domain: str) -> dict:
    """
    Synthesize analysis into prioritized research gaps and hypotheses.
    
    Args:
        analysis: Results from literature_analyzer
        stats: Original statistics from aggregator
        domain: Original research domain string
        
    Returns:
        Dict with prioritized gaps and hypotheses
    """
    llm = get_llm()
    
    formatted_analysis = format_analysis_for_prompt(analysis, stats, domain)
    
    user_message = f"""{formatted_analysis}

Based on this analysis, identify the top 3-5 research gaps and generate specific, testable hypotheses for each."""
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    response = await llm.ainvoke(messages)
    content = response.content
    
    # Parse JSON from response
    try:
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        else:
            json_str = content
        
        result = json.loads(json_str.strip())
        
    except json.JSONDecodeError:
        result = {
            "raw_synthesis": content,
            "parse_error": True
        }
    
    return result


async def synthesize_gaps_streaming(analysis: dict, stats: dict, domain: str):
    """
    Synthesize gaps with streaming output.
    
    Args:
        analysis: Results from literature_analyzer
        stats: Original statistics
        domain: Research domain string
        
    Yields:
        Streaming tokens from LLM
    """
    llm = get_llm()
    
    formatted_analysis = format_analysis_for_prompt(analysis, stats, domain)
    
    user_message = f"""{formatted_analysis}

Based on this analysis, identify the top 3-5 research gaps and generate specific, testable hypotheses for each."""
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content