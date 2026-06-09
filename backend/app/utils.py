from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_json(value: str) -> Any:
    return json.loads(value)


def content_hash(value: Any) -> str:
    payload = dump_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

