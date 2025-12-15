"""
MeSH Term to PICO Category Mappings.

Maps PubMed MeSH (Medical Subject Headings) terms to structured PICO dimensions:
- Population
- Intervention  
- Comparison (not typically in MeSH)
- Outcome
- Setting
- Study Type

No LLM - pure dictionary lookups.
"""

# =============================================================================
# PICO Dimension Mappings
# =============================================================================

MESH_TO_PICO = {
    # =========================================================================
    # POPULATIONS
    # =========================================================================
    
    # Age groups
    "Adult": ("population", "adults"),
    "Young Adult": ("population", "young_adults"),
    "Middle Aged": ("population", "middle_aged"),
    "Aged": ("population", "elderly"),
    "Aged, 80 and over": ("population", "elderly"),
    "Adolescent": ("population", "adolescents"),
    "Child": ("population", "children"),
    "Infant": ("population", "infants"),
    
    # Pregnancy/reproductive
    "Pregnant Women": ("population", "pregnant"),
    "Pregnancy": ("population", "pregnant"),
    "Postpartum Period": ("population", "postpartum"),
    
    # Socioeconomic
    "Poverty": ("population", "low_income"),
    "Socioeconomic Factors": ("population", "low_income"),
    "Medically Uninsured": ("population", "uninsured"),
    "Homeless Persons": ("population", "homeless"),
    "Vulnerable Populations": ("population", "vulnerable"),
    
    # Race/ethnicity
    "Minority Groups": ("population", "minorities"),
    "African Americans": ("population", "african_american"),
    "Hispanic Americans": ("population", "hispanic"),
    "Asian Americans": ("population", "asian"),
    "American Indian or Alaska Native": ("population", "native_american"),
    
    # Health conditions
    "Mental Disorders": ("population", "psychiatric_comorbidity"),
    "Substance-Related Disorders": ("population", "substance_use_disorder"),
    "Alcohol-Related Disorders": ("population", "alcohol_use_disorder"),
    "Depression": ("population", "depression"),
    "Anxiety Disorders": ("population", "anxiety"),
    "Schizophrenia": ("population", "schizophrenia"),
    "Diabetes Mellitus": ("population", "diabetes"),
    "Cardiovascular Diseases": ("population", "cardiovascular"),
    "Pulmonary Disease, Chronic Obstructive": ("population", "copd"),
    "HIV Infections": ("population", "hiv"),
    
    # Occupational
    "Veterans": ("population", "veterans"),
    "Health Personnel": ("population", "healthcare_workers"),
    "Military Personnel": ("population", "military"),
    
    # Sex
    "Male": ("population", "male"),
    "Female": ("population", "female"),
    
    # =========================================================================
    # INTERVENTIONS - Behavioral and Public Health
    # =========================================================================
    
    # Pharmacological (various domains)
    "Nicotine Replacement Therapy": ("intervention", "nrt"),
    "Tobacco Use Cessation Devices": ("intervention", "nrt"),
    "Nicotine": ("intervention", "nrt"),
    "Nicotinic Agonists": ("intervention", "nrt"),
    "Varenicline": ("intervention", "varenicline"),
    "Bupropion": ("intervention", "bupropion"),
    "Cytisine": ("intervention", "cytisine"),
    "Antidepressive Agents": ("intervention", "antidepressants"),
    "Antipsychotic Agents": ("intervention", "antipsychotics"),
    "Naltrexone": ("intervention", "naltrexone"),
    "Methadone": ("intervention", "methadone"),
    
    # Behavioral/Psychotherapy
    "Counseling": ("intervention", "counseling"),
    "Cognitive Behavioral Therapy": ("intervention", "cbt"),
    "Motivational Interviewing": ("intervention", "motivational_interviewing"),
    "Behavior Therapy": ("intervention", "behavior_therapy"),
    "Psychotherapy": ("intervention", "psychotherapy"),
    "Psychotherapy, Group": ("intervention", "group_therapy"),
    "Family Therapy": ("intervention", "family_therapy"),
    "Crisis Intervention": ("intervention", "crisis_intervention"),
    "Mindfulness": ("intervention", "mindfulness"),
    
    # Education and prevention
    "Health Education": ("intervention", "health_education"),
    "Patient Education as Topic": ("intervention", "patient_education"),
    "Health Promotion": ("intervention", "health_promotion"),
    "Preventive Health Services": ("intervention", "prevention"),
    "Primary Prevention": ("intervention", "primary_prevention"),
    "Secondary Prevention": ("intervention", "secondary_prevention"),
    
    # Technology-based
    "Hotlines": ("intervention", "hotlines"),
    "Telephone": ("intervention", "telephone_intervention"),
    "Text Messaging": ("intervention", "mobile_sms"),
    "Telemedicine": ("intervention", "telehealth"),
    "Mobile Applications": ("intervention", "mobile_app"),
    "Internet": ("intervention", "web_based"),
    "Smartphone": ("intervention", "mobile_app"),
    "Video Games": ("intervention", "gamification"),
    
    # Incentives and social support
    "Motivation": ("intervention", "incentives"),
    "Reward": ("intervention", "incentives"),
    "Social Support": ("intervention", "social_support"),
    "Peer Group": ("intervention", "peer_support"),
    "Self-Help Groups": ("intervention", "self_help_groups"),
    "Community Networks": ("intervention", "community_support"),
    
    # Screening and brief interventions
    "Mass Screening": ("intervention", "screening"),
    "Early Medical Intervention": ("intervention", "brief_intervention"),
    "Early Intervention, Educational": ("intervention", "early_intervention"),
    
    # Case management and care coordination
    "Case Management": ("intervention", "case_management"),
    "Patient Navigation": ("intervention", "patient_navigation"),
    "Patient Care Team": ("intervention", "care_coordination"),
    "Referral and Consultation": ("intervention", "referral"),
    
    # Exercise and lifestyle
    "Exercise": ("intervention", "exercise"),
    "Exercise Therapy": ("intervention", "exercise_therapy"),
    "Diet Therapy": ("intervention", "diet_intervention"),
    "Life Style": ("intervention", "lifestyle_intervention"),
    "Weight Loss": ("intervention", "weight_management"),
    
    # =========================================================================
    # SETTINGS
    # =========================================================================
    
    "Emergency Service, Hospital": ("setting", "emergency_department"),
    "Emergency Medical Services": ("setting", "emergency_department"),
    "Hospitals": ("setting", "inpatient"),
    "Hospitalization": ("setting", "inpatient"),
    "Primary Health Care": ("setting", "primary_care"),
    "Ambulatory Care": ("setting", "outpatient"),
    "Community Health Services": ("setting", "community"),
    "Hospitals, Urban": ("setting", "urban_hospital"),
    "Hospitals, Rural": ("setting", "rural_hospital"),
    "Hospitals, Community": ("setting", "community_hospital"),
    "Academic Medical Centers": ("setting", "academic_medical_center"),
    
    # =========================================================================
    # OUTCOMES
    # =========================================================================
    
    "Smoking Cessation": ("outcome", "cessation"),
    "Tobacco Use Cessation": ("outcome", "cessation"),
    "Tobacco Use Disorder": ("outcome", "tobacco_dependence"),
    "Recurrence": ("outcome", "relapse"),
    "Treatment Outcome": ("outcome", "treatment_outcome"),
    
    # Economic
    "Cost-Benefit Analysis": ("outcome", "cost_effectiveness"),
    "Health Care Costs": ("outcome", "cost"),
    "Cost of Illness": ("outcome", "cost"),
    
    # Quality measures
    "Quality of Life": ("outcome", "quality_of_life"),
    "Patient Satisfaction": ("outcome", "satisfaction"),
    "Patient Compliance": ("outcome", "adherence"),
    "Medication Adherence": ("outcome", "adherence"),
    
    # Engagement
    "Patient Acceptance of Health Care": ("outcome", "engagement"),
    "Health Services Accessibility": ("outcome", "access"),
    
    # =========================================================================
    # STUDY TYPES (from PublicationType, not MeSH)
    # =========================================================================
    
    "Randomized Controlled Trial": ("study_type", "rct"),
    "Controlled Clinical Trial": ("study_type", "controlled_trial"),
    "Clinical Trial": ("study_type", "clinical_trial"),
    "Pragmatic Clinical Trial": ("study_type", "pragmatic_trial"),
    "Observational Study": ("study_type", "observational"),
    "Cohort Studies": ("study_type", "cohort"),
    "Cross-Sectional Studies": ("study_type", "cross_sectional"),
    "Case-Control Studies": ("study_type", "case_control"),
    "Systematic Review": ("study_type", "systematic_review"),
    "Meta-Analysis": ("study_type", "meta_analysis"),
    "Review": ("study_type", "review"),
    "Qualitative Research": ("study_type", "qualitative"),
    "Pilot Projects": ("study_type", "pilot"),
}


