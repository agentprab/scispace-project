"""
Shared configuration for Research Gap Finding Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv("../.env")

# =============================================================================
# API Settings
# =============================================================================

# PubMed E-utilities
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_RATE_LIMIT_DELAY = 0.35  # seconds between requests (3 req/sec limit)
PUBMED_MAX_RESULTS_PER_QUERY = 100

# OpenAlex
OPENALEX_BASE_URL = "https://api.openalex.org"
OPENALEX_EMAIL = "research-agent@example.com"  # For polite pool
OPENALEX_BATCH_SIZE = 50

# =============================================================================
# LLM Settings
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
LLM_TEMPERATURE = 0.3
LLM_TEMPERATURE_CREATIVE = 0.7

# =============================================================================
# Pipeline Settings
# =============================================================================

MAX_PAPERS_TOTAL = 500  # Cap to avoid excessive API calls
SPARSE_CELL_THRESHOLD = 3  # Papers below this = potential gap
SAMPLE_ABSTRACTS_COUNT = 15  # Abstracts to send to LLM for contradiction detection
MIN_YEAR = 2018  # Default time range start
