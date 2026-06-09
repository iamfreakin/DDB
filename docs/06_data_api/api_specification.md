# API 명세 초안

| Method | Endpoint | 목적 |
|---|---|---|
| POST | `/brands` | 가게 생성 |
| GET | `/brands/{id}` | 가게 조회 |
| PUT | `/brands/{id}` | 가게 수정 |
| POST | `/brands/{id}/analyze` | 브랜드 분석 생성 |
| POST | `/campaigns` | 캠페인 생성 |
| POST | `/campaigns/{id}/strategy` | 홍보 전략 생성 |
| POST | `/campaigns/{id}/contents` | 콘텐츠 생성 |
| POST | `/contents/{id}/variants` | 콘텐츠 변형 생성 |
| PUT | `/contents/{id}` | 사용자 수정본 저장 |
| POST | `/campaigns/{id}/calendar` | 캘린더 생성 |
| GET | `/contents` | 저장 결과 조회 |
| POST | `/comparisons` | 비교 세트 생성 |

요청 및 응답 JSON Schema는 기능별 구현 직전에 별도 문서 또는 OpenAPI로 확정한다.

