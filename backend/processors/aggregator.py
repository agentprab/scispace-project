"""
Literature Aggregator.

Builds frequency distributions, co-occurrence matrices, and identifies sparse cells.
No LLM - pure Python statistics.
"""

from collections import Counter
from typing import Optional
import random
from .mesh_mapper import (
    POPULATION_CATEGORIES,
    INTERVENTION_CATEGORIES,
    SETTING_CATEGORIES,
    OUTCOME_CATEGORIES,
    STUDY_TYPE_CATEGORIES,
    get_dimension_display_name
)


def aggregate_papers(papers: list[dict]) -> dict:
    """
    Aggregate papers into frequency distributions across PICO dimensions.
    
    Args:
        papers: List of parsed paper dictionaries with 'pico' field
        
    Returns:
        Dictionary with counts, matrices, and computed statistics
    """
    # Initialize counters
    population_counts = Counter()
    intervention_counts = Counter()
    setting_counts = Counter()
    outcome_counts = Counter()
    study_type_counts = Counter()
    year_counts = Counter()
    
    # Track which papers have which categories for co-occurrence
    paper_categories = []
    
    for paper in papers:
        pico = paper.get("pico", {})
        
        # Count each dimension
        for cat in pico.get("population", []):
            population_counts[cat] += 1
        for cat in pico.get("intervention", []):
            intervention_counts[cat] += 1
        for cat in pico.get("setting", []):
            setting_counts[cat] += 1
        for cat in pico.get("outcome", []):
            outcome_counts[cat] += 1
        for cat in pico.get("study_type", []):
            study_type_counts[cat] += 1
        
        # Count years
        year = paper.get("year")
        if year:
            year_counts[str(year)] += 1
        
        # Store for co-occurrence analysis
        paper_categories.append({
            "populations": set(pico.get("population", [])),
            "interventions": set(pico.get("intervention", [])),
            "outcomes": set(pico.get("outcome", [])),
            "settings": set(pico.get("setting", [])),
            "study_types": set(pico.get("study_type", []))
        })
    
    total = len(papers)
    
    return {
        "total_papers": total,
        "population_counts": dict(population_counts),
        "intervention_counts": dict(intervention_counts),
        "setting_counts": dict(setting_counts),
        "outcome_counts": dict(outcome_counts),
        "study_type_counts": dict(study_type_counts),
        "year_counts": dict(year_counts),
        "paper_categories": paper_categories  # For co-occurrence matrix
    }


def build_cooccurrence_matrix(
    paper_categories: list[dict],
    dim1: str = "populations",
    dim2: str = "interventions"
) -> dict[str, dict[str, int]]:
    """
    Build co-occurrence matrix between two dimensions.
    
    Args:
        paper_categories: List of category sets per paper
        dim1: First dimension key (e.g., "populations")
        dim2: Second dimension key (e.g., "interventions")
        
    Returns:
        Nested dict: matrix[dim1_category][dim2_category] = count
    """
    matrix = {}
    
    for paper_cats in paper_categories:
        cats1 = paper_cats.get(dim1, set())
        cats2 = paper_cats.get(dim2, set())
        
        for c1 in cats1:
            if c1 not in matrix:
                matrix[c1] = Counter()
            for c2 in cats2:
                matrix[c1][c2] += 1
    
    # Convert Counters to dicts
    return {k: dict(v) for k, v in matrix.items()}


def find_sparse_cells(
    matrix: dict[str, dict[str, int]],
    dim1_categories: list[str],
    dim2_categories: list[str],
    threshold: int = 3
) -> list[dict]:
    """
    Find cells in co-occurrence matrix with counts below threshold.
    
    Args:
        matrix: Co-occurrence matrix from build_cooccurrence_matrix
        dim1_categories: All possible categories for dimension 1
        dim2_categories: All possible categories for dimension 2
        threshold: Papers below this count = sparse
        
    Returns:
        List of sparse cell dicts with category names and counts
    """
    sparse = []
    
    for cat1 in dim1_categories:
        for cat2 in dim2_categories:
            count = matrix.get(cat1, {}).get(cat2, 0)
            if count < threshold:
                sparse.append({
                    "dimension1": cat1,
                    "dimension2": cat2,
                    "count": count,
                    "display": f"{get_dimension_display_name(cat1)} + {get_dimension_display_name(cat2)}"
                })
    
    # Sort by count ascending (most sparse first)
    sparse.sort(key=lambda x: x["count"])
    
    return sparse


