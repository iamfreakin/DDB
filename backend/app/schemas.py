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
CampaignGoal = Literal[
    "new_product",
    "new_customer",
    "repeat_visit",
    "seasonal_event",
    "brand_awareness",
]
CampaignStatus = Literal[
    "draft",
    "strategy_ready",
    "content_ready",
    "active",
    "completed",
    "archived",
]
ContentStatus = Literal["idea", "draft", "approved", "published", "on_hold"]
ContentOrigin = Literal["ai", "user_edit"]
ContentType = Literal["product", "informational", "relationship", "promotion"]


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


class CampaignCreate(APIModel):
    brand_id: str
    brand_analysis_id: str
    name: str = Field(min_length=1, max_length=100)
    goal: CampaignGoal
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    highlighted_products: list[str] = Field(min_length=1, max_length=5)
    required_facts: dict[str, str] = Field(default_factory=dict)


class CampaignUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    goal: CampaignGoal | None = None
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    highlighted_products: list[str] | None = Field(default=None, min_length=1, max_length=5)
    required_facts: dict[str, str] | None = None

    @model_validator(mode="after")
    def require_change(self) -> "CampaignUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 필드를 한 개 이상 입력해 주세요.")
        return self


class CampaignResponse(APIModel):
    id: str
    brand_id: str
    brand_analysis_id: str
    name: str
    goal: CampaignGoal
    start_date: str
    end_date: str
    channel: Literal["instagram_feed"]
    posts_per_week: int
    highlighted_products: list[str]
    required_facts: dict[str, str]
    status: CampaignStatus
    is_stale: bool = False
    created_at: str
    updated_at: str


class CampaignListResponse(APIModel):
    items: list[CampaignResponse]
    total: int
    limit: int
    offset: int


class GenerateRequest(APIModel):
    regenerate: bool = False


class WeeklyGoal(APIModel):
    week: int = Field(ge=1, le=4)
    goal: str = Field(min_length=1, max_length=200)


class PostTopic(APIModel):
    sequence: int = Field(ge=1, le=8)
    week: int = Field(ge=1, le=4)
    topic: str = Field(min_length=1, max_length=200)
    content_type: ContentType


class CampaignStrategyResponse(APIModel):
    id: str
    campaign_id: str
    version: int
    core_message: str
    weekly_goals: list[WeeklyGoal]
    content_pillars: list[str]
    post_topics: list[PostTopic]
    risk_notes: list[str]
    generation_run_id: str | None
    created_at: str


class ContentGenerateRequest(APIModel):
    strategy_id: str | None = None
    variants_per_content: int = Field(default=1, ge=1, le=3)
    length: Literal["short", "medium", "long"] = "medium"
    emoji_level: Literal["none", "light", "moderate"] = "moderate"
    hashtag_count: int = Field(default=7, ge=5, le=10)


class ContentVariantResponse(APIModel):
    id: str
    content_id: str
    source_variant_id: str | None
    origin: ContentOrigin
    variant_number: int
    tone: str
    opening_line: str
    body: str
    cta: str
    hashtags: list[str]
    image_concept: str
    quality_warnings: list[str]
    generation_run_id: str | None
    created_at: str


class PosterBriefResponse(APIModel):
    id: str
    content_id: str
    headline: str
    supporting_text: str | None
    visual_mood: str
    colors: list[str]
    layout_description: str
    image_prompt: str
    negative_prompt: str | None
    aspect_ratio: str
    generation_run_id: str | None
    created_at: str
    updated_at: str


class ContentResponse(APIModel):
    id: str
    campaign_id: str
    strategy_id: str
    sequence: int
    week_number: int
    content_type: ContentType
    topic: str
    core_message: str
    status: ContentStatus
    selected_variant_id: str | None
    variants: list[ContentVariantResponse] = Field(default_factory=list)
    poster_brief: PosterBriefResponse | None = None
    created_at: str
    updated_at: str


class ContentListResponse(APIModel):
    items: list[ContentResponse]
    total: int
    limit: int
    offset: int


class ContentVariantGenerateRequest(APIModel):
    tone: str | None = Field(default=None, max_length=100)
    length: Literal["short", "medium", "long"] = "medium"
    emoji_level: Literal["none", "light", "moderate"] = "moderate"
    hashtag_count: int = Field(default=7, ge=5, le=10)


class ContentVariantEditRequest(APIModel):
    opening_line: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)
    cta: str = Field(min_length=1, max_length=200)
    hashtags: list[str] = Field(min_length=1, max_length=15)
    image_concept: str = Field(min_length=1, max_length=500)


class SelectedVariantRequest(APIModel):
    variant_id: str


class PosterBriefUpdate(APIModel):
    headline: str | None = Field(default=None, min_length=1, max_length=120)
    supporting_text: str | None = Field(default=None, max_length=200)
    visual_mood: str | None = Field(default=None, min_length=1, max_length=200)
    colors: list[str] | None = None
    layout_description: str | None = Field(default=None, min_length=1, max_length=1000)
    image_prompt: str | None = Field(default=None, min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=1000)
    aspect_ratio: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def require_change(self) -> "PosterBriefUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 필드를 한 개 이상 입력해 주세요.")
        return self


class GeneratedImageCreate(APIModel):
    confirm_cost: bool

    @model_validator(mode="after")
    def require_cost_confirmation(self) -> "GeneratedImageCreate":
        if not self.confirm_cost:
            raise ValueError("이미지 생성 비용 확인이 필요합니다.")
        return self


class GeneratedImageResponse(APIModel):
    id: str
    poster_brief_id: str
    version: int
    status: Literal["draft", "approved", "superseded"]
    provider: str
    model: str
    prompt: str
    aspect_ratio: str
    width: int
    height: int
    generation_run_id: str | None
    approved_at: str | None
    created_at: str


class CalendarCreateRequest(APIModel):
    preferred_weekdays: list[int] = Field(default_factory=lambda: [2, 5])

    @field_validator("preferred_weekdays")
    @classmethod
    def validate_weekdays(cls, values: list[int]) -> list[int]:
        unique = list(dict.fromkeys(values))
        if not unique:
            return [2, 5]
        if any(value < 1 or value > 7 for value in unique):
            raise ValueError("요일은 1~7 사이여야 합니다.")
        return unique


class CalendarItemUpdate(APIModel):
    scheduled_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: ContentStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> "CalendarItemUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 필드를 한 개 이상 입력해 주세요.")
        return self


class CalendarItemResponse(APIModel):
    id: str
    campaign_id: str
    content_id: str
    scheduled_date: str
    status: ContentStatus
    content: ContentResponse | None = None
    approved_image: GeneratedImageResponse | None = None
    created_at: str
    updated_at: str


class ComparisonSetCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    variant_ids: list[str] = Field(min_length=2, max_length=3)


class ComparisonSetResponse(APIModel):
    id: str
    name: str
    variants: list[ContentVariantResponse]
    created_at: str


class HealthResponse(APIModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "error"]
    version: str


class ErrorResponse(APIModel):
    error: dict[str, Any]
