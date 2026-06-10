from __future__ import annotations

import sqlite3
from datetime import date, timedelta
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
        self, profile_version_id: str, provider: str, model: str = "deterministic-v1"
    ) -> dict[str, Any]:
        runs = GenerationRunRepository(self.database)
        return runs.create(
            "brand_analysis",
            provider,
            model,
            "brand_analysis",
            {"profile_version_id": profile_version_id},
        )

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


class GenerationRunRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        generation_type: str,
        provider: str,
        model: str,
        prompt_name: str,
        input_reference: dict[str, Any],
        settings: dict[str, Any] | None = None,
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
                ) VALUES (?, ?, 'running', ?, ?, ?, '1.0.0', ?, ?, ?, ?)
                """,
                (
                    run_id,
                    generation_type,
                    provider,
                    model,
                    prompt_name,
                    content_hash(f"{prompt_name}:1.0.0"),
                    dump_json(input_reference),
                    dump_json(settings or {}),
                    now,
                ),
            )
        return {"id": run_id, "started_at": now}

    def succeeded(self, run_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE generation_runs SET status = 'succeeded', completed_at = ? WHERE id = ?",
                (utc_now(), run_id),
            )

    def failed(self, run_id: str, code: str, message: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE generation_runs
                SET status = 'failed', error_code = ?, error_message = ?, completed_at = ?
                WHERE id = ?
                """,
                (code, message, utc_now(), run_id),
            )


