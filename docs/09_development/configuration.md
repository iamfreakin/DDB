# 환경 설정

예상 환경변수:

```text
APP_ENV=
DATABASE_URL=
TEXT_AI_PROVIDER=
TEXT_AI_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
OPENAI_IMAGE_MODEL=gpt-image-2
IMAGE_AI_PROVIDER=
IMAGE_AI_API_KEY=
GENERATED_IMAGE_PATH=
AI_REQUEST_TIMEOUT_SECONDS=
```

MVP의 권장 사용 방식은 사용자가 프론트엔드에 API 키를 직접 입력하고 요청 헤더로
전달하는 것이다. `.env`의 `OPENAI_API_KEY`는 로컬 개발 편의를 위한 선택 사항이며
저장소에 추가하지 않는다.

현재 웹은 `X-OpenAI-API-Key`, `X-OpenAI-Model`,
`X-OpenAI-Image-Model` 요청 헤더를 사용한다. 키는 브라우저 `sessionStorage`에만
보관하고 백엔드 DB와 로그에 저장하지 않는다. `GENERATED_IMAGE_PATH`를 생략하면
SQLite 파일 옆의 `generated_images` 디렉터리를 사용한다.
