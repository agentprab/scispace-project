"""
Research Gap Finder - Main Orchestrator

LangGraph-based pipeline that coordinates:
1. Query Planner (LLM) - generates search queries
2. Data Fetcher (API) - fetches from PubMed + OpenAlex
3. Aggregator (Python) - builds statistics
4. Literature Analyzer (LLM) - identifies patterns
5. Gap Synthesizer (LLM) - generates prioritized gaps + hypotheses

Usage:
    from gap_finder import run_gap_finder_pipeline, run_gap_finder_streaming
    
    # Non-streaming
    result = await run_gap_finder_pipeline("smoking cessation in emergency departments")
    
    # Streaming (for real-time UI updates)
    async for event in run_gap_finder_streaming("smoking cessation in ED"):
        print(event)
"""

import asyncio
import json
import re
import sys
import os
from typing import TypedDict, AsyncGenerator, Optional
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain imports for streaming
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Local imports - API clients
from api_clients.pubmed import search_multiple_queries, fetch_in_batches
from api_clients.openalex import enrich_papers_by_doi

# Local imports - Processors
from processors.xml_parser import parse_pubmed_xml, deduplicate_papers
from processors.aggregator import generate_statistics_summary

# Local imports - LLM Agents (for prompts and non-streaming functions)
from agents.query_planner import SYSTEM_PROMPT as QP_SYSTEM_PROMPT, THINKING_TEXT as QP_THINKING
from agents.literature_analyzer import SYSTEM_PROMPT as LA_SYSTEM_PROMPT, THINKING_TEXT as LA_THINKING, format_statistics_for_prompt
from agents.gap_synthesizer import SYSTEM_PROMPT as GS_SYSTEM_PROMPT, THINKING_TEXT as GS_THINKING, format_analysis_for_prompt

# Config
from config import MAX_PAPERS_TOTAL, OPENAI_API_KEY, MODEL_NAME, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE


# =============================================================================
# JSON Repair Helper
# =============================================================================

