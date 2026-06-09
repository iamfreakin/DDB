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