def _campaign_from_row(row: sqlite3.Row, is_stale: bool = False) -> dict[str, Any]:
    return {
        "id": row["id"],
        "brand_id": row["brand_id"],
        "brand_analysis_id": row["brand_analysis_id"],
        "name": row["name"],
        "goal": row["goal"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "channel": row["channel"],
        "posts_per_week": row["posts_per_week"],
        "highlighted_products": load_json(row["highlighted_products_json"]),
        "required_facts": load_json(row["required_facts_json"]),
        "status": row["status"],
        "is_stale": is_stale,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _strategy_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "campaign_id": row["campaign_id"],
        "version": row["version"],
        "core_message": row["core_message"],
        "weekly_goals": load_json(row["weekly_goals_json"]),
        "content_pillars": load_json(row["content_pillars_json"]),
        "post_topics": load_json(row["post_topics_json"]),
        "risk_notes": load_json(row["risk_notes_json"]),
        "generation_run_id": row["generation_run_id"],
        "created_at": row["created_at"],
    }


class CampaignRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, request: Any) -> dict[str, Any]:
        now = utc_now()
        campaign_id = new_id()
        start = date.fromisoformat(request.start_date)
        end = start + timedelta(days=27)
        with self.database.connect() as connection:
            analysis = connection.execute(
                """
                SELECT a.*, p.brand_id
                FROM brand_analyses a
                JOIN brand_profile_versions p ON p.id = a.profile_version_id
                WHERE a.id = ?
                """,
                (request.brand_analysis_id,),
            ).fetchone()
            if not analysis:
                raise not_found("브랜드 분석")
            if analysis["status"] != "approved":
                raise AppError(
                    code="ANALYSIS_NOT_APPROVED",
                    message="브랜드 분석을 승인한 뒤 캠페인을 생성해 주세요.",
                    status_code=409,
                )
            if analysis["brand_id"] != request.brand_id:
                raise AppError(
                    code="INVALID_VARIANT_OWNER",
                    message="브랜드와 분석의 소유 관계가 맞지 않습니다.",
                    status_code=400,
                )
            connection.execute(
                """
                INSERT INTO campaigns(
                    id, brand_id, brand_analysis_id, name, goal, start_date, end_date,
                    channel, posts_per_week, highlighted_products_json,
                    required_facts_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'instagram_feed', 2, ?, ?, 'draft', ?, ?)
                """,
                (
                    campaign_id,
                    request.brand_id,
                    request.brand_analysis_id,
                    request.name.strip(),
                    request.goal,
                    request.start_date,
                    end.isoformat(),
                    dump_json(request.highlighted_products),
                    dump_json(request.required_facts),
                    now,
                    now,
                ),
            )
        return self.get(campaign_id)

    def get(self, campaign_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT c.*, a.status AS analysis_status
                FROM campaigns c
                JOIN brand_analyses a ON a.id = c.brand_analysis_id
                WHERE c.id = ?
                """,
                (campaign_id,),
            ).fetchone()
        if not row:
            raise not_found("캠페인")
        return _campaign_from_row(row, is_stale=row["analysis_status"] != "approved")

    def list(
        self, brand_id: str | None, status: str | None, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        values: list[Any] = []
        if brand_id:
            clauses.append("brand_id = ?")
            values.append(brand_id)
        if status:
            clauses.append("status = ?")
            values.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.database.connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM campaigns {where}", values
            ).fetchone()["count"]
            rows = connection.execute(
                f"""
                SELECT id FROM campaigns {where}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (*values, limit, offset),
            ).fetchall()
        return [self.get(row["id"]) for row in rows], total

    def update(self, campaign_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get(campaign_id)
        update: dict[str, Any] = {}
        if "name" in changes:
            update["name"] = changes["name"].strip()
        if "goal" in changes:
            update["goal"] = changes["goal"]
        if "highlighted_products" in changes:
            update["highlighted_products_json"] = dump_json(changes["highlighted_products"])
        if "required_facts" in changes:
            update["required_facts_json"] = dump_json(changes["required_facts"])
        if "start_date" in changes:
            start = date.fromisoformat(changes["start_date"])
            update["start_date"] = changes["start_date"]
            update["end_date"] = (start + timedelta(days=27)).isoformat()
        if not update:
            return current
        update["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in update)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE campaigns SET {assignments} WHERE id = ?",
                (*update.values(), campaign_id),
            )
        return self.get(campaign_id)

    def delete(self, campaign_id: str) -> None:
        self.get(campaign_id)
        with self.database.connect() as connection:
            connection.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))

    def create_strategy(
        self, campaign_id: str, generation_run_id: str, strategy: dict[str, Any]
    ) -> dict[str, Any]:
        now = utc_now()
        strategy_id = new_id()
        with self.database.connect() as connection:
            version = connection.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM campaign_strategies WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchone()["next_version"]
            connection.execute(
                """
                INSERT INTO campaign_strategies(
                    id, campaign_id, version, core_message, weekly_goals_json,
                    content_pillars_json, post_topics_json, risk_notes_json,
                    generation_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    strategy_id,
                    campaign_id,
                    version,
                    strategy["core_message"],
                    dump_json(strategy["weekly_goals"]),
                    dump_json(strategy["content_pillars"]),
                    dump_json(strategy["post_topics"]),
                    dump_json(strategy["risk_notes"]),
                    generation_run_id,
                    now,
                ),
            )
            connection.execute(
                "UPDATE campaigns SET status = 'strategy_ready', updated_at = ? WHERE id = ?",
                (now, campaign_id),
            )
        return self.get_strategy(strategy_id)

    def get_strategy(self, strategy_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM campaign_strategies WHERE id = ?", (strategy_id,)
            ).fetchone()
        if not row:
            raise not_found("캠페인 전략")
        return _strategy_from_row(row)

    def latest_strategy(self, campaign_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM campaign_strategies
                WHERE campaign_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (campaign_id,),
            ).fetchone()
        if not row:
            raise AppError(
                code="STRATEGY_REQUIRED",
                message="콘텐츠 생성 전에 캠페인 전략을 먼저 생성해 주세요.",
                status_code=409,
            )
        return _strategy_from_row(row)

    def list_strategies(self, campaign_id: str) -> list[dict[str, Any]]:
        self.get(campaign_id)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM campaign_strategies
                WHERE campaign_id = ?
                ORDER BY version DESC
                """,
                (campaign_id,),
            ).fetchall()
        return [_strategy_from_row(row) for row in rows]


VARIANT_JSON_FIELDS = {"hashtags", "quality_warnings"}


def _variant_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "content_id": row["content_id"],
        "source_variant_id": row["source_variant_id"],
        "origin": row["origin"],
        "variant_number": row["variant_number"],
        "tone": row["tone"],
        "opening_line": row["opening_line"],
        "body": row["body"],
        "cta": row["cta"],
        "hashtags": load_json(row["hashtags_json"]),
        "image_concept": row["image_concept"],
        "quality_warnings": load_json(row["quality_warnings_json"]),
        "generation_run_id": row["generation_run_id"],
        "created_at": row["created_at"],
    }


