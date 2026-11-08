# _HANDOFF — INVESTMENT MAP 공통 작업 인계 저장소

여러 Claude 작업창(A·B·C·D·E·H)이 **파일 기반 공통 상태**를 통해 작업을 기록하고, 새 창이 한 문장으로 이어받게 하는 도구.
표준 라이브러리만 사용(Python 3.8+, Windows/Linux 공용). 운영 파일(루트의 index.html, data_*.json 등)은 절대 건드리지 않는다.

## 새 Claude 창에서 할 일 (사용자)
```
INVESTMENT MAP C 인계받고 이어서 작업해.
```
Claude Code 세션이라면 루트 `CLAUDE.md` 가 자동 로드되어 아래 명령을 실행하고 브리핑을 읽는다.
그 밖의 환경(예: claude.ai 프로젝트)에서는 `START_PROMPT.md` 내용을 프로젝트 지침에 넣어 두거나, 직접 아래 명령을 실행한다.

```bash
python _HANDOFF/handoff.py --session <창ID> takeover C
```
브리핑은 다음 11개 항목을 출력한다: ① 최상위 목적·우선순위 ② 담당 업무·격리 영역 ③ 최신 후보 / 마지막 합격판(분리) ④ 완료·진행·미완료·차단 작업 ⑤ D 독립 검수 상태 ⑥ 미해결 오류·받을/보낼 인계 ⑦ 중복 실행 금지 목록 ⑧ 마지막 체크포인트 ⑨ 보호 파일 매니페스트 ⑩ 다음 안전 작업·실행 명령·승인 대기 작업 ⑪ 결과 반영 방법. 마지막에 사용자 결정 목록과 마지막 보고 원문이 따라온다.

## 폴더 구조
```
_HANDOFF/
  handoff.py            도구 본체
  PROJECT_CHARTER.md    최상위 지침(역할·우선순위·금지사항·접근 범위)
  START_PROMPT.md       claude.ai 프로젝트 지침용 붙여넣기 문구
  README.md             이 문서
  state/
    project.json        프로젝트 메타(역할 정의·우선순위·금지사항·TTL)
    roles/<역할>.json    창별 최신 상태(후보·작업·재개 명령·체크포인트·마지막 보고 원문)
    candidates.json     고정 후보(SHA-256·기반 후보·자체시험·독립검수·사용자승인·운영반영)
    errors.json         오류 기록부
    decisions.json      사용자 결정·승인 (추가만 가능, 수정·삭제 불가)
    handoffs.json       창 간 인계 메시지(A→B, B→C, C→D …)
    events.json         처리한 인계 이벤트 ID(중복 처리 방지)
    protected.json      보호 파일 SHA 매니페스트
  locks/                역할 임대(lease) 파일 + 쓰기 뮤텍스
  history/              모든 상태 파일의 세대별 이전 버전(복구용)
  journal.log           append-only 변경 저널
  tests/test_handoff.py 독립 프로세스 시험 A~I
```

## 안전장치 요약
| 위험 | 장치 |
|---|---|
| 두 창이 같은 역할을 동시에 인계 | 역할별 임대(lease): 소유 세션·획득 시각·심장박동·TTL. 활성 임대가 있으면 `takeover` 거부(종료코드 3) |
| 같은 상태 파일 동시 수정 | `mkdir` 뮤텍스 + 임시파일→`os.replace` 원자 교체 + 세대 번호(`--expect-gen` 으로 낙관적 검사) |
| 쓰기 도중 종료·파일 손상 | 원본은 교체 전까지 무손상. 손상 시 `history/` 의 마지막 정상 세대로 자동 복구(손상본은 `.corrupt.*` 로 보존) |
| 죽은 창의 임대가 영원히 남음 | TTL 만료, 심장박동 데몬(`heartbeat --daemon`) PID 사망, 임대 파일 손상 → 회수(저널에 기록). CLI 호출 PID 는 생존 판정에 쓰지 않음 |
| 완료 아닌 작업을 완료로 승격 | `task complete` 는 `--evidence` 필수, `in_progress` 가 아니면 거부, 이미 완료면 거부 |
| 검수 보류 후보가 합격판으로 둔갑 | `set-passed` 는 D 의 `pass` + 검수 SHA = 현재 파일 SHA 일 때만 허용. C 는 자기 후보를 검수할 수 없음 |
| 고정 후 수정된 후보 재사용 | 등록 SHA 와 현재 SHA 불일치 시 `verify`/`chain`/`accept`/`review pass` 가 거부 |
| 사용자 승인 없는 배포·운영 변경 | `--requires-approval` 작업은 `decision add --user-approved --approves-task` 없이는 시작 불가. 결정은 수정·삭제 불가 |
| 동일 인계 이벤트 중복 처리 | `handoff send --event-id` 중복이면 무시 |
| 운영 파일 변경 | `protect snapshot` / `protect verify` 로 SHA 대조 |

## 명령 요약
```bash
H=python _HANDOFF/handoff.py --session <창ID>
$H status [역할]                       # 읽기 전용(점유 없음)
$H takeover C [--json] [--force --reason ...]
$H heartbeat C [--daemon --interval 60]
$H task add C C-T3 --title ... --priority 1 [--command ...] [--requires-approval] [--depends-on C-T2]
$H task start C C-T3 ; $H task complete C C-T3 --evidence "..." [--sha-file 파일...]
$H candidate register --role C --path C_work/x.html [--base B-READ-7] [--id C-CAND-9]
$H candidate self-test --id C-CAND-9 --status pass
$H candidate review --id C-CAND-9 --status hold|pass|fail --by D     # D 만 가능
$H candidate set-passed --role C --id C-CAND-9                        # pass 일 때만
$H candidate verify|chain --id C-CAND-9 ; $H candidate list
$H error add --owner C --title ... --basis ... --repro ... --expected ... --actual ... [--affects D]
$H error update --id ERR-... --status fixed_unverified|verified --cause ... --verification ... --fix-file 파일...
$H handoff send --from A --to B --candidate A-SRC-3 --event-id EV-A-3 --note ...
$H handoff accept --role B --id HO-...
$H decision list ; $H decision add --text ... [--approves-task ...] --user-approved   # 사용자 명시 승인 시에만
$H checkpoint C --file 수정파일... --report-file 보고.md --next-command "..." --env "..." --do-not-touch index.html --release
$H protect snapshot --path . --label ... ; $H protect verify
$H release C
```
종료 코드: 0 정상 / 1 검증 불일치 / 2 거부(규칙 위반) / 3 충돌(임대·세대).

## 시험
```bash
python _HANDOFF/tests/test_handoff.py
```
매 명령을 **별도 파이썬 프로세스 + 별도 세션 ID** 로 실행하며 임시 폴더를 사용한다(실제 저장소 무변경). 결과는 `tests/last_result.json`.

## 기존 창이 종료·이전할 때 (인계 생성)
1. `error add/update` 로 미해결 오류 정리
2. 수정 파일을 `candidate register` 로 고정(SHA)하고 필요 시 `handoff send`
3. `checkpoint <역할> --file ... --report-file ... --next-command ... --do-not-touch ... --dependency ... --release`
이 세 단계가 끝나면 다음 창은 `takeover` 만으로 같은 상태를 복원한다.
