from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse

from backend.app.dependencies import (
    get_analysis_service,
    get_brand_service,
    get_campaign_service,
    get_database,
    get_settings,
)
from backend.app.schemas import (
    AnalysisGenerateRequest,
    BrandAnalysisResponse,
    BrandAnalysisUpdate,
    BrandCreate,
    BrandListResponse,
    BrandProfileInput,
    BrandResponse,
    CalendarCreateRequest,
    CalendarItemResponse,
    CalendarItemUpdate,
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignStrategyResponse,
    CampaignUpdate,
    ComparisonSetCreate,
    ComparisonSetResponse,
    ContentGenerateRequest,
    ContentListResponse,
    ContentResponse,
    ContentStatus,
    ContentVariantEditRequest,
    ContentVariantGenerateRequest,
    ContentVariantResponse,
    GenerateRequest,
    GeneratedImageCreate,
    GeneratedImageResponse,
    HealthResponse,
    PosterBriefResponse,
    PosterBriefUpdate,
    SelectedVariantRequest,
)
from backend.app.services import AnalysisService, BrandService, CampaignService


router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    database = get_database()
    database_status = "ok" if database.healthcheck() else "error"
    return HealthResponse(
        status="ok" if database_status == "ok" else "degraded",
        database=database_status,
        version=get_settings().app_version,
    )


@router.post("/brands", response_model=BrandResponse, status_code=201)
def create_brand(
    request: BrandCreate,
    service: BrandService = Depends(get_brand_service),
) -> BrandResponse:
    return BrandResponse.model_validate(service.create(request))


