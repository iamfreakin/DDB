from __future__ import annotations

import base64
import io
import json
import random
import socket
import urllib.error
import urllib.request

from PIL import Image, ImageDraw, ImageFilter

from backend.app.errors import AppError


OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_IMAGE_TIMEOUT_SECONDS = 180


def _parse_size(size: str) -> tuple[int, int]:
    width, height = size.split("x", maxsplit=1)
    return int(width), int(height)


class MockImageGenerationProvider:
    name = "mock"
    model = "local-gradient-v1"

    def generate(self, prompt: str, size: str) -> bytes:
        width, height = _parse_size(size)
        seed = sum((index + 1) * ord(char) for index, char in enumerate(prompt))
        rng = random.Random(seed)
        colors = [
            (rng.randrange(15, 65), rng.randrange(15, 65), rng.randrange(15, 65)),
            (rng.randrange(110, 220), rng.randrange(80, 200), rng.randrange(60, 190)),
            (rng.randrange(180, 245), rng.randrange(175, 240), rng.randrange(150, 230)),
        ]
        image = Image.new("RGB", (width, height), colors[0])
        draw = ImageDraw.Draw(image, "RGBA")
        for y in range(height):
            ratio = y / max(height - 1, 1)
            start, end = colors[0], colors[1]
            color = tuple(int(start[i] * (1 - ratio) + end[i] * ratio) for i in range(3))
            draw.line((0, y, width, y), fill=(*color, 255))
        for _ in range(7):
            radius = rng.randrange(max(80, width // 10), max(120, width // 2))
            x = rng.randrange(-radius, width)
            y = rng.randrange(-radius, height)
            color = colors[rng.randrange(len(colors))]
            draw.ellipse((x, y, x + radius, y + radius), fill=(*color, rng.randrange(35, 95)))
        image = image.filter(ImageFilter.GaussianBlur(max(12, width // 40)))
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()


class OpenAIImageGenerationProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-image-2") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, size: str) -> bytes:
        request = urllib.request.Request(
            OPENAI_IMAGES_URL,
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "size": size,
                    "quality": "low",
                    "output_format": "png",
                    "n": 1,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=OPENAI_IMAGE_TIMEOUT_SECONDS
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            self._raise_http_error(exc)
        except (TimeoutError, socket.timeout) as exc:
            raise AppError(
                code="IMAGE_TIMEOUT",
                message="이미지 생성 시간이 길어 요청이 중단되었습니다. 다시 시도해 주세요.",
                status_code=504,
                retryable=True,
            ) from exc
        except (urllib.error.URLError, ConnectionError) as exc:
            raise AppError(
                code="IMAGE_PROVIDER_UNAVAILABLE",
                message="이미지 생성 API에 연결할 수 없습니다.",
                status_code=503,
                retryable=True,
            ) from exc

        data = payload.get("data")
        encoded = data[0].get("b64_json") if isinstance(data, list) and data else None
        if not isinstance(encoded, str):
            raise AppError(
                code="IMAGE_OUTPUT_INVALID",
                message="이미지 생성 결과를 해석하지 못했습니다.",
                status_code=502,
                retryable=True,
            )
        try:
            return base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise AppError(
                code="IMAGE_OUTPUT_INVALID",
                message="이미지 생성 결과가 올바른 형식이 아닙니다.",
                status_code=502,
                retryable=True,
            ) from exc

    def _raise_http_error(self, exc: urllib.error.HTTPError) -> None:
        status = exc.code
        if status == 401:
            code, message, retryable = (
                "IMAGE_AUTH_FAILED",
                "OpenAI API 키를 확인해 주세요.",
                False,
            )
        elif status == 429:
            code, message, retryable = (
                "IMAGE_RATE_LIMITED",
                "OpenAI 이미지 사용량 제한에 도달했습니다.",
                True,
            )
        elif status in {502, 503}:
            code, message, retryable = (
                "IMAGE_PROVIDER_UNAVAILABLE",
                "OpenAI 이미지 API가 일시적으로 불안정합니다.",
                True,
            )
        elif status == 400:
            code, message, retryable = (
                "IMAGE_SAFETY_BLOCKED",
                "이미지 요청이 정책 또는 입력 조건에 의해 거절되었습니다.",
                False,
            )
        else:
            code, message, retryable = (
                "IMAGE_OUTPUT_INVALID",
                "OpenAI 이미지 API 요청이 실패했습니다.",
                False,
            )
        raise AppError(
            code=code,
            message=message,
            status_code=status,
            retryable=retryable,
        ) from exc