# =============================================================================
# Reverse Lookups
# =============================================================================

def get_all_categories(dimension: str) -> list[str]:
    """Get all unique category values for a given dimension."""
    categories = set()
    for mesh_term, (dim, cat) in MESH_TO_PICO.items():
        if dim == dimension:
            categories.add(cat)
    return sorted(list(categories))


# Pre-computed category lists
POPULATION_CATEGORIES = get_all_categories("population")
INTERVENTION_CATEGORIES = get_all_categories("intervention")
SETTING_CATEGORIES = get_all_categories("setting")
OUTCOME_CATEGORIES = get_all_categories("outcome")
STUDY_TYPE_CATEGORIES = get_all_categories("study_type")


# =============================================================================
# Mapping Functions
# =============================================================================

def map_mesh_term(mesh_term: str) -> tuple[str, str] | None:
    """
    Map a single MeSH term to its PICO dimension and category.
    
    Args:
        mesh_term: MeSH descriptor name
        
    Returns:
        Tuple of (dimension, category) or None if not mapped
    """
    return MESH_TO_PICO.get(mesh_term)


def map_mesh_terms(mesh_terms: list[str]) -> dict[str, list[str]]:
    """
    Map a list of MeSH terms to PICO categories.
    
    Args:
        mesh_terms: List of MeSH descriptor names
        
    Returns:
        Dict with dimensions as keys and lists of matched categories as values
    """
    result = {
        "population": [],
        "intervention": [],
        "setting": [],
        "outcome": [],
        "study_type": []
    }
    
    for term in mesh_terms:
        mapping = MESH_TO_PICO.get(term)
        if mapping:
            dimension, category = mapping
            if category not in result[dimension]:
                result[dimension].append(category)
    
    return result


def get_dimension_display_name(category: str) -> str:
    """Convert category slug to display name."""
    return category.replace("_", " ").title()