def repair_json_response(raw_response: str) -> dict:
    """
    Attempt to parse JSON from LLM response, with repairs for common issues.
    
    Args:
        raw_response: Raw LLM response text
        
    Returns:
        Parsed dict or None if parsing fails
    """
    
    # Step 1: Extract JSON from markdown code blocks if present
    json_str = raw_response.strip()
    
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        parts = json_str.split("```")
        if len(parts) >= 2:
            json_str = parts[1].strip()
    
    # Step 2: Find the JSON object boundaries
    start = json_str.find("{")
    end = json_str.rfind("}") + 1
    if start == -1 or end <= start:
        print(f"[DEBUG] repair_json: No JSON object found")
        return None
    json_str = json_str[start:end]
    
    # Step 3: Try direct parse first
    try:
        result = json.loads(json_str)
        print(f"[DEBUG] repair_json: Direct parse succeeded")
        return result
    except json.JSONDecodeError as e:
        print(f"[DEBUG] repair_json: Direct parse failed at position {e.pos}: {e.msg}")
    
    # Step 4: Try common fixes
    fixed_str = json_str
    
    # Fix trailing commas
    fixed_str = re.sub(r',\s*}', '}', fixed_str)
    fixed_str = re.sub(r',\s*]', ']', fixed_str)
    
    try:
        result = json.loads(fixed_str)
        print(f"[DEBUG] repair_json: Fixed trailing commas, parse succeeded")
        return result
    except json.JSONDecodeError:
        pass
    
    # Fix unescaped quotes in MeSH terms: "term"[MeSH] -> 'term'[MeSH]
    fixed_str = re.sub(r'"(\w+)"\[', r"'\1'[", fixed_str)
    fixed_str = re.sub(r'"(\w+\s+\w+)"\[', r"'\1'[", fixed_str)
    fixed_str = re.sub(r'"(\w+\s+\w+\s+\w+)"\[', r"'\1'[", fixed_str)
    
    try:
        result = json.loads(fixed_str)
        print(f"[DEBUG] repair_json: Fixed MeSH quotes, parse succeeded")
        return result
    except json.JSONDecodeError:
        pass
    
    # Step 5: Try to extract key fields manually as last resort
    try:
        result = {}
        
        # For Query Planner
        if "search_queries" in json_str:
            match = re.search(r'"search_queries"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
            if match:
                queries_content = match.group(1)
                query_lines = re.split(r',\s*\n', queries_content)
                cleaned_queries = []
                for line in query_lines:
                    line = line.strip().strip('"').strip("'").strip(',').strip()
                    if line and len(line) > 5:
                        cleaned_queries.append(line)
                if cleaned_queries:
                    result["search_queries"] = cleaned_queries
        
        # Extract simple string fields
        string_fields = [
            "domain_summary", "search_rationale", "key_findings_summary",
            "synthesis_summary", "field_observations"
        ]
        for field in string_fields:
            match = re.search(rf'"{field}"\s*:\s*"([^"]*)"', json_str)
            if match:
                result[field] = match.group(1)
        
        if result:
            result["partial_parse"] = True
            print(f"[DEBUG] repair_json: Partial extraction with {len(result)} fields")
            return result
            
    except Exception as ex:
        print(f"[DEBUG] repair_json: Extraction failed: {ex}")
    
    print(f"[DEBUG] repair_json: All repair attempts failed")
    return None


# =============================================================================
# State Definition
# =============================================================================

class GapFinderState(TypedDict):
    """State shared across all nodes in the LangGraph pipeline."""
    
    # Input
    user_query: str
    
    # Query Planner outputs
    search_plan: dict
    search_queries: list[str]
    
    # Data Fetcher outputs
    raw_papers: list[dict]
    paper_count: int
    
    # Aggregator outputs
    statistics: dict
    
    # Literature Analyzer outputs
    analysis: dict
    
    # Gap Synthesizer outputs
    gaps: dict
    
    # Status tracking
    current_node: str
    error: Optional[str]


# =============================================================================
# Node Metadata for UI
# =============================================================================

NODE_METADATA = {
    "query_planner": {
        "name": "Query Planner",
        "thinking": QP_THINKING,
        "is_llm": True
    },
    "data_fetcher": {
        "name": "Data Fetcher",
        "thinking": "Searching PubMed database... Fetching paper records... Enriching with citation data from OpenAlex...",
        "is_llm": False
    },
    "aggregator": {
        "name": "Aggregator",
        "thinking": "Parsing MeSH terms... Mapping to PICO categories... Building co-occurrence matrices... Identifying sparse combinations...",
        "is_llm": False
    },
    "literature_analyzer": {
        "name": "Literature Analyzer",
        "thinking": LA_THINKING,
        "is_llm": True
    },
    "gap_synthesizer": {
        "name": "Gap Synthesizer",
        "thinking": GS_THINKING,
        "is_llm": True
    }
}


# =============================================================================
# LLM Streaming Helper
# =============================================================================

def get_streaming_llm(creative: bool = False):
    """Get configured LLM instance for streaming."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=LLM_TEMPERATURE_CREATIVE if creative else LLM_TEMPERATURE,
        streaming=True,
        api_key=OPENAI_API_KEY
    )


def get_llm(creative: bool = False):
    """Get configured LLM instance (non-streaming, for ainvoke)."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=LLM_TEMPERATURE_CREATIVE if creative else LLM_TEMPERATURE,
        streaming=False,
        api_key=OPENAI_API_KEY
    )


async def stream_llm_response(system_prompt: str, user_message: str, creative: bool = False) -> AsyncGenerator[str, None]:
    """Stream LLM response tokens."""
    llm = get_streaming_llm(creative)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


# =============================================================================
# Node Implementations (Non-LLM)
# =============================================================================

