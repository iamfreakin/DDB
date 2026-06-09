# 상태 모델

- 상태: Review

## 브랜드 분석 상태

```text
draft -> approved
draft -> stale
approved -> stale
stale -> superseded
```

| 상태 | 의미 |
|---|---|
| `draft` | 생성 또는 수정 중이며 캠페인의 기준으로 사용할 수 없음 |
| `approved` | 사용자가 승인해 캠페인의 기준으로 사용할 수 있음 |
| `stale` | 기반 프로필 변경으로 최신 정보와 일치하지 않을 수 있음 |
| `superseded` | 새 분석이 승인되어 더 이상 현재 분석이 아님 |

## 캠페인 상태

```text
draft -> strategy_ready -> content_ready -> active -> completed
                                  \-> archived
```

| 상태 | 의미 |
|---|---|
| `draft` | 캠페인 설정만 저장 |
| `strategy_ready` | 전략 생성 완료 |
| `content_ready` | 게시물과 캘린더 생성 완료 |
| `active` | 시작일이 도래하고 운영 중 |
| `completed` | 종료일이 지남 |
| `archived` | 사용자가 보관 처리 |

MVP에서 상태의 자동 시간 전환은 필수가 아니며 조회 시 계산할 수 있다.

## 콘텐츠 상태

```text
idea -> draft -> approved -> published
            \-> on_hold
```

| 상태 | 의미 |
|---|---|
| `idea` | 전략에서 생성된 주제만 존재 |
| `draft` | 게시 문구가 한 개 이상 존재 |
| `approved` | 사용자가 사용할 변형을 선택 |
| `published` | 사용자가 게시 완료로 표시 |
| `on_hold` | 현재 캘린더에서 사용하지 않음 |

## 생성 실행 상태

```text
pending -> running -> succeeded
                   -> failed
                   -> blocked
```

| 상태 | 의미 |
|---|---|
| `pending` | 요청 생성, 실행 전 |
| `running` | 외부 공급자 호출 또는 결과 처리 중 |
| `succeeded` | 결과 검증과 저장 완료 |
| `failed` | 시간 초과, 네트워크, 파싱 등으로 실패 |
| `blocked` | 안전 정책 또는 사전조건 위반으로 실행하지 않음 |

## 오래됨 전파

새 브랜드 프로필 버전이 생성되면 이전 프로필을 참조하는 승인 분석을 `stale`로
표시한다. 해당 분석을 참조하는 캠페인과 콘텐츠는 삭제하지 않고 응답의
`is_stale` 계산 필드로 경고한다.

