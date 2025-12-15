"""
Literature Analyzer Agent.

LLM-powered agent that analyzes aggregated literature statistics to identify patterns,
contradictions, and preliminary gap signals.
"""

import json
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, MODEL_NAME, LLM_TEMPERATURE


SYSTEM_PROMPT = """You are an expert systematic reviewer and epidemiologist analyzing literature statistics for research gap identification.

You will receive aggregated statistics from a corpus of scientific papers, NOT the papers themselves. Your task is to:

1. INTERPRET DISTRIBUTIONS
   - Identify which populations are understudied (< 5% of papers)
   - Identify which interventions are understudied (< 5% of papers)
   - Identify which outcomes are rarely measured (< 10% of papers)
   - Flag if certain study designs are missing (e.g., few RCTs)

2. ANALYZE SPARSE COMBINATIONS
   - For population-intervention pairs with < 3 papers, assess clinical significance
   - Distinguish between "not studied because not relevant" vs "genuine research gap"
   - Prioritize combinations where the gap has clinical/public health implications

3. INTERPRET TEMPORAL TRENDS
   - Identify emerging research areas (growing publication counts)
   - Identify declining or stalled areas that may need revival
   - Note if the field overall is growing, stable, or declining

4. REVIEW SAMPLE ABSTRACTS
   - Look for contradictory findings between studies
   - Identify ongoing debates or unresolved questions
   - Note methodological patterns or limitations

5. SYNTHESIZE FINDINGS
   - Prioritize the most significant gaps
   - Explain WHY each gap matters (clinical significance)
   - Note any caveats about the analysis

*** CRITICAL: APPLY DOMAIN LOGIC TO FILTER IRRELEVANT COMBINATIONS ***

A sparse combination is NOT a genuine research gap if it fails basic domain logic. Apply these principles:

1. INTERVENTION TARGET vs SECONDARY POPULATION
   - Some populations appear in studies as SECONDARY subjects (e.g., affected by someone else's behavior) rather than INTERVENTION TARGETS
   - Example: In parenting interventions, children are affected but parents receive the intervention
   - Example: In caregiver studies, patients are affected but caregivers are the targets
   - Only flag gaps where the population would directly RECEIVE the intervention

2. AGE/DEVELOPMENTAL APPROPRIATENESS
   - Consider whether the intervention is designed for and appropriate to the population's developmental stage
   - Consider regulatory and ethical constraints for different age groups

3. CAPACITY TO PARTICIPATE
   - Can this population physically, cognitively, or legally participate in this intervention?
   - Consider consent capacity, communication ability, and practical feasibility

4. LOGICAL COHERENCE
   - Does the combination make sense given the nature of the health behavior or condition?
   - Ask: "Would a researcher actually design a study with this exact population-intervention pair?"

For each sparse combination, explicitly state whether it represents:
- A GENUINE GAP: The population could receive the intervention, but research is lacking
- A FALSE POSITIVE: The population cannot logically be an intervention target (explain why)
- UNCLEAR: Needs more context to determine

OUTPUT FORMAT - Respond with valid JSON only:
{
    "distribution_insights": {
        "understudied_populations": [
            {"category": "name", "percentage": X, "significance": "why this matters", "is_valid_intervention_target": true/false, "rationale": "why or why not"}
        ],
        "understudied_interventions": [
            {"category": "name", "percentage": X, "significance": "why this matters"}
        ],
        "understudied_outcomes": [
            {"category": "name", "percentage": X, "significance": "why this matters"}
        ],
        "methodological_observations": "Note on study types, e.g., 'Only 20% RCTs suggests need for more rigorous evidence'",
        "filtered_out": [
            {"population_or_combination": "name", "reason": "why it's not a valid research gap"}
        ]
    },
    "sparse_combination_analysis": [
        {
            "combination": "Population + Intervention",
            "paper_count": X,
            "is_genuine_gap": true/false,
            "gap_type": "genuine_gap | false_positive | unclear",
            "reasoning": "Explain your logic for why this is or isn't a valid gap",
            "clinical_significance": "Why this combination matters (if genuine) or why it's not applicable",
            "priority": "high/medium/low/excluded"
        }
    ],
    "temporal_insights": {
        "overall_trend": "growing/stable/declining",
        "emerging_topics": ["topic1", "topic2"],
        "declining_topics": ["topic1"],
        "interpretation": "What this means for the field"
    },
    "contradictions_and_debates": [
        {
            "topic": "What the debate is about",
            "summary": "Brief description of conflicting findings",
            "research_implication": "What research is needed to resolve"
        }
    ],
    "key_findings_summary": "2-3 sentence high-level summary of GENUINE gaps identified (excluding false positives)",
    "analysis_caveats": ["caveat1", "caveat2"]
}"""


THINKING_TEXT = "Analyzing population distributions... Examining intervention coverage... Identifying sparse research combinations... Reviewing temporal publication trends... Scanning abstracts for contradictions... Synthesizing gap patterns..."


