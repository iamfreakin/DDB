# Agent 아키텍처

- 상태: Draft

## 역할

| Agent | 책임 |
|---|---|
| Brand Analyst | 입력에서 타깃, 강점, 보이스, 핵심 키워드 도출 |
| Marketing Strategist | 목표와 기간에 맞는 캠페인 전략 추천 |
| Copywriter | 채널별 게시물 문구와 CTA 생성 |
| Visual Director | 포스터 콘셉트와 이미지 생성 프롬프트 작성 |
| Calendar Planner | 콘텐츠를 날짜와 채널에 배치 |
| Quality Reviewer | 사실성, 브랜드 일관성, 금지 표현 검수 |

## MVP 조정

각 역할을 별도 LLM Agent로 구현할 필요는 없다. 초기에는 독립 프롬프트와
구조화된 입출력을 가진 서비스 단계로 구현하고, 분기와 재계획이 필요한 부분만
Agent orchestration을 적용한다.

