# FastAPI 명세

- 상태: Review
- Base URL: `/api/v1`
- 데이터 형식: `application/json`
- 날짜: `YYYY-MM-DD`
- 시각: UTC ISO 8601

## 공통 규칙

- 리소스 생성 성공은 `201 Created`를 반환한다.
- 조회 성공은 `200 OK`, 내용 없는 삭제는 `204 No Content`를 반환한다.
- AI 생성 요청은 MVP에서 동기식으로 처리한다.
- 생성 요청의 공급자 제한 시간은 기본 180초다.
- 오류는 `error_contract.md`의 공통 형식을 사용한다.
- 목록 API는 `limit`, `offset` 페이지네이션을 사용한다.
- 응답의 계산 필드는 데이터베이스에 저장하지 않을 수 있다.

## 상태 확인

| Method | Endpoint | 응답 |
|---|---|---|
| GET | `/health` | 앱, DB 상태 |

## 가게와 프로필

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/brands` | 가게와 첫 프로필 생성 | 201 |
| GET | `/brands` | 가게 목록 | 200 |
| GET | `/brands/{brand_id}` | 현재 프로필 포함 상세 조회 | 200 |
| PUT | `/brands/{brand_id}/profile` | 새 프로필 버전 생성 | 201 |
| DELETE | `/brands/{brand_id}` | 가게와 연결 데이터 삭제 | 204 |

`PUT /brands/{brand_id}/profile`은 기존 프로필을 덮어쓰지 않는다. 내용이 현재
버전과 동일하면 `409 PROFILE_UNCHANGED`를 반환한다.

## 브랜드 분석

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/brands/{brand_id}/analyses` | 현재 프로필 분석 생성 | 201 |
| GET | `/brands/{brand_id}/analyses` | 분석 이력 조회 | 200 |
| GET | `/analyses/{analysis_id}` | 분석 상세 조회 | 200 |
| PATCH | `/analyses/{analysis_id}` | 초안 분석 수정 | 200 |
| POST | `/analyses/{analysis_id}/approve` | 분석 승인 | 200 |

승인 시 같은 브랜드의 이전 승인 분석은 `superseded`로 변경한다. `stale` 분석은
바로 승인할 수 없으며 현재 프로필에서 새 분석을 생성해야 한다.

## 캠페인과 전략

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/campaigns` | 캠페인 설정 생성 | 201 |
| GET | `/campaigns` | 캠페인 목록 | 200 |
| GET | `/campaigns/{campaign_id}` | 캠페인 상세 조회 | 200 |
| PATCH | `/campaigns/{campaign_id}` | 이름, 시작일, 상품 등 수정 | 200 |
| DELETE | `/campaigns/{campaign_id}` | 캠페인 삭제 | 204 |
| POST | `/campaigns/{campaign_id}/strategies` | 4주 전략 생성 | 201 |
| GET | `/campaigns/{campaign_id}/strategies` | 전략 이력 조회 | 200 |

캠페인은 `approved` 분석만 참조할 수 있다. 전략을 다시 생성하면 버전이 증가하며
기존 콘텐츠는 자동 삭제하지 않고 `is_stale=true`로 계산한다.

## 콘텐츠와 변형

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/campaigns/{campaign_id}/contents:generate` | 게시물 8개 일괄 생성 | 201 |
| GET | `/contents` | 전체 저장 콘텐츠 검색 | 200 |
| GET | `/campaigns/{campaign_id}/contents` | 캠페인 게시물 조회 | 200 |
| GET | `/contents/{content_id}` | 변형 포함 게시물 상세 | 200 |
| PATCH | `/contents/{content_id}` | 게시물 상태 변경 | 200 |
| POST | `/contents/{content_id}/variants` | AI 문구 변형 생성 | 201 |
| POST | `/variants/{variant_id}/edits` | 사용자 수정본 생성 | 201 |
| POST | `/contents/{content_id}/selected-variant` | 사용할 변형 선택 | 200 |

AI origin 변형은 게시물당 3개를 초과할 수 없다. 사용자 수정본 생성은 AI 변형
개수 제한에 포함하지 않는다.

## 포스터 브리프

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/contents/{content_id}/poster-brief` | 포스터 브리프 생성 | 201 |
| GET | `/contents/{content_id}/poster-brief` | 브리프 조회 | 200 |
| PATCH | `/contents/{content_id}/poster-brief` | 브리프 수정 | 200 |
| POST | `/poster-briefs/{id}/images` | 실제 포스터 생성 | 201 |
| GET | `/poster-briefs/{id}/images` | 포스터 생성 이력 조회 | 200 |
| POST | `/generated-images/{id}/approve` | 포스터 승인 | 200 |
| GET | `/generated-images/{id}/file` | 합성본 또는 배경 PNG 조회·다운로드 | 200 |

이미지 생성 요청은 `confirm_cost=true`를 요구한다. `variant=background`를 지정하면
텍스트 합성 전 배경을 조회하며, `download=true`는 첨부 파일 응답을 반환한다.

## 캘린더

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/campaigns/{campaign_id}/calendar` | 4주 캘린더 생성 | 201 |
| GET | `/campaigns/{campaign_id}/calendar` | 캘린더 조회 | 200 |
| POST | `/campaigns/{campaign_id}/calendar:refresh` | 콘텐츠 상태와 승인 포스터 최신화 | 200 |
| PATCH | `/calendar-items/{item_id}` | 게시일 또는 상태 수정 | 200 |

게시일은 캠페인 기간 밖으로 이동할 수 없다. 조회와 최신화 응답은 연결된 콘텐츠,
선택 문구, 승인된 포스터 이미지 요약을 함께 반환한다.

## 결과 비교

| Method | Endpoint | 목적 | 성공 |
|---|---|---|---|
| POST | `/comparison-sets` | 2~3개 변형 비교 세트 생성 | 201 |
| GET | `/comparison-sets/{set_id}` | 비교 데이터 조회 | 200 |
| DELETE | `/comparison-sets/{set_id}` | 비교 세트 삭제 | 204 |

## 내보내기

| Method | Endpoint | Content-Type |
|---|---|---|
| GET | `/analyses/{analysis_id}/export.md` | `text/markdown; charset=utf-8` |
| GET | `/campaigns/{campaign_id}/calendar/export.csv` | `text/csv; charset=utf-8` |

캘린더 CSV에는 날짜, 채널, 유형, 주제, 선택 문구, 핵심 메시지, 상태, 승인 포스터
여부를 포함한다. 다운로드 파일명은 안전하게 정규화한 가게명과 생성일을 포함한다.

## 필터와 페이지네이션

### `GET /campaigns`

- `brand_id`
- `status`
- `limit`: 기본 20, 최대 100
- `offset`: 기본 0

### `GET /campaigns/{campaign_id}/contents`

- `status`
- `week_number`
- `content_type`

### `GET /contents`

- `brand_id`
- `campaign_id`
- `status`
- `content_type`
- `created_from`
- `created_to`
- `limit`: 기본 20, 최대 100
- `offset`: 기본 0

## OpenAPI

FastAPI가 생성한 `/docs`를 개발용 API 탐색기로 사용한다. Pydantic 모델의 필드
설명과 예시는 `request_response_schemas.md`를 기준으로 작성한다.
