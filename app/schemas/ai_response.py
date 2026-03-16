from pydantic import BaseModel
from typing import List

class AIRecommendation(BaseModel):
    analysis: str
    recommendations: List[str]