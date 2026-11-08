# land-map / INVESTMENT MAP

이 저장소의 루트는 **운영 중인 정적 투자지도**(index.html, data_*.json, inline_data.js, netlify/)다. 사용자 승인 없이 수정하지 않는다.
여러 Claude 작업창(A·B·C·D·E·H)의 공통 인계 저장소는 `_HANDOFF/` 에 있다.

## 인계 시작 규칙
사용자가 **"INVESTMENT MAP <역할> 인계받고 이어서 작업해"** 라고 하면 `_HANDOFF/START_PROMPT.md` 의 절차를 따른다. 요약:

```bash
python _HANDOFF/handoff.py --session <역할-날짜-임의문자> takeover <역할>
```
- 먼저 `_HANDOFF/PROJECT_CHARTER.md` 를 읽는다.
- 종료코드 3(다른 창이 사용 중)이면 `--force` 하지 말고 사용자에게 알린다.
- 역할이 지정되지 않았으면 `python _HANDOFF/handoff.py status` 만 실행해 보여 주고 확인을 요청한다.
- 완료(✔) 작업은 다시 하지 않는다. "다음 안전 작업"부터 `task start` 로 시작하고, "사용자 승인 대기" 작업은 자동 실행하지 않는다.
- 오류는 `error add`, 결과물은 `candidate register`, 종료 전에는 `checkpoint <역할> ... --release` 로 기록한다.

## 금지
- 루트 운영 파일·다른 역할의 작업 파일 수정, 고정판 덮어쓰기, 승인 없는 배포, 검수 보류 후보의 합격 승격, 미검증 결과의 성공 보고.
- `_HANDOFF/state/decisions.json` 의 사용자 결정 수정·삭제.

## 검증
`python _HANDOFF/tests/test_handoff.py` (독립 프로세스 시험 A~I), `python _HANDOFF/handoff.py protect verify` (운영 파일 SHA 대조).
