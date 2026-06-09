# 데이터 모델

- 상태: Review
- 저장소: SQLite
- 식별자: UUID 문자열
- 시각: UTC ISO 8601

## 엔터티 관계

```text
Brand 1 ── N BrandProfileVersion
BrandProfileVersion 1 ── N BrandAnalysis
BrandAnalysis 1 ── N Campaign
Campaign 1 ── N CampaignStrategy
Campaign 1 ── N Content
Content 1 ── N ContentVariant
Content 1 ── 0..1 PosterBrief
Campaign 1 ── N CalendarItem
Content 1 ── 0..N CalendarItem

GenerationRun 1 ── 0..N AI 생성 결과
ComparisonSet N ── M ContentVariant
```

## 주요 엔터티

| 엔터티 | 책임 |
|---|---|
| Brand | 가게의 고정 식별정보와 현재 프로필 버전 |
| BrandProfileVersion | 사용자가 입력한 가게 정보의 불변 버전 |
| BrandAnalysis | 특정 프로필 버전에서 생성·수정·승인된 브랜드 분석 |
| Campaign | 승인된 분석을 참조하는 4주 홍보 캠페인 |
| CampaignStrategy | AI가 생성한 캠페인 전략 버전 |
| Content | 게시물 슬롯, 주차, 주제, 상태 |
| ContentVariant | AI 원본 또는 사용자 수정 문구 |
| PosterBrief | 게시물용 이미지 및 포스터 제작 지시 |
| CalendarItem | 게시 예정일과 연결 콘텐츠 |
| GenerationRun | AI 요청의 실행 상태와 추적 메타데이터 |
| ComparisonSet | 사용자가 비교하기 위해 선택한 콘텐츠 변형 묶음 |

## 설계 원칙

- 프로필 수정은 기존 행을 덮어쓰지 않고 새 버전을 만든다.
- 승인된 분석은 어떤 프로필 버전을 사용했는지 항상 추적한다.
- AI 원본 콘텐츠는 수정하지 않는다. 사용자 편집은 새 변형으로 저장한다.
- JSON 배열과 구조화 결과는 MVP에서 SQLite `TEXT` JSON으로 저장한다.
- 도메인 계층에서는 JSON 문자열이 아니라 타입이 지정된 객체를 사용한다.
- 외래키 검사를 활성화하고 가게 삭제 시 연결 데이터를 함께 삭제한다.

## 삭제 규칙

| 부모 | 자식 | 규칙 |
|---|---|---|
| Brand | 모든 하위 데이터 | `ON DELETE CASCADE` |
| Campaign | 전략, 콘텐츠, 캘린더 | `ON DELETE CASCADE` |
| Content | 변형, 포스터, 캘린더 연결 | 변형·포스터 삭제, 캘린더는 함께 삭제 |
| GenerationRun | 생성 결과 | 실행 기록 삭제를 기본 제공하지 않음 |

## 동시성

MVP는 단일 사용자이므로 복잡한 잠금은 사용하지 않는다. 수정 API는
`updated_at`을 반환하고, 후속 다중 사용자 버전에서 낙관적 잠금을 추가한다.

