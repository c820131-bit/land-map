#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인계 시스템 독립 프로세스 시험 (시험 A ~ I)

- 모든 명령은 subprocess 로 '별도 파이썬 프로세스 + 별도 세션 ID' 로 실행한다.
  (같은 프로세스에서 함수를 두 번 호출하는 방식이 아님)
- 임시 프로젝트 폴더를 만들어 실제 저장소(_HANDOFF)에는 손대지 않는다.

실행:  python _HANDOFF/tests/test_handoff.py [--keep]
종료 코드 0 = 전부 통과
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "handoff.py")
PY = sys.executable
RESULTS = []


def run(root, session, *args, expect=0, timeout=60):
    cmd = [PY, TOOL, "--root", root, "--session", session] + [str(a) for a in args]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if expect is not None and p.returncode != expect:
        raise AssertionError("명령 %s\n기대 종료코드 %s, 실제 %s\nSTDOUT:\n%s\nSTDERR:\n%s" % (
            " ".join(args), expect, p.returncode, p.stdout, p.stderr))
    return p


def takeover_json(root, session, role, *extra):
    p = run(root, session, "takeover", role, "--json", *extra)
    js = p.stdout[p.stdout.index("\n{") + 1:]
    return json.loads(js), p.stdout


def fresh_project():
    proj = tempfile.mkdtemp(prefix="imap_handoff_test_")
    root = os.path.join(proj, "_HANDOFF")
    os.makedirs(root)
    run(root, "init-sess", "init")
    return proj, root


