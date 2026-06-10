from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS brands (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 50),
    industry TEXT NOT NULL,
    active_profile_version_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(active_profile_version_id)
        REFERENCES brand_profile_versions(id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS brand_profile_versions (
    id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(version >= 1),
    products_json TEXT NOT NULL,
    target_customers TEXT NOT NULL,
    strengths TEXT NOT NULL,
    desired_moods_json TEXT NOT NULL,
    region TEXT,
    price_range TEXT,
    existing_copy TEXT,
    avoid_expressions_json TEXT NOT NULL DEFAULT '[]',
    campaign_facts_json TEXT NOT NULL DEFAULT '{}',
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(brand_id, version),
    FOREIGN KEY(brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generation_runs (
    id TEXT PRIMARY KEY,
    generation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    input_reference_json TEXT NOT NULL,
    settings_json TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost REAL,
    error_code TEXT,
    error_message TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS brand_analyses (
    id TEXT PRIMARY KEY,
    profile_version_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('draft', 'approved', 'stale', 'superseded')),
    brand_summary TEXT NOT NULL,
    target_segments_json TEXT NOT NULL,
    customer_needs_json TEXT NOT NULL,
    value_proposition TEXT NOT NULL,
    differentiators_json TEXT NOT NULL,
    brand_voice_json TEXT NOT NULL,
    recommended_keywords_json TEXT NOT NULL,
    avoid_expressions_json TEXT NOT NULL,
    missing_information_json TEXT NOT NULL,
    generation_run_id TEXT,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(profile_version_id)
        REFERENCES brand_profile_versions(id) ON DELETE CASCADE,
    FOREIGN KEY(generation_run_id)
        REFERENCES generation_runs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_profiles_brand_version
    ON brand_profile_versions(brand_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_profile_status
    ON brand_analyses(profile_version_id, status);

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    brand_analysis_id TEXT NOT NULL,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
    goal TEXT NOT NULL CHECK(goal IN (
        'new_product', 'new_customer', 'repeat_visit',
        'seasonal_event', 'brand_awareness'
    )),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'instagram_feed',
    posts_per_week INTEGER NOT NULL DEFAULT 2,
    highlighted_products_json TEXT NOT NULL,
    required_facts_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK(status IN (
        'draft', 'strategy_ready', 'content_ready',
        'active', 'completed', 'archived'
    )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY(brand_analysis_id) REFERENCES brand_analyses(id)
);

CREATE TABLE IF NOT EXISTS campaign_strategies (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    core_message TEXT NOT NULL,
    weekly_goals_json TEXT NOT NULL,
    content_pillars_json TEXT NOT NULL,
    post_topics_json TEXT NOT NULL,
    risk_notes_json TEXT NOT NULL,
    generation_run_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(campaign_id, version),
    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY(generation_run_id) REFERENCES generation_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS contents (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 8),
    week_number INTEGER NOT NULL CHECK(week_number BETWEEN 1 AND 4),
    content_type TEXT NOT NULL CHECK(content_type IN (
        'product', 'informational', 'relationship', 'promotion'
    )),
    topic TEXT NOT NULL,
    core_message TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'idea', 'draft', 'approved', 'published', 'on_hold'
    )),
    selected_variant_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(campaign_id, sequence),
    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY(strategy_id) REFERENCES campaign_strategies(id),
    FOREIGN KEY(selected_variant_id)
        REFERENCES content_variants(id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS content_variants (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    source_variant_id TEXT,
    origin TEXT NOT NULL CHECK(origin IN ('ai', 'user_edit')),
    variant_number INTEGER NOT NULL,
    tone TEXT NOT NULL,
    opening_line TEXT NOT NULL,
    body TEXT NOT NULL,
    cta TEXT NOT NULL,
    hashtags_json TEXT NOT NULL,
    image_concept TEXT NOT NULL,
    quality_warnings_json TEXT NOT NULL,
    generation_run_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY(source_variant_id) REFERENCES content_variants(id) ON DELETE SET NULL,
    FOREIGN KEY(generation_run_id) REFERENCES generation_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS poster_briefs (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL UNIQUE,
    headline TEXT NOT NULL,
    supporting_text TEXT,
    visual_mood TEXT NOT NULL,
    colors_json TEXT NOT NULL,
    layout_description TEXT NOT NULL,
    image_prompt TEXT NOT NULL,
    negative_prompt TEXT,
    aspect_ratio TEXT NOT NULL,
    generation_run_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY(generation_run_id) REFERENCES generation_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS generated_images (
    id TEXT PRIMARY KEY,
    poster_brief_id TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(version >= 1),
    status TEXT NOT NULL CHECK(status IN ('draft', 'approved', 'superseded')),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    background_path TEXT NOT NULL,
    composed_path TEXT NOT NULL,
    generation_run_id TEXT,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(poster_brief_id, version),
    FOREIGN KEY(poster_brief_id) REFERENCES poster_briefs(id) ON DELETE CASCADE,
    FOREIGN KEY(generation_run_id) REFERENCES generation_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS calendar_items (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    content_id TEXT NOT NULL UNIQUE,
    scheduled_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'idea', 'draft', 'approved', 'published', 'on_hold'
    )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY(content_id) REFERENCES contents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comparison_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comparison_members (
    comparison_set_id TEXT NOT NULL,
    content_variant_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY(comparison_set_id, content_variant_id),
    UNIQUE(comparison_set_id, position),
    FOREIGN KEY(comparison_set_id) REFERENCES comparison_sets(id) ON DELETE CASCADE,
    FOREIGN KEY(content_variant_id) REFERENCES content_variants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaigns_brand_created
    ON campaigns(brand_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_strategies_campaign_version
    ON campaign_strategies(campaign_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_contents_campaign_sequence
    ON contents(campaign_id, sequence);
CREATE INDEX IF NOT EXISTS idx_variants_content_created
    ON content_variants(content_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_images_brief_version
    ON generated_images(poster_brief_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_calendar_campaign_date
    ON calendar_items(campaign_id, scheduled_date);
CREATE INDEX IF NOT EXISTS idx_generation_status_started
    ON generation_runs(status, started_at DESC);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def healthcheck(self) -> bool:
        try:
            with self.connect() as connection:
                row = connection.execute("SELECT 1 AS healthy").fetchone()
            return bool(row and row["healthy"] == 1)
        except sqlite3.Error:
            return False
