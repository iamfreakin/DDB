# 시스템 아키텍처

- 상태: Review

## 권장 논리 구조

```text
Web UI
  -> Application Service
      -> Brand Analysis Service
      -> Strategy Service
      -> Content Service
      -> Calendar Service
      -> Comparison Service
          -> AI Provider Adapter
          -> Repository
```

## 초기 기술 방향

- UI: Streamlit
- API: FastAPI
- 저장소: SQLite
- AI orchestration: LangGraph 또는 단순 서비스 파이프라인
- 텍스트 생성: 공급자 어댑터
- 이미지 생성: 후속 공급자 어댑터

## MVP 구조 결정

- FastAPI와 Streamlit은 HTTP/JSON으로 통신한다.
- FastAPI가 입력 검증, 비즈니스 규칙, AI 호출, SQLite 저장을 담당한다.
- Streamlit은 데이터베이스와 AI SDK에 직접 접근하지 않는다.
- AI 생성 요청은 60초 제한의 동기식 API로 시작한다.
- 실제 공급자 연결 전 모의 AI Provider로 전체 흐름을 검증한다.
- 장시간 작업과 다중 사용자 요구가 생기면 작업 큐 방식으로 확장한다.
