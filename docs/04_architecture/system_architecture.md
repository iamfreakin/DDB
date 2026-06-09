# 시스템 아키텍처

- 상태: Draft

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

최종 기술 선택은 MVP 배포 환경과 API 비용을 확인한 뒤 ADR로 확정한다.

