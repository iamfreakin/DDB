from __future__ import annotations

from typing import Any

from backend.app.errors import AppError
from backend.app.providers.base import TextGenerationProvider
from backend.app.repositories import AnalysisRepository, BrandRepository
from backend.app.schemas import BrandAnalysisUpdate, BrandCreate, BrandProfileInput


class BrandService:
    def __init__(self, brands: BrandRepository) -> None:
        self.brands = brands

    def create(self, request: BrandCreate) -> dict[str, Any]:
        return self.brands.create(request)

    def get(self, brand_id: str) -> dict[str, Any]:
        return self.brands.get(brand_id)

    def list(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        return self.brands.list(limit, offset)

    def create_profile_version(
        self, brand_id: str, profile: BrandProfileInput
    ) -> dict[str, Any]:
        return self.brands.create_profile_version(brand_id, profile)


class AnalysisService:
    def __init__(
        self,
        brands: BrandRepository,
        analyses: AnalysisRepository,
        provider: TextGenerationProvider,
    ) -> None:
        self.brands = brands
        self.analyses = analyses
        self.provider = provider

    def generate(self, brand_id: str, regenerate: bool) -> dict[str, Any]:
        brand = self.brands.get(brand_id)
        profile = brand["active_profile"]
        existing = self.analyses.list_for_brand(brand_id)
        current_drafts = [
            analysis
            for analysis in existing
            if analysis["profile_version_id"] == profile["id"]
            and analysis["status"] == "draft"
        ]
        if current_drafts and not regenerate:
            return current_drafts[0]

        run = self.analyses.create_generation_run(profile["id"], self.provider.name)
        try:
            generated = self.provider.generate_brand_analysis(brand, profile)
            analysis = self.analyses.create(profile["id"], run["id"], generated)
            self.analyses.mark_generation_succeeded(run["id"])
            return analysis
        except AppError:
            self.analyses.mark_generation_failed(
                run["id"], "AI_OUTPUT_INVALID", "브랜드 분석 생성에 실패했습니다."
            )
            raise
        except Exception as exc:
            self.analyses.mark_generation_failed(
                run["id"], "AI_PROVIDER_UNAVAILABLE", type(exc).__name__
            )
            raise AppError(
                code="AI_PROVIDER_UNAVAILABLE",
                message="AI 서비스를 일시적으로 사용할 수 없습니다.",
                status_code=503,
                retryable=True,
            ) from exc

    def get(self, analysis_id: str) -> dict[str, Any]:
        return self.analyses.get(analysis_id)

    def list_for_brand(self, brand_id: str) -> list[dict[str, Any]]:
        self.brands.get(brand_id)
        return self.analyses.list_for_brand(brand_id)

    def update(
        self, analysis_id: str, request: BrandAnalysisUpdate
    ) -> dict[str, Any]:
        return self.analyses.update(
            analysis_id, request.model_dump(exclude_unset=True, mode="json")
        )

    def approve(self, analysis_id: str) -> dict[str, Any]:
        return self.analyses.approve(analysis_id)

