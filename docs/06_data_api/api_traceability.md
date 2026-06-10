# API 추적표

- 상태: Review
- 목적: 기능 요구사항을 API와 데이터 저장 구조에 연결한다.

| 요구사항 | 주요 API | 주요 테이블 |
|---|---|---|
| FR-101 | `POST /brands`, `PUT /brands/{id}/profile` | `brands`, `brand_profile_versions` |
| FR-102 | `POST /brands/{id}/analyses` | `brand_analyses`, `generation_runs` |
| FR-103 | `PATCH /analyses/{id}`, `POST /analyses/{id}/approve` | `brand_analyses` |
| FR-104 | `POST /campaigns` | `campaigns` |
| FR-105 | `POST /campaigns/{id}/strategies` | `campaign_strategies`, `generation_runs` |
| FR-106 | `POST /campaigns/{id}/contents:generate` | `contents`, `content_variants` |
| FR-107 | `POST /contents/{id}/variants` | `content_variants`, `generation_runs` |
| FR-108 | `POST /contents/{id}/poster-brief` | `poster_briefs`, `generation_runs` |
| FR-109 | `POST /campaigns/{id}/calendar`, `GET /campaigns/{id}/calendar`, `POST /campaigns/{id}/calendar:refresh` | `calendar_items`, `contents`, `generated_images` |
| FR-110 | `POST /variants/{id}/edits` | `content_variants` |
| FR-111 | `GET /contents`, `GET /contents/{id}` | 콘텐츠 관련 테이블 |
| FR-112 | `POST /comparison-sets`, `GET /comparison-sets/{id}` | 비교 관련 테이블 |
| FR-113 | `GET /analyses/{id}/export.md` | `brand_analyses` |
| FR-114 | `GET /campaigns/{id}/calendar/export.csv` | `calendar_items` |
| FR-115 | 모든 AI 생성 API | `generation_runs` |
| FR-116 | 프로필 생성 및 모든 조회 응답 | 버전 참조와 `is_stale` 계산 |
| FR-117 | `POST/GET /poster-briefs/{id}/images`, `POST /generated-images/{id}/approve`, `GET /generated-images/{id}/file` | `generated_images`, `generation_runs` |
