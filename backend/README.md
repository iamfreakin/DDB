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
- 공통 오류 응답
