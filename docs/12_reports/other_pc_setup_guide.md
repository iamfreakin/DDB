# 다른 컴퓨터 실행 준비 가이드

- 상태: Review
- 대상: 프로젝트 파일을 다른 컴퓨터로 옮겨 실행하려는 사용자
- 기준 환경: Windows 10/11, PowerShell 또는 명령 프롬프트

## 1. 개요

이 프로젝트는 FastAPI 백엔드와 Next.js 프론트엔드로 구성되어 있다.
다른 컴퓨터에서 실행하려면 Python, Node.js, 프로젝트 의존성을 설치해야 한다.

API 키가 없어도 Mock 생성기로 대부분의 흐름을 시연할 수 있다. 실제 OpenAI API를
사용하려면 웹 화면에서 사용자가 직접 API 키를 입력한다.

## 2. 필수 설치 프로그램

### Python

백엔드 실행에 필요하다.

- 권장 버전: Python 3.11 이상
- 설치 시 `Add Python to PATH` 옵션을 체크한다.

설치 확인:

```powershell
python --version
```

만약 `python` 명령이 동작하지 않으면 다음 명령을 확인한다.

```powershell
py --version
```

### Node.js

Next.js 프론트엔드 실행에 필요하다.

- 권장 버전: Node.js LTS
- Node.js를 설치하면 `npm`도 함께 설치된다.

설치 확인:

```powershell
node --version
npm --version
```

## 3. 프로젝트 파일 옮기기

프로젝트 폴더 전체를 다른 컴퓨터로 복사한다.

예시 폴더:

```text
C:\Users\user\Documents\은혜과제
```

복사할 때 포함해야 하는 주요 폴더와 파일은 다음과 같다.

```text
backend/
docs/
scripts/
web/
frontend/
requirements.txt
README.md
.env.example
```

`node_modules/`, `.next/`, `data/`는 반드시 복사하지 않아도 된다.

- `node_modules/`: 새 컴퓨터에서 `npm install`로 다시 생성
- `.next/`: Next.js 빌드 결과물, 다시 생성 가능
- `data/`: SQLite DB와 생성 이미지 저장 위치. 기존 데이터까지 옮기고 싶을 때만 복사

## 4. 백엔드 의존성 설치

프로젝트 루트에서 실행한다.

```powershell
pip install -r requirements.txt
```

`python` 명령이 안 되면 다음처럼 실행할 수 있다.

```powershell
py -m pip install -r requirements.txt
```

설치되는 주요 패키지는 다음과 같다.

- FastAPI
- Uvicorn
- Pydantic
- Pillow

Pillow는 포스터 이미지에 한글 문구를 합성할 때 사용한다.

## 5. 프론트엔드 의존성 설치

프로젝트 루트에서 다음 명령을 실행한다.

```powershell
cd web
npm install
cd ..
```

이 과정에서 `web/node_modules` 폴더가 생성된다.

## 6. 실행 방법

터미널을 두 개 연다.

### 터미널 1: 백엔드 실행

프로젝트 루트에서 실행한다.

```powershell
.\scripts\run_backend.cmd
```

정상 실행되면 기본 주소는 다음과 같다.

```text
http://localhost:8000
```

개발용 API 문서는 다음 주소에서 확인할 수 있다.

```text
http://localhost:8000/docs
```

### 터미널 2: 프론트엔드 실행

프로젝트 루트에서 실행한다.

```powershell
.\scripts\run_frontend.cmd
```

정상 실행되면 브라우저에서 다음 주소로 접속한다.

```text
http://localhost:3000
```

## 7. API 키 설정

API 키는 파일이나 코드에 넣지 않는다.

웹 화면에서 브랜드 작업실에 들어간 뒤 왼쪽의 `AI 설정`을 열고 입력한다.

| 항목 | 기본값 또는 설명 |
|---|---|
| OpenAI API 키 | 사용자가 직접 입력 |
| 텍스트 모델 | `gpt-5-mini` |
| 이미지 모델 | `gpt-image-2` |