def _poster_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row["id"],
        "content_id": row["content_id"],
        "headline": row["headline"],
        "supporting_text": row["supporting_text"],
        "visual_mood": row["visual_mood"],
        "colors": load_json(row["colors_json"]),
        "layout_description": row["layout_description"],
        "image_prompt": row["image_prompt"],
        "negative_prompt": row["negative_prompt"],
        "aspect_ratio": row["aspect_ratio"],
        "generation_run_id": row["generation_run_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class ContentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_batch(
        self,
        campaign_id: str,
        strategy_id: str,
        generation_run_id: str,
        contents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        now = utc_now()
        created_ids: list[str] = []
        with self.database.connect() as connection:
            connection.execute("DELETE FROM contents WHERE campaign_id = ?", (campaign_id,))
            for item in contents:
                content_id = new_id()
                created_ids.append(content_id)
                connection.execute(
                    """
                    INSERT INTO contents(
                        id, campaign_id, strategy_id, sequence, week_number,
                        content_type, topic, core_message, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    """,
                    (
                        content_id,
                        campaign_id,
                        strategy_id,
                        item["sequence"],
                        item["week_number"],
                        item["content_type"],
                        item["topic"],
                        item["core_message"],
                        now,
                        now,
                    ),
                )
                for index, variant in enumerate(item["variants"], start=1):
                    self._insert_variant(
                        connection,
                        content_id,
                        variant,
                        index,
                        "ai",
                        None,
                        generation_run_id,
                    )
            connection.execute(
                "UPDATE campaigns SET status = 'content_ready', updated_at = ? WHERE id = ?",
                (now, campaign_id),
            )
        return [self.get(content_id) for content_id in created_ids]

    def get(self, content_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            content = connection.execute(
                "SELECT * FROM contents WHERE id = ?", (content_id,)
            ).fetchone()
            if not content:
                raise not_found("콘텐츠")
            variants = connection.execute(
                """
                SELECT * FROM content_variants
                WHERE content_id = ?
                ORDER BY origin, variant_number, created_at
                """,
                (content_id,),
            ).fetchall()
            poster = connection.execute(
                "SELECT * FROM poster_briefs WHERE content_id = ?", (content_id,)
            ).fetchone()
        return {
            "id": content["id"],
            "campaign_id": content["campaign_id"],
            "strategy_id": content["strategy_id"],
            "sequence": content["sequence"],
            "week_number": content["week_number"],
            "content_type": content["content_type"],
            "topic": content["topic"],
            "core_message": content["core_message"],
            "status": content["status"],
            "selected_variant_id": content["selected_variant_id"],
            "variants": [_variant_from_row(row) for row in variants],
            "poster_brief": _poster_from_row(poster),
            "created_at": content["created_at"],
            "updated_at": content["updated_at"],
        }

    def list_for_campaign(
        self, campaign_id: str, status: str | None = None, week_number: int | None = None
    ) -> list[dict[str, Any]]:
        clauses = ["campaign_id = ?"]
        values: list[Any] = [campaign_id]
        if status:
            clauses.append("status = ?")
            values.append(status)
        if week_number:
            clauses.append("week_number = ?")
            values.append(week_number)
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id FROM contents
                WHERE {' AND '.join(clauses)}
                ORDER BY sequence
                """,
                values,
            ).fetchall()
        return [self.get(row["id"]) for row in rows]

    def search(
        self,
        brand_id: str | None,
        campaign_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        values: list[Any] = []
        if brand_id:
            clauses.append("c.brand_id = ?")
            values.append(brand_id)
        if campaign_id:
            clauses.append("ct.campaign_id = ?")
            values.append(campaign_id)
        if status:
            clauses.append("ct.status = ?")
            values.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.database.connect() as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM contents ct
                JOIN campaigns c ON c.id = ct.campaign_id
                {where}
                """,
                values,
            ).fetchone()["count"]
            rows = connection.execute(
                f"""
                SELECT ct.id
                FROM contents ct
                JOIN campaigns c ON c.id = ct.campaign_id
                {where}
                ORDER BY ct.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (*values, limit, offset),
            ).fetchall()
        return [self.get(row["id"]) for row in rows], total

    def update_status(self, content_id: str, status: str) -> dict[str, Any]:
        self.get(content_id)
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE contents SET status = ?, updated_at = ? WHERE id = ?",
                (status, utc_now(), content_id),
            )
        return self.get(content_id)

    def create_variant(
        self,
        content_id: str,
        variant: dict[str, Any],
        generation_run_id: str | None,
    ) -> dict[str, Any]:
        existing = self.get(content_id)["variants"]
        ai_count = len([item for item in existing if item["origin"] == "ai"])
        if ai_count >= 3:
            raise AppError(
                code="VARIANT_LIMIT_REACHED",
                message="AI 변형은 게시물당 최대 3개까지 생성할 수 있습니다.",
                status_code=409,
            )
        with self.database.connect() as connection:
            variant_id = self._insert_variant(
                connection,
                content_id,
                variant,
                ai_count + 1,
                "ai",
                None,
                generation_run_id,
            )
        return self.get_variant(variant_id)

    def create_user_edit(
        self, source_variant_id: str, variant: dict[str, Any]
    ) -> dict[str, Any]:
        source = self.get_variant(source_variant_id)
        user_edit_count = len(
            [
                item
                for item in self.get(source["content_id"])["variants"]
                if item["origin"] == "user_edit"
            ]
        )
        with self.database.connect() as connection:
            variant_id = self._insert_variant(
                connection,
                source["content_id"],
                variant,
                user_edit_count + 1,
                "user_edit",
                source_variant_id,
                None,
            )
        return self.get_variant(variant_id)

    def select_variant(self, content_id: str, variant_id: str) -> dict[str, Any]:
        variant = self.get_variant(variant_id)
        if variant["content_id"] != content_id:
            raise AppError(
                code="INVALID_VARIANT_OWNER",
                message="해당 콘텐츠에 속한 변형만 선택할 수 있습니다.",
                status_code=400,
            )
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE contents
                SET selected_variant_id = ?, status = 'approved', updated_at = ?
                WHERE id = ?
                """,
                (variant_id, now, content_id),
            )
        return self.get(content_id)

    def get_variant(self, variant_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM content_variants WHERE id = ?", (variant_id,)
            ).fetchone()
        if not row:
            raise not_found("콘텐츠 변형")
        return _variant_from_row(row)

    def _insert_variant(
        self,
        connection: sqlite3.Connection,
        content_id: str,
        variant: dict[str, Any],
        variant_number: int,
        origin: str,
        source_variant_id: str | None,
        generation_run_id: str | None,
    ) -> str:
        variant_id = new_id()
        connection.execute(
            """
            INSERT INTO content_variants(
                id, content_id, source_variant_id, origin, variant_number, tone,
                opening_line, body, cta, hashtags_json, image_concept,
                quality_warnings_json, generation_run_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                variant_id,
                content_id,
                source_variant_id,
                origin,
                variant_number,
                variant["tone"],
                variant["opening_line"],
                variant["body"],
                variant["cta"],
                dump_json(variant["hashtags"]),
                variant["image_concept"],
                dump_json(variant.get("quality_warnings", [])),
                generation_run_id,
                utc_now(),
            ),
        )
        return variant_id


class PosterBriefRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_content(self, content_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM poster_briefs WHERE content_id = ?", (content_id,)
            ).fetchone()
        if not row:
            raise not_found("포스터 브리프")
        return _poster_from_row(row)  # type: ignore[return-value]

    def get(self, brief_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM poster_briefs WHERE id = ?", (brief_id,)
            ).fetchone()
        if not row:
            raise not_found("포스터 브리프")
        return _poster_from_row(row)  # type: ignore[return-value]

    def upsert(
        self, content_id: str, brief: dict[str, Any], generation_run_id: str | None
    ) -> dict[str, Any]:
        now = utc_now()
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM poster_briefs WHERE content_id = ?", (content_id,)
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE poster_briefs
                    SET headline = ?, supporting_text = ?, visual_mood = ?,
                        colors_json = ?, layout_description = ?, image_prompt = ?,
                        negative_prompt = ?, aspect_ratio = ?, generation_run_id = ?,
                        updated_at = ?
                    WHERE content_id = ?
                    """,
                    (
                        brief["headline"],
                        brief.get("supporting_text"),
                        brief["visual_mood"],
                        dump_json(brief["colors"]),
                        brief["layout_description"],
                        brief["image_prompt"],
                        brief.get("negative_prompt"),
                        brief["aspect_ratio"],
                        generation_run_id,
                        now,
                        content_id,
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO poster_briefs(
                        id, content_id, headline, supporting_text, visual_mood,
                        colors_json, layout_description, image_prompt,
                        negative_prompt, aspect_ratio, generation_run_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id(),
                        content_id,
                        brief["headline"],
                        brief.get("supporting_text"),
                        brief["visual_mood"],
                        dump_json(brief["colors"]),
                        brief["layout_description"],
                        brief["image_prompt"],
                        brief.get("negative_prompt"),
                        brief["aspect_ratio"],
                        generation_run_id,
                        now,
                        now,
                    ),
                )
        return self.get_by_content(content_id)

    def update(self, content_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        self.get_by_content(content_id)
        serialized = {
            ("colors_json" if key == "colors" else key): (
                dump_json(value) if key == "colors" else value
            )
            for key, value in changes.items()
        }
        serialized["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE poster_briefs SET {assignments} WHERE content_id = ?",
                (*serialized.values(), content_id),
            )
        return self.get_by_content(content_id)


class GeneratedImageRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        poster_brief_id: str,
        provider: str,
        model: str,
        prompt: str,
        aspect_ratio: str,
        width: int,
        height: int,
        background_path: str,
        composed_path: str,
        generation_run_id: str,
    ) -> dict[str, Any]:
        image_id = new_id()
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1
                FROM generated_images
                WHERE poster_brief_id = ?
                """,
                (poster_brief_id,),
            ).fetchone()
            version = int(row[0])
            connection.execute(
                """
                INSERT INTO generated_images(
                    id, poster_brief_id, version, status, provider, model,
                    prompt, aspect_ratio, width, height, background_path,
                    composed_path, generation_run_id, created_at
                ) VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image_id,
                    poster_brief_id,
                    version,
                    provider,
                    model,
                    prompt,
                    aspect_ratio,
                    width,
                    height,
                    background_path,
                    composed_path,
                    generation_run_id,
                    utc_now(),
                ),
            )
        return self.get(image_id)

    def get(self, image_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM generated_images WHERE id = ?", (image_id,)
            ).fetchone()
        if not row:
            raise not_found("생성 이미지")
        return dict(row)

    def list_for_brief(self, poster_brief_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM generated_images
                WHERE poster_brief_id = ?
                ORDER BY version DESC
                """,
                (poster_brief_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def approve(self, image_id: str) -> dict[str, Any]:
        image = self.get(image_id)
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE generated_images
                SET status = 'superseded'
                WHERE poster_brief_id = ? AND status = 'approved' AND id != ?
                """,
                (image["poster_brief_id"], image_id),
            )
            connection.execute(
                """
                UPDATE generated_images
                SET status = 'approved', approved_at = ?
                WHERE id = ?
                """,
                (now, image_id),
            )
        return self.get(image_id)


