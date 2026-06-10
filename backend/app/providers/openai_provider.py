from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from backend.app.errors import AppError
from backend.app.providers.mock import MockTextGenerationProvider


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_REQUEST_TIMEOUT_SECONDS = 180


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter for bring-your-own-key usage.

    The API key is kept only on this in-memory provider instance for the request
    lifetime. It is never written to the database or logs by application code.
    """

    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-5-mini") -> None:
        self.api_key = api_key
        self.model = model
        self._fallback = MockTextGenerationProvider()

    def generate_brand_analysis(
        self, brand: dict[str, Any], profile: dict[str, Any]
    ) -> dict[str, Any]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand_summary": {"type": "string"},
                "target_segments": {"type": "array", "items": {"type": "string"}},
                "customer_needs": {"type": "array", "items": {"type": "string"}},
                "value_proposition": {"type": "string"},
                "differentiators": {"type": "array", "items": {"type": "string"}},
                "brand_voice": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                },
                "recommended_keywords": {"type": "array", "items": {"type": "string"}},
                "avoid_expressions": {"type": "array", "items": {"type": "string"}},
                "missing_information": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "brand_summary",
                "target_segments",
                "customer_needs",
                "value_proposition",
                "differentiators",
                "brand_voice",
                "recommended_keywords",
                "avoid_expressions",
                "missing_information",
            ],
        }
        return self._json_response(
            "brand_analysis",
            schema,
            {
                "task": "브랜드 분석을 한국어로 생성하세요.",
                "brand": brand,
                "profile": profile,
            },
        )

    def generate_campaign_strategy(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
    ) -> dict[str, Any]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "core_message": {"type": "string"},
                "weekly_goals": {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "week": {"type": "integer"},
                            "goal": {"type": "string"},
                        },
                        "required": ["week", "goal"],
                    },
                },
                "content_pillars": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "post_topics": {
                    "type": "array",
                    "minItems": 8,
                    "maxItems": 8,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "sequence": {"type": "integer"},
                            "week": {"type": "integer"},
                            "topic": {"type": "string"},
                            "content_type": {
                                "type": "string",
                                "enum": [
                                    "product",
                                    "informational",
                                    "relationship",
                                    "promotion",
                                ],
                            },
                        },
                        "required": ["sequence", "week", "topic", "content_type"],
                    },
                },
                "risk_notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "core_message",
                "weekly_goals",
                "content_pillars",
                "post_topics",
                "risk_notes",
            ],
        }
        return self._json_response(
            "campaign_strategy",
            schema,
            {
                "task": "소상공인 Instagram 4주 캠페인 전략을 생성하세요.",
                "brand": brand,
                "analysis": analysis,
                "campaign": campaign,
                "rules": [
                    "post_topics는 정확히 8개입니다.",
                    "입력에 없는 가격, 할인, 기간을 만들지 마세요.",
                ],
            },
        )

    def generate_content_batch(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        strategy: dict[str, Any],
        options: dict[str, Any],
    ) -> list[dict[str, Any]]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "contents": {
                    "type": "array",
                    "minItems": 8,
                    "maxItems": 8,
                    "items": self._content_item_schema(),
                }
            },
            "required": ["contents"],
        }
        data = self._json_response(
            "content_batch",
            schema,
            {
                "task": "전략의 post_topics 8개에 맞춰 Instagram 게시물 초안을 생성하세요.",
                "brand": brand,
                "analysis": analysis,
                "campaign": campaign,
                "strategy": strategy,
                "options": options,
            },
        )
        return data["contents"]

    def generate_content_variant(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        existing_variants: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        schema = self._variant_schema()
        return self._json_response(
            "content_variant",
            schema,
            {
                "task": "기존 변형과 접근 방식이 다른 Instagram 문구 변형을 하나 생성하세요.",
                "brand": brand,
                "analysis": analysis,
                "campaign": campaign,
                "content": content,
                "existing_variants": existing_variants,
                "options": options,
            },
        )

    def generate_poster_brief(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        selected_variant: dict[str, Any] | None,
    ) -> dict[str, Any]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "supporting_text": {"type": ["string", "null"]},
                "visual_mood": {"type": "string"},
                "colors": {"type": "array", "items": {"type": "string"}},
                "layout_description": {"type": "string"},
                "image_prompt": {"type": "string"},
                "negative_prompt": {"type": ["string", "null"]},
                "aspect_ratio": {"type": "string"},
            },
            "required": [
                "headline",
                "supporting_text",
                "visual_mood",
                "colors",
                "layout_description",
                "image_prompt",
                "negative_prompt",
                "aspect_ratio",
            ],
        }
        return self._json_response(
            "poster_brief",
            schema,
            {
                "task": "이미지 생성 API에 넘길 포스터 브리프를 생성하세요.",
                "brand": brand,
                "analysis": analysis,
                "campaign": campaign,
                "content": content,
                "selected_variant": selected_variant,
                "rules": ["이미지 자체에 긴 한글 텍스트를 넣지 않도록 안내하세요."],
            },
        )

    def _json_response(
        self, schema_name: str, schema: dict[str, Any], prompt_payload: dict[str, Any]
    ) -> dict[str, Any]:
        body = {
            "model": self.model,
            "instructions": (
                "당신은 소상공인을 돕는 한국어 마케팅 코파일럿입니다. "
                "반드시 제공된 JSON Schema에 맞는 JSON만 반환하세요. "
                "사용자가 제공하지 않은 사실은 만들지 마세요."
            ),
            "input": json.dumps(prompt_payload, ensure_ascii=False),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            OPENAI_RESPONSES_URL,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=OPENAI_REQUEST_TIMEOUT_SECONDS
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            self._raise_http_error(exc)
        except (TimeoutError, socket.timeout) as exc:
            raise AppError(
                code="AI_TIMEOUT",
                message="OpenAI 응답 시간이 길어 생성 요청이 중단되었습니다. 다시 시도해 주세요.",
                status_code=504,
                retryable=True,
            ) from exc
        except (urllib.error.URLError, ConnectionError) as exc:
            raise AppError(
                code="AI_PROVIDER_UNAVAILABLE",
                message="OpenAI API에 연결할 수 없습니다.",
                status_code=503,
                retryable=True,
            ) from exc

        text = self._extract_text(payload)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AppError(
                code="AI_OUTPUT_INVALID",
                message="OpenAI 응답을 구조화된 JSON으로 해석하지 못했습니다.",
                status_code=502,
                retryable=True,
            ) from exc

    def _extract_text(self, payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str):
                        return text
        raise AppError(
            code="AI_OUTPUT_INVALID",
            message="OpenAI 응답에서 텍스트 출력을 찾지 못했습니다.",
            status_code=502,
            retryable=True,
        )

    def _raise_http_error(self, exc: urllib.error.HTTPError) -> None:
        status = exc.code
        if status == 401:
            code, message, retryable = "AI_SAFETY_BLOCKED", "OpenAI API 키를 확인해 주세요.", False
        elif status == 429:
            code, message, retryable = "AI_RATE_LIMITED", "OpenAI 사용량 제한에 도달했습니다.", True
        elif status in {502, 503}:
            code, message, retryable = "AI_PROVIDER_UNAVAILABLE", "OpenAI API가 일시적으로 불안정합니다.", True
        else:
            code, message, retryable = "AI_OUTPUT_INVALID", "OpenAI API 요청이 실패했습니다.", False
        raise AppError(code=code, message=message, status_code=status, retryable=retryable) from exc

    def _variant_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "tone": {"type": "string"},
                "opening_line": {"type": "string"},
                "body": {"type": "string"},
                "cta": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
                "image_concept": {"type": "string"},
                "quality_warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "tone",
                "opening_line",
                "body",
                "cta",
                "hashtags",
                "image_concept",
                "quality_warnings",
            ],
        }

    def _content_item_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "sequence": {"type": "integer"},
                "week_number": {"type": "integer"},
                "content_type": {
                    "type": "string",
                    "enum": ["product", "informational", "relationship", "promotion"],
                },
                "topic": {"type": "string"},
                "core_message": {"type": "string"},
                "variants": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": self._variant_schema(),
                },
            },
            "required": [
                "sequence",
                "week_number",
                "content_type",
                "topic",
                "core_message",
                "variants",
            ],
        }
