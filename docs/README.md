# 프로젝트 문서 인덱스

## 문서 지도

| 영역 | 목적 | 시작 문서 |
|---|---|---|
| `00_governance` | 문서 작성 및 의사결정 관리 | `documentation_rules.md` |
| `01_product` | 제품의 문제, 사용자, 범위 정의 | `product_brief.md` |
| `02_requirements` | 기능 및 품질 요구사항 정의 | `functional_requirements.md` |
| `03_ux` | 화면, 사용자 흐름, 메시지 정의 | `information_architecture.md` |
| `04_architecture` | 시스템 구조와 기술적 경계 정의 | `system_architecture.md` |
| `05_ai` | Agent, 프롬프트, 생성 및 검수 정책 | `agent_architecture.md` |
| `06_data_api` | 데이터 모델과 API 계약 정의 | `data_model.md` |
| `07_security` | 보안, 개인정보, 콘텐츠 안전 정의 | `security_policy.md` |
| `08_testing` | 기능 및 AI 품질 검증 정의 | `test_strategy.md` |
| `09_development` | 구현 순서와 작업 지시 관리 | `implementation_plan.md` |
| `10_operations` | 배포, 모니터링, 장애 대응 정의 | `deployment_guide.md` |
| `11_templates` | 서비스가 생성할 결과물 형식 정의 | `brand_report_template.md` |
| `12_reports` | AI 에이전트 활용 보고서와 서비스 사용방법 | `ai_agent_usage_report.md` |

## 현재 핵심 기준 문서

- 제품 경계: `01_product/product_scope.md`
- MVP 완료 정의: `01_product/mvp_definition.md`
- 미결정 사항: `01_product/open_questions.md`
- 기능 요구사항: `02_requirements/functional_requirements.md`
- 상세 화면: `03_ux/screen_specifications.md`
- 와이어프레임: `03_ux/wireframes.md`
- 요구사항 추적: `08_testing/requirements_traceability.md`
- 엔터티 관계: `06_data_api/data_model.md`
- SQLite 스키마: `06_data_api/database_schema.md`
- API 엔드포인트: `06_data_api/api_specification.md`
- 요청·응답 예시: `06_data_api/request_response_schemas.md`
- API 오류: `06_data_api/error_contract.md`
- 기능·API 연결: `06_data_api/api_traceability.md`
- AI 에이전트 활용 보고서: `12_reports/ai_agent_usage_report.md`
- 서비스 사용방법: `12_reports/service_usage_guide.md`
- 다른 컴퓨터 실행 준비: `12_reports/other_pc_setup_guide.md`

## 권장 작성 순서

1. 제품 개요와 MVP 범위를 확정한다.
2. 사용자 흐름과 기능 요구사항을 확정한다.
3. 화면 및 시스템 아키텍처를 설계한다.
4. AI Agent, 프롬프트, 생성 품질 기준을 정의한다.
5. 데이터 모델과 API 계약을 정의한다.
6. 테스트 기준을 요구사항과 연결한다.
7. 구현 계획과 단계별 과업 지시를 작성한다.

## 현재 결정된 MVP

```text
로그인 없는 단일 가게
-> 브랜드 분석
-> 4주 캠페인 전략
-> Instagram 게시물 8개
-> 포스터 브리프
-> 광고 포스터
-> 저장·비교
-> 캘린더 CSV 내보내기
```

## 문서 상태 표기

- `Draft`: 초안
- `Review`: 검토 중
- `Approved`: 구현 기준으로 승인
- `Deprecated`: 더 이상 사용하지 않음
