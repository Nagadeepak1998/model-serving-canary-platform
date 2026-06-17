from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionFeatures(BaseModel):
    ticket_id: str = Field(min_length=3)
    account_tier: str
    minutes_open: int = Field(ge=0)
    message_length: int = Field(ge=1)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    similar_incidents: int = Field(ge=0)
    escalation_keywords: int = Field(ge=0)


class PredictionResult(BaseModel):
    model: str
    risk_score: float = Field(ge=0.0, le=1.0)
    priority: str
    summary: str


class ReleaseDecision(BaseModel):
    selected_model: str
    canary_percent: int = Field(ge=0, le=100)
    reason: str


class ShadowComparison(BaseModel):
    absolute_score_delta: float = Field(ge=0.0, le=1.0)
    priority_changed: bool
    baseline_priority: str
    canary_priority: str
