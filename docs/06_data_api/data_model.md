# 데이터 모델

## 주요 엔터티

| 엔터티 | 주요 필드 |
|---|---|
| Brand | ID, 가게명, 업종, 생성일 |
| BrandProfileVersion | 입력 정보, 버전, 상태 |
| BrandAnalysis | 프로필 버전, 구조화 분석, 프롬프트 버전 |
| Campaign | 목표, 기간, 채널, 전략 |
| Content | 유형, 채널, 원본, 수정본, 상태 |
| GenerationRun | 공급자, 모델, 설정, 입력 참조, 오류 |
| CalendarItem | 날짜, 채널, 콘텐츠 ID, 상태 |
| ComparisonSet | 비교 대상 콘텐츠 ID 목록 |

구체적인 타입과 관계는 데이터베이스 설계 단계에서 확정한다.

