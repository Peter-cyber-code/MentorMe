from typing import List

from pydantic import BaseModel, Field


class AuditScores(BaseModel):

    problem_clarity: int = Field(ge=1, le=5)

    solution: int = Field(ge=1, le=5)

    market: int = Field(ge=1, le=5)

    business_model: int = Field(ge=1, le=5)

    financial_readiness: int = Field(ge=1, le=5)

    team: int = Field(ge=1, le=5)


class AuditResult(BaseModel):

    executive_summary: str

    scores: AuditScores

    strengths: List[str]

    risks: List[str]

    market_analysis: str

    business_model_analysis: str

    financial_analysis: str

    recommendations: List[str]

    recommended_support: List[str]