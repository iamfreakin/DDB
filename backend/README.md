# Backend

## 실행

```powershell
.\scripts\run_backend.cmd
```

개발용 API 문서는 `http://localhost:8000/docs`에서 확인한다.

## 테스트

```powershell
.\scripts\test_backend.cmd
```

스크립트는 PATH의 `python`, `py`, Codex 번들 Python 순서로 실행 파일을 찾는다.
`.cmd` 진입점은 현재 PowerShell 실행 정책을 변경하지 않는다.

## 현재 구현 범위

- 상태 확인
- 가게 생성, 목록, 상세 조회
- 브랜드 프로필 버전 생성
- Mock AI 브랜드 분석 생성
- 브랜드 분석 수정 및 승인
- 캠페인 생성
- 4주 전략 생성
- Instagram 게시물 8개 생성
- 게시물 변형 생성, 선택, 사용자 수정본 저장
- 포스터 브리프 생성 및 수정
- Mock 또는 OpenAI 이미지 배경 생성
- 정확한 한글 문구 합성, PNG 미리보기·다운로드·승인
- 콘텐츠 캘린더 생성
- 비교 세트 생성
- 브랜드 보고서 Markdown 및 캘린더 CSV 내보내기
- 공통 오류 응답

## OpenAI 연동

생성 요청에 `X-OpenAI-API-Key` 헤더가 있으면 OpenAI Responses API를 사용한다.
헤더가 없으면 Mock Provider를 사용한다.

선택 헤더:

```text
X-OpenAI-Model: gpt-5-mini
X-OpenAI-Image-Model: gpt-image-2
```

API 키는 요청 처리 중 메모리에만 존재하고 DB에 저장하지 않는다.
이미지 생성 결과는 기본적으로 `data/generated_images`에 저장하며 DB에는 상대
파일 경로만 기록한다. API 키가 없으면 로컬 Mock 포스터를 생성한다.