def write(proj, rel, text):
    full = os.path.join(proj, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    return full


def load(root, name):
    with open(os.path.join(root, "state", name + ".json"), "r", encoding="utf-8") as f:
        return json.load(f)


def record(name, fn):
    t0 = time.time()
    try:
        detail = fn() or ""
        RESULTS.append((name, "PASS", detail, round(time.time() - t0, 2)))
        print("PASS  %s  %s" % (name, detail))
    except Exception as e:  # noqa
        RESULTS.append((name, "FAIL", str(e), round(time.time() - t0, 2)))
        print("FAIL  %s\n%s" % (name, e))


# ----------------------------------------------------------------------------
def test_A_normal_handoff():
    proj, root = fresh_project()
    S1, S2 = "C-창-1", "C-창-2"
    run(root, S1, "takeover", "C")
    run(root, S1, "task", "add", "C", "C-T1", "--title", "완전일치 오류 재현", "--priority", "1", "--command", "python c_repro.py")
    run(root, S1, "task", "add", "C", "C-T2", "--title", "100m 경계 거리 검증", "--priority", "2", "--command", "python c_dist_check.py --m 100")
    run(root, S1, "task", "start", "C", "C-T1")
    run(root, S1, "task", "complete", "C", "C-T1", "--evidence", "c_repro.py 실행 결과 117건 일치 확인")
    run(root, S1, "task", "start", "C", "C-T2")
    run(root, S1, "checkpoint", "C", "--next-command", "python c_dist_check.py --m 100 --resume", "--env", "Windows / Python 3.11",
        "--note-resume", "운영 index.html 수정 금지", "--do-not-touch", "index.html", "--report", "C 창 1차 보고 원문", "--release")
    # 새 세션(별도 프로세스)
    js, out = takeover_json(root, S2, "C")
    assert js["done_ids"] == ["C-T1"], js["done_ids"]
    assert js["next"]["id"] == "C-T2" and js["next"]["status"] == "in_progress", js["next"]
    assert "python c_dist_check.py --m 100 --resume" in out
    assert "C 창 1차 보고 원문" in out and "index.html" in out and "Windows / Python 3.11" in out
    run(root, S2, "release", "C")
    return "완료 C-T1 / 다음 C-T2 / 재개명령·보고원문·변경금지 파일 복원 확인"


def test_B_no_duplicate():
    proj, root = fresh_project()
    run(root, "s1", "takeover", "C")
    run(root, "s1", "task", "add", "C", "T1", "--title", "x")
    run(root, "s1", "task", "start", "C", "T1")
    run(root, "s1", "task", "complete", "C", "T1", "--evidence", "ok")
    run(root, "s1", "release", "C")
    js, _ = takeover_json(root, "s2", "C")
    assert js["next"] is None
    p = run(root, "s2", "task", "start", "C", "T1", expect=2)
    assert "이미 완료" in p.stderr
    p = run(root, "s2", "task", "complete", "C", "T1", "--evidence", "again", expect=2)
    # 증거 없는 완료 거부
    run(root, "s2", "task", "add", "C", "T2", "--title", "y")
    run(root, "s2", "task", "start", "C", "T2")
    p = run(root, "s2", "task", "complete", "C", "T2", expect=2)
    assert "evidence" in p.stderr
    return "완료 작업 재시작·재완료 거부(종료코드 2), 증거 없는 완료 거부"


def test_C_review_hold_preserved():
    proj, root = fresh_project()
    cand = write(proj, "C_work/map_candidate.html", "<html>cand v1</html>")
    run(root, "c1", "takeover", "C")
    run(root, "c1", "candidate", "register", "--role", "C", "--id", "C-CAND-1", "--path", "C_work/map_candidate.html")
    run(root, "c1", "candidate", "self-test", "--id", "C-CAND-1", "--status", "pass", "--note", "자체 회귀 통과")
    run(root, "c1", "release", "C")
    # C 자신은 독립 검수 기록 불가
    run(root, "c1", "takeover", "C")
    p = run(root, "c1", "candidate", "review", "--id", "C-CAND-1", "--status", "pass", "--by", "C", expect=2)
    run(root, "c1", "release", "C")
    # D 검수 보류
    run(root, "d1", "takeover", "D")
    run(root, "d1", "candidate", "review", "--id", "C-CAND-1", "--status", "hold", "--by", "D", "--note", "완전일치 3건 불일치")
    run(root, "d1", "release", "D")
    # 새 C 창: 보류 상태 보존, 합격판 승격 거부
    js, out = takeover_json(root, "c2", "C")
    assert js["latest_candidate"]["independent_review"]["status"] == "hold"
    assert js["last_passed_candidate"] is None
    assert "독립 검수 보류" in out and "자체시험=pass" in out
    p = run(root, "c2", "candidate", "set-passed", "--role", "C", "--id", "C-CAND-1", expect=2)
    assert "hold" in p.stderr
    assert load(root, "roles/C")["last_passed_candidate"] is None
    # 검수 중 후보를 수정하면 같은 후보로 취급하지 않음
    with open(cand, "a", encoding="utf-8") as f:
        f.write("<!-- edited after freeze -->")
    p = run(root, "c2", "candidate", "verify", "--id", "C-CAND-1", expect=1)
    assert "등록 해시와 다름" in p.stdout
    run(root, "c2", "release", "C")
    run(root, "d2", "takeover", "D")
    p = run(root, "d2", "candidate", "review", "--id", "C-CAND-1", "--status", "pass", "--by", "D", expect=2)
    run(root, "d2", "release", "D")
    # 정상 경로: 새 고정 후보 → D 합격 → set-passed 허용
    run(root, "c3", "takeover", "C")
    run(root, "c3", "candidate", "register", "--role", "C", "--id", "C-CAND-2", "--path", "C_work/map_candidate.html", "--base", "C-CAND-1")
    run(root, "c3", "release", "C")
    run(root, "d3", "takeover", "D")
    run(root, "d3", "candidate", "review", "--id", "C-CAND-2", "--status", "pass", "--by", "D")
    run(root, "d3", "release", "D")
    run(root, "c4", "takeover", "C")
    run(root, "c4", "candidate", "set-passed", "--role", "C", "--id", "C-CAND-2")
    js, out = takeover_json(root, "c4", "C")
    assert js["last_passed_candidate"]["id"] == "C-CAND-2" and js["latest_candidate"]["id"] == "C-CAND-2"
    # 더 최신 후보를 등록해도 합격판은 그대로
    write(proj, "C_work/map_candidate_v3.html", "<html>v3</html>")
    run(root, "c4", "candidate", "register", "--role", "C", "--id", "C-CAND-3", "--path", "C_work/map_candidate_v3.html", "--base", "C-CAND-2")
    js, out = takeover_json(root, "c4", "C")
    assert js["latest_candidate"]["id"] == "C-CAND-3" and js["last_passed_candidate"]["id"] == "C-CAND-2"
    assert "최신 후보 ≠ 마지막 합격판" in out
    return "보류 보존, 보류→합격판 거부, 고정 후 수정 탐지, 최신후보/합격판 분리"


def test_D_error_restore():
    proj, root = fresh_project()
    run(root, "c1", "takeover", "C")
    run(root, "c1", "error", "add", "--owner", "C", "--id", "ERR-C-001", "--title", "완전일치 지번 누락",
        "--basis", "국토부 고시 제2026-12호 토지조서 3면", "--repro", "python c_match.py --pnu 4113510300100120003",
        "--expected", "편입 117건", "--actual", "114건", "--affects", "D")
    run(root, "c1", "error", "add", "--owner", "C", "--id", "ERR-C-002", "--title", "거리 계산 오차", "--repro", "python c_dist.py --m 100")
    run(root, "c1", "error", "update", "--id", "ERR-C-002", "--status", "fixed_unverified", "--cause", "좌표계 변환 누락")
    # verified 전환은 재시험 결과 없이는 거부
    p = run(root, "c1", "error", "update", "--id", "ERR-C-002", "--status", "verified", expect=2)
    run(root, "c1", "release", "C")
    js, out = takeover_json(root, "c2", "C")
    ids = {e["id"]: e for e in js["open_errors"]}
    assert set(ids) == {"ERR-C-001", "ERR-C-002"}, ids.keys()
    e = ids["ERR-C-001"]
    assert e["repro"] == "python c_match.py --pnu 4113510300100120003" and e["expected"] == "편입 117건" and e["actual"] == "114건"
    assert e["basis"].startswith("국토부 고시")
    assert ids["ERR-C-002"]["status"] == "fixed_unverified"
    assert "python c_match.py --pnu" in out
    # D 창에도 affects 로 전달
    js_d, _ = takeover_json(root, "d1", "D")
    assert "ERR-C-001" in {e["id"] for e in js_d["open_errors"]}
    run(root, "c2", "release", "C"); run(root, "d1", "release", "D")
    return "오류 2건·재현 명령·기대/실제·근거 누락 없이 새 세션 복원, 미검증 verified 거부"


def test_E_concurrent():
    proj, root = fresh_project()
    # 1) 두 새 세션이 동시에 같은 역할 인계 시도
    cmds = [[PY, TOOL, "--root", root, "--session", "new-%d" % i, "takeover", "C"] for i in range(2)]
    procs = [subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for c in cmds]
    outs = [p.communicate(timeout=60) for p in procs]
    codes = sorted(p.returncode for p in procs)
    assert codes == [0, 3], "동시 인계 종료코드 %s\n%s" % (codes, outs)
    loser = [o for p, o in zip(procs, outs) if p.returncode == 3][0]
    assert "다른 작업창이 사용 중" in loser[1]
    # 2) 활성 임대 중 순차 재시도도 거부; 소유자가 아닌 세션의 release 거부
    run(root, "new-9", "takeover", "C", expect=3)
    run(root, "new-9", "release", "C", expect=2)
    # 3) 임대 없이 상태 변경 거부
    run(root, "new-9", "task", "add", "C", "X", "--title", "x", expect=2)
    # 4) 같은 상태 파일에 다중 프로세스 동시 쓰기 → 기록 유실 없음
    owner = "new-%d" % [i for i, p in enumerate(procs) if p.returncode == 0][0]
    N = 12
    ps = [subprocess.Popen([PY, TOOL, "--root", root, "--session", owner, "task", "add", "C", "PAR-%02d" % i, "--title", "t"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(N)]
    for p in ps:
        p.communicate(timeout=120)
    assert all(p.returncode == 0 for p in ps), [p.returncode for p in ps]
    rs = load(root, "roles/C")
    assert sorted(t["id"] for t in rs["tasks"]) == ["PAR-%02d" % i for i in range(N)]
    # 5) 세대 번호 기반 낙관적 변경: 오래된 세대로 쓰기 거부
    gen = rs["generation"]
    run(root, owner, "task", "add", "C", "G1", "--title", "g", "--expect-gen", gen)
    p = run(root, owner, "task", "add", "C", "G2", "--title", "g", "--expect-gen", gen, expect=3)
    assert "세대 충돌" in p.stderr
    # 6) 변경 이력 보존
    hist = [f for f in os.listdir(os.path.join(root, "history")) if f.startswith("roles__C.gen")]
    assert len(hist) >= N + 2, len(hist)
    run(root, owner, "release", "C")
    return "동시 인계 1승1패(코드 0/3), 비소유 변경 거부, 병렬 %d건 쓰기 무손실, 세대 충돌 거부, 이력 %d건" % (N, len(hist))


def test_F_crash_recovery():
    proj, root = fresh_project()
    run(root, "s1", "takeover", "C")
    run(root, "s1", "task", "add", "C", "T1", "--title", "a")
    run(root, "s1", "task", "add", "C", "T2", "--title", "b")
    good = load(root, "roles/C")
    rc = os.path.join(root, "state", "roles", "C.json")
    # 1) 쓰기 도중 종료 시뮬레이션: 임시파일만 남기고 프로세스가 죽음 (os.replace 전)
    crash_code = (
        "import os,sys\np=sys.argv[1]\nt=p+'.tmp.99999.crash'\n"
        "f=open(t,'w');f.write('{\"generation\": 9999, \"tasks\": [  ');f.flush();os._exit(1)\n")
    subprocess.run([PY, "-c", crash_code, rc], check=False)
    assert os.path.exists(rc + ".tmp.99999.crash")
    assert load(root, "roles/C") == good, "원본이 변경됨"
    # 2) 상태 파일 자체가 잘린 경우(부분 쓰기/디스크 오류) → history 에서 마지막 정상 세대 복구
    with open(rc, "w", encoding="utf-8") as f:
        f.write(json.dumps(good)[: len(json.dumps(good)) // 2])
    p = run(root, "s1", "role", "show", "C")
    rec = json.loads(p.stdout)
    assert rec["generation"] == good["generation"] and [t["id"] for t in rec["tasks"]] == ["T1", "T2"]
    assert any(f.startswith("C.json.corrupt.") for f in os.listdir(os.path.dirname(rc)))
    assert load(root, "roles/C") == good
    # 3) 인계 기록(checkpoint) 중 종료 → 임대는 남아있고 심장박동이 멈춘 상태 → 만료 전엔 거부, 만료 후 회수
    lease_path = os.path.join(root, "locks", "C.lease.json")
    with open(lease_path, "r", encoding="utf-8") as f:
        lease = json.load(f)
    run(root, "s2", "takeover", "C", expect=3)  # 아직 살아있는 것으로 보임(다른 호스트 가정 못함 → 같은 호스트, pid 살아있음)
    lease["heartbeat_at"] = "2000-01-01T00:00:00.000000Z"
    with open(lease_path, "w", encoding="utf-8") as f:
        json.dump(lease, f)
    p = run(root, "s2", "takeover", "C")
    assert "expired" in p.stdout and "회수" in p.stdout
    run(root, "s2", "release", "C")
    # 4) 같은 호스트에서 소유 프로세스가 죽은 경우(PID 없음) → dead 로 판정해 회수
    # CLI 호출 PID 는 생존 판정에 쓰이지 않아야 함(이미 종료된 PID 라도 TTL 내에는 active)
    lease.update({"session": "ghost", "pid": 2 ** 22 - 7, "heartbeat_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
    with open(lease_path, "w", encoding="utf-8") as f:
        json.dump(lease, f)
    run(root, "s3", "takeover", "C", expect=3)
    # 심장박동 데몬 PID(tracked_pid)가 죽은 경우에만 dead 판정
    lease.update({"tracked_pid": 2 ** 22 - 7, "tracked_host": __import__("socket").gethostname()})
    with open(lease_path, "w", encoding="utf-8") as f:
        json.dump(lease, f)
    p = run(root, "s3", "takeover", "C")
    assert "dead" in p.stdout
    run(root, "s3", "release", "C")
    # 5) 손상된 임대 파일 → corrupt 로 판정해 회수
    with open(lease_path, "w", encoding="utf-8") as f:
        f.write("{broken")
    p = run(root, "s4", "takeover", "C")
    assert "corrupt" in p.stdout
    run(root, "s4", "release", "C")
    # 6) 비정상 종료로 남은 뮤텍스(30초 초과) → 회수 후 정상 진행
    m = os.path.join(root, "locks", "mutex__roles__C")
    os.makedirs(m)
    old = time.time() - 120
    os.utime(m, (old, old))
    run(root, "s5", "takeover", "C")
    run(root, "s5", "task", "add", "C", "T3", "--title", "c")
    jl = open(os.path.join(root, "journal.log"), encoding="utf-8").read()
    assert "mutex_stale_reclaimed" in jl and "recovered_from_history" in jl
    run(root, "s5", "release", "C")
    return "쓰기 중 종료 원본 무손상, 손상 파일 history 복구, 만료/사망/손상 임대 회수, 잔류 뮤텍스 회수"


def test_G_chain_A_B_C_D():
    proj, root = fresh_project()
    write(proj, "A_work/notice_2026-12.json", '{"notice":"국토부 고시 2026-12"}')
    write(proj, "B_work/ledger_2026-12.json", '{"parcels":117}')
    write(proj, "C_work/map_cand.html", "<html>cand</html>")
    run(root, "a1", "takeover", "A")
    run(root, "a1", "candidate", "register", "--role", "A", "--id", "A-SRC-1", "--path", "A_work/notice_2026-12.json")
    run(root, "a1", "handoff", "send", "--from", "A", "--to", "B", "--candidate", "A-SRC-1", "--event-id", "EV-A-1", "--note", "고시 원문 및 첨부")
    # 동일 이벤트 중복 전송 → 무시
    p = run(root, "a1", "handoff", "send", "--from", "A", "--to", "B", "--candidate", "A-SRC-1", "--event-id", "EV-A-1")
    assert "중복 무시" in p.stdout
    run(root, "a1", "release", "A")
    assert len(load(root, "handoffs")["items"]) == 1
    run(root, "b1", "takeover", "B")
    inbound = [h for h in load(root, "handoffs")["items"].values() if h["to"] == "B"]
    run(root, "b1", "handoff", "accept", "--role", "B", "--id", inbound[0]["id"])
    run(root, "b1", "candidate", "register", "--role", "B", "--id", "B-READ-1", "--path", "B_work/ledger_2026-12.json", "--base", "A-SRC-1")
    run(root, "b1", "handoff", "send", "--from", "B", "--to", "C", "--candidate", "B-READ-1", "--event-id", "EV-B-1")
    run(root, "b1", "release", "B")
    run(root, "c1", "takeover", "C")
    inbound = [h for h in load(root, "handoffs")["items"].values() if h["to"] == "C"]
    run(root, "c1", "handoff", "accept", "--role", "C", "--id", inbound[0]["id"])
    run(root, "c1", "candidate", "register", "--role", "C", "--id", "C-CAND-1", "--path", "C_work/map_cand.html", "--base", "B-READ-1")
    run(root, "c1", "handoff", "send", "--from", "C", "--to", "D", "--candidate", "C-CAND-1", "--event-id", "EV-C-1")
    run(root, "c1", "release", "C")
    run(root, "d1", "takeover", "D")
    inbound = [h for h in load(root, "handoffs")["items"].values() if h["to"] == "D"]
    run(root, "d1", "handoff", "accept", "--role", "D", "--id", inbound[0]["id"])
    run(root, "d1", "candidate", "review", "--id", "C-CAND-1", "--status", "pass", "--by", "D")
    run(root, "d1", "release", "D")
    p = run(root, "x", "candidate", "chain", "--id", "C-CAND-1")
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    assert [l.split()[0] for l in lines] == ["C-CAND-1", "B-READ-1", "A-SRC-1"], lines
    assert all("[OK]" in l for l in lines)
    cands = load(root, "candidates")["items"]
    hs = load(root, "handoffs")["items"]
    for h in hs.values():
        assert h["sha256"] == cands[h["candidate"]]["sha256"] and h["status"] == "accepted"
    # 중간 B 판독 파일이 바뀌면 연계 검증 실패로 탐지
    write(proj, "B_work/ledger_2026-12.json", '{"parcels":118}')
    p = run(root, "x", "candidate", "chain", "--id", "C-CAND-1", expect=1)
    assert "SHA불일치" in p.stdout
    # 바뀐 후보를 인계로 수락하려 하면 거부
    run(root, "b2", "takeover", "B")
    run(root, "b2", "handoff", "send", "--from", "B", "--to", "C", "--candidate", "B-READ-1", "--event-id", "EV-B-2")
    run(root, "b2", "release", "B")
    run(root, "c2", "takeover", "C")
    hid = [h["id"] for h in load(root, "handoffs")["items"].values() if h["event_id"] == "EV-B-2"][0]
    p = run(root, "c2", "handoff", "accept", "--role", "C", "--id", hid, expect=2)
    run(root, "c2", "release", "C")
    return "A→B→C→D 3단 SHA 연계 OK, 이벤트 중복 무시, 중간 파일 변경 시 연계 불일치·수락 거부"


def test_H_user_approval_protection():
    proj, root = fresh_project()
    run(root, "c1", "takeover", "C")
    run(root, "c1", "task", "add", "C", "DEPLOY-1", "--title", "운영 index.html 교체(배포)", "--priority", "1", "--requires-approval")
    run(root, "c1", "task", "add", "C", "SAFE-1", "--title", "회귀검사", "--priority", "5")
    js, out = takeover_json(root, "c1", "C")
    assert js["next"]["id"] == "SAFE-1", js["next"]
    assert "사용자 승인 대기(자동 실행 금지): DEPLOY-1" in out
    p = run(root, "c1", "task", "start", "C", "DEPLOY-1", expect=2)
    assert "사용자 승인" in p.stderr
    # 결정은 --user-approved 없이는 기록 불가, 수정·삭제 불가
    run(root, "c1", "decision", "add", "--text", "배포 승인", "--approves-task", "DEPLOY-1", expect=2)
    run(root, "c1", "decision", "edit", expect=2)
    run(root, "c1", "decision", "delete", expect=2)
    run(root, "c1", "candidate", "approve", "--id", "X", expect=2)
    assert load(root, "decisions")["items"] == {}
    # 사용자가 명시 승인한 뒤에만 시작 가능
    run(root, "c1", "decision", "add", "--text", "사용자: index.html 교체 배포 승인", "--approves-task", "DEPLOY-1", "--user-approved")
    run(root, "c1", "task", "start", "C", "DEPLOY-1")
    js, out = takeover_json(root, "c1", "C")
    assert js["next"]["id"] == "DEPLOY-1"
    run(root, "c1", "release", "C")
    # 새 세션에서도 결정 보존
    p = run(root, "c2", "decision", "list")
    assert "DEPLOY-1" in p.stdout and "사용자: index.html 교체 배포 승인" in p.stdout
    return "승인 필요 작업 자동 선택·시작 거부, 결정 무단 기록/수정/삭제 거부, 명시 승인 후 허용, 새 세션 보존"


def test_I_resume_and_update():
    proj, root = fresh_project()
    write(proj, "ops/index.html", "<html>prod</html>")
    write(proj, "ops/data.json", "{}")
    run(root, "h0", "protect", "snapshot", "--path", "ops", "--label", "ops-baseline")
    run(root, "h0", "takeover", "H")
    run(root, "h0", "task", "add", "H", "H-VERIFY", "--title", "보호 파일 SHA 검증", "--priority", "1",
        "--command", "python _HANDOFF/handoff.py protect verify")
    run(root, "h0", "task", "add", "H", "H-NEXT", "--title", "다음 과제", "--priority", "2", "--depends-on", "H-VERIFY")
    run(root, "h0", "release", "H")
    # 새 세션 1: 인계 → 다음 작업 실행(실제 검증) → 결과 반영 → 체크포인트 → 해제
    js, out = takeover_json(root, "h1", "H")
    assert js["next"]["id"] == "H-VERIFY"
    run(root, "h1", "task", "start", "H", "H-VERIFY")
    p = run(root, "h1", "protect", "verify")
    assert "변경 0 / 누락 0" in p.stdout
    run(root, "h1", "task", "complete", "H", "H-VERIFY", "--evidence", p.stdout.strip())
    run(root, "h1", "checkpoint", "H", "--file", os.path.join(proj, "ops/index.html"), "--note", "검증 완료", "--release")
    # 새 세션 2: 결과를 읽는다
    js2, out2 = takeover_json(root, "h2", "H")
    assert js2["done_ids"] == ["H-VERIFY"] and js2["next"]["id"] == "H-NEXT"
    rs = load(root, "roles/H")
    assert rs["last_checkpoint"]["tasks"] == {"H-VERIFY": "done", "H-NEXT": "todo"}
    assert "일치 2 / 변경 0" in [t for t in rs["tasks"] if t["id"] == "H-VERIFY"][0]["evidence"]
    assert "CP-" in out2 and "검증 완료" in out2
    # 운영 파일이 바뀌면 verify 가 탐지
    write(proj, "ops/index.html", "<html>changed</html>")
    p = run(root, "h2", "protect", "verify", expect=1)
    assert "변경됨: ops/index.html" in p.stdout
    run(root, "h2", "release", "H")
    return "새 세션이 미완료 과제(보호 SHA 검증)를 실제 수행·기록, 다음 세션이 완료/체크포인트 읽음, 변경 탐지"


def test_X_no_role_specified():
    proj, root = fresh_project()
    p = run(root, "anon", "status")
    assert "점유하지 않았습니다" in p.stdout
    assert not os.listdir(os.path.join(root, "locks")) or all(f.startswith("mutex") is False for f in os.listdir(os.path.join(root, "locks")))
    run(root, "anon", "takeover", "Z", expect=2)
    return "역할 미지정 시 점유 없음, 미등록 역할 거부"


def main():
    keep = "--keep" in sys.argv
    tests = [("A 정상 인계", test_A_normal_handoff), ("B 중복 방지", test_B_no_duplicate),
             ("C 검수 보류 보존", test_C_review_hold_preserved), ("D 오류 복원", test_D_error_restore),
             ("E 동시 실행", test_E_concurrent), ("F 비정상 종료", test_F_crash_recovery),
             ("G A→B→C→D 연계", test_G_chain_A_B_C_D), ("H 사용자 승인 보호", test_H_user_approval_protection),
             ("I 재개 후 상태 갱신", test_I_resume_and_update), ("X 역할 미지정", test_X_no_role_specified)]
    for name, fn in tests:
        record(name, fn)
    print("\n" + "=" * 78)
    passed = sum(1 for r in RESULTS if r[1] == "PASS")
    for name, status, detail, sec in RESULTS:
        print("%-5s %-22s %5.2fs  %s" % (status, name, sec, detail if status == "PASS" else (detail.splitlines() or ["?"])[0]))
    print("합계: %d/%d 통과  (방식: 매 명령 독립 파이썬 프로세스 + 독립 세션 ID, 임시 프로젝트 폴더)" % (passed, len(RESULTS)))
    out = {"ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "python": sys.version.split()[0], "platform": sys.platform,
           "results": [{"name": n, "status": s, "detail": d, "sec": t} for n, s, d, t in RESULTS]}
    with open(os.path.join(HERE, "last_result.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    if not keep:
        for d in os.listdir(tempfile.gettempdir()):
            if d.startswith("imap_handoff_test_"):
                shutil.rmtree(os.path.join(tempfile.gettempdir(), d), ignore_errors=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
