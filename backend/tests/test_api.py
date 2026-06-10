from __future__ import annotations

import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from backend.app.dependencies import get_database, get_settings
from backend.app.main import create_app


VALID_BRAND = {
    "name": "은혜 커피",
    "industry": "cafe",
    "profile": {
        "products": ["수제 크림라떼", "아메리카노"],
        "target_customers": "조용히 쉬거나 대화할 공간을 찾는 20~30대 지역 주민",
        "strengths": "매장에서 직접 만드는 크림과 따뜻한 동네 분위기",
        "desired_moods": ["warm", "friendly", "emotional"],
        "region": "서울 성북구",
        "price_range": "medium",
        "existing_copy": None,
        "avoid_expressions": ["무조건", "최고"],
        "campaign_facts": {"cream_latte_price": "6500원"},
    },
}


class APITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"
        get_settings.cache_clear()
        get_database.cache_clear()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.client.close()
        get_database.cache_clear()
        get_settings.cache_clear()
        os.environ.pop("DATABASE_URL", None)
        self.temp_dir.cleanup()

    def create_brand(self) -> dict:
        response = self.client.post("/api/v1/brands", json=VALID_BRAND)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_health(self) -> None:
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["database"], "ok")
        self.assertIn("X-Request-ID", response.headers)

    def test_database_initializes_vertical_slice_tables(self) -> None:
        database = get_database()
        with closing(sqlite3.connect(database.path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type = 'table'
                    """
                )
            }
        self.assertTrue(
            {
                "brands",
                "brand_profile_versions",
                "brand_analyses",
                "generation_runs",
                "generated_images",
            }.issubset(tables)
        )

    def test_openapi_contains_vertical_slice_routes(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        self.assertIn("/api/v1/brands", paths)
        self.assertIn("/api/v1/brands/{brand_id}/profile", paths)
        self.assertIn("/api/v1/brands/{brand_id}/analyses", paths)
        self.assertIn("/api/v1/analyses/{analysis_id}/approve", paths)

    def test_create_and_get_brand(self) -> None:
        brand = self.create_brand()
        self.assertEqual(brand["active_profile"]["version"], 1)

        response = self.client.get(f"/api/v1/brands/{brand['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], VALID_BRAND["name"])

    def test_validation_error_contract(self) -> None:
        invalid = {**VALID_BRAND, "profile": {**VALID_BRAND["profile"], "products": []}}
        response = self.client.post("/api/v1/brands", json=invalid)
        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertFalse(error["retryable"])
        self.assertTrue(error["field_errors"])

    def test_profile_version_and_stale_analysis(self) -> None:
        brand = self.create_brand()
        analysis_response = self.client.post(
            f"/api/v1/brands/{brand['id']}/analyses",
            json={"regenerate": False},
        )
        self.assertEqual(analysis_response.status_code, 201, analysis_response.text)
        analysis = analysis_response.json()

        updated_profile = {
            **VALID_BRAND["profile"],
            "strengths": "직접 만든 크림과 늦은 시간까지 머물 수 있는 편안한 공간",
        }
        profile_response = self.client.put(
            f"/api/v1/brands/{brand['id']}/profile",
            json=updated_profile,
        )
        self.assertEqual(profile_response.status_code, 201, profile_response.text)
        self.assertEqual(profile_response.json()["active_profile"]["version"], 2)

        stale = self.client.get(f"/api/v1/analyses/{analysis['id']}").json()
        self.assertEqual(stale["status"], "stale")

    def test_duplicate_profile_returns_conflict(self) -> None:
        brand = self.create_brand()
        response = self.client.put(
            f"/api/v1/brands/{brand['id']}/profile",
            json=VALID_BRAND["profile"],
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PROFILE_UNCHANGED")

    def test_analysis_generate_edit_and_approve(self) -> None:
        brand = self.create_brand()
        response = self.client.post(
            f"/api/v1/brands/{brand['id']}/analyses",
            json={"regenerate": False},
        )
        self.assertEqual(response.status_code, 201, response.text)
        analysis = response.json()
        self.assertEqual(analysis["status"], "draft")
        self.assertEqual(len(analysis["brand_voice"]), 3)

        edit_response = self.client.patch(
            f"/api/v1/analyses/{analysis['id']}",
            json={"brand_summary": "수제 크림과 편안한 시간을 전하는 동네 카페"},
        )
        self.assertEqual(edit_response.status_code, 200, edit_response.text)

        approve_response = self.client.post(
            f"/api/v1/analyses/{analysis['id']}/approve"
        )
        self.assertEqual(approve_response.status_code, 200, approve_response.text)
        self.assertEqual(approve_response.json()["status"], "approved")
        self.assertIsNotNone(approve_response.json()["approved_at"])

    def test_campaign_content_calendar_and_exports_flow(self) -> None:
        brand = self.create_brand()
        analysis = self.client.post(
            f"/api/v1/brands/{brand['id']}/analyses",
            json={"regenerate": False},
        ).json()
        approved = self.client.post(
            f"/api/v1/analyses/{analysis['id']}/approve"
        ).json()

        campaign_response = self.client.post(
            "/api/v1/campaigns",
            json={
                "brand_id": brand["id"],
                "brand_analysis_id": approved["id"],
                "name": "여름 크림라떼 4주 캠페인",
                "goal": "new_product",
                "start_date": "2026-07-01",
                "highlighted_products": ["수제 크림라떼"],
                "required_facts": {"price": "6500원"},
            },
        )
        self.assertEqual(campaign_response.status_code, 201, campaign_response.text)
        campaign = campaign_response.json()

        strategy_response = self.client.post(
            f"/api/v1/campaigns/{campaign['id']}/strategies",
            json={"regenerate": False},
        )
        self.assertEqual(strategy_response.status_code, 201, strategy_response.text)
        strategy = strategy_response.json()
        self.assertEqual(len(strategy["post_topics"]), 8)

        contents_response = self.client.post(
            f"/api/v1/campaigns/{campaign['id']}/contents:generate",
            json={
                "strategy_id": strategy["id"],
                "variants_per_content": 2,
                "hashtag_count": 5,
            },
        )
        self.assertEqual(contents_response.status_code, 201, contents_response.text)
        contents = contents_response.json()
        self.assertEqual(len(contents), 8)
        self.assertEqual(len(contents[0]["variants"]), 2)

        content = contents[0]
        extra_variant = self.client.post(
            f"/api/v1/contents/{content['id']}/variants",
            json={"hashtag_count": 5},
        )
        self.assertEqual(extra_variant.status_code, 201, extra_variant.text)

        fourth_variant = self.client.post(
            f"/api/v1/contents/{content['id']}/variants",
            json={"hashtag_count": 5},
        )
        self.assertEqual(fourth_variant.status_code, 409)
        self.assertEqual(fourth_variant.json()["error"]["code"], "VARIANT_LIMIT_REACHED")

        selected = self.client.post(
            f"/api/v1/contents/{content['id']}/selected-variant",
            json={"variant_id": content["variants"][0]["id"]},
        )
        self.assertEqual(selected.status_code, 200, selected.text)
        self.assertEqual(selected.json()["status"], "approved")

        brief_response = self.client.post(
            f"/api/v1/contents/{content['id']}/poster-brief"
        )
        self.assertEqual(brief_response.status_code, 201, brief_response.text)
        brief = brief_response.json()
        self.assertIn("image_prompt", brief)

        missing_confirmation = self.client.post(
            f"/api/v1/poster-briefs/{brief['id']}/images",
            json={"confirm_cost": False},
        )
        self.assertEqual(missing_confirmation.status_code, 422)

        image_response = self.client.post(
            f"/api/v1/poster-briefs/{brief['id']}/images",
            json={"confirm_cost": True},
        )
        self.assertEqual(image_response.status_code, 201, image_response.text)
        generated_image = image_response.json()
        self.assertEqual(generated_image["provider"], "mock")
        self.assertEqual(generated_image["status"], "draft")

        poster_file = self.client.get(
            f"/api/v1/generated-images/{generated_image['id']}/file"
        )
        self.assertEqual(poster_file.status_code, 200, poster_file.text)
        self.assertEqual(poster_file.headers["content-type"], "image/png")
        with Image.open(io.BytesIO(poster_file.content)) as poster:
            self.assertEqual(
                poster.size,
                (generated_image["width"], generated_image["height"]),
            )

        approved_image = self.client.post(
            f"/api/v1/generated-images/{generated_image['id']}/approve"
        )
        self.assertEqual(approved_image.status_code, 200, approved_image.text)
        self.assertEqual(approved_image.json()["status"], "approved")

        image_list = self.client.get(
            f"/api/v1/poster-briefs/{brief['id']}/images"
        )
        self.assertEqual(image_list.status_code, 200, image_list.text)
        self.assertEqual(len(image_list.json()), 1)

        calendar_response = self.client.post(
            f"/api/v1/campaigns/{campaign['id']}/calendar",
            json={"preferred_weekdays": [2, 5]},
        )
        self.assertEqual(calendar_response.status_code, 201, calendar_response.text)
        self.assertEqual(len(calendar_response.json()), 8)
        first_calendar_item = calendar_response.json()[0]
        self.assertIsNotNone(first_calendar_item["approved_image"])
        self.assertEqual(first_calendar_item["approved_image"]["id"], generated_image["id"])

        status_update = self.client.patch(
            f"/api/v1/contents/{content['id']}",
            params={"status": "published"},
        )
        self.assertEqual(status_update.status_code, 200, status_update.text)

        refreshed_calendar = self.client.post(
            f"/api/v1/campaigns/{campaign['id']}/calendar:refresh"
        )
        self.assertEqual(refreshed_calendar.status_code, 200, refreshed_calendar.text)
        refreshed_item = next(
            item
            for item in refreshed_calendar.json()
            if item["content_id"] == content["id"]
        )
        self.assertEqual(refreshed_item["status"], "published")
        self.assertEqual(refreshed_item["content"]["status"], "published")

        comparison_response = self.client.post(
            "/api/v1/comparison-sets",
            json={
                "name": "첫 게시물 비교",
                "variant_ids": [
                    content["variants"][0]["id"],
                    content["variants"][1]["id"],
                ],
            },
        )
        self.assertEqual(comparison_response.status_code, 201, comparison_response.text)

        markdown = self.client.get(f"/api/v1/analyses/{analysis['id']}/export.md")
        self.assertEqual(markdown.status_code, 200)
        self.assertIn("브랜드 분석 보고서", markdown.text)

        csv = self.client.get(
            f"/api/v1/campaigns/{campaign['id']}/calendar/export.csv"
        )
        self.assertEqual(csv.status_code, 200)
        self.assertIn("날짜,채널,유형,주제,선택 문구", csv.text)
        self.assertIn("있음", csv.text)


if __name__ == "__main__":
    unittest.main()
