"""
OpenAlex API Client.

Handles enrichment of papers with citation counts, concepts, and trends.
No LLM - pure API calls.
"""

import asyncio
import httpx
from typing import Optional
from config import OPENALEX_BASE_URL, OPENALEX_EMAIL, OPENALEX_BATCH_SIZE


async def enrich_papers_by_doi(
    papers: list[dict],
    on_progress: Optional[callable] = None
) -> list[dict]:
    """
    Enrich papers with OpenAlex data (citation counts, concepts).
    
    Args:
        papers: List of paper dicts, each should have 'doi' field
        on_progress: Optional callback for progress updates
        
    Returns:
        Same papers list with added 'citation_count' and 'concepts' fields
    """
    # Filter papers that have DOIs
    papers_with_doi = [(i, p) for i, p in enumerate(papers) if p.get("doi")]
    
    if not papers_with_doi:
        if on_progress:
            on_progress("No DOIs found, skipping OpenAlex enrichment")
        return papers
    
    if on_progress:
        on_progress(f"Enriching {len(papers_with_doi)} papers with OpenAlex data...")
    
    headers = {"mailto": OPENALEX_EMAIL}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Process in batches
        for batch_start in range(0, len(papers_with_doi), OPENALEX_BATCH_SIZE):
            batch = papers_with_doi[batch_start:batch_start + OPENALEX_BATCH_SIZE]
            
            # Build DOI filter - OpenAlex expects DOIs without https://doi.org/ prefix
            dois = []
            for _, paper in batch:
                doi = paper["doi"]
                # Clean DOI format
                if doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")
                elif doi.startswith("http://doi.org/"):
                    doi = doi.replace("http://doi.org/", "")
                dois.append(doi)
            
            doi_filter = "|".join(dois)
            
            try:
                response = await client.get(
                    f"{OPENALEX_BASE_URL}/works",
                    params={"filter": f"doi:{doi_filter}"},
                    headers=headers
                )
                response.raise_for_status()
                
                results = response.json().get("results", [])
                
                # Create lookup by DOI
                doi_to_data = {}
                for result in results:
                    result_doi = result.get("doi", "")
                    if result_doi:
                        # Normalize DOI for matching
                        clean_doi = result_doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
                        doi_to_data[clean_doi.lower()] = {
                            "citation_count": result.get("cited_by_count", 0),
                            "concepts": [c.get("display_name") for c in result.get("concepts", [])[:5]],
                            "open_access": result.get("open_access", {}).get("is_oa", False),
                            "referenced_works_count": len(result.get("referenced_works", []))
                        }
                
                # Merge back into papers
                for idx, paper in batch:
                    paper_doi = paper["doi"]
                    if paper_doi.startswith("https://doi.org/"):
                        paper_doi = paper_doi.replace("https://doi.org/", "")
                    elif paper_doi.startswith("http://doi.org/"):
                        paper_doi = paper_doi.replace("http://doi.org/", "")
                    
                    if paper_doi.lower() in doi_to_data:
                        data = doi_to_data[paper_doi.lower()]
                        papers[idx]["citation_count"] = data["citation_count"]
                        papers[idx]["openalex_concepts"] = data["concepts"]
                        papers[idx]["open_access"] = data["open_access"]
                
            except Exception as e:
                if on_progress:
                    on_progress(f"OpenAlex batch error (non-fatal): {str(e)}")
            
            # Small delay between batches
            if batch_start + OPENALEX_BATCH_SIZE < len(papers_with_doi):
                await asyncio.sleep(0.1)
    
    if on_progress:
        enriched_count = sum(1 for p in papers if p.get("citation_count") is not None)
        on_progress(f"Enriched {enriched_count} papers with citation data")
    
    return papers


async def get_concept_trends(
    concept: str,
    years: int = 6,
    on_progress: Optional[callable] = None
) -> dict[str, int]:
    """
    Get publication count trends for a concept over time.
    
    Args:
        concept: Search concept/term
        years: Number of years to look back
        on_progress: Optional callback for progress updates
        
    Returns:
        Dict mapping year (str) to publication count
    """
    from datetime import datetime
    
    current_year = datetime.now().year
    start_year = current_year - years
    
    headers = {"mailto": OPENALEX_EMAIL}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{OPENALEX_BASE_URL}/works",
                params={
                    "search": concept,
                    "group_by": "publication_year",
                    "filter": f"publication_year:{start_year}-{current_year}"
                },
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            trends = {}
            
            for group in data.get("group_by", []):
                year = group.get("key")
                count = group.get("count", 0)
                if year:
                    trends[str(year)] = count
            
            return trends
            
        except Exception as e:
            if on_progress:
                on_progress(f"OpenAlex trends error: {str(e)}")
            return {}


async def search_openalex(
    query: str,
    max_results: int = 50,
    on_progress: Optional[callable] = None
) -> list[dict]:
    """
    Direct search on OpenAlex (alternative to PubMed for broader coverage).
    
    Args:
        query: Search query
        max_results: Maximum results to return
        on_progress: Optional callback for progress updates
        
    Returns:
        List of paper dicts
    """
    headers = {"mailto": OPENALEX_EMAIL}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{OPENALEX_BASE_URL}/works",
                params={
                    "search": query,
                    "per_page": min(max_results, 100),
                    "sort": "relevance_score:desc",
                    "filter": "is_paratext:false"
                },
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for work in data.get("results", []):
                paper = {
                    "id": work.get("id", ""),
                    "title": work.get("title", "Untitled"),
                    "year": work.get("publication_year"),
                    "citation_count": work.get("cited_by_count", 0),
                    "doi": work.get("doi"),
                    "concepts": [c.get("display_name") for c in work.get("concepts", [])[:5]],
                    "source": "openalex",
                    "open_access": work.get("open_access", {}).get("is_oa", False),
                    "authors": [
                        a.get("author", {}).get("display_name") 
                        for a in work.get("authorships", [])[:3]
                    ],
                }
                
                # Try to reconstruct abstract from inverted index
                abstract_inv = work.get("abstract_inverted_index")
                if abstract_inv:
                    try:
                        max_pos = max(max(positions) for positions in abstract_inv.values())
                        words = [""] * (max_pos + 1)
                        for word, positions in abstract_inv.items():
                            for pos in positions:
                                words[pos] = word
                        paper["abstract"] = " ".join(words)
                    except:
                        paper["abstract"] = None
                else:
                    paper["abstract"] = None
                
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            if on_progress:
                on_progress(f"OpenAlex search error: {str(e)}")
            return []
