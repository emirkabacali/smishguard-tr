"""Request and response schemas (pydantic v2). FastAPI validates requests against them and
uses them to generate the OpenAPI documentation at ``/docs``."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from smishguard import config

EXAMPLE_TEXT = (
    "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. "
    "24 saat icinde guncelleyin: hxxps://ptt-kargo-takip[.]xyz"
)


class AnalyzeRequest(BaseModel):
    """A message to analyze. Leading/trailing whitespace is stripped before validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(
        min_length=1,
        max_length=config.API_MAX_TEXT_LENGTH,
        description="SMS text (defanged links such as hxxps://a[.]xyz are accepted).",
        examples=[EXAMPLE_TEXT],
    )


class ReasonOut(BaseModel):
    """One fired rule."""

    code: str = Field(examples=["BRAND_IMPERSONATION"])
    weight: float = Field(ge=0, le=1, examples=[0.35])
    message: str


class AnalyzeResponse(BaseModel):
    """Risk assessment for one message."""

    risk_score: float = Field(ge=0, le=1, description="Fused score: alpha*ml + (1-alpha)*rules.")
    risk_level: Literal["low", "medium", "high"]
    ml_probability: float = Field(ge=0, le=1, description="Text model probability (malicious).")
    rule_score: float = Field(ge=0, le=1, description="Sum of fired rule weights, capped at 1.")
    reasons: list[ReasonOut]
    model_version: str


class HealthResponse(BaseModel):
    """Service status."""

    status: Literal["ok", "unavailable"]
    model_loaded: bool
    version: str