def calculate_temporal_trends(year_counts: dict[str, int]) -> dict:
    """
    Calculate year-over-year trends and identify emerging/declining topics.
    
    Args:
        year_counts: Dict mapping year to paper count
        
    Returns:
        Dict with trend analysis
    """
    if not year_counts:
        return {"trend": "insufficient_data", "changes": []}
    
    # Sort years
    sorted_years = sorted(year_counts.keys())
    
    if len(sorted_years) < 2:
        return {"trend": "insufficient_data", "changes": []}
    
    # Calculate year-over-year changes
    changes = []
    for i in range(1, len(sorted_years)):
        prev_year = sorted_years[i-1]
        curr_year = sorted_years[i]
        prev_count = year_counts[prev_year]
        curr_count = year_counts[curr_year]
        
        if prev_count > 0:
            pct_change = ((curr_count - prev_count) / prev_count) * 100
        else:
            pct_change = 100 if curr_count > 0 else 0
        
        changes.append({
            "from_year": prev_year,
            "to_year": curr_year,
            "from_count": prev_count,
            "to_count": curr_count,
            "pct_change": round(pct_change, 1)
        })
    
    # Determine overall trend
    recent_changes = changes[-3:] if len(changes) >= 3 else changes
    avg_change = sum(c["pct_change"] for c in recent_changes) / len(recent_changes)
    
    if avg_change > 15:
        trend = "growing"
    elif avg_change < -15:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "avg_recent_change": round(avg_change, 1),
        "changes": changes,
        "peak_year": max(year_counts.keys(), key=lambda y: year_counts[y]),
        "peak_count": max(year_counts.values())
    }


