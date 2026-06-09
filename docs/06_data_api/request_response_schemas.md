# 요청 및 응답 스키마

- 상태: Review
- 목적: Pydantic 요청·응답 모델 구현 기준

## 공통 타입

### 캠페인 목표

```text
new_product
new_customer
repeat_visit
seasonal_event
brand_awareness
```

### 분위기 예시

```text
warm, friendly, emotional, premium, playful, clean, trustworthy
```

### 페이지 응답

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

## 가게 생성

`POST /brands`

```json
{
  "name": "은혜 커피",
  "industry": "cafe",
  "profile": {
    "products": ["수제 크림라떼", "아메리카노"],
    "target_customers": "조용히 쉬거나 대화할 공간을 찾는 20~30대 지역 주민",
    "strengths": "매장에서 직접 만드는 크림과 따뜻한 동네 분위기",
    "desired_moods": ["warm", "friendly", "emotional"],
    "region": "서울 성북구",
    "price_range": "medium",
    "existing_copy": null,
    "avoid_expressions": ["무조건", "최고"],
    "campaign_facts": {
      "cream_latte_price": "6500원"
    }
  }
}
```

응답:

```json
{
  "id": "uuid",
  "name": "은혜 커피",
  "industry": "cafe",
  "active_profile": {
    "id": "uuid",
    "version": 1,
    "products": ["수제 크림라떼", "아메리카노"],
    "target_customers": "조용히 쉬거나 대화할 공간을 찾는 20~30대 지역 주민",
    "strengths": "매장에서 직접 만드는 크림과 따뜻한 동네 분위기",
    "desired_moods": ["warm", "friendly", "emotional"],
    "region": "서울 성북구",
    "price_range": "medium",
    "existing_copy": null,
    "avoid_expressions": ["무조건", "최고"],
    "campaign_facts": {
      "cream_latte_price": "6500원"
    },
    "created_at": "2026-06-09T12:00:00Z"
  },
  "created_at": "2026-06-09T12:00:00Z",
  "updated_at": "2026-06-09T12:00:00Z"
}
```

## 브랜드 분석 생성

`POST /brands/{brand_id}/analyses`

```json
{
  "regenerate": false
}
```

응답 핵심:

```json
{
  "id": "uuid",
  "profile_version_id": "uuid",
  "status": "draft",
  "brand_summary": "동네의 편안함과 수제 메뉴를 함께 전하는 카페",
  "target_segments": ["20~30대 지역 주민"],
  "customer_needs": ["편안한 휴식", "개성 있는 음료"],
  "value_proposition": "직접 만든 크림 메뉴를 따뜻한 공간에서 즐기는 경험",
  "differentiators": ["수제 크림", "동네 중심 분위기"],
  "brand_voice": ["따뜻한", "솔직한", "친근한"],
  "recommended_keywords": ["동네카페", "수제크림", "잠깐의여유"],
  "avoid_expressions": ["무조건", "최고"],
  "missing_information": ["신메뉴 판매 시작일"],
  "generation_run_id": "uuid",
  "created_at": "2026-06-09T12:01:00Z"
}
```

## 분석 수정과 승인

`PATCH /analyses/{analysis_id}`는 수정 가능한 분석 필드만 받는다. `status`,
`profile_version_id`, 생성 메타데이터는 요청으로 변경할 수 없다.

`POST /analyses/{analysis_id}/approve`는 본문 없이 호출하며 승인된 분석을 반환한다.

## 캠페인 생성

`POST /campaigns`

```json
{
  "brand_id": "uuid",
  "brand_analysis_id": "uuid",
  "name": "여름 크림라떼 4주 캠페인",
  "goal": "new_product",
  "start_date": "2026-07-01",
  "highlighted_products": ["수제 크림라떼"],
  "required_facts": {
    "price": "6500원",
    "sales_period": "2026-07-01~2026-07-31"
  }
}
```

서버는 `end_date`, `channel`, `posts_per_week`, 초기 `status`를 계산한다.

## 전략 생성

`POST /campaigns/{campaign_id}/strategies`

```json
{
  "regenerate": false
}
```

응답에는 다음이 포함된다.

```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "version": 1,
  "core_message": "여름의 달콤한 휴식을 동네에서 만나보세요.",
  "weekly_goals": [
    {"week": 1, "goal": "신메뉴 인지"},
    {"week": 2, "goal": "재료와 특징 소개"},
    {"week": 3, "goal": "방문 동기 강화"},
    {"week": 4, "goal": "기간 종료 전 방문 유도"}
  ],
  "content_pillars": ["메뉴", "제작 과정", "공간", "방문 유도"],
  "post_topics": [
    {"sequence": 1, "week": 1, "topic": "신메뉴 첫 공개", "content_type": "product"}
  ],
  "risk_notes": ["가격과 판매 기간은 입력값만 사용"],
  "generation_run_id": "uuid"
}
```

`post_topics`는 실제 응답에서 정확히 8개다.

## 게시물 일괄 생성

`POST /campaigns/{campaign_id}/contents:generate`

```json
{
  "strategy_id": "uuid",
  "variants_per_content": 1,
  "length": "medium",
  "emoji_level": "moderate",
  "hashtag_count": 7
}
```

제약:

- `variants_per_content`: 1~3
- `hashtag_count`: 5~10
- 캠페인당 콘텐츠 슬롯: 정확히 8개

응답은 콘텐츠 8개와 각 콘텐츠의 초기 변형을 포함한다.

## 사용자 수정본

`POST /variants/{variant_id}/edits`

```json
{
  "opening_line": "여름 한 잔, 동네에서 준비했어요.",
  "body": "직접 만든 부드러운 크림을 올린 여름 한정 라떼입니다.",
  "cta": "7월 한 달 동안 매장에서 만나보세요.",
  "hashtags": ["은혜커피", "성북구카페", "크림라떼", "여름메뉴", "동네카페"],
  "image_concept": "창가에 놓인 크림라떼와 여름 햇빛"
}
```

응답의 `origin`은 `user_edit`, `source_variant_id`는 원본 변형 ID다.

## 사용할 변형 선택

`POST /contents/{content_id}/selected-variant`

```json
{
  "variant_id": "uuid"
}
```

변형은 해당 콘텐츠에 속해야 한다. 성공하면 콘텐츠 상태를 `approved`로 변경할 수
있다.

## 캘린더 생성

`POST /campaigns/{campaign_id}/calendar`

```json
{
  "preferred_weekdays": [2, 5]
}
```

요일은 ISO 기준 월요일 1, 일요일 7이다. 응답은 8개의 캘린더 항목을 반환한다.

## 캘린더 항목 변경

`PATCH /calendar-items/{item_id}`

```json
{
  "scheduled_date": "2026-07-04",
  "status": "draft"
}
```

두 필드 중 하나 이상이 필요하다.

## 비교 세트 생성

`POST /comparison-sets`

```json
{
  "name": "첫 게시물 문구 비교",
  "variant_ids": ["uuid-a", "uuid-b", "uuid-c"]
}
```

`variant_ids`는 2~3개이며 같은 콘텐츠의 변형이어야 한다.

