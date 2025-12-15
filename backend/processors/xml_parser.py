"""
PubMed XML Parser.

Extracts structured data from PubMed efetch XML responses.
No LLM - pure XML parsing.
"""

import xml.etree.ElementTree as ET
from typing import Optional
from .mesh_mapper import map_mesh_terms, MESH_TO_PICO


def parse_pubmed_xml(xml_string: str) -> list[dict]:
    """
    Parse PubMed XML and extract structured paper data.
    
    Args:
        xml_string: Raw XML from PubMed efetch
        
    Returns:
        List of paper dictionaries with standardized fields
    """
    papers = []
    
    # Handle multiple XML documents concatenated together
    # Wrap in a root element if needed
    if xml_string.count("<?xml") > 1:
        # Multiple XML docs, need to handle each separately
        xml_parts = xml_string.split("<?xml")
        for part in xml_parts:
            if part.strip():
                if not part.startswith("<?xml"):
                    part = "<?xml" + part
                papers.extend(_parse_single_xml(part))
    else:
        papers = _parse_single_xml(xml_string)
    
    return papers


def _parse_single_xml(xml_string: str) -> list[dict]:
    """Parse a single PubMed XML document."""
    papers = []
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        # Try to fix common XML issues
        try:
            # Remove any content before first <
            start_idx = xml_string.find("<")
            if start_idx > 0:
                xml_string = xml_string[start_idx:]
            root = ET.fromstring(xml_string)
        except:
            return []
    
    # Find all PubmedArticle elements
    for article in root.findall(".//PubmedArticle"):
        paper = _parse_article(article)
        if paper:
            papers.append(paper)
    
    return papers


def _parse_article(article: ET.Element) -> Optional[dict]:
    """Parse a single PubmedArticle element."""
    
    paper = {
        "pmid": None,
        "title": None,
        "abstract": None,
        "year": None,
        "journal": None,
        "authors": [],
        "mesh_terms": [],
        "publication_types": [],
        "doi": None,
        "pico": {},
        "source": "pubmed"
    }
    
    # PMID
    pmid_elem = article.find(".//PMID")
    if pmid_elem is not None:
        paper["pmid"] = pmid_elem.text
    
    # Title
    title_elem = article.find(".//ArticleTitle")
    if title_elem is not None:
        paper["title"] = _get_text_content(title_elem)
    
    # Abstract
    abstract_parts = []
    for abstract_text in article.findall(".//AbstractText"):
        label = abstract_text.get("Label", "")
        text = _get_text_content(abstract_text)
        if text:
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    
    if abstract_parts:
        paper["abstract"] = " ".join(abstract_parts)
    
    # Year - try multiple locations
    year = None
    
    # Try PubDate Year
    pub_date_year = article.find(".//PubDate/Year")
    if pub_date_year is not None and pub_date_year.text:
        year = pub_date_year.text
    
    # Try ArticleDate Year
    if not year:
        article_date_year = article.find(".//ArticleDate/Year")
        if article_date_year is not None and article_date_year.text:
            year = article_date_year.text
    
    # Try MedlineDate (format like "2023 Jan-Feb")
    if not year:
        medline_date = article.find(".//PubDate/MedlineDate")
        if medline_date is not None and medline_date.text:
            # Extract first 4-digit year
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', medline_date.text)
            if year_match:
                year = year_match.group(0)
    
    if year:
        try:
            paper["year"] = int(year)
        except ValueError:
            pass
    
    # Journal
    journal_elem = article.find(".//Journal/Title")
    if journal_elem is not None:
        paper["journal"] = journal_elem.text
    else:
        # Try ISOAbbreviation
        journal_abbrev = article.find(".//Journal/ISOAbbreviation")
        if journal_abbrev is not None:
            paper["journal"] = journal_abbrev.text
    
    # Authors
    for author in article.findall(".//Author"):
        last_name = author.find("LastName")
        fore_name = author.find("ForeName")
        initials = author.find("Initials")
        
        if last_name is not None:
            name_parts = [last_name.text]
            if fore_name is not None:
                name_parts.append(fore_name.text)
            elif initials is not None:
                name_parts.append(initials.text)
            paper["authors"].append(" ".join(name_parts))
    
    # MeSH Terms
    for mesh_heading in article.findall(".//MeshHeading"):
        descriptor = mesh_heading.find("DescriptorName")
        if descriptor is not None and descriptor.text:
            paper["mesh_terms"].append(descriptor.text)
        
        # Also get qualifiers for more context
        for qualifier in mesh_heading.findall("QualifierName"):
            if qualifier.text:
                # Store as "Descriptor/Qualifier" for reference
                pass  # Keep simple for now
    
    # Publication Types
    for pub_type in article.findall(".//PublicationType"):
        if pub_type.text:
            paper["publication_types"].append(pub_type.text)
            # Also check if it's in our mapping
            if pub_type.text in MESH_TO_PICO:
                paper["mesh_terms"].append(pub_type.text)
    
    # DOI
    for article_id in article.findall(".//ArticleId"):
        if article_id.get("IdType") == "doi":
            paper["doi"] = article_id.text
            break
    
    # Map MeSH terms to PICO categories
    paper["pico"] = map_mesh_terms(paper["mesh_terms"])
    
    return paper


def _get_text_content(element: ET.Element) -> str:
    """Extract all text content from an element, including nested tags."""
    texts = []
    if element.text:
        texts.append(element.text)
    for child in element:
        if child.text:
            texts.append(child.text)
        if child.tail:
            texts.append(child.tail)
    return " ".join(texts).strip()


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """
    Remove duplicate papers based on PMID or title.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Deduplicated list
    """
    seen_pmids = set()
    seen_titles = set()
    unique_papers = []
    
    for paper in papers:
        pmid = paper.get("pmid")
        title = paper.get("title", "").lower().strip()
        
        # Skip if we've seen this PMID
        if pmid and pmid in seen_pmids:
            continue
        
        # Skip if we've seen very similar title (exact match)
        if title and title in seen_titles:
            continue
        
        if pmid:
            seen_pmids.add(pmid)
        if title:
            seen_titles.add(title)
        
        unique_papers.append(paper)
    
    return unique_papers
