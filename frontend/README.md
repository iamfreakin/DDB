# Frontend

FastAPI 백엔드를 호출하는 Streamlit 웹 UI다. Step 2(브랜드 프로필·분석) 흐름을 다룬다.

## 실행

먼저 백엔드를 실행한다.

```powershell
.\scripts\run_backend.cmd
```

그다음 프론트엔드를 실행한다.

```powershell
.\scripts\run_frontend.cmd
```

브라우저에서 `http://localhost:8501`이 자동으로 열린다.

## 의존성 설치 (최초 1회)

```powershell
python -m pip install -r frontend/requirements.txt
```

## 설정

- 백엔드 주소는 사이드바에서 바꾸거나 환경변수 `BACKEND_URL`로 지정한다.
- 기본값은 `http://localhost:8000`이다.

## 현재 화면 범위

- 백엔드 연결 상태 확인
- 가게 생성, 목록, 선택
- 브랜드 프로필 입력과 새 버전 생성
- AI 브랜드 분석 생성, 수정, 승인
