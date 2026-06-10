from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.errors import AppError
from backend.app.providers.image import OpenAIImageGenerationProvider
from backend.app.providers.openai_provider import OpenAIResponsesProvider


class OpenAIProviderTestCase(unittest.TestCase):
    @patch("backend.app.providers.openai_provider.urllib.request.urlopen")
    def test_timeout_uses_retryable_error_contract(self, urlopen) -> None:
        urlopen.side_effect = TimeoutError()
        provider = OpenAIResponsesProvider("test-key")

        with self.assertRaises(AppError) as context:
            provider.generate_brand_analysis(
                {"name": "테스트 가게"},
                {
                    "products": ["대표 상품"],
                    "target_customers": "테스트 고객을 위한 충분히 긴 설명",
                    "strengths": "테스트 가게의 충분히 긴 강점 설명",
                },
            )

        self.assertEqual(context.exception.code, "AI_TIMEOUT")
        self.assertEqual(context.exception.status_code, 504)
        self.assertTrue(context.exception.retryable)

    @patch("backend.app.providers.image.urllib.request.urlopen")
    def test_image_timeout_uses_retryable_error_contract(self, urlopen) -> None:
        urlopen.side_effect = TimeoutError()
        provider = OpenAIImageGenerationProvider("test-key")

        with self.assertRaises(AppError) as context:
            provider.generate("텍스트가 없는 따뜻한 카페 광고 배경", "1080x1344")

        self.assertEqual(context.exception.code, "IMAGE_TIMEOUT")
        self.assertEqual(context.exception.status_code, 504)
        self.assertTrue(context.exception.retryable)


if __name__ == "__main__":
    unittest.main()
