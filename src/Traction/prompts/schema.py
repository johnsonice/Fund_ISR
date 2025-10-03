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
    staff_current: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="IMF staff current fiscal policy stance")
    staff_future: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="IMF staff future fiscal policy stance")
    authority_current: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="Country authority current fiscal policy stance")
    authority_future: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="Country authority future fiscal policy stance")
    agreement_other: Literal["agree", "disagree", "neutral", "irrelevant"] = Field(..., description="Agreement on non-stance fiscal policy issues")

class FiscalStanceChainOfThoughtResponse(BaseModel):
    staff_current: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="IMF staff current fiscal policy stance")
    staff_future: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="IMF staff future fiscal policy stance")
    authority_current: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="Country authority current fiscal policy stance")
    authority_future: Literal["contractionary", "moderately contractionary", "neutral", "moderately expansionary", "expansionary"] = Field(..., description="Country authority future fiscal policy stance")
    agreement_other: Literal["agree", "disagree", "neutral", "irrelevant"] = Field(..., description="Agreement on non-stance fiscal policy issues")
    reason: str = Field(..., description="Reasoning for the classifications")

# Fiscal Agreement Classification Schemas
class FiscalAgreementResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities on fiscal policy")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")

class FiscalAgreementChainOfThoughtResponse(BaseModel):
    agreement: Literal["irrelevant", "disagreement exists", "mostly agree"] = Field(..., description="Level of agreement between IMF staff and country authorities on fiscal policy")
    disagreement_areas: str = Field(..., description="List of disagreement areas or empty string")
    reason: str = Field(..., description="Reasoning for the classification")
    
    
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
}