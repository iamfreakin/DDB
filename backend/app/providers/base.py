from __future__ import annotations

from typing import Any, Protocol


class ImageGenerationProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, size: str) -> bytes:
        """Generate one raster background image and return encoded bytes."""


class TextGenerationProvider(Protocol):
    name: str
    model: str

    def generate_brand_analysis(
        self, brand: dict[str, Any], profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a structured brand analysis."""

    def generate_campaign_strategy(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a structured four-week campaign strategy."""

    def generate_content_batch(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        strategy: dict[str, Any],
        options: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate content slots with initial variants."""

    def generate_content_variant(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        existing_variants: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate one additional content variant."""

    def generate_poster_brief(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        selected_variant: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate an image and poster brief."""