입력한 키는 현재 브라우저 탭의 `sessionStorage`에만 저장된다. 백엔드 DB나 로그에는
저장되지 않는다.

API 키를 입력하지 않으면 Mock 생성기가 사용된다. 따라서 발표나 테스트는 API 키 없이도
진행할 수 있다.

## 8. 자동 생성되는 파일과 폴더

처음 실행하면 다음 폴더와 파일이 자동으로 생성될 수 있다.

```text
data/app.db
data/generated_images/
web/.next/
web/node_modules/
```

각 항목의 의미는 다음과 같다.

| 경로 | 설명 |
|---|---|
| `data/app.db` | SQLite 데이터베이스 |
| `data/generated_images/` | 생성된 포스터 이미지 저장 위치 |
| `web/.next/` | Next.js 개발·빌드 결과 |
| `web/node_modules/` | 프론트엔드 의존성 |

## 9. 선택 사항: 레거시 Streamlit 화면

현재 메인 프론트엔드는 `web/` 폴더의 Next.js 버전이다.

기존 Streamlit 화면도 실행하려면 다음 의존성을 추가로 설치한다.

```powershell
pip install -r frontend/requirements.txt
```

실행:

```powershell
.\scripts\run_frontend_legacy.cmd
```

주소:

```text
http://localhost:8501
```

## 10. 자주 생기는 문제

### `python` 명령을 찾을 수 없음

Python 설치 시 PATH 등록이 안 된 경우다.

해결 방법:

```powershell
py --version
py -m pip install -r requirements.txt
```

또는 Python을 다시 설치하면서 `Add Python to PATH`를 체크한다.

### `npm` 실행이 막힘

PowerShell 실행 정책 때문에 `npm.ps1`이 막힐 수 있다.

해결 방법:

```powershell
npm.cmd install
npm.cmd run dev
```

프로젝트의 `.cmd` 실행 스크립트를 사용하면 대부분 이 문제를 피할 수 있다.

### 포트가 이미 사용 중

기본 포트는 다음과 같다.

| 서비스 | 포트 |
|---|---|
| 백엔드 | 8000 |
| 프론트엔드 | 3000 |
| 레거시 Streamlit | 8501 |

해당 포트를 다른 프로그램이 사용 중이면 서버 실행이 실패할 수 있다. 기존 서버를
종료하거나 다른 포트로 실행해야 한다.

### 이미지 생성이 느림

실제 OpenAI 이미지 API를 사용할 때는 생성 시간이 걸릴 수 있다. 비용과 시간이
발생하므로 이미지 생성 버튼을 누르기 전에 안내 문구를 확인한다.

API 키가 없으면 Mock 이미지가 즉시 생성된다.

## 11. 실행 확인 체크리스트

다른 컴퓨터에서 실행하기 전 다음을 확인한다.

- Python 3.11 이상 설치
- Node.js LTS 설치
- `pip install -r requirements.txt` 완료
- `web` 폴더에서 `npm install` 완료
- `.\scripts\run_backend.cmd` 실행 성공
- `.\scripts\run_frontend.cmd` 실행 성공
- `http://localhost:3000` 접속 성공
- API 키 없이 Mock 생성 흐름 확인
- 실제 API 사용 시 웹 화면의 `AI 설정`에 키 입력

## 12. 발표용 권장 실행 방식

수업 발표나 시연에서는 API 키 없이 Mock 모드로 먼저 전체 흐름을 확인하는 것을
추천한다.

이후 실제 API 키가 준비되어 있다면 다음 기능만 실제 API로 보여주면 된다.

- 브랜드 분석 생성
- 게시물 생성
- 포스터 이미지 생성

이렇게 하면 비용과 실패 가능성을 줄이면서도 전체 서비스 흐름을 안정적으로 보여줄
수 있다.