def sample_abstracts(
    papers: list[dict],
    n: int = 15,
    strategy: str = "diverse"
) -> list[dict]:
    """
    Sample abstracts for LLM analysis.
    
    Args:
        papers: List of paper dictionaries
        n: Number of abstracts to sample
        strategy: "diverse" (spread across categories) or "random"
        
    Returns:
        List of sampled paper dicts with abstracts
    """
    # Filter to papers with abstracts
    with_abstracts = [p for p in papers if p.get("abstract")]
    
    if len(with_abstracts) <= n:
        return with_abstracts
    
    if strategy == "random":
        return random.sample(with_abstracts, n)
    
    # Diverse sampling: try to get papers from different categories
    sampled = []
    sampled_pmids = set()
    
    # Group by study type first (want mix of RCTs, reviews, observational)
    by_study_type = {}
    for paper in with_abstracts:
        study_types = paper.get("pico", {}).get("study_type", ["unknown"])
        st = study_types[0] if study_types else "unknown"
        if st not in by_study_type:
            by_study_type[st] = []
        by_study_type[st].append(paper)
    
    # Sample proportionally from each study type
    per_type = max(1, n // len(by_study_type)) if by_study_type else n
    
    for study_type, type_papers in by_study_type.items():
        available = [p for p in type_papers if p.get("pmid") not in sampled_pmids]
        to_sample = min(per_type, len(available))
        if to_sample > 0:
            selected = random.sample(available, to_sample)
            for p in selected:
                sampled.append(p)
                sampled_pmids.add(p.get("pmid"))
    
    # Fill remaining slots randomly
    remaining = n - len(sampled)
    if remaining > 0:
        available = [p for p in with_abstracts if p.get("pmid") not in sampled_pmids]
        if available:
            additional = random.sample(available, min(remaining, len(available)))
            sampled.extend(additional)
    
    return sampled[:n]


def compute_distribution_percentages(counts: dict[str, int], total: int) -> dict:
    """
    Convert counts to percentages.
    
    Args:
        counts: Category counts
        total: Total paper count
        
    Returns:
        Dict with count and percentage for each category
    """
    result = {}
    for cat, count in counts.items():
        pct = (count / total * 100) if total > 0 else 0
        result[cat] = {
            "count": count,
            "percentage": round(pct, 1),
            "display_name": get_dimension_display_name(cat)
        }
    return result


def identify_understudied(
    counts: dict[str, int],
    total: int,
    threshold_pct: float = 5.0
) -> list[dict]:
    """
    Identify categories studied in less than threshold% of papers.
    
    Args:
        counts: Category counts
        total: Total paper count
        threshold_pct: Percentage threshold for "understudied"
        
    Returns:
        List of understudied category dicts
    """
    understudied = []
    
    for cat, count in counts.items():
        pct = (count / total * 100) if total > 0 else 0
        if pct < threshold_pct:
            understudied.append({
                "category": cat,
                "display_name": get_dimension_display_name(cat),
                "count": count,
                "percentage": round(pct, 1)
            })
    
    # Sort by percentage ascending (most understudied first)
    understudied.sort(key=lambda x: x["percentage"])
    
    return understudied


def generate_statistics_summary(papers: list[dict]) -> dict:
    """
    Generate complete statistics summary for LLM input.
    
    Args:
        papers: List of parsed papers
        
    Returns:
        Comprehensive statistics dictionary
    """
    # Basic aggregation
    agg = aggregate_papers(papers)
    total = agg["total_papers"]
    
    # Co-occurrence matrices
    pop_interv_matrix = build_cooccurrence_matrix(
        agg["paper_categories"], "populations", "interventions"
    )
    pop_outcome_matrix = build_cooccurrence_matrix(
        agg["paper_categories"], "populations", "outcomes"
    )
    interv_outcome_matrix = build_cooccurrence_matrix(
        agg["paper_categories"], "interventions", "outcomes"
    )
    
    # Find sparse cells (potential gaps)
    # Get categories that actually appear in data
    active_populations = list(agg["population_counts"].keys())
    active_interventions = list(agg["intervention_counts"].keys())
    active_outcomes = list(agg["outcome_counts"].keys())
    
    sparse_pop_interv = find_sparse_cells(
        pop_interv_matrix, active_populations, active_interventions, threshold=3
    )
    
    # Temporal trends
    temporal = calculate_temporal_trends(agg["year_counts"])
    
    # Understudied categories
    understudied_pops = identify_understudied(agg["population_counts"], total, 5.0)
    understudied_intervs = identify_understudied(agg["intervention_counts"], total, 5.0)
    understudied_outcomes = identify_understudied(agg["outcome_counts"], total, 10.0)
    
    # Sample abstracts
    abstract_samples = sample_abstracts(papers, n=15, strategy="diverse")
    
    return {
        "total_papers": total,
        "year_range": {
            "min": min(agg["year_counts"].keys()) if agg["year_counts"] else None,
            "max": max(agg["year_counts"].keys()) if agg["year_counts"] else None
        },
        "distributions": {
            "population": compute_distribution_percentages(agg["population_counts"], total),
            "intervention": compute_distribution_percentages(agg["intervention_counts"], total),
            "setting": compute_distribution_percentages(agg["setting_counts"], total),
            "outcome": compute_distribution_percentages(agg["outcome_counts"], total),
            "study_type": compute_distribution_percentages(agg["study_type_counts"], total)
        },
        "temporal_trends": temporal,
        "sparse_combinations": sparse_pop_interv[:20],  # Top 20 gaps
        "understudied": {
            "populations": understudied_pops,
            "interventions": understudied_intervs,
            "outcomes": understudied_outcomes
        },
        "sample_abstracts": [
            {
                "pmid": p.get("pmid"),
                "title": p.get("title"),
                "abstract": p.get("abstract", "")[:500],  # Truncate for LLM
                "year": p.get("year"),
                "study_type": p.get("pico", {}).get("study_type", [])
            }
            for p in abstract_samples
        ],
        "raw_counts": {
            "population": agg["population_counts"],
            "intervention": agg["intervention_counts"],
            "outcome": agg["outcome_counts"],
            "study_type": agg["study_type_counts"]
        }
    }
