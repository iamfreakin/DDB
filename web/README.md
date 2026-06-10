# Next.js Frontend

Brand Studio의 기본 제품 프론트엔드다. 홈페이지와 브랜드 작업실을 분리하고
FastAPI 백엔드를 그대로 사용한다.

## 실행

먼저 프로젝트 루트에서 백엔드를 실행한다.

```powershell
.\scripts\run_backend.cmd
```

다른 터미널에서 Next.js를 실행한다.

```powershell
.\scripts\run_frontend.cmd
```

브라우저 주소는 `http://localhost:3000`이다.

## 직접 실행

```powershell
npm.cmd --prefix web run dev
```

## 환경변수

- `BACKEND_URL`: Next.js가 프록시할 FastAPI 주소
- 기본값: `http://127.0.0.1:8000`

`/api/*`는 Next.js Route Handler가 FastAPI로 전달한다. 게시물 일괄 생성처럼 오래
걸리는 AI 요청은 최대 200초까지 기다리고, 연결 종료와 시간 초과를 JSON 오류로
변환한다.

API 키는 환경변수나 파일에 저장하지 않는다. 사용자가 작업실에서 입력한 키는
브라우저 탭의 `sessionStorage`에만 보관되고 AI 생성 요청에만 전달된다.

## 검증

```powershell
npm.cmd --prefix web run lint
npm.cmd --prefix web run build
```