async def data_fetcher_node(state: GapFinderState) -> GapFinderState:
    """
    Node 2: Data Fetcher (No LLM)
    Executes PubMed searches and fetches paper data.
    """
    try:
        queries = state["search_queries"]
        
        if not queries:
            return {
                **state,
                "raw_papers": [],
                "paper_count": 0,
                "current_node": "data_fetcher",
                "error": "No search queries provided"
            }
        
        # Search PubMed with all queries
        all_pmids = await search_multiple_queries(queries, max_per_query=100)
        
        # Limit total papers
        pmids = list(all_pmids)[:MAX_PAPERS_TOTAL]
        
        if not pmids:
            return {
                **state,
                "raw_papers": [],
                "paper_count": 0,
                "current_node": "data_fetcher",
                "error": "No papers found for search queries"
            }
        
        # Fetch paper details
        xml_data = await fetch_in_batches(pmids, batch_size=50)
        
        # Parse XML
        papers = parse_pubmed_xml(xml_data)
        papers = deduplicate_papers(papers)
        
        # Enrich with OpenAlex (optional, may fail)
        try:
            dois = [p.get("doi") for p in papers if p.get("doi")]
            if dois:
                enrichments = await enrich_papers_by_doi(dois[:50])
                doi_to_enrichment = {e["doi"]: e for e in enrichments if e.get("doi")}
                for paper in papers:
                    if paper.get("doi") in doi_to_enrichment:
                        paper["citations"] = doi_to_enrichment[paper["doi"]].get("cited_by_count", 0)
        except Exception:
            pass
        
        return {
            **state,
            "raw_papers": papers,
            "paper_count": len(papers),
            "current_node": "data_fetcher",
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "raw_papers": [],
            "paper_count": 0,
            "current_node": "data_fetcher",
            "error": f"Data fetch error: {str(e)}"
        }


async def aggregator_node(state: GapFinderState) -> GapFinderState:
    """
    Node 3: Aggregator (No LLM)
    Computes statistics from papers.
    """
    try:
        papers = state["raw_papers"]
        
        if not papers:
            return {
                **state,
                "statistics": {"error": "No papers to aggregate"},
                "current_node": "aggregator",
                "error": "No papers available for aggregation"
            }
        
        # Generate comprehensive statistics
        statistics = generate_statistics_summary(papers)
        
        return {
            **state,
            "statistics": statistics,
            "current_node": "aggregator",
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "statistics": {},
            "current_node": "aggregator",
            "error": f"Aggregation error: {str(e)}"
        }


# =============================================================================
# Streaming Pipeline Runner
# =============================================================================

