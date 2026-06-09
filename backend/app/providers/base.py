from __future__ import annotations

from typing import Any, Protocol


class TextGenerationProvider(Protocol):
    name: str

    def generate_brand_analysis(
        self, brand: dict[str, Any], profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a structured brand analysis."""