def get_llm():
    """Get configured LLM instance."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY
    )


def format_statistics_for_prompt(stats: dict) -> str:
    """
    Format statistics dictionary into readable prompt text.
    
    Args:
        stats: Statistics from aggregator.generate_statistics_summary()
        
    Returns:
        Formatted string for LLM prompt
    """
    lines = []
    
    # Header
    lines.append(f"CORPUS SUMMARY: {stats['total_papers']} papers")
    if stats.get('year_range', {}).get('min') and stats.get('year_range', {}).get('max'):
        lines.append(f"Year range: {stats['year_range']['min']} - {stats['year_range']['max']}")
    lines.append("")
    
    # Population distribution
    lines.append("POPULATION DISTRIBUTION:")
    pop_dist = stats.get('distributions', {}).get('population', {})
    for cat, data in sorted(pop_dist.items(), key=lambda x: x[1]['count'], reverse=True):
        lines.append(f"  - {data['display_name']}: {data['count']} papers ({data['percentage']}%)")
    lines.append("")
    
    # Intervention distribution
    lines.append("INTERVENTION DISTRIBUTION:")
    int_dist = stats.get('distributions', {}).get('intervention', {})
    for cat, data in sorted(int_dist.items(), key=lambda x: x[1]['count'], reverse=True):
        lines.append(f"  - {data['display_name']}: {data['count']} papers ({data['percentage']}%)")
    lines.append("")
    
    # Outcome distribution
    lines.append("OUTCOME DISTRIBUTION:")
    out_dist = stats.get('distributions', {}).get('outcome', {})
    for cat, data in sorted(out_dist.items(), key=lambda x: x[1]['count'], reverse=True):
        lines.append(f"  - {data['display_name']}: {data['count']} papers ({data['percentage']}%)")
    lines.append("")
    
    # Study type distribution
    lines.append("STUDY TYPE DISTRIBUTION:")
    st_dist = stats.get('distributions', {}).get('study_type', {})
    for cat, data in sorted(st_dist.items(), key=lambda x: x[1]['count'], reverse=True):
        lines.append(f"  - {data['display_name']}: {data['count']} papers ({data['percentage']}%)")
    lines.append("")
    
    # Sparse combinations
    lines.append("SPARSE POPULATION-INTERVENTION COMBINATIONS (< 3 papers):")
    sparse = stats.get('sparse_combinations', [])[:15]
    for item in sparse:
        lines.append(f"  - {item['display']}: {item['count']} papers")
    lines.append("")
    
    # Temporal trends
    lines.append("TEMPORAL TRENDS:")
    temporal = stats.get('temporal_trends', {})
    lines.append(f"  Overall trend: {temporal.get('trend', 'unknown')}")
    lines.append(f"  Recent avg change: {temporal.get('avg_recent_change', 'N/A')}%")
    if temporal.get('peak_year'):
        lines.append(f"  Peak year: {temporal['peak_year']} ({temporal['peak_count']} papers)")
    lines.append("")
    
    # Sample abstracts
    lines.append("SAMPLE ABSTRACTS FOR REVIEW:")
    for i, sample in enumerate(stats.get('sample_abstracts', [])[:10], 1):
        lines.append(f"\n[{i}] {sample.get('title', 'Untitled')} ({sample.get('year', 'N/A')})")
        study_types = sample.get('study_type', [])
        if study_types:
            lines.append(f"    Type: {', '.join(study_types)}")
        abstract = sample.get('abstract', '')
        if abstract:
            lines.append(f"    Abstract: {abstract[:300]}...")
    
    return "\n".join(lines)


async def analyze_literature(stats: dict, domain: str) -> dict:
    """
    Analyze literature statistics to identify patterns and gaps.
    
    Args:
        stats: Statistics from generate_statistics_summary()
        domain: Original research domain string
        
    Returns:
        Dict with analysis results
    """
    llm = get_llm()
    
    formatted_stats = format_statistics_for_prompt(stats)
    
    user_message = f"""RESEARCH DOMAIN: {domain}

{formatted_stats}

Analyze these statistics and identify research gaps, patterns, and opportunities."""
    
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
        # Return raw content if JSON parsing fails
        result = {
            "raw_analysis": content,
            "parse_error": True
        }
    
    return result


async def analyze_literature_streaming(stats: dict, domain: str):
    """
    Analyze literature with streaming output.
    
    Args:
        stats: Statistics from generate_statistics_summary()
        domain: Original research domain string
        
    Yields:
        Streaming tokens from LLM
    """
    llm = get_llm()
    
    formatted_stats = format_statistics_for_prompt(stats)
    
    user_message = f"""RESEARCH DOMAIN: {domain}

{formatted_stats}

Analyze these statistics and identify research gaps, patterns, and opportunities."""
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content