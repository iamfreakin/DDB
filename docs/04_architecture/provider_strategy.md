# AI 공급자 연동 전략

## 목표

텍스트 및 이미지 생성 API가 변경되어도 도메인과 UI를 수정하지 않도록 한다.

## 인터페이스 개념

```text
TextGenerationProvider.generate(request) -> TextGenerationResult
ImageGenerationProvider.generate(request) -> ImageGenerationResult
```

## 공통 처리

- 시간 초과
- 재시도 가능 오류
- 사용량 제한
- 안전 필터 거절
- 비용 및 토큰 메타데이터
- 공급자 응답을 내부 결과 형식으로 변환

