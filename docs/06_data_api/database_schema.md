# SQLite 데이터베이스 스키마

- 상태: Review
- 목적: ORM 모델과 마이그레이션 작성의 기준을 제공한다.

## 공통 규칙

- 기본키는 UUID 문자열을 저장하는 `TEXT`다.
- 불리언은 `INTEGER`의 `0`, `1`을 사용한다.
- 날짜는 `YYYY-MM-DD`, 시각은 UTC ISO 8601 문자열로 저장한다.
- JSON 필드는 유효한 JSON 문자열이어야 한다.
- 애플리케이션 시작 시 `PRAGMA foreign_keys = ON`을 실행한다.

## `brands`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `name` | TEXT | NOT NULL, 1~50자 |
| `industry` | TEXT | NOT NULL |
| `active_profile_version_id` | TEXT | NULL, FK, SET NULL, DEFERRABLE |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

## `brand_profile_versions`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `brand_id` | TEXT | NOT NULL, FK, CASCADE |
| `version` | INTEGER | NOT NULL, 1 이상 |
| `products_json` | TEXT | NOT NULL, 1~5개 |
| `target_customers` | TEXT | NOT NULL, 10~300자 |
| `strengths` | TEXT | NOT NULL, 10~500자 |
| `desired_moods_json` | TEXT | NOT NULL, 1~3개 |
| `region` | TEXT | NULL |
| `price_range` | TEXT | NULL |
| `existing_copy` | TEXT | NULL |
| `avoid_expressions_json` | TEXT | NOT NULL, 기본 `[]` |
| `campaign_facts_json` | TEXT | NOT NULL, 기본 `{}` |
| `content_hash` | TEXT | NOT NULL |
| `created_at` | TEXT | NOT NULL |

고유 제약: `(brand_id, version)`.

## `brand_analyses`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `profile_version_id` | TEXT | NOT NULL, FK, CASCADE |
| `status` | TEXT | NOT NULL, 상태 enum |
| `brand_summary` | TEXT | NOT NULL |
| `target_segments_json` | TEXT | NOT NULL |
| `customer_needs_json` | TEXT | NOT NULL |
| `value_proposition` | TEXT | NOT NULL |
| `differentiators_json` | TEXT | NOT NULL |
| `brand_voice_json` | TEXT | NOT NULL, 3개 |
| `recommended_keywords_json` | TEXT | NOT NULL |
| `avoid_expressions_json` | TEXT | NOT NULL |
| `missing_information_json` | TEXT | NOT NULL |
| `generation_run_id` | TEXT | NULL, FK |
| `approved_at` | TEXT | NULL |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

한 브랜드에서 현재 `approved` 분석은 애플리케이션 규칙상 하나만 유지한다.

## `campaigns`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `brand_id` | TEXT | NOT NULL, FK, CASCADE |
| `brand_analysis_id` | TEXT | NOT NULL, FK |
| `name` | TEXT | NOT NULL, 1~100자 |
| `goal` | TEXT | NOT NULL, 목표 enum |
| `start_date` | TEXT | NOT NULL |
| `end_date` | TEXT | NOT NULL, 시작일 + 27일 |
| `channel` | TEXT | NOT NULL, 기본 `instagram_feed` |
| `posts_per_week` | INTEGER | NOT NULL, 기본 2 |
| `highlighted_products_json` | TEXT | NOT NULL |
| `required_facts_json` | TEXT | NOT NULL, 기본 `{}` |
| `status` | TEXT | NOT NULL |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

## `campaign_strategies`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `campaign_id` | TEXT | NOT NULL, FK, CASCADE |
| `version` | INTEGER | NOT NULL |
| `core_message` | TEXT | NOT NULL |
| `weekly_goals_json` | TEXT | NOT NULL, 4개 |
| `content_pillars_json` | TEXT | NOT NULL, 3~4개 |
| `post_topics_json` | TEXT | NOT NULL, 8개 |
| `risk_notes_json` | TEXT | NOT NULL |
| `generation_run_id` | TEXT | NULL, FK |
| `created_at` | TEXT | NOT NULL |

고유 제약: `(campaign_id, version)`.

## `contents`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `campaign_id` | TEXT | NOT NULL, FK, CASCADE |
| `strategy_id` | TEXT | NOT NULL, FK |
| `sequence` | INTEGER | NOT NULL, 1~8 |
| `week_number` | INTEGER | NOT NULL, 1~4 |
| `content_type` | TEXT | NOT NULL |
| `topic` | TEXT | NOT NULL |
| `core_message` | TEXT | NOT NULL |
| `status` | TEXT | NOT NULL |
| `selected_variant_id` | TEXT | NULL, FK, SET NULL, DEFERRABLE |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

고유 제약: `(campaign_id, sequence)`.

`active_profile_version_id`와 `selected_variant_id`처럼 부모가 자신의 하위 리소스를
가리키는 외래키는 `DEFERRABLE INITIALLY DEFERRED`로 정의해 생성·삭제 순서의
순환 문제를 피한다.

