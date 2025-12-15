"""
Unified Multi-Agent Pipeline Backend

Supports:
1. Drug Discovery Pipeline (6 agents with dynamic routing)
2. Research Gap Finder Pipeline (5 agents, linear flow)

Run with: uvicorn backend:app --reload --port 8000
"""

import asyncio
import json
import re
import sys
import os
from typing import AsyncGenerator, Dict, Any, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv("../.env")

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Multi-Agent Research Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Configuration
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_LOOPS = 3

# =============================================================================
# LLM Instances
# =============================================================================

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0.3,
    streaming=True,
    api_key=OPENAI_API_KEY
)

llm_creative = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0.7,
    streaming=True,
    api_key=OPENAI_API_KEY
)

# =============================================================================
# Pipeline Type Enum
# =============================================================================

class PipelineType(str, Enum):
    DRUG_DISCOVERY = "drug_discovery"
    RESEARCH_GAP = "research_gap"

# =============================================================================
# RESEARCH GAP PIPELINE
# =============================================================================
# Note: Drug discovery code has been moved to drug_discovery.py

RESEARCH_GAP_AGENTS = {
    "query_planner": {
        "name": "Query Planner",
        "thinking": "Analyzing research domain... Identifying key concepts and MeSH terms... Formulating comprehensive search strategy... Defining PICO dimensions... Planning systematic literature coverage..."
    },
    "data_fetcher": {
        "name": "Data Fetcher", 
        "thinking": "Connecting to PubMed E-utilities... Executing search queries... Retrieving paper metadata... Deduplicating results... Enriching with citation data..."
    },
    "aggregator": {
        "name": "Aggregator",
        "thinking": "Parsing MeSH terms from papers... Mapping to PICO categories... Building frequency distributions... Constructing co-occurrence matrices... Identifying sparse cells..."
    },
    "literature_analyzer": {
        "name": "Literature Analyzer",
        "thinking": "Analyzing population distributions... Examining intervention coverage... Identifying sparse research combinations... Reviewing temporal publication trends... Scanning abstracts for contradictions... Synthesizing gap patterns..."
    },
    "gap_synthesizer": {
        "name": "Gap Synthesizer",
        "thinking": "Prioritizing research gaps by impact and feasibility... Formulating testable hypotheses... Designing study approaches... Assessing resource requirements... Generating actionable recommendations..."
    }
}

RESEARCH_GAP_SEQUENCE = [
    "query_planner",
    "data_fetcher",
    "aggregator",
    "literature_analyzer",
    "gap_synthesizer"
]


# Import drug discovery pipeline
from drug_discovery import (
    run_drug_discovery_pipeline,
    DRUG_DISCOVERY_AGENTS,
    DRUG_DISCOVERY_SEQUENCE
)

# Import gap_finder at module level (will fail gracefully if not available)
try:
    from gap_finder import run_gap_finder_streaming
    GAP_FINDER_AVAILABLE = True
except ImportError as e:
    GAP_FINDER_AVAILABLE = False
    GAP_FINDER_ERROR = str(e)


async def run_research_gap_pipeline(question: str) -> AsyncGenerator[str, None]:
    """Run the 5-agent research gap finder pipeline."""
    
    print(f"[DEBUG] Starting research gap pipeline for: {question}")
    print(f"[DEBUG] GAP_FINDER_AVAILABLE: {GAP_FINDER_AVAILABLE}")
    
    if not GAP_FINDER_AVAILABLE:
        print(f"[DEBUG] Gap finder not available: {GAP_FINDER_ERROR}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'Research gap pipeline not available: {GAP_FINDER_ERROR}'})}\n\n"
        return
    
    iteration = 1
    yield f"data: {json.dumps({'type': 'iteration_start', 'iteration': iteration})}\n\n"
    
    try:
        async for event in run_gap_finder_streaming(question):
            # Convert gap_finder events to frontend-compatible SSE format
            if event.get("type") == "agent_event":
                agent = event.get("agent", "unknown")
                phase = event.get("phase", "working")
                content = event.get("content", "")
                
                # Map phases to frontend expectations
                if phase == "thinking":
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'thinking', 'content': content})}\n\n"
                elif phase == "output":
                    # Streaming LLM tokens
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'output', 'content': content})}\n\n"
                elif phase == "working":
                    # Non-LLM progress updates
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'output', 'content': content})}\n\n"
                elif phase == "complete":
                    full_output = event.get("full_output", content)
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'complete', 'full_output': full_output})}\n\n"
                elif phase == "error":
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'complete', 'full_output': f'Error: {content}'})}\n\n"
                elif phase == "warning":
                    # Pass through warnings
                    yield f"data: {json.dumps({'agent': agent, 'phase': 'output', 'content': f'Warning: {content}'})}\n\n"
            
            elif event.get("type") == "pipeline_complete":
                yield f"data: {json.dumps({'type': 'iteration_end', 'iteration': iteration, 'action': 'complete'})}\n\n"
                yield f"data: {json.dumps({'type': 'pipeline_complete', 'decision': 'COMPLETE', 'result': event.get('result', {}), 'iterations': iteration})}\n\n"
            
            elif event.get("type") == "pipeline_error":
                yield f"data: {json.dumps({'type': 'error', 'message': event.get('error', 'Unknown error')})}\n\n"
            
            elif event.get("type") == "pipeline_start":
                # Already sent iteration_start
                pass
                
    except Exception as e:
        print(f"[DEBUG] Exception in pipeline: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': f'Pipeline error: {str(e)}'})}\n\n"


# =============================================================================
# API Endpoints
# =============================================================================

class PipelineRequest(BaseModel):
    question: str
    pipeline_type: Optional[str] = "drug_discovery"


@app.post("/api/pipeline/stream")
async def stream_pipeline(request: PipelineRequest):
    """Stream pipeline execution based on type."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    
    pipeline_type = request.pipeline_type or "drug_discovery"
    
    if pipeline_type == "research_gap":
        generator = run_research_gap_pipeline(request.question)
    else:
        generator = run_drug_discovery_pipeline(request.question, llm, MAX_LOOPS)
    
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/api/health")
async def health():
    return {"status": "healthy", "pipelines": ["drug_discovery", "research_gap"]}


@app.get("/api/pipelines")
async def list_pipelines():
    """List available pipelines and their agents."""
    return {
        "pipelines": [
            {
                "id": "drug_discovery",
                "name": "Drug Discovery Pipeline",
                "description": "6-agent hypothesis generation with dynamic routing",
                "agents": [{"id": k, "name": v["name"]} for k, v in DRUG_DISCOVERY_AGENTS.items()]
            },
            {
                "id": "research_gap",
                "name": "Research Gap Finder",
                "description": "5-agent literature gap analysis",
                "agents": [{"id": k, "name": v["name"]} for k, v in RESEARCH_GAP_AGENTS.items()]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)