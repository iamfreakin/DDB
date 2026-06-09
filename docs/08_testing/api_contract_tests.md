# API 계약 테스트

- 상태: Draft

## 공통

- 모든 JSON 오류가 `error.code`, `error.message`, `request_id`, `retryable`을 가진다.
- 존재하지 않는 UUID는 `404 RESOURCE_NOT_FOUND`를 반환한다.
- 잘못된 UUID 또는 필드 형식은 `422 VALIDATION_ERROR`를 반환한다.
- 생성 성공 응답의 모든 ID는 UUID 형식이다.
- 모든 시각은 UTC ISO 8601 형식이다.

## 가게와 프로필

- 가게 생성은 `201`과 프로필 버전 1을 반환한다.
- 동일 내용으로 프로필 갱신 시 `409 PROFILE_UNCHANGED`를 반환한다.
- 변경된 프로필은 버전을 1 증가시키고 기존 버전을 보존한다.

## AI 생성

- 성공한 요청은 `generation_run_id`를 반환한다.
- 시간 초과는 `504 AI_TIMEOUT`, `retryable=true`를 반환한다.
- 구조화 출력 실패는 제한된 재시도 후 `502 AI_OUTPUT_INVALID`를 반환한다.
- 실패 실행도 `generation_runs`에 남는다.

## 캠페인과 콘텐츠

- 승인되지 않은 분석으로 캠페인을 만들면 `409 ANALYSIS_NOT_APPROVED`를 반환한다.
- 일괄 생성은 콘텐츠 8개를 반환한다.
- AI 변형 네 번째 생성은 `409 VARIANT_LIMIT_REACHED`를 반환한다.
- 다른 콘텐츠의 변형 선택은 `400 INVALID_VARIANT_OWNER`를 반환한다.

## 캘린더와 비교

- 캠페인 기간 밖 날짜는 `422 CALENDAR_DATE_OUT_OF_RANGE`를 반환한다.
- 비교 대상이 1개 또는 4개이면 `422 COMPARISON_SIZE_INVALID`를 반환한다.
- 비교 대상이 서로 다른 콘텐츠에 속하면 `400`을 반환한다.

