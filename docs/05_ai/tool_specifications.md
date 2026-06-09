# Agent Tool 명세

- 상태: Review

| Tool | 입력 | 출력 |
|---|---|---|
| `get_brand_profile` | `brand_id`, `version` | 브랜드 프로필 |
| `save_brand_analysis` | 프로필 버전 ID, 분석 결과 | 분석 ID |
| `get_campaign_context` | 캠페인 ID | 목표, 기간, 채널 |
| `save_content_variant` | 콘텐츠 ID, 구조화된 문구 | 변형 ID |
| `list_saved_contents` | 필터 | 결과 목록 |
| `build_calendar` | 콘텐츠 목록, 기간 | 캘린더 |
| `validate_factual_claims` | 입력 정보, 생성 문구 | 위반 목록 |

Tool은 FastAPI 엔드포인트와 동일한 Pydantic 도메인 모델을 사용한다. 상세 필드는
`request_response_schemas.md`, 실패 코드는 `error_contract.md`를 따른다.
