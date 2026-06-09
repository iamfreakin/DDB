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

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.prefix = f"{self.base_url}/api/v1"

    def _request(self, method: str, path: str, payload: Any | None = None) -> Any:
        url = f"{self.prefix}{path}"
        try:
            response = requests.request(
                method,
                url,
                json=payload,
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
            "POST", f"/brands/{brand_id}/analyses", {"regenerate": regenerate}
        )

    def list_analyses(self, brand_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/brands/{brand_id}/analyses")

    def update_analysis(
        self, analysis_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request("PATCH", f"/analyses/{analysis_id}", payload)

    def approve_analysis(self, analysis_id: str) -> dict[str, Any]:
        return self._request("POST", f"/analyses/{analysis_id}/approve")
