# AI 소상공인 콘텐츠 제작실

가게 정보를 입력하면 브랜드를 분석하고, 홍보 전략과 SNS 콘텐츠, 포스터 브리프,
콘텐츠 캘린더를 생성하는 웹 기반 AI 서비스입니다.

## 핵심 흐름

```text
가게 정보 입력
-> 브랜드 분석
-> 홍보 전략 추천
-> SNS 게시물 생성
-> 광고 포스터 생성
-> 콘텐츠 캘린더 작성
-> 결과물 저장 및 비교
```

## 현재 단계

Next.js, FastAPI와 SQLite 기반의 MVP 수직 흐름을 구현했습니다. 현재 가게 프로필 생성,
브랜드 분석, 캠페인 전략, Instagram 게시물 8개, 포스터 브리프, 콘텐츠 캘린더,
결과 비교와 내보내기가 동작합니다.

상세 문서는 [`docs/README.md`](docs/README.md), 실행 방법은
[`backend/README.md`](backend/README.md)와 [`frontend/README.md`](frontend/README.md)에서
확인할 수 있습니다.

## 실행

```powershell
.\scripts\run_backend.cmd
```

다른 터미널에서:

```powershell
.\scripts\run_frontend.cmd
```

브라우저에서 `http://localhost:3000`을 연다.

기존 Streamlit 화면은 비교 및 비상용으로 보존한다.

```powershell
.\scripts\run_frontend_legacy.cmd
```

레거시 화면 주소는 `http://localhost:8501`이다.

## GPT API 키 방식

- API 키는 사용자가 브랜드 작업실의 `AI 설정`에 직접 입력한다.
- 키는 브라우저 탭의 `sessionStorage`에만 있고 백엔드 데이터베이스에 저장하지 않는다.
- 생성 요청 때만 `X-OpenAI-API-Key` 헤더로 백엔드에 전달한다.
- 키를 입력하지 않으면 Mock 생성기로 전체 흐름을 시연할 수 있다.

## 문서화 원칙

- 프로젝트의 결정 사항은 관련 문서에 기록합니다.
- 한 문서는 하나의 주요 책임만 다룹니다.
- 요구사항에는 식별자를 부여해 설계 및 테스트와 연결합니다.
- 확정되지 않은 내용은 사실처럼 기록하지 않고 `TBD`로 표시합니다.
- 구현 변경으로 문서와 코드가 달라지면 같은 작업에서 함께 수정합니다.
