from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.app.errors import AppError
from backend.app.poster_composer import PosterComposer, provider_size
from backend.app.providers.base import ImageGenerationProvider, TextGenerationProvider
from backend.app.repositories import (
    AnalysisRepository,
    BrandRepository,
    CalendarRepository,
    CampaignRepository,
    ComparisonRepository,
    ContentRepository,
    GeneratedImageRepository,
    GenerationRunRepository,
    PosterBriefRepository,
)
from backend.app.schemas import (
    BrandAnalysisUpdate,
    BrandCreate,
    BrandProfileInput,
    CalendarCreateRequest,
    CalendarItemUpdate,
    CampaignCreate,
    CampaignUpdate,
    ComparisonSetCreate,
    ContentGenerateRequest,
    ContentVariantEditRequest,
    ContentVariantGenerateRequest,
    PosterBriefUpdate,
)


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

        run = self.analyses.create_generation_run(
            profile["id"], self.provider.name, self.provider.model
        )
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


class CampaignService:
    def __init__(
        self,
        brands: BrandRepository,
        analyses: AnalysisRepository,
        campaigns: CampaignRepository,
        contents: ContentRepository,
        posters: PosterBriefRepository,
        calendar: CalendarRepository,
        comparisons: ComparisonRepository,
        runs: GenerationRunRepository,
        images: GeneratedImageRepository,
        provider: TextGenerationProvider,
        image_provider: ImageGenerationProvider,
        generated_image_path: Path,
    ) -> None:
        self.brands = brands
        self.analyses = analyses
        self.campaigns = campaigns
        self.contents = contents
        self.posters = posters
        self.calendar = calendar
        self.comparisons = comparisons
        self.runs = runs
        self.images = images
        self.provider = provider
        self.image_provider = image_provider
        self.generated_image_path = generated_image_path
        self.poster_composer = PosterComposer()

    def create_campaign(self, request: CampaignCreate) -> dict[str, Any]:
        return self.campaigns.create(request)

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        return self.campaigns.get(campaign_id)

    def list_campaigns(
        self, brand_id: str | None, status: str | None, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        return self.campaigns.list(brand_id, status, limit, offset)

    def update_campaign(
        self, campaign_id: str, request: CampaignUpdate
    ) -> dict[str, Any]:
        return self.campaigns.update(
            campaign_id, request.model_dump(exclude_unset=True, mode="json")
        )

    def delete_campaign(self, campaign_id: str) -> None:
        self.campaigns.delete(campaign_id)

    def generate_strategy(self, campaign_id: str, regenerate: bool) -> dict[str, Any]:
        existing = self.campaigns.list_strategies(campaign_id)
        if existing and not regenerate:
            return existing[0]
        campaign = self.campaigns.get(campaign_id)
        brand = self.brands.get(campaign["brand_id"])
        analysis = self.analyses.get(campaign["brand_analysis_id"])
        if analysis["status"] != "approved":
            raise AppError(
                code="ANALYSIS_STALE",
                message="최신 승인 브랜드 분석으로 캠페인을 다시 만들어 주세요.",
                status_code=409,
            )
        run = self.runs.create(
            "campaign_strategy",
            self.provider.name,
            self.provider.model,
            "campaign_strategy",
            {"campaign_id": campaign_id},
        )
        try:
            generated = self.provider.generate_campaign_strategy(brand, analysis, campaign)
            strategy = self.campaigns.create_strategy(campaign_id, run["id"], generated)
            self.runs.succeeded(run["id"])
            return strategy
        except Exception as exc:
            self._fail_run(run["id"], exc)

    def list_strategies(self, campaign_id: str) -> list[dict[str, Any]]:
        return self.campaigns.list_strategies(campaign_id)

    def generate_contents(
        self, campaign_id: str, request: ContentGenerateRequest
    ) -> list[dict[str, Any]]:
        campaign = self.campaigns.get(campaign_id)
        strategy = (
            self.campaigns.get_strategy(request.strategy_id)
            if request.strategy_id
            else self.campaigns.latest_strategy(campaign_id)
        )
        brand = self.brands.get(campaign["brand_id"])
        analysis = self.analyses.get(campaign["brand_analysis_id"])
        run = self.runs.create(
            "content_batch",
            self.provider.name,
            self.provider.model,
            "content_batch",
            {"campaign_id": campaign_id, "strategy_id": strategy["id"]},
            request.model_dump(mode="json"),
        )
        try:
            generated = self.provider.generate_content_batch(
                brand,
                analysis,
                campaign,
                strategy,
                request.model_dump(mode="json"),
            )
            contents = self.contents.create_batch(
                campaign_id, strategy["id"], run["id"], generated
            )
            self.runs.succeeded(run["id"])
            return contents
        except Exception as exc:
            self._fail_run(run["id"], exc)

    def search_contents(
        self,
        brand_id: str | None,
        campaign_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        return self.contents.search(brand_id, campaign_id, status, limit, offset)

    def list_contents(self, campaign_id: str, status: str | None, week_number: int | None) -> list[dict[str, Any]]:
        self.campaigns.get(campaign_id)
        return self.contents.list_for_campaign(campaign_id, status, week_number)

    def get_content(self, content_id: str) -> dict[str, Any]:
        return self.contents.get(content_id)

    def update_content_status(self, content_id: str, status: str) -> dict[str, Any]:
        return self.contents.update_status(content_id, status)

    def generate_variant(
        self, content_id: str, request: ContentVariantGenerateRequest
    ) -> dict[str, Any]:
        content = self.contents.get(content_id)
        campaign = self.campaigns.get(content["campaign_id"])
        brand = self.brands.get(campaign["brand_id"])
        analysis = self.analyses.get(campaign["brand_analysis_id"])
        run = self.runs.create(
            "content_variant",
            self.provider.name,
            self.provider.model,
            "content_variant",
            {"content_id": content_id},
            request.model_dump(mode="json"),
        )
        try:
            generated = self.provider.generate_content_variant(
                brand,
                analysis,
                campaign,
                content,
                content["variants"],
                request.model_dump(mode="json"),
            )
            variant = self.contents.create_variant(content_id, generated, run["id"])
            self.runs.succeeded(run["id"])
            return variant
        except Exception as exc:
            self._fail_run(run["id"], exc)

    def create_user_edit(
        self, variant_id: str, request: ContentVariantEditRequest
    ) -> dict[str, Any]:
        source = self.contents.get_variant(variant_id)
        return self.contents.create_user_edit(
            variant_id,
            {
                **request.model_dump(mode="json"),
                "tone": "사용자 수정",
                "quality_warnings": source["quality_warnings"],
            },
        )

    def select_variant(self, content_id: str, variant_id: str) -> dict[str, Any]:
        return self.contents.select_variant(content_id, variant_id)

    def generate_poster_brief(self, content_id: str) -> dict[str, Any]:
        content = self.contents.get(content_id)
        campaign = self.campaigns.get(content["campaign_id"])
        brand = self.brands.get(campaign["brand_id"])
        analysis = self.analyses.get(campaign["brand_analysis_id"])
        selected = None
        if content["selected_variant_id"]:
            selected = self.contents.get_variant(content["selected_variant_id"])
        elif content["variants"]:
            selected = content["variants"][0]
        run = self.runs.create(
            "poster_brief",
            self.provider.name,
            self.provider.model,
            "poster_brief",
            {"content_id": content_id},
        )
        try:
            generated = self.provider.generate_poster_brief(
                brand, analysis, campaign, content, selected
            )
            brief = self.posters.upsert(content_id, generated, run["id"])
            self.runs.succeeded(run["id"])
            return brief
        except Exception as exc:
            self._fail_run(run["id"], exc)

    def get_poster_brief(self, content_id: str) -> dict[str, Any]:
        return self.posters.get_by_content(content_id)

    def update_poster_brief(
        self, content_id: str, request: PosterBriefUpdate
    ) -> dict[str, Any]:
        return self.posters.update(
            content_id, request.model_dump(exclude_unset=True, mode="json")
        )

    def generate_image(self, brief_id: str) -> dict[str, Any]:
        brief = self.posters.get(brief_id)
        prompt = self._image_prompt(brief)
        size = provider_size(
            brief["aspect_ratio"],
            flexible=self.image_provider.model.startswith("gpt-image-2"),
        )
        run = self.runs.create(
            "image_generation",
            self.image_provider.name,
            self.image_provider.model,
            "poster_background",
            {"poster_brief_id": brief_id},
            {"aspect_ratio": brief["aspect_ratio"], "size": size},
        )
        background_path: Path | None = None
        composed_path: Path | None = None
        try:
            background = self.image_provider.generate(prompt, size)
            composed, width, height = self.poster_composer.compose(background, brief)
            self.generated_image_path.mkdir(parents=True, exist_ok=True)
            stem = run["id"]
            background_path = self.generated_image_path / f"{stem}-background.png"
            composed_path = self.generated_image_path / f"{stem}-poster.png"
            self._atomic_write(background_path, background)
            self._atomic_write(composed_path, composed)
            image = self.images.create(
                poster_brief_id=brief_id,
                provider=self.image_provider.name,
                model=self.image_provider.model,
                prompt=prompt,
                aspect_ratio=brief["aspect_ratio"],
                width=width,
                height=height,
                background_path=background_path.name,
                composed_path=composed_path.name,
                generation_run_id=run["id"],
            )
            self.runs.succeeded(run["id"])
            return self._public_image(image)
        except Exception as exc:
            for path in (background_path, composed_path):
                if path:
                    path.unlink(missing_ok=True)
            self._fail_run(run["id"], exc)

    def list_images(self, brief_id: str) -> list[dict[str, Any]]:
        self.posters.get(brief_id)
        return [
            self._public_image(image)
            for image in self.images.list_for_brief(brief_id)
        ]

    def approve_image(self, image_id: str) -> dict[str, Any]:
        return self._public_image(self.images.approve(image_id))

    def get_image_file(self, image_id: str, variant: str) -> tuple[Path, str]:
        image = self.images.get(image_id)
        field = "background_path" if variant == "background" else "composed_path"
        path = (self.generated_image_path / image[field]).resolve()
        root = self.generated_image_path.resolve()
        if root not in path.parents or not path.is_file():
            raise AppError(
                code="IMAGE_FILE_NOT_FOUND",
                message="생성 이미지 파일을 찾을 수 없습니다.",
                status_code=404,
            )
        return path, f"poster-v{image['version']}.png"

    def create_calendar(
        self, campaign_id: str, request: CalendarCreateRequest
    ) -> list[dict[str, Any]]:
        campaign = self.campaigns.get(campaign_id)
        return self.calendar.create_for_campaign(campaign, request.preferred_weekdays)

    def list_calendar(self, campaign_id: str) -> list[dict[str, Any]]:
        self.campaigns.get(campaign_id)
        return self.calendar.list_for_campaign(campaign_id)

    def refresh_calendar(self, campaign_id: str) -> list[dict[str, Any]]:
        self.campaigns.get(campaign_id)
        return self.calendar.refresh_for_campaign(campaign_id)

    def update_calendar_item(
        self, item_id: str, request: CalendarItemUpdate
    ) -> dict[str, Any]:
        item = self.calendar.get(item_id)
        campaign = self.campaigns.get(item["campaign_id"])
        return self.calendar.update(
            item_id, campaign, request.model_dump(exclude_unset=True, mode="json")
        )

    def create_comparison(self, request: ComparisonSetCreate) -> dict[str, Any]:
        return self.comparisons.create(request.name, request.variant_ids)

    def get_comparison(self, set_id: str) -> dict[str, Any]:
        return self.comparisons.get(set_id)

    def delete_comparison(self, set_id: str) -> None:
        self.comparisons.delete(set_id)

    def export_analysis_markdown(self, analysis_id: str) -> str:
        analysis = self.analyses.get(analysis_id)
        return "\n".join(
            [
                "# 브랜드 분석 보고서",
                "",
                f"## 브랜드 정의\n{analysis['brand_summary']}",
                f"## 핵심 고객\n{_bullets(analysis['target_segments'])}",
                f"## 고객 니즈\n{_bullets(analysis['customer_needs'])}",
                f"## 가치 제안\n{analysis['value_proposition']}",
                f"## 차별점\n{_bullets(analysis['differentiators'])}",
                f"## 브랜드 보이스\n{_bullets(analysis['brand_voice'])}",
                f"## 추천 키워드\n{_bullets(analysis['recommended_keywords'])}",
                f"## 피해야 할 표현\n{_bullets(analysis['avoid_expressions'])}",
                f"## 정보 부족\n{_bullets(analysis['missing_information'])}",
            ]
        )

    def export_calendar_csv(self, campaign_id: str) -> str:
        rows = self.calendar.list_for_campaign(campaign_id)
        lines = ["날짜,채널,유형,주제,선택 문구,핵심 메시지,상태,승인 포스터"]
        for row in rows:
            content = row["content"]
            selected_variant = next(
                (
                    variant
                    for variant in content["variants"]
                    if variant["id"] == content["selected_variant_id"]
                ),
                content["variants"][0] if content["variants"] else None,
            )
            lines.append(
                ",".join(
                    _csv_cell(value)
                    for value in [
                        row["scheduled_date"],
                        "instagram_feed",
                        content["content_type"],
                        content["topic"],
                        selected_variant["opening_line"] if selected_variant else "",
                        content["core_message"],
                        row["status"],
                        "있음" if row.get("approved_image") else "없음",
                    ]
                )
            )
        return "\ufeff" + "\n".join(lines)

    def _fail_run(self, run_id: str, exc: Exception):
        if isinstance(exc, AppError):
            self.runs.failed(run_id, exc.code, exc.message)
            raise exc
        self.runs.failed(run_id, "AI_PROVIDER_UNAVAILABLE", type(exc).__name__)
        raise AppError(
            code="AI_PROVIDER_UNAVAILABLE",
            message="AI 서비스를 일시적으로 사용할 수 없습니다.",
            status_code=503,
            retryable=True,
        ) from exc

    def _image_prompt(self, brief: dict[str, Any]) -> str:
        return (
            f"{brief['image_prompt']}\n"
            f"분위기: {brief['visual_mood']}\n"
            f"권장 색상: {', '.join(brief['colors'])}\n"
            f"레이아웃 참고: {brief['layout_description']}\n"
            f"제외 요소: {brief.get('negative_prompt') or '없음'}\n"
            "광고 포스터의 배경 비주얼만 생성한다. 글자, 문장, 로고, 워터마크, "
            "간판 텍스트는 절대 포함하지 않는다. 제목이 올라갈 하단 영역은 시각적으로 "
            "단순하고 충분한 여백을 둔다."
        )

    def _atomic_write(self, path: Path, content: bytes) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, path)

    def _public_image(self, image: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in image.items()
            if key not in {"background_path", "composed_path"}
        }


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- 없음"


def _csv_cell(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'
