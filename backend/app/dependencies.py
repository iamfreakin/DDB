from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header

from backend.app.config import Settings
from backend.app.db import Database
from backend.app.providers.mock import MockTextGenerationProvider
from backend.app.providers.image import (
    MockImageGenerationProvider,
    OpenAIImageGenerationProvider,
)
from backend.app.providers.openai_provider import OpenAIResponsesProvider
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
from backend.app.services import AnalysisService, BrandService, CampaignService


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_database() -> Database:
    database = Database(get_settings().database_path)
    database.initialize()
    return database


def get_brand_service() -> BrandService:
    return BrandService(BrandRepository(get_database()))


def get_text_provider(
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    if x_openai_api_key:
        return OpenAIResponsesProvider(
            api_key=x_openai_api_key,
            model=x_openai_model or "gpt-5-mini",
        )
    return MockTextGenerationProvider()


def get_image_provider(
    x_openai_api_key: str | None = Header(default=None),
    x_openai_image_model: str | None = Header(default=None),
):
    if x_openai_api_key:
        return OpenAIImageGenerationProvider(
            api_key=x_openai_api_key,
            model=x_openai_image_model or "gpt-image-2",
        )
    return MockImageGenerationProvider()


def get_analysis_service(provider=Depends(get_text_provider)) -> AnalysisService:
    database = get_database()
    return AnalysisService(
        BrandRepository(database),
        AnalysisRepository(database),
        provider,
    )


def get_campaign_service(
    provider=Depends(get_text_provider),
    image_provider=Depends(get_image_provider),
) -> CampaignService:
    database = get_database()
    contents = ContentRepository(database)
    return CampaignService(
        BrandRepository(database),
        AnalysisRepository(database),
        CampaignRepository(database),
        contents,
        PosterBriefRepository(database),
        CalendarRepository(database, contents),
        ComparisonRepository(database, contents),
        GenerationRunRepository(database),
        GeneratedImageRepository(database),
        provider,
        image_provider,
        get_settings().generated_image_path,
    )