@router.get("/brands", response_model=BrandListResponse)
def list_brands(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: BrandService = Depends(get_brand_service),
) -> BrandListResponse:
    items, total = service.list(limit, offset)
    return BrandListResponse(
        items=[BrandResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/brands/{brand_id}", response_model=BrandResponse)
def get_brand(
    brand_id: str,
    service: BrandService = Depends(get_brand_service),
) -> BrandResponse:
    return BrandResponse.model_validate(service.get(brand_id))


@router.put(
    "/brands/{brand_id}/profile",
    response_model=BrandResponse,
    status_code=201,
)
def create_profile_version(
    brand_id: str,
    request: BrandProfileInput,
    service: BrandService = Depends(get_brand_service),
) -> BrandResponse:
    return BrandResponse.model_validate(
        service.create_profile_version(brand_id, request)
    )


@router.post(
    "/brands/{brand_id}/analyses",
    response_model=BrandAnalysisResponse,
    status_code=201,
)
def generate_analysis(
    brand_id: str,
    request: AnalysisGenerateRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> BrandAnalysisResponse:
    return BrandAnalysisResponse.model_validate(
        service.generate(brand_id, request.regenerate)
    )


@router.get(
    "/brands/{brand_id}/analyses",
    response_model=list[BrandAnalysisResponse],
)
def list_analyses(
    brand_id: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> list[BrandAnalysisResponse]:
    return [
        BrandAnalysisResponse.model_validate(item)
        for item in service.list_for_brand(brand_id)
    ]


@router.get(
    "/analyses/{analysis_id}",
    response_model=BrandAnalysisResponse,
)
def get_analysis(
    analysis_id: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> BrandAnalysisResponse:
    return BrandAnalysisResponse.model_validate(service.get(analysis_id))


@router.patch(
    "/analyses/{analysis_id}",
    response_model=BrandAnalysisResponse,
)
def update_analysis(
    analysis_id: str,
    request: BrandAnalysisUpdate,
    service: AnalysisService = Depends(get_analysis_service),
) -> BrandAnalysisResponse:
    return BrandAnalysisResponse.model_validate(service.update(analysis_id, request))


@router.post(
    "/analyses/{analysis_id}/approve",
    response_model=BrandAnalysisResponse,
)
def approve_analysis(
    analysis_id: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> BrandAnalysisResponse:
    return BrandAnalysisResponse.model_validate(service.approve(analysis_id))


@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
def create_campaign(
    request: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    return CampaignResponse.model_validate(service.create_campaign(request))


@router.get("/campaigns", response_model=CampaignListResponse)
def list_campaigns(
    brand_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignListResponse:
    items, total = service.list_campaigns(brand_id, status, limit, offset)
    return CampaignListResponse(
        items=[CampaignResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    return CampaignResponse.model_validate(service.get_campaign(campaign_id))


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    request: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    return CampaignResponse.model_validate(service.update_campaign(campaign_id, request))


@router.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> Response:
    service.delete_campaign(campaign_id)
    return Response(status_code=204)


@router.post(
    "/campaigns/{campaign_id}/strategies",
    response_model=CampaignStrategyResponse,
    status_code=201,
)
def generate_strategy(
    campaign_id: str,
    request: GenerateRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignStrategyResponse:
    return CampaignStrategyResponse.model_validate(
        service.generate_strategy(campaign_id, request.regenerate)
    )


@router.get(
    "/campaigns/{campaign_id}/strategies",
    response_model=list[CampaignStrategyResponse],
)
def list_strategies(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> list[CampaignStrategyResponse]:
    return [
        CampaignStrategyResponse.model_validate(item)
        for item in service.list_strategies(campaign_id)
    ]


@router.post(
    "/campaigns/{campaign_id}/contents:generate",
    response_model=list[ContentResponse],
    status_code=201,
)
def generate_contents(
    campaign_id: str,
    request: ContentGenerateRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> list[ContentResponse]:
    return [
        ContentResponse.model_validate(item)
        for item in service.generate_contents(campaign_id, request)
    ]


@router.get("/contents", response_model=ContentListResponse)
def search_contents(
    brand_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: CampaignService = Depends(get_campaign_service),
) -> ContentListResponse:
    items, total = service.search_contents(brand_id, campaign_id, status, limit, offset)
    return ContentListResponse(
        items=[ContentResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/campaigns/{campaign_id}/contents", response_model=list[ContentResponse])
def list_campaign_contents(
    campaign_id: str,
    status: str | None = None,
    week_number: int | None = Query(default=None, ge=1, le=4),
    service: CampaignService = Depends(get_campaign_service),
) -> list[ContentResponse]:
    return [
        ContentResponse.model_validate(item)
        for item in service.list_contents(campaign_id, status, week_number)
    ]


@router.get("/contents/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> ContentResponse:
    return ContentResponse.model_validate(service.get_content(content_id))


@router.patch("/contents/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: str,
    status: ContentStatus,
    service: CampaignService = Depends(get_campaign_service),
) -> ContentResponse:
    return ContentResponse.model_validate(service.update_content_status(content_id, status))


@router.post(
    "/contents/{content_id}/variants",
    response_model=ContentVariantResponse,
    status_code=201,
)
def generate_variant(
    content_id: str,
    request: ContentVariantGenerateRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> ContentVariantResponse:
    return ContentVariantResponse.model_validate(
        service.generate_variant(content_id, request)
    )


@router.post(
    "/variants/{variant_id}/edits",
    response_model=ContentVariantResponse,
    status_code=201,
)
def create_user_edit(
    variant_id: str,
    request: ContentVariantEditRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> ContentVariantResponse:
    return ContentVariantResponse.model_validate(
        service.create_user_edit(variant_id, request)
    )


@router.post("/contents/{content_id}/selected-variant", response_model=ContentResponse)
def select_variant(
    content_id: str,
    request: SelectedVariantRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> ContentResponse:
    return ContentResponse.model_validate(
        service.select_variant(content_id, request.variant_id)
    )


@router.post(
    "/contents/{content_id}/poster-brief",
    response_model=PosterBriefResponse,
    status_code=201,
)
def generate_poster_brief(
    content_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> PosterBriefResponse:
    return PosterBriefResponse.model_validate(service.generate_poster_brief(content_id))


@router.get("/contents/{content_id}/poster-brief", response_model=PosterBriefResponse)
def get_poster_brief(
    content_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> PosterBriefResponse:
    return PosterBriefResponse.model_validate(service.get_poster_brief(content_id))


@router.patch("/contents/{content_id}/poster-brief", response_model=PosterBriefResponse)
def update_poster_brief(
    content_id: str,
    request: PosterBriefUpdate,
    service: CampaignService = Depends(get_campaign_service),
) -> PosterBriefResponse:
    return PosterBriefResponse.model_validate(
        service.update_poster_brief(content_id, request)
    )


@router.post(
    "/poster-briefs/{brief_id}/images",
    response_model=GeneratedImageResponse,
    status_code=201,
)
def generate_image(
    brief_id: str,
    request: GeneratedImageCreate,
    service: CampaignService = Depends(get_campaign_service),
) -> GeneratedImageResponse:
    return GeneratedImageResponse.model_validate(service.generate_image(brief_id))


@router.get(
    "/poster-briefs/{brief_id}/images",
    response_model=list[GeneratedImageResponse],
)
def list_images(
    brief_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> list[GeneratedImageResponse]:
    return [
        GeneratedImageResponse.model_validate(item)
        for item in service.list_images(brief_id)
    ]


@router.post(
    "/generated-images/{image_id}/approve",
    response_model=GeneratedImageResponse,
)
def approve_image(
    image_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> GeneratedImageResponse:
    return GeneratedImageResponse.model_validate(service.approve_image(image_id))


@router.get("/generated-images/{image_id}/file")
def get_generated_image_file(
    image_id: str,
    variant: str = Query(default="composed", pattern="^(composed|background)$"),
    download: bool = Query(default=False),
    service: CampaignService = Depends(get_campaign_service),
) -> FileResponse:
    path, filename = service.get_image_file(image_id, variant)
    return FileResponse(
        path,
        media_type="image/png",
        filename=filename if download else None,
        content_disposition_type="attachment" if download else "inline",
    )


@router.post(
    "/campaigns/{campaign_id}/calendar",
    response_model=list[CalendarItemResponse],
    status_code=201,
)
def create_calendar(
    campaign_id: str,
    request: CalendarCreateRequest,
    service: CampaignService = Depends(get_campaign_service),
) -> list[CalendarItemResponse]:
    return [
        CalendarItemResponse.model_validate(item)
        for item in service.create_calendar(campaign_id, request)
    ]


@router.get(
    "/campaigns/{campaign_id}/calendar",
    response_model=list[CalendarItemResponse],
)
def list_calendar(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> list[CalendarItemResponse]:
    return [
        CalendarItemResponse.model_validate(item)
        for item in service.list_calendar(campaign_id)
    ]


@router.post(
    "/campaigns/{campaign_id}/calendar:refresh",
    response_model=list[CalendarItemResponse],
)
def refresh_calendar(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> list[CalendarItemResponse]:
    return [
        CalendarItemResponse.model_validate(item)
        for item in service.refresh_calendar(campaign_id)
    ]


@router.patch("/calendar-items/{item_id}", response_model=CalendarItemResponse)
def update_calendar_item(
    item_id: str,
    request: CalendarItemUpdate,
    service: CampaignService = Depends(get_campaign_service),
) -> CalendarItemResponse:
    return CalendarItemResponse.model_validate(
        service.update_calendar_item(item_id, request)
    )


@router.post("/comparison-sets", response_model=ComparisonSetResponse, status_code=201)
def create_comparison(
    request: ComparisonSetCreate,
    service: CampaignService = Depends(get_campaign_service),
) -> ComparisonSetResponse:
    return ComparisonSetResponse.model_validate(service.create_comparison(request))


@router.get("/comparison-sets/{set_id}", response_model=ComparisonSetResponse)
def get_comparison(
    set_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> ComparisonSetResponse:
    return ComparisonSetResponse.model_validate(service.get_comparison(set_id))


@router.delete("/comparison-sets/{set_id}", status_code=204)
def delete_comparison(
    set_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> Response:
    service.delete_comparison(set_id)
    return Response(status_code=204)


@router.get("/analyses/{analysis_id}/export.md")
def export_analysis_markdown(
    analysis_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> Response:
    return Response(
        content=service.export_analysis_markdown(analysis_id),
        media_type="text/markdown; charset=utf-8",
    )


@router.get("/campaigns/{campaign_id}/calendar/export.csv")
def export_calendar_csv(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> Response:
    return Response(
        content=service.export_calendar_csv(campaign_id),
        media_type="text/csv; charset=utf-8",
    )