async def run_gap_finder_streaming(user_query: str) -> AsyncGenerator[dict, None]:
    """
    Run the gap finder pipeline with streaming events for UI updates.
    
    Args:
        user_query: Research domain or question
        
    Yields:
        Event dicts with type, agent, phase, and content
    """
    
    yield {"type": "pipeline_start", "query": user_query}
    
    current_state: GapFinderState = {
        "user_query": user_query,
        "search_plan": {},
        "search_queries": [],
        "raw_papers": [],
        "paper_count": 0,
        "statistics": {},
        "analysis": {},
        "gaps": {},
        "current_node": "",
        "error": None
    }
    
    # =========================================================================
    # Node 1: Query Planner (LLM)
    # =========================================================================
    
    node_id = "query_planner"
    meta = NODE_METADATA[node_id]
    
    yield {"type": "agent_event", "agent": node_id, "phase": "thinking", "content": meta["thinking"]}
    await asyncio.sleep(0.5)
    
    yield {"type": "agent_event", "agent": node_id, "phase": "output", "content": "Generating search strategy..."}
    
    # Run LLM (not streaming raw tokens)
    try:
        user_message = f"""Research domain: {user_query}

Generate a comprehensive PubMed search strategy for research gap analysis.

IMPORTANT: Respond with ONLY a valid JSON object. No markdown code blocks, no explanations, just the raw JSON."""
        
        llm = get_llm(creative=False)
        messages = [SystemMessage(content=QP_SYSTEM_PROMPT), HumanMessage(content=user_message)]
        response = await llm.ainvoke(messages)
        full_response = response.content
        
        print(f"[DEBUG] Query Planner raw response length: {len(full_response)}")
        print(f"[DEBUG] Query Planner response preview: {full_response[:500]}...")
        
        # Parse response using repair function
        plan = repair_json_response(full_response)
        
        if plan and plan.get("search_queries"):
            queries = plan.get("search_queries", [])
            print(f"[DEBUG] Successfully parsed {len(queries)} queries")
        else:
            print(f"[DEBUG] repair_json_response returned: {plan}")
            # Fallback: try to extract queries from text using regex
            
            # Look for quoted strings that look like search queries
            query_patterns = re.findall(r'"([^"]{10,}(?:AND|OR)[^"]{5,})"', full_response)
            if query_patterns:
                queries = query_patterns[:6]
                plan = {"domain_summary": user_query, "search_rationale": "Extracted via pattern matching"}
                print(f"[DEBUG] Extracted {len(queries)} queries via AND/OR pattern")
            else:
                queries = [user_query, f'{user_query}[Title/Abstract]']
                plan = {"domain_summary": user_query, "search_rationale": "Fallback search due to parsing error"}
                print(f"[DEBUG] Using fallback queries")
        
        current_state["search_plan"] = plan
        current_state["search_queries"] = queries
        current_state["current_node"] = node_id
        
    except Exception as e:
        print(f"[DEBUG] Query Planner exception: {e}")
        import traceback
        traceback.print_exc()
        yield {"type": "agent_event", "agent": node_id, "phase": "error", "content": str(e)}
        current_state["error"] = str(e)
        current_state["search_queries"] = [user_query]
    
    # Format display output
    display_output = _format_query_planner_output(current_state)
    yield {"type": "agent_event", "agent": node_id, "phase": "complete", "content": display_output, "full_output": display_output}
    
    await asyncio.sleep(0.2)
    
    # =========================================================================
    # Node 2: Data Fetcher (No LLM)
    # =========================================================================
    
    node_id = "data_fetcher"
    meta = NODE_METADATA[node_id]
    
    yield {"type": "agent_event", "agent": node_id, "phase": "thinking", "content": meta["thinking"]}
    await asyncio.sleep(0.3)
    
    yield {"type": "agent_event", "agent": node_id, "phase": "output", "content": "Searching PubMed..."}
    
    current_state = await data_fetcher_node(current_state)
    
    display_output = f"Retrieved {current_state['paper_count']} papers from PubMed.\nPapers enriched with citation data."
    yield {"type": "agent_event", "agent": node_id, "phase": "complete", "content": display_output, "full_output": display_output}
    
    if current_state.get("error"):
        yield {"type": "agent_event", "agent": node_id, "phase": "warning", "content": current_state["error"]}
    
    await asyncio.sleep(0.2)
    
    # =========================================================================
    # Node 3: Aggregator (No LLM)
    # =========================================================================
    
    node_id = "aggregator"
    meta = NODE_METADATA[node_id]
    
    yield {"type": "agent_event", "agent": node_id, "phase": "thinking", "content": meta["thinking"]}
    await asyncio.sleep(0.3)
    
    yield {"type": "agent_event", "agent": node_id, "phase": "output", "content": "Building statistics..."}
    
    current_state = await aggregator_node(current_state)
    
    display_output = _format_aggregator_output(current_state)
    yield {"type": "agent_event", "agent": node_id, "phase": "complete", "content": display_output, "full_output": display_output}
    
    await asyncio.sleep(0.2)
    
    # =========================================================================
    # Node 4: Literature Analyzer (LLM)
    # =========================================================================
    
    node_id = "literature_analyzer"
    meta = NODE_METADATA[node_id]
    
    yield {"type": "agent_event", "agent": node_id, "phase": "thinking", "content": meta["thinking"]}
    await asyncio.sleep(0.5)
    
    yield {"type": "agent_event", "agent": node_id, "phase": "output", "content": "Analyzing literature patterns..."}
    
    try:
        stats = current_state.get("statistics", {})
        if stats and not stats.get("error"):
            formatted_stats = format_statistics_for_prompt(stats)
            user_message = f"""RESEARCH DOMAIN: {user_query}

{formatted_stats}

Analyze these statistics and identify research gaps, patterns, and opportunities.

IMPORTANT: Respond with ONLY valid JSON. No markdown code blocks."""
            
            llm = get_llm(creative=False)
            messages = [SystemMessage(content=LA_SYSTEM_PROMPT), HumanMessage(content=user_message)]
            response = await llm.ainvoke(messages)
            full_response = response.content
            
            print(f"[DEBUG] Literature Analyzer response length: {len(full_response)}")
            
            # Parse response using repair function
            analysis = repair_json_response(full_response)
            
            if not analysis:
                print(f"[DEBUG] Literature Analyzer JSON repair failed, using raw")
                analysis = {"raw_analysis": full_response, "parse_error": True}
            else:
                print(f"[DEBUG] Literature Analyzer parsed successfully")
            
            current_state["analysis"] = analysis
        else:
            current_state["analysis"] = {"error": "No statistics to analyze"}
        
        current_state["current_node"] = node_id
        
    except Exception as e:
        print(f"[DEBUG] Literature Analyzer exception: {e}")
        yield {"type": "agent_event", "agent": node_id, "phase": "error", "content": str(e)}
        current_state["analysis"] = {"error": str(e)}
    
    display_output = _format_literature_analyzer_output(current_state)
    yield {"type": "agent_event", "agent": node_id, "phase": "complete", "content": display_output, "full_output": display_output}
    
    await asyncio.sleep(0.2)
    
    # =========================================================================
    # Node 5: Gap Synthesizer (LLM)
    # =========================================================================
    
    node_id = "gap_synthesizer"
    meta = NODE_METADATA[node_id]
    
    yield {"type": "agent_event", "agent": node_id, "phase": "thinking", "content": meta["thinking"]}
    await asyncio.sleep(0.5)
    
    yield {"type": "agent_event", "agent": node_id, "phase": "output", "content": "Synthesizing research gaps and generating hypotheses..."}
    
    try:
        analysis = current_state.get("analysis", {})
        stats = current_state.get("statistics", {})
        
        if analysis and not analysis.get("error"):
            formatted_input = format_analysis_for_prompt(analysis, stats, user_query)
            formatted_input += "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown code blocks."
            
            llm = get_llm(creative=True)
            messages = [SystemMessage(content=GS_SYSTEM_PROMPT), HumanMessage(content=formatted_input)]
            response = await llm.ainvoke(messages)
            full_response = response.content
            
            print(f"[DEBUG] Gap Synthesizer response length: {len(full_response)}")
            
            # Parse response using repair function
            gaps = repair_json_response(full_response)
            
            if not gaps:
                print(f"[DEBUG] Gap Synthesizer JSON repair failed, using raw")
                gaps = {"raw_synthesis": full_response, "parse_error": True}
            else:
                print(f"[DEBUG] Gap Synthesizer parsed successfully")
            
            current_state["gaps"] = gaps
        else:
            current_state["gaps"] = {"error": "No analysis to synthesize"}
        
        current_state["current_node"] = node_id
        
    except Exception as e:
        print(f"[DEBUG] Gap Synthesizer exception: {e}")
        yield {"type": "agent_event", "agent": node_id, "phase": "error", "content": str(e)}
        current_state["gaps"] = {"error": str(e)}
    
    display_output = _format_gap_synthesizer_output(current_state)
    yield {"type": "agent_event", "agent": node_id, "phase": "complete", "content": display_output, "full_output": display_output}
    
    # =========================================================================
    # Pipeline Complete
    # =========================================================================
    
    yield {
        "type": "pipeline_complete",
        "result": {
            "gaps": current_state.get("gaps", {}),
            "statistics": {
                "total_papers": current_state.get("paper_count", 0),
                "queries_used": len(current_state.get("search_queries", []))
            }
        }
    }


