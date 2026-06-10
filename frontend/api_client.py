from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests


DEFAULT_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30


@dataclass
class ApiError(Exception):
    """백엔드 오류 계약을 사용자에게 보여줄 형태로 옮긴 예외."""

    code: str
    message: str
    status_code: int
    retryable: bool = False
    field_errors: list[dict[str, str]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message


class BackendClient:
    """FastAPI 백엔드를 호출하는 얇은 클라이언트.

    UI 로직과 분리하기 위해 Streamlit 객체를 일절 다루지 않는다.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        openai_api_key: str | None = None,
        openai_model: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.prefix = f"{self.base_url}/api/v1"
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model or "gpt-5-mini"
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        path: str,
        payload: Any | None = None,
        *,
        use_ai: bool = False,
    ) -> Any:
        url = f"{self.prefix}{path}"
        headers: dict[str, str] = {}
        if use_ai and self.openai_api_key:
            headers["X-OpenAI-API-Key"] = self.openai_api_key
            headers["X-OpenAI-Model"] = self.openai_model
        try:
            response = self.session.request(
                method,
                url,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise ApiError(
                code="BACKEND_UNREACHABLE",
                message="백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.",
                status_code=0,
                retryable=True,
            ) from exc

        if response.status_code >= 400:
            raise self._to_api_error(response)

        if response.content:
            return response.json()
        return None

    @staticmethod
    def _to_api_error(response: requests.Response) -> ApiError:
        try:
            body = response.json().get("error", {})
        except ValueError:
            body = {}
        return ApiError(
            code=body.get("code", "UNKNOWN_ERROR"),
            message=body.get("message", "알 수 없는 오류가 발생했습니다."),
            status_code=response.status_code,
            retryable=bool(body.get("retryable", False)),
            field_errors=body.get("field_errors", []),
        )

    # --- 상태 ---
    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    # --- 브랜드 ---
    def create_brand(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/brands", payload)

    def list_brands(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return self._request("GET", f"/brands?limit={limit}&offset={offset}")

    def get_brand(self, brand_id: str) -> dict[str, Any]:
        return self._request("GET", f"/brands/{brand_id}")

    def create_profile_version(
        self, brand_id: str, profile: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request("PUT", f"/brands/{brand_id}/profile", profile)

    # --- 분석 ---
    def generate_analysis(
        self, brand_id: str, regenerate: bool = False
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/brands/{brand_id}/analyses",
            {"regenerate": regenerate},
            use_ai=True,
        )

    def list_analyses(self, brand_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/brands/{brand_id}/analyses")

    def update_analysis(
        self, analysis_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request("PATCH", f"/analyses/{analysis_id}", payload)

    def approve_analysis(self, analysis_id: str) -> dict[str, Any]:
        return self._request("POST", f"/analyses/{analysis_id}/approve")

    # --- 캠페인 ---
    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/campaigns", payload)

    def list_campaigns(self, brand_id: str | None = None) -> dict[str, Any]:
        query = f"?brand_id={brand_id}" if brand_id else ""
        return self._request("GET", f"/campaigns{query}")

    def generate_strategy(
        self, campaign_id: str, regenerate: bool = False
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/campaigns/{campaign_id}/strategies",
            {"regenerate": regenerate},
            use_ai=True,
        )

    def list_strategies(self, campaign_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/campaigns/{campaign_id}/strategies")

    def generate_contents(
        self,
        campaign_id: str,
        strategy_id: str,
        variants_per_content: int = 1,
        hashtag_count: int = 7,
    ) -> list[dict[str, Any]]:
        return self._request(
            "POST",
            f"/campaigns/{campaign_id}/contents:generate",
            {
                "strategy_id": strategy_id,
                "variants_per_content": variants_per_content,
                "hashtag_count": hashtag_count,
            },
            use_ai=True,
        )

    def list_contents(self, campaign_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/campaigns/{campaign_id}/contents")

    def get_content(self, content_id: str) -> dict[str, Any]:
        return self._request("GET", f"/contents/{content_id}")

    def generate_variant(self, content_id: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/contents/{content_id}/variants", {}, use_ai=True
        )

    def save_variant_edit(self, variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/variants/{variant_id}/edits", payload)

    def select_variant(self, content_id: str, variant_id: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/contents/{content_id}/selected-variant", {"variant_id": variant_id}
        )

    def generate_poster_brief(self, content_id: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/contents/{content_id}/poster-brief", {}, use_ai=True
        )

    def get_poster_brief(self, content_id: str) -> dict[str, Any]:
        return self._request("GET", f"/contents/{content_id}/poster-brief")

    def create_calendar(
        self, campaign_id: str, preferred_weekdays: list[int] | None = None
    ) -> list[dict[str, Any]]:
        return self._request(
            "POST",
            f"/campaigns/{campaign_id}/calendar",
            {"preferred_weekdays": preferred_weekdays or [2, 5]},
        )

    def list_calendar(self, campaign_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/campaigns/{campaign_id}/calendar")

    def create_comparison(self, name: str, variant_ids: list[str]) -> dict[str, Any]:
        return self._request(
            "POST", "/comparison-sets", {"name": name, "variant_ids": variant_ids}
        )

    def export_analysis_markdown_url(self, analysis_id: str) -> str:
        return f"{self.prefix}/analyses/{analysis_id}/export.md"

    def export_calendar_csv_url(self, campaign_id: str) -> str:
        return f"{self.prefix}/campaigns/{campaign_id}/calendar/export.csv"