## `content_variants`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `content_id` | TEXT | NOT NULL, FK, CASCADE |
| `source_variant_id` | TEXT | NULL, 자기 참조 FK |
| `origin` | TEXT | NOT NULL, `ai` 또는 `user_edit` |
| `variant_number` | INTEGER | NOT NULL |
| `tone` | TEXT | NOT NULL |
| `opening_line` | TEXT | NOT NULL |
| `body` | TEXT | NOT NULL |
| `cta` | TEXT | NOT NULL |
| `hashtags_json` | TEXT | NOT NULL, 5~10개 |
| `image_concept` | TEXT | NOT NULL |
| `quality_warnings_json` | TEXT | NOT NULL |
| `generation_run_id` | TEXT | NULL, FK |
| `created_at` | TEXT | NOT NULL |

AI origin 변형은 콘텐츠당 최대 3개다. 사용자 편집본은 이 제한에 포함하지 않는다.

## `poster_briefs`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `content_id` | TEXT | NOT NULL, UNIQUE, FK, CASCADE |
| `headline` | TEXT | NOT NULL |
| `supporting_text` | TEXT | NULL |
| `visual_mood` | TEXT | NOT NULL |
| `colors_json` | TEXT | NOT NULL |
| `layout_description` | TEXT | NOT NULL |
| `image_prompt` | TEXT | NOT NULL |
| `negative_prompt` | TEXT | NULL |
| `aspect_ratio` | TEXT | NOT NULL |
| `generation_run_id` | TEXT | NULL, FK |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

## `generated_images`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `poster_brief_id` | TEXT | NOT NULL, FK, CASCADE |
| `version` | INTEGER | NOT NULL, 1 이상 |
| `status` | TEXT | NOT NULL, `draft`, `approved`, `superseded` |
| `provider` | TEXT | NOT NULL |
| `model` | TEXT | NOT NULL |
| `prompt` | TEXT | NOT NULL |
| `aspect_ratio` | TEXT | NOT NULL |
| `width` | INTEGER | NOT NULL |
| `height` | INTEGER | NOT NULL |
| `background_path` | TEXT | NOT NULL |
| `composed_path` | TEXT | NOT NULL |
| `generation_run_id` | TEXT | NULL, FK |
| `approved_at` | TEXT | NULL |
| `created_at` | TEXT | NOT NULL |

고유 제약: `(poster_brief_id, version)`. 한 브리프의 현재 `approved` 이미지는
애플리케이션 규칙상 하나만 유지한다. DB에는 파일 자체나 API 키가 아닌 생성 파일의
상대 경로만 저장한다.

## `calendar_items`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `campaign_id` | TEXT | NOT NULL, FK, CASCADE |
| `content_id` | TEXT | NOT NULL, UNIQUE, FK, CASCADE |
| `scheduled_date` | TEXT | NOT NULL |
| `status` | TEXT | NOT NULL |
| `created_at` | TEXT | NOT NULL |
| `updated_at` | TEXT | NOT NULL |

`scheduled_date`는 캠페인의 시작일과 종료일 사이여야 한다.

## `generation_runs`

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | TEXT | PK |
| `generation_type` | TEXT | NOT NULL |
| `status` | TEXT | NOT NULL |
| `provider` | TEXT | NOT NULL |
| `model` | TEXT | NOT NULL |
| `prompt_name` | TEXT | NOT NULL |
| `prompt_version` | TEXT | NOT NULL |
| `prompt_hash` | TEXT | NOT NULL |
| `input_reference_json` | TEXT | NOT NULL |
| `settings_json` | TEXT | NOT NULL |
| `input_tokens` | INTEGER | NULL |
| `output_tokens` | INTEGER | NULL |
| `estimated_cost` | REAL | NULL |
| `error_code` | TEXT | NULL |
| `error_message` | TEXT | NULL, 민감정보 제거 |
| `started_at` | TEXT | NOT NULL |
| `completed_at` | TEXT | NULL |

## `comparison_sets`와 `comparison_members`

`comparison_sets`는 `id`, `name`, `created_at`을 가진다.
`comparison_members`는 `comparison_set_id`, `content_variant_id`, `position`을
가지며 비교 세트당 2~3개만 허용한다.

비교 대상이 같은 콘텐츠에 속하는지와 항목 개수는 트랜잭션 안의 애플리케이션
규칙으로 검증한다.

## 권장 인덱스

- `brand_profile_versions(brand_id, version DESC)`
- `brand_analyses(profile_version_id, status)`
- `campaigns(brand_id, created_at DESC)`
- `contents(campaign_id, sequence)`
- `content_variants(content_id, created_at DESC)`
- `generated_images(poster_brief_id, version DESC)`
- `calendar_items(campaign_id, scheduled_date)`
- `generation_runs(status, started_at DESC)`
