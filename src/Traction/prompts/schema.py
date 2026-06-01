from typing import List, Optional, Dict, Type, Literal
from pydantic import BaseModel, Field

class TopicLabel(BaseModel):
    topic: Literal["Economic Outlook", 
                   "Monetary Policy", 
                   "Fiscal Stance", 
                   "Financial Stability", 
                   "External Stance","Other"] = Field(..., description="Topic label from the predefined list")
    confidence: int = Field(..., description="Confidence score from 0-100", ge=0, le=100)

class TopicResponse(BaseModel):
    reasoning: str = Field(..., description="Explanation for the topic classification")
    topic_labels: List[TopicLabel] = Field(..., description="List of topic labels with confidence scores")

# Monetary Stance Classification Schemas
class MonetaryStanceResponse(BaseModel):
    stance_current: Literal["restrictive", "neutral", "accommodative", "unclear", "irrelevant"] = Field(..., description="Current monetary policy stance")
    stance_future: Literal["tightening", "tightening bias", "no change", "loosening bias", "loosening", "unclear", "irrelevant"] = Field(..., description="Future monetary policy direction")

class MonetaryStanceChainOfThoughtResponse(BaseModel):
    stance_current: Literal["restrictive", "neutral", "accommodative", "unclear", "irrelevant"] = Field(..., description="Current monetary policy stance")
    stance_future: Literal["tightening", "tightening bias", "no change", "loosening bias", "loosening", "unclear", "irrelevant"] = Field(..., description="Future monetary policy direction")
    reason: str = Field(..., description="Reasoning for the classifications")

# Monetary Agreement Classification Schemas
class MonetaryAgreementResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")

class MonetaryAgreementChainOfThoughtResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")
    reason: str = Field(..., description="Reasoning for the classification")

# Fiscal Policy Classification Schemas
class FiscalStanceResponse(BaseModel):
    # NOTE: Fiscal stance prompts in `prompts/` were updated to only return the near-term
    # (next-year) direction of change in fiscal policy stance, not a "current stance".
    stance_near_term: Literal[
        "tightening",
        "tightening bias",
        "no change",
        "loosening bias",
        "loosening",
        "unclear",
        "irrelevant",
    ] = Field(..., description="Near-term (next-year) fiscal policy direction")

class FiscalStanceChainOfThoughtResponse(BaseModel):
    reason: str = Field(..., description="Reasoning for the classification")
    stance_near_term: Literal[
        "tightening",
        "tightening bias",
        "no change",
        "loosening bias",
        "loosening",
        "unclear",
        "irrelevant",
    ] = Field(..., description="Near-term (next-year) fiscal policy direction")

# Fiscal Agreement Classification Schemas
class FiscalAgreementResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities on fiscal policy")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")

class FiscalAgreementChainOfThoughtResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities on fiscal policy")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")
    reason: str = Field(..., description="Reasoning for the classification")


# General (cross-sector) zero-shot Agreement Classification Schema
# Ports the output structure of temp/reference_code/9.llm_general.py: per-sector
# numeric agreement scores (-5..5, with 99 as the "insufficient info" sentinel)
# plus per-sector disagreement-area lists and an "other_areas" bucket.
#
# Wire-format choice: OpenAI's strict structured-output mode requires
# `additionalProperties: false` on every object, which conflicts with the
# reference script's open-ended `{area_name: severity}` dicts. We instead
# represent disagreement areas as a list of {area, severity} objects — same
# information, strict-mode compatible. Field names use underscores
# (`Monetary_Sector`) for consistency with `Agreement_Monetary`.
class DisagreementArea(BaseModel):
    area: str = Field(..., description="Short phrase describing the area of disagreement")
    severity: int = Field(..., description="Level of disagreement, -5 (highest) to -1")


class GeneralAgreementResponse(BaseModel):
    Agreement_General: int = Field(..., description="Overall agreement score, -5 (complete disagreement) to 5 (complete agreement)")
    Agreement_Monetary: int = Field(..., description="Monetary sector agreement score, -5(complete disagreement)..5(complete agreement); 99 if insufficient info")
    Agreement_Fiscal: int = Field(..., description="Fiscal sector agreement score, -5(complete disagreement)..5(complete agreement); 99 if insufficient info")
    Agreement_External: int = Field(..., description="External sector agreement score, -5(complete disagreement)..5(complete agreement); 99 if insufficient info")
    Agreement_Financial: int = Field(..., description="Financial sector agreement score, -5(complete disagreement)..5(complete agreement); 99 if insufficient info")
    Agreement_Real: int = Field(..., description="Real sector agreement score, -5(complete disagreement)..5(complete agreement); 99 if insufficient info")
    Monetary_Sector: List[DisagreementArea] = Field(..., description="Monetary disagreement areas (empty list if none)")
    Fiscal_Sector: List[DisagreementArea] = Field(..., description="Fiscal disagreement areas (empty list if none)")
    External_Sector: List[DisagreementArea] = Field(..., description="External disagreement areas (empty list if none)")
    Financial_Sector: List[DisagreementArea] = Field(..., description="Financial disagreement areas (empty list if none)")
    Real_Sector: List[DisagreementArea] = Field(..., description="Real disagreement areas (empty list if none)")
    other_areas: List[DisagreementArea] = Field(..., description="Cross-sector disagreement areas (empty list if none)")


