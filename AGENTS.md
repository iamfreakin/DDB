# AI Coding Agent Rules

## 프로젝트 목표

소상공인이 전문 마케팅 지식 없이도 일관된 브랜드 콘텐츠를 만들고 관리할 수
있는 웹 서비스를 개발한다.

## 작업 원칙

1. 작업 전 `docs/README.md`와 관련 설계 문서를 확인한다.
2. 요구사항 식별자와 테스트 식별자의 추적 관계를 유지한다.
3. 비즈니스 로직, AI 생성 로직, UI 로직을 분리한다.
4. LLM 및 이미지 생성 공급자는 교체 가능한 인터페이스로 구현한다.
5. 생성된 콘텐츠는 초안이며 사용자가 검토하고 수정할 수 있어야 한다.
6. API 키, 개인정보, 인증정보를 코드나 로그에 남기지 않는다.
7. 외부 API 실패, 시간 초과, 사용량 제한을 정상적인 실패로 처리한다.
8. 구현 완료 전 관련 테스트와 문서 갱신 여부를 확인한다.

## 문서 우선순위

충돌이 있을 경우 다음 순서로 해석한다.

1. `docs/01_product/product_scope.md`
2. `docs/02_requirements/functional_requirements.md`
3. `docs/04_architecture/system_architecture.md`
4. `docs/05_ai/`
5. `docs/09_development/implementation_plan.md`