# =============================================================================
# Display Formatters
# =============================================================================

def _format_query_planner_output(state: GapFinderState) -> str:
    """Format query planner output for display."""
    plan = state.get("search_plan", {})
    queries = state.get("search_queries", [])
    lines = [
        f"Domain: {plan.get('domain_summary', state['user_query'])}",
        "",
        "Search Queries Generated:",
    ]
    for i, q in enumerate(queries, 1):
        lines.append(f"  {i}. {q}")
    if plan.get("search_rationale"):
        lines.extend(["", f"Rationale: {plan['search_rationale']}"])
    return "\n".join(lines)


def _format_aggregator_output(state: GapFinderState) -> str:
    """Format aggregator output for display."""
    stats = state.get("statistics", {})
    total = stats.get("total_papers", 0)
    
    lines = [f"Analyzed {total} papers", ""]
    
    # Population summary
    pop_counts = stats.get("distributions", {}).get("population", {})
    if pop_counts:
        lines.append("Population Coverage:")
        for cat, data in sorted(pop_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
            lines.append(f"  - {data['display_name']}: {data['count']} ({data['percentage']}%)")
    
    # Intervention summary
    int_counts = stats.get("distributions", {}).get("intervention", {})
    if int_counts:
        lines.append("\nIntervention Coverage:")
        for cat, data in sorted(int_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
            lines.append(f"  - {data['display_name']}: {data['count']} ({data['percentage']}%)")
    
    # Sparse combinations
    sparse = stats.get("sparse_combinations", [])
    if sparse:
        lines.append(f"\nIdentified {len(sparse)} sparse combinations (potential gaps)")
    
    return "\n".join(lines)


def _format_literature_analyzer_output(state: GapFinderState) -> str:
    """Format literature analyzer output for display."""
    analysis = state.get("analysis", {})
    
    # Check for errors
    if analysis.get("error"):
        return f"Error: {analysis.get('error')}"
    
    # If we have a partial parse or full parse, try to display it
    summary = analysis.get("key_findings_summary", "")
    lines = []
    
    if summary:
        lines.append(f"Summary: {summary}")
        lines.append("")
    
    dist = analysis.get("distribution_insights", {})
    
    understudied_pops = dist.get("understudied_populations", [])
    if understudied_pops:
        lines.append("Understudied Populations:")
        for item in understudied_pops[:5]:
            cat = item.get('category', 'Unknown')
            pct = item.get('percentage', 'N/A')
            sig = item.get('significance', '')
            valid = item.get('is_valid_intervention_target', True)
            status = "✓" if valid else "✗"
            lines.append(f"  {status} {cat} ({pct}%): {sig}")
    
    understudied_intervs = dist.get("understudied_interventions", [])
    if understudied_intervs:
        lines.append("\nUnderstudied Interventions:")
        for item in understudied_intervs[:5]:
            cat = item.get('category', 'Unknown')
            sig = item.get('significance', '')
            lines.append(f"  - {cat}: {sig}")
    
    sparse = analysis.get("sparse_combination_analysis", [])
    genuine_gaps = [s for s in sparse if s.get("is_genuine_gap")]
    if genuine_gaps:
        lines.append(f"\nGenuine Research Gaps ({len(genuine_gaps)}):")
        for gap in genuine_gaps[:5]:
            combo = gap.get('combination', 'Unknown')
            count = gap.get('paper_count', 0)
            lines.append(f"  - {combo}: {count} papers")
    
    temporal = analysis.get("temporal_insights", {})
    if temporal:
        lines.append(f"\nField Trend: {temporal.get('overall_trend', 'unknown')}")
    
    return "\n".join(lines) if lines else "Analysis completed"


def _format_gap_synthesizer_output(state: GapFinderState) -> str:
    """Format gap synthesizer output for display."""
    gaps = state.get("gaps", {})
    
    # Check for errors
    if gaps.get("error"):
        return f"Error: {gaps.get('error')}"
    
    lines = []
    
    if gaps.get("synthesis_summary"):
        lines.append(f"SUMMARY: {gaps['synthesis_summary']}")
        lines.append("")
    
    research_gaps = gaps.get("research_gaps", [])
    if research_gaps:
        lines.append(f"{'='*50}")
        lines.append(f"TOP {len(research_gaps)} RESEARCH GAPS")
        lines.append(f"{'='*50}")
        
        for gap in research_gaps:
            rank = gap.get('rank', '?')
            title = gap.get('title', 'Untitled')
            lines.append(f"\n#{rank}: {title}")
            lines.append("-" * 40)
            
            if gap.get('description'):
                lines.append(f"Description: {gap['description']}")
            
            impact = gap.get('impact_rating', 'N/A')
            feasibility = gap.get('feasibility_rating', 'N/A')
            novelty = gap.get('novelty_rating', 'N/A')
            lines.append(f"Ratings: Impact={impact}, Feasibility={feasibility}, Novelty={novelty}")
            
            hypothesis = gap.get("hypothesis", {})
            if hypothesis.get("statement"):
                lines.append(f"Hypothesis: {hypothesis['statement']}")
            
            study = gap.get("suggested_study_design", {})
            if study:
                lines.append(f"Study Design: {study.get('design', 'N/A')} - {study.get('population', 'N/A')}")
    
    recs = gaps.get("methodological_recommendations", [])
    if recs:
        lines.append("\nRecommendations:")
        for rec in recs[:3]:
            lines.append(f"  • {rec}")
    
    return "\n".join(lines) if lines else "Synthesis completed"


# =============================================================================
# Non-Streaming Pipeline (for programmatic use)
# =============================================================================

async def run_gap_finder_pipeline(user_query: str) -> dict:
    """
    Run the gap finder pipeline and return final results.
    
    Args:
        user_query: Research domain or question
        
    Returns:
        Dict with gaps, statistics, and metadata
    """
    final_result = {}
    
    async for event in run_gap_finder_streaming(user_query):
        if event.get("type") == "pipeline_complete":
            final_result = event.get("result", {})
    
    return final_result