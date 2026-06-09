# Agent Tool 명세

| Tool | 입력 | 출력 |
|---|---|---|
| `get_brand_profile` | `brand_id`, `version` | 브랜드 프로필 |
| `save_brand_analysis` | 분석 결과 | 저장 ID |
| `get_campaign_context` | 캠페인 ID | 목표, 기간, 채널 |
| `save_content_draft` | 콘텐츠 초안 | 콘텐츠 ID |
| `list_saved_contents` | 필터 | 결과 목록 |
| `build_calendar` | 콘텐츠 목록, 기간 | 캘린더 |
| `validate_factual_claims` | 입력 정보, 생성 문구 | 위반 목록 |

각 Tool의 상세 스키마와 실패 코드는 API 및 구현 단계에서 확정한다.