class CalendarRepository:
    def __init__(self, database: Database, contents: ContentRepository) -> None:
        self.database = database
        self.contents = contents

    def create_for_campaign(
        self, campaign: dict[str, Any], preferred_weekdays: list[int]
    ) -> list[dict[str, Any]]:
        content_items = self.contents.list_for_campaign(campaign["id"])
        if not content_items:
            raise AppError(
                code="STRATEGY_REQUIRED",
                message="캘린더 생성 전에 콘텐츠를 먼저 생성해 주세요.",
                status_code=409,
            )
        start = date.fromisoformat(campaign["start_date"])
        end = date.fromisoformat(campaign["end_date"])
        scheduled_dates = self._make_dates(start, end, preferred_weekdays, len(content_items))
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM calendar_items WHERE campaign_id = ?", (campaign["id"],)
            )
            for item, scheduled_date in zip(content_items, scheduled_dates, strict=True):
                connection.execute(
                    """
                    INSERT INTO calendar_items(
                        id, campaign_id, content_id, scheduled_date, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id(),
                        campaign["id"],
                        item["id"],
                        scheduled_date.isoformat(),
                        item["status"],
                        now,
                        now,
                    ),
                )
        return self.list_for_campaign(campaign["id"])

    def list_for_campaign(self, campaign_id: str) -> list[dict[str, Any]]:
        self.refresh_for_campaign(campaign_id)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM calendar_items
                WHERE campaign_id = ?
                ORDER BY scheduled_date
                """,
                (campaign_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def refresh_for_campaign(self, campaign_id: str) -> list[dict[str, Any]]:
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE calendar_items
                SET status = (
                        SELECT contents.status
                        FROM contents
                        WHERE contents.id = calendar_items.content_id
                    ),
                    updated_at = ?
                WHERE campaign_id = ?
                  AND EXISTS (
                        SELECT 1
                        FROM contents
                        WHERE contents.id = calendar_items.content_id
                          AND contents.status != calendar_items.status
                    )
                """,
                (now, campaign_id),
            )
        return self._list_for_campaign_without_refresh(campaign_id)

    def _list_for_campaign_without_refresh(self, campaign_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM calendar_items
                WHERE campaign_id = ?
                ORDER BY scheduled_date
                """,
                (campaign_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update(self, item_id: str, campaign: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        if "scheduled_date" in changes:
            scheduled = date.fromisoformat(changes["scheduled_date"])
            if scheduled < date.fromisoformat(campaign["start_date"]) or scheduled > date.fromisoformat(campaign["end_date"]):
                raise AppError(
                    code="CALENDAR_DATE_OUT_OF_RANGE",
                    message="게시일은 캠페인 기간 안에서만 선택할 수 있습니다.",
                    status_code=422,
                )
        update = dict(changes)
        update["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in update)
        with self.database.connect() as connection:
            exists = connection.execute(
                "SELECT id FROM calendar_items WHERE id = ? AND campaign_id = ?",
                (item_id, campaign["id"]),
            ).fetchone()
            if not exists:
                raise not_found("캘린더 항목")
            connection.execute(
                f"UPDATE calendar_items SET {assignments} WHERE id = ?",
                (*update.values(), item_id),
            )
        return self.get(item_id)

    def get(self, item_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM calendar_items WHERE id = ?", (item_id,)
            ).fetchone()
        if not row:
            raise not_found("캘린더 항목")
        return self._from_row(row)

    def _from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        content = self.contents.get(row["content_id"])
        return {
            "id": row["id"],
            "campaign_id": row["campaign_id"],
            "content_id": row["content_id"],
            "scheduled_date": row["scheduled_date"],
            "status": row["status"],
            "content": content,
            "approved_image": self._approved_image_for_content(row["content_id"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _approved_image_for_content(self, content_id: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT generated_images.*
                FROM generated_images
                JOIN poster_briefs
                  ON poster_briefs.id = generated_images.poster_brief_id
                WHERE poster_briefs.content_id = ?
                  AND generated_images.status = 'approved'
                ORDER BY generated_images.approved_at DESC
                LIMIT 1
                """,
                (content_id,),
            ).fetchone()
        if not row:
            return None
        image = dict(row)
        return {
            key: value
            for key, value in image.items()
            if key not in {"background_path", "composed_path"}
        }

    def _make_dates(
        self, start: date, end: date, preferred_weekdays: list[int], count: int
    ) -> list[date]:
        dates: list[date] = []
        current = start
        weekday_set = set(preferred_weekdays)
        while current <= end and len(dates) < count:
            if current.isoweekday() in weekday_set:
                dates.append(current)
            current += timedelta(days=1)
        current = start
        while len(dates) < count:
            if current not in dates:
                dates.append(current)
            current += timedelta(days=1)
            if current > end:
                current = start
        return sorted(dates[:count])


class ComparisonRepository:
    def __init__(self, database: Database, contents: ContentRepository) -> None:
        self.database = database
        self.contents = contents

    def create(self, name: str, variant_ids: list[str]) -> dict[str, Any]:
        variants = [self.contents.get_variant(variant_id) for variant_id in variant_ids]
        content_ids = {variant["content_id"] for variant in variants}
        if len(content_ids) != 1:
            raise AppError(
                code="INVALID_VARIANT_OWNER",
                message="같은 콘텐츠의 변형만 비교할 수 있습니다.",
                status_code=400,
            )
        set_id = new_id()
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO comparison_sets(id, name, created_at) VALUES (?, ?, ?)",
                (set_id, name, now),
            )
            for position, variant_id in enumerate(variant_ids, start=1):
                connection.execute(
                    """
                    INSERT INTO comparison_members(
                        comparison_set_id, content_variant_id, position
                    ) VALUES (?, ?, ?)
                    """,
                    (set_id, variant_id, position),
                )
        return self.get(set_id)

    def get(self, set_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM comparison_sets WHERE id = ?", (set_id,)
            ).fetchone()
            if not row:
                raise not_found("비교 세트")
            member_rows = connection.execute(
                """
                SELECT content_variant_id FROM comparison_members
                WHERE comparison_set_id = ?
                ORDER BY position
                """,
                (set_id,),
            ).fetchall()
        return {
            "id": row["id"],
            "name": row["name"],
            "variants": [
                self.contents.get_variant(member["content_variant_id"])
                for member in member_rows
            ],
            "created_at": row["created_at"],
        }

    def delete(self, set_id: str) -> None:
        self.get(set_id)
        with self.database.connect() as connection:
            connection.execute("DELETE FROM comparison_sets WHERE id = ?", (set_id,))
