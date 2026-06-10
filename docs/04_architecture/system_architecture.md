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

- UI: Next.js App Router, React, TypeScript
- API: FastAPI
- 저장소: SQLite
- AI orchestration: LangGraph 또는 단순 서비스 파이프라인
- 텍스트 생성: 공급자 어댑터
- 이미지 생성: 후속 공급자 어댑터

## MVP 구조 결정

- Next.js와 FastAPI는 HTTP/JSON으로 통신한다.
- FastAPI가 입력 검증, 비즈니스 규칙, AI 호출, SQLite 저장을 담당한다.
- Next.js는 데이터베이스와 AI SDK에 직접 접근하지 않는다.
- Next.js Route Handler가 `/api/*` 요청을 FastAPI로 프록시한다.
- 브라우저는 동일 출처의 Next.js 경로만 호출하므로 별도 CORS 설정을 요구하지 않는다.
- API 키는 브라우저 탭의 `sessionStorage`에만 보관하고 AI 생성 요청 헤더에만 포함한다.
- AI 생성 요청은 동기식으로 시작하며 OpenAI 호출은 최대 180초, 프록시는 최대 200초 기다린다.
- 시간 초과와 연결 종료는 재시도 가능한 구조화 오류로 반환한다.
- 실제 공급자 연결 전 모의 AI Provider로 전체 흐름을 검증한다.
- 장시간 작업과 다중 사용자 요구가 생기면 작업 큐 방식으로 확장한다.

## 프론트엔드 경계

- `web/`: 기본 제품 프론트엔드
- `frontend/`: 이전 Streamlit 구현, 비교와 비상 실행을 위해 보존
- 홈페이지와 브랜드 작업실은 별도 URL로 구분한다.
- 작업실은 현재 선택한 단계의 데이터만 요청하고 콘텐츠 상세는 선택한 게시물만 렌더링한다.
