from typing import List, Optional, Dict, Type, Literal
from pydantic import BaseModel, Field
from enum import Enum

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