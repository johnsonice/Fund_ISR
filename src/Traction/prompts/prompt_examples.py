"""
Prompt examples and configuration for evaluation pipeline.

This module contains all hardcoded examples, explanations, and metadata
used for stance and agreement classification tasks. Extracted from
evaluate_fiscal_monetray_pipeline.py for better maintainability and reusability.
"""

# ============================================================================
# Section A: Universal Author Type Mappings
# ============================================================================

AUTHOR_TYPE_MAPPING = {
    'staff': 'IMF staff',
    'buff': "a country's authorities"
}

AUTHOR_TYPE_POSSESSIVE_MAPPING = {
    'staff': "IMF staff's",
    'buff': "country's authorities'"
}

AUTHOR_VERB_MAPPING = {
    'staff': 'recommended',
    'buff': 'planned'
}

# ============================================================================
# Section B: Fiscal Stance Examples and Explanations
# ============================================================================

FISCAL_STANCE_EXAMPLES = {
    'staff': (
        'Example 1: Country: Tunisia; Year: 2015; Text: "The modest fiscal loosening in 2015 appropriately responds to weaker economic activity. '
        'Going forward, fiscal consolidation is needed to reduce external imbalances, restore private sector confidence, and ensure debt sustainability." '
        'Answer: "tightening".\n'
        'Example 2: Country: Denmark; Year: 2019; Text: "The fiscal stance should remain neutral, while letting automatic stabilizers operate fully in case of shocks to aggregate demand." '
        'Answer: "no change".\n'
        'Example 3: Country: Denmark; Year: 2017; Text: "Thus, provided that strong new labor market reforms are agreed to raise labor supply, it would be appropriate to slow the pace of consolidation somewhat to facilitate cuts in the high tax burden." '
        'Answer: "loosening bias".'
    ),
    'buff': (
        'Example 1: Country: Tunisia; Year: 2015; Text: "The authorities are firmly committed to take additional measures to attain their fiscal objectives in 2015, including through reduction of non-essential non-wage expenditure. '
        'They are committed to fiscal adjustment from 2016 onwards." Answer: "tightening".\n'
        'Example 2: Country: China; Year: 2019; Text: "We concur with staff\'s suggestion that there is no need for a further large-scale fiscal stimulus at this moment since the effects of trade tensions have already been factored into this year\'s budget." '
        'Answer: "no change".\n'
        'Example 3: Country: Singapore; Year: 2019; Text: "While fiscal policy is focused on medium- to long-term restructuring, the authorities stand ready to provide fiscal stimulus should economic conditions take a significant turn for the worse." '
        'Answer: "loosening bias".'
    ),
}

FISCAL_STANCE_EXPLANATIONS = {
    'staff': "Note that the near-term policy direction recommended by staff is different in concept from staff's projected near-term policy direction of the authorities.",
    'buff': "Note that the near-term policy direction planned by the authorities are different in concept from IMF staff's recommended or projected near-term policy direction.",
}

# ============================================================================
# Section C: Monetary Stance Examples and Explanations
# ============================================================================

MONETARY_STANCE_EXAMPLES = {
    'staff': (
        'Example 1: Country: Guyana; Year: 2017; Text: "The accommodative monetary policy is appropriate, but should gradually move towards a neutral stance in 2017." '
        'Answer: {"stance_current": "accommodative", "stance_future": "tightening"}.\n'
        'Example 2: Country: Mauritius; Year: 2015; Text: "The monetary policy stance is broadly appropriate given the low-inflation environment." '
        'Answer: {"stance_current": "unclear", "stance_future": "no change"}.'
    ),
    'buff': (
        'Example 1: Country: Mauritius; Year: 2015; Text: "The monetary policy pursued by Bank of Mauritius will remain cautiously accommodative to subdue inflation." '
        'Answer: {"stance_current": "accommodative", "stance_future": "no change"}.\n'
        'Example 2: Country: Guyana; Year: 2017; Text: "The authorities note staff\\\'s recommendation to gradually tighten monetary policy in 2017. However, ... the BoG will continue to closely monitor ... before adjusting its policy stance." '
        'Answer: {"stance_current": "accommodative", "stance_future": "tightening bias"}.'
    ),
}

MONETARY_STANCE_EXPLANATIONS = {
    'staff': "Note that the near-term policy direction recommended by staff is different in concept from staff's projected near-term policy direction of the authorities.",
    'buff': "Note that the near-term policy direction planned by the authorities are different in concept from IMF staff's recommended or projected near-term policy direction.",
}

# ============================================================================
# Section D: Task Configuration
# ============================================================================

# Ground truth columns for each task type
TASK_GROUND_TRUTH_COLS = {
    'fiscal_stance': ['stance_near_term'],
    'monetary_stance': ['stance_current', 'stance_future'],
    'monetary_agreement': ['agreement_general', 'disagreement_areas'],
    'fiscal_agreement': ['agreement_general', 'disagreement_areas']
}

# Task-specific example/explanation mappings
TASK_EXAMPLES = {
    'fiscal_stance': FISCAL_STANCE_EXAMPLES,
    'monetary_stance': MONETARY_STANCE_EXAMPLES
}

TASK_EXPLANATIONS = {
    'fiscal_stance': FISCAL_STANCE_EXPLANATIONS,
    'monetary_stance': MONETARY_STANCE_EXPLANATIONS
}

# Column mappings for each task type
TASK_COLUMN_MAPPINGS = {
    'agreement': {
        'COUNTRY': 'country',
        'YEAR': 'year',
        'STAFF_TEXT': 'staff',
        'AUTHORITY_TEXT': 'buff',
    },
    'stance': {
        'COUNTRY': 'country',
        'YEAR': 'year',
        'TEXT': 'text',
        'TYPE': 'author_type',
        'TYPE_POSSESSIVE': 'type_possessive',
        'VERB': 'verb',
        'EXAMPLES': 'examples',
        'EXPLANATION': 'explanation',
    }
}
