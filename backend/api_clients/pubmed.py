"""
PubMed E-utilities API Client.

Handles searching and fetching papers from PubMed.
No LLM - pure API calls.
"""

import asyncio
import httpx
from typing import Optional
from config import (
    PUBMED_BASE_URL, 
    PUBMED_RATE_LIMIT_DELAY, 
    PUBMED_MAX_RESULTS_PER_QUERY
)


async def search_pubmed(query: str, max_results: int = PUBMED_MAX_RESULTS_PER_QUERY) -> list[str]:
    """
    Search PubMed and return list of PMIDs.
    
    Uses esearch.fcgi endpoint.
    
    Args:
        query: Search query string (use MeSH terms for best results)
        max_results: Maximum number of results to return
        
    Returns:
        List of PMID strings
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 200),
            "retmode": "json",
            "sort": "relevance"
        }
        
        response = await client.get(f"{PUBMED_BASE_URL}/esearch.fcgi", params=params)
        response.raise_for_status()
        
        data = response.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        
        return pmids


async def fetch_pubmed_records(pmids: list[str]) -> str:
    """
    Fetch full PubMed records for given PMIDs.
    
    Uses efetch.fcgi endpoint.
    
    Args:
        pmids: List of PMID strings
        
    Returns:
        Raw XML string containing all records
    """
    if not pmids:
        return ""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        response = await client.get(f"{PUBMED_BASE_URL}/efetch.fcgi", params=params)
        response.raise_for_status()
        
        return response.text


async def search_and_fetch(
    query: str, 
    max_results: int = PUBMED_MAX_RESULTS_PER_QUERY,
    on_progress: Optional[callable] = None
) -> str:
    """
    Combined search and fetch - returns XML for a single query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results
        on_progress: Optional callback for progress updates
        
    Returns:
        Raw XML string containing records
    """
    if on_progress:
        on_progress(f"Searching PubMed: {query}")
    
    pmids = await search_pubmed(query, max_results)
    
    if on_progress:
        on_progress(f"Found {len(pmids)} papers, fetching records...")
    
    # Rate limit compliance
    await asyncio.sleep(PUBMED_RATE_LIMIT_DELAY)
    
    xml_data = await fetch_pubmed_records(pmids)
    
    return xml_data


async def search_multiple_queries(
    queries: list[str],
    max_per_query: int = PUBMED_MAX_RESULTS_PER_QUERY,
    on_progress: Optional[callable] = None
) -> list[str]:
    """
    Execute multiple search queries and return combined PMIDs (deduplicated).
    
    Args:
        queries: List of search query strings
        max_per_query: Maximum results per query
        on_progress: Optional callback for progress updates
        
    Returns:
        List of unique PMID strings
    """
    all_pmids = set()
    
    for i, query in enumerate(queries):
        if on_progress:
            on_progress(f"Query {i+1}/{len(queries)}: {query}")
        
        pmids = await search_pubmed(query, max_per_query)
        all_pmids.update(pmids)
        
        # Rate limit between queries
        if i < len(queries) - 1:
            await asyncio.sleep(PUBMED_RATE_LIMIT_DELAY)
    
    if on_progress:
        on_progress(f"Total unique papers found: {len(all_pmids)}")
    
    return list(all_pmids)


async def fetch_in_batches(
    pmids: list[str], 
    batch_size: int = 100,
    on_progress: Optional[callable] = None
) -> str:
    """
    Fetch PMIDs in batches to avoid overwhelming the API.
    
    Args:
        pmids: List of all PMIDs to fetch
        batch_size: Number of PMIDs per batch
        on_progress: Optional callback for progress updates
        
    Returns:
        Combined XML string of all records
    """
    xml_parts = []
    
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        
        if on_progress:
            on_progress(f"Fetching batch {i//batch_size + 1}/{(len(pmids)-1)//batch_size + 1} ({len(batch)} papers)")
        
        xml_data = await fetch_pubmed_records(batch)
        xml_parts.append(xml_data)
        
        # Rate limit between batches
        if i + batch_size < len(pmids):
            await asyncio.sleep(PUBMED_RATE_LIMIT_DELAY)
    
    return "\n".join(xml_parts)
