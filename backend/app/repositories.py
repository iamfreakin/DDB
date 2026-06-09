from __future__ import annotations

import sqlite3
from typing import Any

from backend.app.db import Database
from backend.app.errors import AppError, not_found
from backend.app.schemas import BrandCreate, BrandProfileInput
from backend.app.utils import content_hash, dump_json, load_json, new_id, utc_now


def _profile_payload(profile: BrandProfileInput) -> dict[str, Any]:
    return profile.model_dump(mode="json")


def _serialize_profile(profile: BrandProfileInput) -> dict[str, Any]:
    payload = _profile_payload(profile)
    return {
        "products_json": dump_json(payload["products"]),
        "target_customers": payload["target_customers"],
        "strengths": payload["strengths"],
        "desired_moods_json": dump_json(payload["desired_moods"]),
        "region": payload["region"],
        "price_range": payload["price_range"],
        "existing_copy": payload["existing_copy"],
        "avoid_expressions_json": dump_json(payload["avoid_expressions"]),
        "campaign_facts_json": dump_json(payload["campaign_facts"]),
        "content_hash": content_hash(payload),
    }


def _profile_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "version": row["version"],
        "products": load_json(row["products_json"]),
        "target_customers": row["target_customers"],
        "strengths": row["strengths"],
        "desired_moods": load_json(row["desired_moods_json"]),
        "region": row["region"],
        "price_range": row["price_range"],
        "existing_copy": row["existing_copy"],
        "avoid_expressions": load_json(row["avoid_expressions_json"]),
        "campaign_facts": load_json(row["campaign_facts_json"]),
        "created_at": row["created_at"],
    }


class BrandRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, request: BrandCreate) -> dict[str, Any]:
        now = utc_now()
        brand_id = new_id()
        profile_id = new_id()
        serialized = _serialize_profile(request.profile)
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO brands(id, name, industry, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (brand_id, request.name.strip(), request.industry.strip(), now, now),
            )
            connection.execute(
                """
                INSERT INTO brand_profile_versions(
                    id, brand_id, version, products_json, target_customers,
                    strengths, desired_moods_json, region, price_range,
                    existing_copy, avoid_expressions_json, campaign_facts_json,
                    content_hash, created_at
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    brand_id,
                    serialized["products_json"],
                    serialized["target_customers"],
                    serialized["strengths"],
                    serialized["desired_moods_json"],
                    serialized["region"],
                    serialized["price_range"],
                    serialized["existing_copy"],
                    serialized["avoid_expressions_json"],
                    serialized["campaign_facts_json"],
                    serialized["content_hash"],
                    now,
                ),
            )
            connection.execute(
                "UPDATE brands SET active_profile_version_id = ? WHERE id = ?",
                (profile_id, brand_id),
            )
        return self.get(brand_id)

    def get(self, brand_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            brand = connection.execute(
                "SELECT * FROM brands WHERE id = ?", (brand_id,)
            ).fetchone()
            if not brand:
                raise not_found("가게")
            profile = connection.execute(
                "SELECT * FROM brand_profile_versions WHERE id = ?",
                (brand["active_profile_version_id"],),
            ).fetchone()
        if not profile:
            raise AppError(
                code="DATABASE_ERROR",
                message="현재 브랜드 프로필을 불러오지 못했습니다.",
                status_code=500,
            )
        return {
            "id": brand["id"],
            "name": brand["name"],
            "industry": brand["industry"],
            "active_profile": _profile_from_row(profile),
            "created_at": brand["created_at"],
            "updated_at": brand["updated_at"],
        }

    def list(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        with self.database.connect() as connection:
            total = connection.execute("SELECT COUNT(*) AS count FROM brands").fetchone()[
                "count"
            ]
            ids = connection.execute(
                """
                SELECT id FROM brands
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [self.get(row["id"]) for row in ids], total

    def create_profile_version(
        self, brand_id: str, profile: BrandProfileInput
    ) -> dict[str, Any]:
        serialized = _serialize_profile(profile)
        now = utc_now()
        profile_id = new_id()
        with self.database.connect() as connection:
            brand = connection.execute(
                """
                SELECT b.*, p.content_hash
                FROM brands b
                JOIN brand_profile_versions p ON p.id = b.active_profile_version_id
                WHERE b.id = ?
                """,
                (brand_id,),
            ).fetchone()
            if not brand:
                raise not_found("가게")
            if brand["content_hash"] == serialized["content_hash"]:
                raise AppError(
                    code="PROFILE_UNCHANGED",
                    message="현재 프로필과 동일한 내용입니다.",
                    status_code=409,
                )
            version = connection.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM brand_profile_versions WHERE brand_id = ?
                """,
                (brand_id,),
            ).fetchone()["next_version"]
            connection.execute(
                """
                INSERT INTO brand_profile_versions(
                    id, brand_id, version, products_json, target_customers,
                    strengths, desired_moods_json, region, price_range,
                    existing_copy, avoid_expressions_json, campaign_facts_json,
                    content_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    brand_id,
                    version,
                    serialized["products_json"],
                    serialized["target_customers"],
                    serialized["strengths"],
                    serialized["desired_moods_json"],
                    serialized["region"],
                    serialized["price_range"],
                    serialized["existing_copy"],
                    serialized["avoid_expressions_json"],
                    serialized["campaign_facts_json"],
                    serialized["content_hash"],
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE brand_analyses
                SET status = 'stale', updated_at = ?
                WHERE profile_version_id IN (
                    SELECT id FROM brand_profile_versions
                    WHERE brand_id = ? AND id != ?
                ) AND status IN ('draft', 'approved')
                """,
                (now, brand_id, profile_id),
            )
            connection.execute(
                """
                UPDATE brands
                SET active_profile_version_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (profile_id, now, brand_id),
            )
        return self.get(brand_id)


ANALYSIS_JSON_FIELDS = {
    "target_segments",
    "customer_needs",
    "differentiators",
    "brand_voice",
    "recommended_keywords",
    "avoid_expressions",
    "missing_information",
}


def _analysis_from_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    for field in ANALYSIS_JSON_FIELDS:
        result[field] = load_json(result.pop(f"{field}_json"))
    return result


class AnalysisRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, analysis_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM brand_analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
        if not row:
            raise not_found("브랜드 분석")
        return _analysis_from_row(row)

    def list_for_brand(self, brand_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT a.*
                FROM brand_analyses a
                JOIN brand_profile_versions p ON p.id = a.profile_version_id
                WHERE p.brand_id = ?
                ORDER BY a.created_at DESC
                """,
                (brand_id,),
            ).fetchall()
        return [_analysis_from_row(row) for row in rows]

    def create_generation_run(
        self, profile_version_id: str, provider: str
    ) -> dict[str, Any]:
        run_id = new_id()
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_runs(
                    id, generation_type, status, provider, model, prompt_name,
                    prompt_version, prompt_hash, input_reference_json,
                    settings_json, started_at
                ) VALUES (?, 'brand_analysis', 'running', ?, ?, ?, ?, ?, ?, '{}', ?)
                """,
                (
                    run_id,
                    provider,
                    "deterministic-v1",
                    "brand_analysis",
                    "1.0.0",
                    content_hash("brand_analysis:1.0.0"),
                    dump_json({"profile_version_id": profile_version_id}),
                    now,
                ),
            )
        return {"id": run_id, "started_at": now}

    def mark_generation_succeeded(self, run_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE generation_runs
                SET status = 'succeeded', completed_at = ?
                WHERE id = ?
                """,
                (utc_now(), run_id),
            )

    def mark_generation_failed(
        self, run_id: str, error_code: str, error_message: str
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE generation_runs
                SET status = 'failed', error_code = ?, error_message = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (error_code, error_message, utc_now(), run_id),
            )

    def create(
        self,
        profile_version_id: str,
        generation_run_id: str,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        analysis_id = new_id()
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO brand_analyses(
                    id, profile_version_id, status, brand_summary,
                    target_segments_json, customer_needs_json, value_proposition,
                    differentiators_json, brand_voice_json,
                    recommended_keywords_json, avoid_expressions_json,
                    missing_information_json, generation_run_id,
                    created_at, updated_at
                ) VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    profile_version_id,
                    analysis["brand_summary"],
                    dump_json(analysis["target_segments"]),
                    dump_json(analysis["customer_needs"]),
                    analysis["value_proposition"],
                    dump_json(analysis["differentiators"]),
                    dump_json(analysis["brand_voice"]),
                    dump_json(analysis["recommended_keywords"]),
                    dump_json(analysis["avoid_expressions"]),
                    dump_json(analysis["missing_information"]),
                    generation_run_id,
                    now,
                    now,
                ),
            )
        return self.get(analysis_id)

    def update(self, analysis_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get(analysis_id)
        if current["status"] != "draft":
            raise AppError(
                code="ANALYSIS_NOT_EDITABLE",
                message="초안 상태의 브랜드 분석만 수정할 수 있습니다.",
                status_code=409,
            )
        assignments: list[str] = []
        values: list[Any] = []
        for field, value in changes.items():
            column = f"{field}_json" if field in ANALYSIS_JSON_FIELDS else field
            assignments.append(f"{column} = ?")
            values.append(dump_json(value) if field in ANALYSIS_JSON_FIELDS else value)
        assignments.append("updated_at = ?")
        values.extend([utc_now(), analysis_id])
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE brand_analyses SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
        return self.get(analysis_id)

    def approve(self, analysis_id: str) -> dict[str, Any]:
        current = self.get(analysis_id)
        if current["status"] == "stale":
            raise AppError(
                code="ANALYSIS_STALE",
                message="현재 프로필에서 새 브랜드 분석을 생성해 주세요.",
                status_code=409,
            )
        if current["status"] != "draft":
            raise AppError(
                code="ANALYSIS_NOT_EDITABLE",
                message="초안 상태의 브랜드 분석만 승인할 수 있습니다.",
                status_code=409,
            )
        now = utc_now()
        with self.database.connect() as connection:
            brand_id = connection.execute(
                """
                SELECT brand_id FROM brand_profile_versions
                WHERE id = ?
                """,
                (current["profile_version_id"],),
            ).fetchone()["brand_id"]
            connection.execute(
                """
                UPDATE brand_analyses
                SET status = 'superseded', updated_at = ?
                WHERE status = 'approved'
                  AND profile_version_id IN (
                    SELECT id FROM brand_profile_versions WHERE brand_id = ?
                  )
                """,
                (now, brand_id),
            )
            connection.execute(
                """
                UPDATE brand_analyses
                SET status = 'approved', approved_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, analysis_id),
            )
        return self.get(analysis_id)
