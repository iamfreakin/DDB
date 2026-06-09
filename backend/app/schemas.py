from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Mood = Literal[
    "warm",
    "friendly",
    "emotional",
    "premium",
    "playful",
    "clean",
    "trustworthy",
]
AnalysisStatus = Literal["draft", "approved", "stale", "superseded"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrandProfileInput(APIModel):
    products: list[str] = Field(min_length=1, max_length=5)
    target_customers: str = Field(min_length=10, max_length=300)
    strengths: str = Field(min_length=10, max_length=500)
    desired_moods: list[Mood] = Field(min_length=1, max_length=3)
    region: str | None = Field(default=None, max_length=100)
    price_range: str | None = Field(default=None, max_length=50)
    existing_copy: str | None = Field(default=None, max_length=1000)
    avoid_expressions: list[str] = Field(default_factory=list, max_length=20)
    campaign_facts: dict[str, str] = Field(default_factory=dict)

    @field_validator("products", "avoid_expressions")
    @classmethod
    def validate_short_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value or len(value) > 50 for value in cleaned):
            raise ValueError("각 항목은 1~50자여야 합니다.")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("중복 항목은 입력할 수 없습니다.")
        return cleaned

    @field_validator("desired_moods")
    @classmethod
    def validate_unique_moods(cls, values: list[Mood]) -> list[Mood]:
        if len(set(values)) != len(values):
            raise ValueError("분위기는 중복 선택할 수 없습니다.")
        return values


class BrandCreate(APIModel):
    name: str = Field(min_length=1, max_length=50)
    industry: str = Field(min_length=1, max_length=50)
    profile: BrandProfileInput


class BrandProfileResponse(BrandProfileInput):
    id: str
    version: int
    created_at: str


class BrandResponse(APIModel):
    id: str
    name: str
    industry: str
    active_profile: BrandProfileResponse
    created_at: str
    updated_at: str


class BrandListResponse(APIModel):
    items: list[BrandResponse]
    total: int
    limit: int
    offset: int


class AnalysisGenerateRequest(APIModel):
    regenerate: bool = False


class BrandAnalysisResponse(APIModel):
    id: str
    profile_version_id: str
    status: AnalysisStatus
    brand_summary: str
    target_segments: list[str]
    customer_needs: list[str]
    value_proposition: str
    differentiators: list[str]
    brand_voice: list[str]
    recommended_keywords: list[str]
    avoid_expressions: list[str]
    missing_information: list[str]
    generation_run_id: str | None
    approved_at: str | None
    created_at: str
    updated_at: str


class BrandAnalysisUpdate(APIModel):
    brand_summary: str | None = Field(default=None, min_length=1, max_length=300)
    target_segments: list[str] | None = None
    customer_needs: list[str] | None = None
    value_proposition: str | None = Field(default=None, min_length=1, max_length=500)
    differentiators: list[str] | None = None
    brand_voice: list[str] | None = None
    recommended_keywords: list[str] | None = None
    avoid_expressions: list[str] | None = None
    missing_information: list[str] | None = None

    @model_validator(mode="after")
    def require_change(self) -> "BrandAnalysisUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 필드를 한 개 이상 입력해 주세요.")
        if self.brand_voice is not None and len(self.brand_voice) != 3:
            raise ValueError("브랜드 보이스는 정확히 3개여야 합니다.")
        return self


class HealthResponse(APIModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "error"]
    version: str


class ErrorResponse(APIModel):
    error: dict[str, Any]
