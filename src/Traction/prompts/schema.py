from typing import List, Optional, Dict, Type
from pydantic import BaseModel, Field

class TopicLabel(BaseModel):
    topic: str = Field(..., description="Topic label from the predefined list")
    confidence: int = Field(..., description="Confidence score from 0-100", ge=0, le=100)

class TopicResponse(BaseModel):
    reasoning: str = Field(..., description="Explanation for the topic classification")
    topic_labels: List[TopicLabel] = Field(..., description="List of topic labels with confidence scores")