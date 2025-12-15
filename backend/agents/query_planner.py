"""
Query Planner Agent.

LLM-powered agent that decomposes a research domain into searchable queries.
"""

import json
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, MODEL_NAME, LLM_TEMPERATURE


SYSTEM_PROMPT = """You are a systematic review methodologist specializing in public health and behavioral interventions research.

TASK: Given a research domain or question, generate an optimal PubMed search strategy to comprehensively capture the literature for research gap analysis.

Your search strategy should:
1. Use MeSH (Medical Subject Headings) terms where appropriate
2. Include synonyms and alternative phrasings
3. Balance sensitivity (finding all relevant papers) with specificity (avoiding irrelevant results)
4. Cover different aspects of the domain (population, intervention, setting, outcomes)

CRITICAL JSON FORMATTING RULES:
- Respond with ONLY a valid JSON object
- Do NOT use double quotes inside string values - use single quotes instead
- Example: Use 'Smoking Cessation'[MeSH] NOT "Smoking Cessation"[MeSH]
- No markdown code blocks, no explanations before or after

OUTPUT FORMAT:
{
    "domain_summary": "Brief 1-2 sentence summary of the research domain",
    "search_queries": [
        "'Smoking Cessation'[MeSH] AND 'Hispanic Americans'[MeSH]",
        "tobacco cessation AND (Hispanic OR Latino) AND low-income",
        "quit smoking AND minority populations"
    ],
    "key_populations": ["population1", "population2"],
    "key_interventions": ["intervention1", "intervention2"],
    "key_outcomes": ["outcome1", "outcome2"],
    "time_range_suggestion": "YYYY-YYYY",
    "search_rationale": "Brief explanation of search strategy logic"
}

GUIDELINES:
- Generate 4-6 distinct search queries that together cover the domain comprehensively
- Each query should be 3-8 terms, optimized for PubMed
- Use SINGLE quotes for exact phrases: 'emergency department'
- Use [MeSH] suffix for MeSH terms: 'Smoking Cessation'[MeSH]
- Avoid overly broad queries that would return thousands of irrelevant papers
- Consider both US and international terminology"""


THINKING_TEXT = "Analyzing research domain... Identifying key concepts and MeSH terms... Designing comprehensive search strategy... Balancing sensitivity and specificity... Generating optimized PubMed queries..."


def get_llm():
    """Get configured LLM instance."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY
    )


async def plan_queries(user_query: str) -> dict:
    """
    Generate search queries for a research domain.
    
    Args:
        user_query: User's research domain or question
        
    Returns:
        Dict with search queries and PICO dimensions
    """
    llm = get_llm()
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Research Domain: {user_query}")
    ]
    
    response = await llm.ainvoke(messages)
    content = response.content
    
    # Parse JSON from response
    try:
        # Try to extract JSON from response
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        else:
            json_str = content
        
        result = json.loads(json_str.strip())
        
    except json.JSONDecodeError:
        # Fallback: construct basic query from user input
        result = {
            "domain_summary": user_query,
            "search_queries": [
                user_query,
                f'"{user_query}"[Title/Abstract]'
            ],
            "key_populations": [],
            "key_interventions": [],
            "key_outcomes": [],
            "time_range_suggestion": "2018-2024",
            "search_rationale": "Fallback search due to parsing error"
        }
    
    return result


async def plan_queries_streaming(user_query: str):
    """
    Generate search queries with streaming output.
    
    Args:
        user_query: User's research domain or question
        
    Yields:
        Streaming tokens from LLM
    """
    llm = get_llm()
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Research Domain: {user_query}")
    ]
    
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content