# v2 of the general-agreement response: promotes "Other" to a first-class sector
# (with its own Agreement_Other score and Other_Sector disagreement-area list),
# replacing the legacy free-form `other_areas` bucket. Used by
# `general_agreement_simple_v2`, which adds explicit guidance on
# policy-vs-outlook weighting and diplomatic-language interpretation.
class GeneralAgreementResponseV2(BaseModel):
    Agreement_General: int = Field(..., description="Overall agreement score, -5 (complete disagreement) to 5 (complete agreement)")
    Agreement_Monetary: int = Field(..., description="Monetary sector agreement score, -5..5; 99 if insufficient info")
    Agreement_Fiscal: int = Field(..., description="Fiscal sector agreement score, -5..5; 99 if insufficient info")
    Agreement_External: int = Field(..., description="External sector agreement score, -5..5; 99 if insufficient info")
    Agreement_Financial: int = Field(..., description="Financial sector agreement score, -5..5; 99 if insufficient info")
    Agreement_Real: int = Field(..., description="Real sector agreement score, -5..5; 99 if insufficient info")
    Agreement_Other: int = Field(..., description="Other-sector (structural reforms, climate, gender, inclusion, governance, digitalization, etc.) agreement score, -5..5; 99 if insufficient info")
    Monetary_Sector: List[DisagreementArea] = Field(..., description="Monetary disagreement areas (empty list if none)")
    Fiscal_Sector: List[DisagreementArea] = Field(..., description="Fiscal disagreement areas (empty list if none)")
    External_Sector: List[DisagreementArea] = Field(..., description="External disagreement areas (empty list if none)")
    Financial_Sector: List[DisagreementArea] = Field(..., description="Financial disagreement areas (empty list if none)")
    Real_Sector: List[DisagreementArea] = Field(..., description="Real disagreement areas (empty list if none)")
    Other_Sector: List[DisagreementArea] = Field(..., description="Other-sector disagreement areas (empty list if none)")


PROMPT_REGISTRY: Dict[str, Dict[str, object]] = {
    # Topic classification
    "topic_classification": {
        "prompt_file": "topic_classification.md",
        "response_model": TopicResponse,
    },

    # Monetary stance
    "monetary_stance_simple": {
        "prompt_file": "monetary_stance_simple.md",
        "response_model": MonetaryStanceResponse,
    },
    "monetary_stance_with_definitions": {
        "prompt_file": "monetary_stance_with_definitions.md",
        "response_model": MonetaryStanceResponse,
    },
    "monetary_stance_few_shot": {
        "prompt_file": "monetary_stance_few_shot.md",
        "response_model": MonetaryStanceResponse,
    },
    "monetary_stance_chain_of_thought": {
        "prompt_file": "monetary_stance_chain_of_thought.md",
        "response_model": MonetaryStanceChainOfThoughtResponse,
    },

    # Monetary agreement
    "monetary_agreement_simple": {
        "prompt_file": "monetary_agreement_simple.md",
        "response_model": MonetaryAgreementResponse,
    },
    "monetary_agreement_with_definitions": {
        "prompt_file": "monetary_agreement_with_definitions.md",
        "response_model": MonetaryAgreementResponse,
    },
    "monetary_agreement_few_shot": {
        "prompt_file": "monetary_agreement_few_shot.md",
        "response_model": MonetaryAgreementResponse,
    },
    "monetary_agreement_chain_of_thought": {
        "prompt_file": "monetary_agreement_chain_of_thought.md",
        "response_model": MonetaryAgreementChainOfThoughtResponse,
    },

    # Fiscal stance
    "fiscal_stance_simple": {
        "prompt_file": "fiscal_stance_simple.md",
        "response_model": FiscalStanceResponse,
    },
    "fiscal_stance_with_definitions": {
        "prompt_file": "fiscal_stance_with_definitions.md",
        "response_model": FiscalStanceResponse,
    },
    "fiscal_stance_few_shot": {
        "prompt_file": "fiscal_stance_few_shot.md",
        "response_model": FiscalStanceResponse,
    },
    "fiscal_stance_chain_of_thought": {
        "prompt_file": "fiscal_stance_chain_of_thought.md",
        "response_model": FiscalStanceChainOfThoughtResponse,
    },

    # Fiscal agreement
    "fiscal_agreement_simple": {
        "prompt_file": "fiscal_agreement_simple.md",
        "response_model": FiscalAgreementResponse,
    },
    "fiscal_agreement_with_definitions": {
        "prompt_file": "fiscal_agreement_with_definitions.md",
        "response_model": FiscalAgreementResponse,
    },
    "fiscal_agreement_few_shot": {
        "prompt_file": "fiscal_agreement_few_shot.md",
        "response_model": FiscalAgreementResponse,
    },
    "fiscal_agreement_chain_of_thought": {
        "prompt_file": "fiscal_agreement_chain_of_thought.md",
        "response_model": FiscalAgreementChainOfThoughtResponse,
    },

    # General (cross-sector) zero-shot agreement
    "general_agreement_simple": {
        "prompt_file": "general_agreement_simple.md",
        "response_model": GeneralAgreementResponse,
    },
    "general_agreement_simple_v2": {
        "prompt_file": "general_agreement_simple_v2.md",
        "response_model": GeneralAgreementResponseV2,
    },
}