# 모듈 책임

| 모듈 | 책임 |
|---|---|
| `frontend` | 입력, 결과 표시, 편집, 비교 UI |
| `api` | HTTP 계약, 요청 검증, 응답 변환 |
| `domain` | 브랜드, 캠페인, 콘텐츠 규칙 |
| `services` | 유스케이스 실행과 트랜잭션 조정 |
| `agents` | 단계별 AI 판단과 Tool 조정 |
| `providers` | LLM 및 이미지 API 연동 |
| `repositories` | 프로젝트와 생성 결과 영속화 |
| `prompts` | 버전 관리되는 프롬프트 템플릿 |

