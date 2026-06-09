from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int
    retryable: bool = False
    field_errors: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message


def not_found(resource: str) -> AppError:
    return AppError(
        code="RESOURCE_NOT_FOUND",
        message=f"{resource}을(를) 찾을 수 없습니다.",
        status_code=404,
    )

