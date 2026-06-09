# API 오류 계약

- 상태: Review

## 공통 형식

```json
{
  "error": {
    "code": "ANALYSIS_NOT_APPROVED",
    "message": "브랜드 분석을 승인한 뒤 캠페인을 생성해 주세요.",
    "field_errors": [],
    "request_id": "uuid",
    "retryable": false
  }
}
```

## HTTP 상태 사용

| 상태 | 사용 |
|---|---|
| 400 | 요청 조합이나 비즈니스 규칙 위반 |
| 404 | 리소스를 찾을 수 없음 |
| 409 | 현재 상태와 충돌 |
| 422 | 필드 형식 및 길이 검증 실패 |
| 429 | 외부 또는 내부 사용량 제한 |
| 502 | AI 공급자 응답 오류 |
| 503 | AI 공급자 일시 사용 불가 |
| 504 | AI 생성 시간 초과 |

## 필드 오류

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 내용을 확인해 주세요.",
    "field_errors": [
      {
        "field": "profile.target_customers",
        "message": "10자 이상 입력해 주세요."
      }
    ],
    "request_id": "uuid",
    "retryable": false
  }
}
```

## 오류 코드

| 코드 | HTTP | 의미 | 재시도 |
|---|---:|---|---|
| `VALIDATION_ERROR` | 422 | 필드 검증 실패 | 아니오 |
| `RESOURCE_NOT_FOUND` | 404 | 대상 없음 | 아니오 |
| `PROFILE_UNCHANGED` | 409 | 현재 프로필과 동일 | 아니오 |
| `ANALYSIS_NOT_APPROVED` | 409 | 승인 분석 필요 | 아니오 |
| `ANALYSIS_STALE` | 409 | 오래된 분석 사용 시도 | 아니오 |
| `STRATEGY_REQUIRED` | 409 | 콘텐츠 생성 전 전략 필요 | 아니오 |
| `VARIANT_LIMIT_REACHED` | 409 | AI 변형 3개 초과 | 아니오 |
| `INVALID_VARIANT_OWNER` | 400 | 다른 콘텐츠의 변형 선택 | 아니오 |
| `CALENDAR_DATE_OUT_OF_RANGE` | 422 | 캠페인 기간 밖 날짜 | 아니오 |
| `COMPARISON_SIZE_INVALID` | 422 | 비교 항목 2~3개 위반 | 아니오 |
| `AI_RATE_LIMITED` | 429 | AI 공급자 사용량 제한 | 예 |
| `AI_TIMEOUT` | 504 | AI 응답 시간 초과 | 예 |
| `AI_PROVIDER_UNAVAILABLE` | 503 | 공급자 일시 장애 | 예 |
| `AI_OUTPUT_INVALID` | 502 | 구조화 출력 검증 실패 | 예 |
| `AI_SAFETY_BLOCKED` | 400 | 안전 정책 차단 | 수정 후 가능 |
| `DATABASE_ERROR` | 500 | 저장 또는 조회 실패 | 상황에 따라 |

## 보안 원칙

- 사용자 메시지에 스택 추적, SQL, 공급자 원문 오류를 포함하지 않는다.
- 내부 로그는 `request_id`와 `generation_run_id`로 연결한다.
- `retryable=true`일 때만 UI가 동일 요청 재시도를 기본 제안한다.

