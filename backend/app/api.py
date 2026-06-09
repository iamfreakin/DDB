from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import (
    get_analysis_service,
    get_brand_service,
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
    HealthResponse,
)
from backend.app.services import AnalysisService, BrandService


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
