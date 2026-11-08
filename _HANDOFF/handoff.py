#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTMENT MAP 공통 작업 인계 도구 (_HANDOFF/handoff.py)

목적
  여러 Claude 작업창(A·B·C·D·E…)이 파일 기반 공통 상태 저장소를 통해
  서로의 기록을 덮어쓰지 않고 작업을 기록·인계·복원할 수 있게 한다.

설계 원칙
  - 표준 라이브러리만 사용 (Windows / Linux 공용, Python 3.8+)
  - 모든 상태 파일은 JSON + 세대 번호(generation) + 변경 이력(history/)
  - 쓰기는 임시 파일 → os.replace 원자 교체, 읽기-수정-쓰기는 mkdir 뮤텍스
  - 역할별 소유권은 임대(lease) 파일: 소유자·PID·호스트·심장박동·TTL 구분
  - 완료 승격·검수 합격·사용자 결정 변경은 각각 증거/권한 검사
  - 자동 실행은 사용자 승인 범위(requires_user_approval=False) 작업으로 제한

시작 명령(새 Claude 창):
  python _HANDOFF/handoff.py takeover C --session <세션ID>
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import shutil
import socket
import sys
import time
import uuid

SCHEMA_VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.environ.get("HANDOFF_ROOT", HERE)

STATE_FILES = ("project", "candidates", "errors", "decisions", "handoffs", "events", "protected")
ROLE_DIR = "roles"
LOCK_DIR = "locks"
HIST_DIR = "history"
JOURNAL = "journal.log"
MUTEX_STALE_SEC = 30
DEFAULT_LEASE_TTL = 3600  # 1시간 심장박동 없으면 임대 만료로 간주 (project.json lease_ttl_sec 로 조정)

TASK_STATUS = ("todo", "in_progress", "done", "blocked")
REVIEW_STATUS = ("pending", "hold", "pass", "fail")


# ----------------------------------------------------------------------------
# 공용 유틸
# ----------------------------------------------------------------------------
def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pid_alive(pid):
    """같은 호스트에서만 의미 있음. 확인 불가 시 None."""
    try:
        pid = int(pid)
    except Exception:
        return None
    if pid <= 0:
        return None
    if platform.system() == "Windows":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        except Exception:
            return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return None


class HandoffError(Exception):
    """사용자에게 보여 줄 거부/충돌 오류. 종료 코드 2."""


class ConflictError(HandoffError):
    """동시 변경 충돌. 종료 코드 3."""


# ----------------------------------------------------------------------------
# 저장소
# ----------------------------------------------------------------------------
class Store:
    def __init__(self, root=DEFAULT_ROOT, session=None):
        self.root = os.path.abspath(root)
        self.state_dir = os.path.join(self.root, "state")
        self.roles_dir = os.path.join(self.state_dir, ROLE_DIR)
        self.lock_dir = os.path.join(self.root, LOCK_DIR)
        self.hist_dir = os.path.join(self.root, HIST_DIR)
        self.journal_path = os.path.join(self.root, JOURNAL)
        self.session = session or os.environ.get("HANDOFF_SESSION") or ("anon-%s" % uuid.uuid4().hex[:8])
        self.host = socket.gethostname()
        self.pid = os.getpid()

    # ---- 경로 ----
    def path_of(self, name):
        if name.startswith("roles/"):
            return os.path.join(self.roles_dir, name.split("/", 1)[1] + ".json")
        return os.path.join(self.state_dir, name + ".json")

    def exists(self):
        return os.path.isfile(self.path_of("project"))

    def ensure_dirs(self):
        for d in (self.state_dir, self.roles_dir, self.lock_dir, self.hist_dir):
            os.makedirs(d, exist_ok=True)

    # ---- 저널 ----
    def journal(self, kind, **data):
        rec = {"ts": now_iso(), "session": self.session, "pid": self.pid, "host": self.host, "kind": kind}
        rec.update(data)
        os.makedirs(self.root, exist_ok=True)
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---- 뮤텍스 (mkdir 원자성 이용) ----
    def _mutex_path(self, name):
        return os.path.join(self.lock_dir, "mutex__" + name.replace("/", "__"))

    def _acquire_mutex(self, name, timeout=10.0):
        mpath = self._mutex_path(name)
        os.makedirs(self.lock_dir, exist_ok=True)  # 새로 clone 한 저장소에는 빈 locks/ 가 없을 수 있음
        deadline = time.time() + timeout
        while True:
            try:
                os.mkdir(mpath)
                with open(os.path.join(mpath, "owner"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"session": self.session, "pid": self.pid, "host": self.host, "ts": now_iso()}))
                return mpath
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(mpath)
                except OSError:
                    age = 0
                if age > MUTEX_STALE_SEC:
                    # 비정상 종료로 남은 뮤텍스 → 회수(저널 기록)
                    shutil.rmtree(mpath, ignore_errors=True)
                    self.journal("mutex_stale_reclaimed", target=name, age_sec=round(age, 1))
                    continue
                if time.time() > deadline:
                    raise ConflictError("상태 파일 '%s' 뮤텍스 획득 실패(다른 프로세스가 사용 중). 잠시 후 재시도하세요." % name)
                time.sleep(0.05)

    def _release_mutex(self, mpath):
        shutil.rmtree(mpath, ignore_errors=True)

    # ---- 읽기 (손상 시 history에서 복구) ----
    def load(self, name, default=None):
        path = self.path_of(name)
        if not os.path.isfile(path):
            if default is None:
                raise HandoffError("상태 파일이 없습니다: %s" % path)
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "generation" not in data:
                raise ValueError("generation 없음")
            return data
        except (ValueError, json.JSONDecodeError) as e:
            recovered = self._recover_from_history(name)
            if recovered is None:
                raise HandoffError("상태 파일 손상 및 복구 불가: %s (%s)" % (path, e))
            self.journal("recovered_from_history", target=name, generation=recovered.get("generation"), reason=str(e))
            # 손상본은 보존 후 정상본으로 교체
            try:
                shutil.copy2(path, path + ".corrupt.%d" % int(time.time()))
            except OSError:
                pass
            self._atomic_write(path, recovered)
            return recovered

    def _hist_prefix(self, name):
        return os.path.join(self.hist_dir, name.replace("/", "__") + ".gen")

    def _recover_from_history(self, name):
        prefix = os.path.basename(self._hist_prefix(name))
        cands = []
        for fn in os.listdir(self.hist_dir) if os.path.isdir(self.hist_dir) else []:
            if fn.startswith(prefix) and fn.endswith(".json"):
                try:
                    gen = int(fn[len(prefix):-5])
                except ValueError:
                    continue
                cands.append((gen, fn))
        for gen, fn in sorted(cands, reverse=True):
            try:
                with open(os.path.join(self.hist_dir, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and data.get("generation") == gen:
                    return data
            except (OSError, ValueError):
                continue
        return None

    # ---- 쓰기 (원자 교체 + 이력) ----
    def _atomic_write(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.tmp.%d.%s" % (path, self.pid, uuid.uuid4().hex[:6])
        payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def _save_history(self, name, data):
        os.makedirs(self.hist_dir, exist_ok=True)
        hp = self._hist_prefix(name) + "%06d.json" % data["generation"]
        if not os.path.exists(hp):
            self._atomic_write(hp, data)

    def update(self, name, fn, expected_generation=None, default_factory=None):
        """읽기-수정-쓰기. fn(data)->data. 세대 검사로 덮어쓰기 거부."""
        mpath = self._acquire_mutex(name)
        try:
            if os.path.isfile(self.path_of(name)):
                data = self.load(name)
            else:
                if default_factory is None:
                    raise HandoffError("상태 파일이 없습니다: %s" % name)
                data = default_factory()
                data.setdefault("generation", 0)
            if expected_generation is not None and data["generation"] != expected_generation:
                raise ConflictError(
                    "세대 충돌: '%s' 기대 세대 %s, 현재 세대 %s. 최신 상태를 다시 읽은 뒤 재시도하세요."
                    % (name, expected_generation, data["generation"]))
            before_gen = data["generation"]
            new = fn(json.loads(json.dumps(data)))  # 깊은 복사본에 적용
            if new is None:
                return data  # 변경 없음
            new["generation"] = before_gen + 1
            new["updated_at"] = now_iso()
            new["updated_by"] = {"session": self.session, "pid": self.pid, "host": self.host}
            self._save_history(name, new)
            self._atomic_write(self.path_of(name), new)
            return new
        finally:
            self._release_mutex(mpath)

    # ---- 역할 임대(lease) ----
    def lease_path(self, role):
        return os.path.join(self.lock_dir, "%s.lease.json" % role)

    def read_lease(self, role):
        p = self.lease_path(role)
        if not os.path.isfile(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"corrupt": True}

    def lease_state(self, role):
        """(state, lease) state ∈ free | mine | active | expired | dead | corrupt"""
        lease = self.read_lease(role)
        if lease is None:
            return "free", None
        if lease.get("corrupt"):
            return "corrupt", lease
        if lease.get("session") == self.session:
            return "mine", lease
        try:
            hb = _dt.datetime.strptime(lease["heartbeat_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=_dt.timezone.utc)
        except Exception:
            return "corrupt", lease
        age = (_dt.datetime.now(_dt.timezone.utc) - hb).total_seconds()
        if age > lease.get("ttl_sec", DEFAULT_LEASE_TTL):
            return "expired", lease
        # CLI 호출 PID 는 명령 종료와 함께 사라지므로 생존 판정에 쓰지 않는다.
        # 'heartbeat --daemon' 이 등록한 tracked_pid 만 같은 호스트에서 생존 검사한다.
        tp = lease.get("tracked_pid")
        if tp and lease.get("tracked_host") == self.host and pid_alive(tp) is False:
            return "dead", lease
        return "active", lease

    def acquire_lease(self, role, ttl=DEFAULT_LEASE_TTL, force=False, reason=""):
        mpath = self._acquire_mutex("lease__" + role)
        try:
            state, lease = self.lease_state(role)
            takeover_note = None
            if state == "active" and not force:
                raise ConflictError(
                    "역할 %s 는 다른 작업창이 사용 중입니다 (세션=%s, 호스트=%s, PID=%s, 마지막 심장박동=%s). "
                    "같은 역할을 두 창이 동시에 이어받을 수 없습니다. 기존 창에서 'release' 하거나 TTL 만료 후 재시도하세요. "
                    "비정상 종료가 확실하면 --force --reason 으로 회수할 수 있습니다."
                    % (role, lease.get("session"), lease.get("host"), lease.get("pid"), lease.get("heartbeat_at")))
            if state in ("expired", "dead", "corrupt") or (state == "active" and force):
                takeover_note = {"previous": lease, "previous_state": state, "forced": force, "reason": reason}
            new = {
                "role": role, "session": self.session, "pid": self.pid, "host": self.host,
                "acquired_at": now_iso(), "heartbeat_at": now_iso(), "ttl_sec": ttl,
                "lease_id": uuid.uuid4().hex, "takeover_from": takeover_note,
                "tracked_pid": None, "tracked_host": None,
            }
            self._atomic_write(self.lease_path(role), new)
            self.journal("lease_acquired", role=role, previous_state=state, forced=force, reason=reason)
            return new, state
        finally:
            self._release_mutex(mpath)

    def heartbeat(self, role, track_pid=None):
        state, lease = self.lease_state(role)
        if state != "mine":
            raise HandoffError("역할 %s 임대를 이 세션이 소유하고 있지 않습니다 (상태=%s)." % (role, state))
        lease["heartbeat_at"] = now_iso()
        if track_pid:
            lease["tracked_pid"] = int(track_pid)
            lease["tracked_host"] = self.host
        self._atomic_write(self.lease_path(role), lease)
        return lease

    def release_lease(self, role):
        state, lease = self.lease_state(role)
        if state == "free":
            return
        if state not in ("mine", "expired", "dead", "corrupt"):
            raise HandoffError("다른 세션이 소유한 활성 임대는 해제할 수 없습니다 (역할 %s, 세션 %s)." % (role, lease.get("session")))
        try:
            os.remove(self.lease_path(role))
        except FileNotFoundError:
            pass
        self.journal("lease_released", role=role, previous_state=state)

    def require_lease(self, role):
        state, _ = self.lease_state(role)
        if state != "mine":
            raise HandoffError(
                "역할 %s 의 상태를 변경하려면 먼저 'takeover %s' 로 임대를 획득해야 합니다 (현재 임대 상태=%s)." % (role, role, state))


# ----------------------------------------------------------------------------
# 기본 데이터
# ----------------------------------------------------------------------------
DEFAULT_ROLES = {
    "A": {"name": "공식 공고·출처 수집", "duties": "공식 공고·첨부·출처·사업 구간·정정·취소·증분 수집"},
    "B": {"name": "토지조서 판독", "duties": "PDF·HWP·HWPX·XLSX 토지조서 판독·지번·권리·면적·원문 위치"},
    "C": {"name": "지도·연결·패널", "duties": "경매물건 연결·지도·API·보상사업 패널·공식 원문·거리 검색"},
    "D": {"name": "독립 검수", "duties": "독립 검수·공식 원문 대조·보상사례 및 투자분석", "reviewer": True},
    "E": {"name": "업무관리 브라우저·기타", "duties": "업무관리 브라우저 개선, 별도 검증 또는 명시된 담당 업무"},
    "H": {"name": "인계 체계", "duties": "공통 인계 저장소·복원 도구·시험 (A~E 작업 침범 금지)"},
}

DEFAULT_PRIORITIES = [
    "완전일치 중대 오류 수정",
    "D 독립 검수 통과",
    "A 출처 계약·B 최신 판독의 C 실제 통합",
    "신규·정정·회수 공고의 증분 갱신",
    "100m 경계 거리 정확성 검증",
    "이후 500m → 1km 단계적 확장",
    "공식 원문·도면·타임라인·낙찰·보상사례·투자분석 고도화",
]

DEFAULT_FORBIDDEN = [
    "기존 개발창의 실행 중단",
    "다른 창의 작업 파일 직접 수정",
    "운영 서버·원장·지도·수집기·좌표 변경",
    "기존 고정판 덮어쓰기",
    "사용자 승인 없는 배포",
    "기존 업무관리 브라우저 UI 및 버튼 변경",
    "파일 수정 시각만으로 최신 합격판 결정",
    "검수 보류 후보를 합격으로 승격",
    "미검증 결과를 성공이라고 보고",
    "인계 문서 하나 생성한 것으로 자동 인계 완성 선언",
    "실제로 지원되지 않는 Claude 기능을 구현했다고 주장",
]


def _items():
    return {"schema": SCHEMA_VERSION, "generation": 0, "items": {}}


def default_role_state(role, meta):
    return {
        "schema": SCHEMA_VERSION, "generation": 0, "role": role,
        "name": meta.get("name", ""), "duties": meta.get("duties", ""),
        "reviewer": bool(meta.get("reviewer", False)),
        "workspace": meta.get("workspace", ""),        # 이 역할의 격리 작업 폴더(상대/절대)
        "latest_candidate": None,                        # 최신 개발 후보 ID (검수 여부와 무관)
        "last_passed_candidate": None,                   # 마지막 D 검수 합격판 ID
        "tasks": [],                                     # 작업 목록
        "resume": {"env": "", "command": "", "inputs": [], "notes": [], "do_not_touch": []},
        "dependencies": [],                              # 다른 역할에 기다리는 인계
        "last_report": "",                               # 마지막 보고 원문(요약 아님)
        "last_checkpoint": None,
    }


# ----------------------------------------------------------------------------
# 명령 구현
# ----------------------------------------------------------------------------
def cmd_init(st, args):
    if st.exists() and not args.force:
        print("이미 초기화되어 있습니다: %s" % st.path_of("project"))
        return 0
    st.ensure_dirs()
    project = {
        "schema": SCHEMA_VERSION, "generation": 0,
        "project": "INVESTMENT MAP",
        "purpose": "실제 경매물건을 클릭하면 보상사업 편입관계·공식 고시·법적 단계·토지조서·권리별 면적·도면·타임라인·인근 낙찰 및 보상사례를 확인하는 투자지도",
        "charter_file": "PROJECT_CHARTER.md",
        "roles": DEFAULT_ROLES,
        "priorities": DEFAULT_PRIORITIES,
        "forbidden": DEFAULT_FORBIDDEN,
        "lease_ttl_sec": DEFAULT_LEASE_TTL,
    }
    st.update("project", lambda d: project, default_factory=lambda: dict(project))
    for name in STATE_FILES[1:]:
        if not os.path.isfile(st.path_of(name)):
            st.update(name, lambda d: d, default_factory=_items)
    for role, meta in DEFAULT_ROLES.items():
        if not os.path.isfile(st.path_of("roles/" + role)):
            st.update("roles/" + role, lambda d: d, default_factory=lambda r=role, m=meta: default_role_state(r, m))
    st.journal("init")
    print("초기화 완료: %s" % st.root)
    return 0


def _project(st):
    return st.load("project")


def _role(st, role):
    p = _project(st)
    if role not in p["roles"]:
        raise HandoffError("알 수 없는 역할 '%s'. 등록된 역할: %s" % (role, ", ".join(sorted(p["roles"]))))
    return st.load("roles/" + role)


def _find_task(rs, task_id):
    for t in rs["tasks"]:
        if t["id"] == task_id:
            return t
    raise HandoffError("작업 ID '%s' 를 역할 %s 에서 찾을 수 없습니다." % (task_id, rs["role"]))


def _open_errors(st, role=None):
    errs = st.load("errors")["items"]
    out = []
    for eid, e in sorted(errs.items()):
        if e.get("status") in ("open", "fixed_unverified") and (role is None or e.get("owner") == role or role in e.get("affects", [])):
            out.append(e)
    return out


def _pending_handoffs(st, role):
    hs = st.load("handoffs")["items"]
    inbound = [h for h in hs.values() if h["to"] == role and h["status"] == "pending"]
    outbound = [h for h in hs.values() if h["from"] == role and h["status"] == "pending"]
    return inbound, outbound


def _resume_plan(st, rs):
    """완료 작업 건너뛰고 다음 안전 작업 선택."""
    done = [t for t in rs["tasks"] if t["status"] == "done"]
    in_prog = [t for t in rs["tasks"] if t["status"] == "in_progress"]
    blocked = [t for t in rs["tasks"] if t["status"] == "blocked"]
    todo = [t for t in rs["tasks"] if t["status"] == "todo"]
    approvals = st.load("decisions")["items"]
    approved_tasks = {d.get("approves_task") for d in approvals.values() if d.get("approves_task")}

    def deps_done(t):
        ids = {x["id"]: x for x in rs["tasks"]}
        return all(ids.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))

    waiting_approval, next_task = [], None
    for t in in_prog + sorted(todo, key=lambda x: (x.get("priority", 99), x["id"])):
        if t.get("requires_user_approval") and t["id"] not in approved_tasks:
            waiting_approval.append(t)
            continue
        if not deps_done(t):
            continue
        if next_task is None:
            next_task = t
    return {"done": done, "in_progress": in_prog, "blocked": blocked, "todo": todo,
            "waiting_user_approval": waiting_approval, "next": next_task}


def _candidate_view(st, cand_id):
    if not cand_id:
        return None
    c = st.load("candidates")["items"].get(cand_id)
    if c is None:
        return {"id": cand_id, "missing": True}
    v = dict(c)
    v["id"] = cand_id
    path = c.get("path")
    if path:
        full = path if os.path.isabs(path) else os.path.join(os.path.dirname(st.root), path)
        if os.path.isfile(full):
            cur = sha256_file(full)
            v["file_exists"] = True
            v["sha_matches"] = (cur == c["sha256"])
            v["current_sha256"] = cur
        else:
            v["file_exists"] = False
            v["sha_matches"] = None
    return v


def _label_candidate(v):
    if not v:
        return "없음"
    if v.get("missing"):
        return "%s (후보 등록 없음!)" % v["id"]
    rv = v.get("independent_review", {}).get("status", "pending")
    lab = {"pending": "독립 검수 대기", "hold": "독립 검수 보류", "pass": "독립 검수 합격", "fail": "독립 검수 불합격"}[rv]
    s = "%s  sha256=%s…  기반=%s  자체시험=%s  %s  사용자승인=%s  운영반영=%s" % (
        v["id"], v["sha256"][:16], v.get("base_candidate") or "-",
        v.get("self_test", {}).get("status", "none"), lab,
        "예" if v.get("user_approved") else "아니오", "예" if v.get("deployed") else "아니오")
    if v.get("file_exists") is False:
        s += "  [파일 없음: %s]" % v.get("path")
    elif v.get("sha_matches") is False:
        s += "  [경고: 파일이 등록 해시와 다름 → 고정 후 수정됨, 새 후보로 등록 필요]"
    return s


def briefing(st, role, lease_prev_state=None):
    p = _project(st)
    rs = _role(st, role)
    plan = _resume_plan(st, rs)
    errs = _open_errors(st, role)
    inbound, outbound = _pending_handoffs(st, role)
    latest = _candidate_view(st, rs["latest_candidate"])
    passed = _candidate_view(st, rs["last_passed_candidate"])
    decisions = st.load("decisions")["items"]
    prot = st.load("protected", default={"items": {}})
    lines = []
    A = lines.append
    A("=" * 78)
    A("INVESTMENT MAP 인계 브리핑  역할=%s (%s)  세션=%s" % (role, rs["name"], st.session))
    A("=" * 78)
    A("[1] 프로젝트 최상위 목적: %s" % p["purpose"])
    A("    상세 지침: %s  (반드시 읽을 것)" % os.path.join(st.root, p.get("charter_file", "PROJECT_CHARTER.md")))
    A("    우선순위: " + " > ".join("%d.%s" % (i + 1, x) for i, x in enumerate(p["priorities"])))
    A("[2] 담당 업무: %s" % rs["duties"])
    A("    격리 작업 영역: %s" % (rs["workspace"] or "(미설정 — 'role set-workspace' 로 지정)"))
    if lease_prev_state is not None:
        A("    임대 획득: 이전 상태=%s" % lease_prev_state)
    A("[3] 최신 개발 후보: %s" % _label_candidate(latest))
    A("    마지막 정상 합격판: %s" % _label_candidate(passed))
    if latest and passed and latest["id"] != passed["id"]:
        A("    ※ 최신 후보 ≠ 마지막 합격판. 최신 후보를 합격판으로 취급하지 말 것.")
    A("[4] 완료 작업 %d건 / 진행 중 %d건 / 미완료 %d건 / 차단 %d건" % (
        len(plan["done"]), len(plan["in_progress"]), len(plan["todo"]), len(plan["blocked"])))
    for t in plan["done"][-5:]:
        A("    ✔ %s  %s  (완료 %s)" % (t["id"], t["title"], t.get("completed_at", "")))
    for t in plan["in_progress"]:
        A("    ▶ %s  %s  (진행 중, 시작 %s)" % (t["id"], t["title"], t.get("started_at", "")))
    for t in plan["todo"]:
        A("    ☐ %s  %s%s" % (t["id"], t["title"], "  [사용자 승인 필요]" if t.get("requires_user_approval") else ""))
    for t in plan["blocked"]:
        A("    ⛔ %s  %s  (차단: %s)" % (t["id"], t["title"], t.get("blocked_reason", "")))
    A("[5] D 독립 검수: 최신 후보=%s / 합격판=%s" % (
        latest.get("independent_review", {}).get("status", "-") if latest and not latest.get("missing") else "-",
        passed.get("independent_review", {}).get("status", "-") if passed and not passed.get("missing") else "-"))
    A("[6] 미해결 오류 %d건" % len(errs))
    for e in errs:
        A("    ✖ %s [%s] %s" % (e["id"], e["status"], e["title"]))
        A("        재현: %s" % e.get("repro", ""))
        A("        기대/실제: %s / %s" % (e.get("expected", ""), e.get("actual", "")))
    A("    받을 인계(대기) %d건, 보낼 인계(대기) %d건" % (len(inbound), len(outbound)))
    for h in inbound:
        A("    ⇦ %s  %s→%s  후보=%s  sha=%s…  %s" % (h["id"], h["from"], h["to"], h.get("candidate"), (h.get("sha256") or "")[:16], h.get("note", "")))
    for h in outbound:
        A("    ⇨ %s  %s→%s  후보=%s  (상대 창이 아직 수락 안 함)" % (h["id"], h["from"], h["to"], h.get("candidate")))
    for d in rs.get("dependencies", []):
        A("    의존: %s" % d)
    A("[7] 중복 실행 방지: 위 ✔ 작업은 다시 수행하지 말 것. 'task complete' 는 증거 없이는 거부됨.")
    A("[8] 마지막 정상 체크포인트: %s" % json.dumps(rs.get("last_checkpoint"), ensure_ascii=False))
    A("[9] 보호 파일 매니페스트 %d건 — 'protect verify' 로 변경 여부 확인" % len(prot.get("items", {})))
    nt = plan["next"]
    A("[10] 다음 안전 작업: %s" % ("%s  %s" % (nt["id"], nt["title"]) if nt else "없음(모두 완료/차단/승인 대기)"))
    if nt:
        A("     작업 명령: %s" % (nt.get("command") or "(미기록)"))
    A("     역할 재개 명령(마지막 체크포인트): %s" % (rs["resume"].get("command") or "(미기록)"))
    for t in plan["waiting_user_approval"]:
        A("     ⏸ 사용자 승인 대기(자동 실행 금지): %s  %s" % (t["id"], t["title"]))
    A("     재개 환경: %s" % (rs["resume"].get("env") or "(미기록)"))
    for n in rs["resume"].get("notes", []):
        A("     주의: %s" % n)
    for f in rs["resume"].get("do_not_touch", []):
        A("     변경 금지: %s" % f)
    A("[11] 결과 반영: task start/complete, error add/update, checkpoint, release 명령으로 공통 저장소에 기록할 것.")
    A("사용자 결정 %d건(변경 금지, 'decision list'):" % len(decisions))
    for did, d in sorted(decisions.items())[-5:]:
        A("    • %s  %s" % (did, d["text"]))
    if rs.get("last_report"):
        A("-" * 78)
        A("마지막 보고 원문:")
        A(rs["last_report"])
    A("=" * 78)
    return "\n".join(lines)


def cmd_takeover(st, args):
    if not st.exists():
        raise HandoffError("공통 인계 저장소가 없습니다: %s  (먼저 'init' 실행)" % st.root)
    role = args.role.upper()
    _role(st, role)  # 존재 검증
    p = _project(st)
    lease, prev = st.acquire_lease(role, ttl=p.get("lease_ttl_sec", DEFAULT_LEASE_TTL), force=args.force, reason=args.reason or "")
    if prev in ("expired", "dead", "corrupt"):
        print("※ 이전 작업창의 임대가 '%s' 상태였으므로 회수했습니다. 진행 중 작업은 비정상 종료 가능성을 염두에 두고 검토하세요." % prev)
    print(briefing(st, role, lease_prev_state=prev))
    if args.json:
        rs = _role(st, role)
        plan = _resume_plan(st, rs)
        out = {"role": role, "session": st.session, "lease": lease, "next": plan["next"],
               "done_ids": [t["id"] for t in plan["done"]],
               "latest_candidate": _candidate_view(st, rs["latest_candidate"]),
               "last_passed_candidate": _candidate_view(st, rs["last_passed_candidate"]),
               "open_errors": _open_errors(st, role)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_status(st, args):
    if not st.exists():
        raise HandoffError("공통 인계 저장소가 없습니다: %s" % st.root)
    p = _project(st)
    if args.role:
        print(briefing(st, args.role.upper()))
        return 0
    print("INVESTMENT MAP 프로젝트 상태 (읽기 전용)  저장소=%s" % st.root)
    for role in sorted(p["roles"]):
        rs = _role(st, role)
        state, lease = st.lease_state(role)
        plan = _resume_plan(st, rs)
        owner = "" if state == "free" else " 소유=%s(%s)" % (lease.get("session"), state)
        print("  %s %-14s 임대=%-7s%s  완료%d 진행%d 미완%d 차단%d  최신후보=%s 합격판=%s" % (
            role, rs["name"], state, owner, len(plan["done"]), len(plan["in_progress"]), len(plan["todo"]), len(plan["blocked"]),
            rs["latest_candidate"] or "-", rs["last_passed_candidate"] or "-"))
    print("담당 역할을 지정하지 않았으므로 어떤 역할의 작업도 점유하지 않았습니다. 'takeover <역할>' 로 지정하세요.")
    return 0


def cmd_heartbeat(st, args):
    role = args.role.upper()
    if args.daemon:
        # 장기 실행 심장박동: 이 프로세스 PID 를 추적 대상으로 등록 → 죽으면 'dead' 로 판정되어 회수 가능
        st.heartbeat(role, track_pid=os.getpid())
        print("심장박동 데몬 시작: %s (PID %d, %ds 간격). Ctrl+C 로 종료." % (role, os.getpid(), args.interval))
        try:
            while True:
                time.sleep(args.interval)
                st.heartbeat(role, track_pid=os.getpid())
        except KeyboardInterrupt:
            return 0
        except HandoffError as e:
            print("심장박동 중단: %s" % e, file=sys.stderr)
            return 2
    st.heartbeat(role)
    print("심장박동 갱신: %s" % role)
    return 0


def cmd_release(st, args):
    st.release_lease(args.role.upper())
    print("임대 해제: %s" % args.role.upper())
    return 0


# ---- 작업 ----
def cmd_task(st, args):
    role = args.role.upper()
    st.require_lease(role)
    if args.action == "add":
        def fn(d):
            if any(t["id"] == args.id for t in d["tasks"]):
                raise HandoffError("작업 ID 중복: %s" % args.id)
            d["tasks"].append({
                "id": args.id, "title": args.title, "status": "todo", "priority": args.priority,
                "requires_user_approval": bool(args.requires_approval), "depends_on": args.depends_on or [],
                "command": args.command or "", "created_at": now_iso(), "created_by": st.session,
            })
            return d
        st.update("roles/" + role, fn, expected_generation=args.expect_gen)
        st.journal("task_add", role=role, task=args.id)
    elif args.action == "start":
        def fn(d):
            t = _find_task(d, args.id)
            if t["status"] == "done":
                raise HandoffError("이미 완료된 작업입니다(중복 실행 거부): %s  완료 %s  증거=%s" % (t["id"], t.get("completed_at"), t.get("evidence")))
            if t.get("requires_user_approval"):
                approvals = st.load("decisions")["items"]
                if not any(dd.get("approves_task") == t["id"] for dd in approvals.values()):
                    raise HandoffError("사용자 승인이 필요한 작업입니다. 승인 결정('decision add --approves-task %s --user-approved')이 없어 시작을 거부합니다." % t["id"])
            t["status"] = "in_progress"
            t["started_at"] = now_iso()
            t["started_by"] = st.session
            return d
        st.update("roles/" + role, fn, expected_generation=args.expect_gen)
        st.journal("task_start", role=role, task=args.id)
    elif args.action == "complete":
        if not args.evidence:
            raise HandoffError("완료 승격에는 --evidence (검증 결과/명령 출력/파일 SHA 등 증거)가 필요합니다.")
        def fn(d):
            t = _find_task(d, args.id)
            if t["status"] == "done":
                raise HandoffError("이미 완료된 작업입니다: %s" % t["id"])
            if t["status"] != "in_progress" and not args.allow_direct:
                raise HandoffError("진행 중(in_progress)이 아닌 작업을 바로 완료할 수 없습니다 (status=%s). 먼저 'task start'." % t["status"])
            t["status"] = "done"
            t["completed_at"] = now_iso()
            t["completed_by"] = st.session
            t["evidence"] = args.evidence
            if args.sha_file:
                t["evidence_files"] = {f: sha256_file(f) for f in args.sha_file}
            return d
        st.update("roles/" + role, fn, expected_generation=args.expect_gen)
        st.journal("task_complete", role=role, task=args.id)
    elif args.action == "block":
        def fn(d):
            t = _find_task(d, args.id)
            t["status"] = "blocked"
            t["blocked_reason"] = args.reason or ""
            return d
        st.update("roles/" + role, fn, expected_generation=args.expect_gen)
    elif args.action == "reopen":
        def fn(d):
            t = _find_task(d, args.id)
            if t["status"] == "done" and not args.reason:
                raise HandoffError("완료 작업을 다시 열려면 --reason 이 필요합니다.")
            t["status"] = "todo"
            t["reopened_reason"] = args.reason or ""
            return d
        st.update("roles/" + role, fn, expected_generation=args.expect_gen)
    print("작업 %s: %s/%s" % (args.action, role, args.id))
    return 0


# ---- 후보 ----
def cmd_candidate(st, args):
    if args.action == "register":
        role = args.role.upper()
        st.require_lease(role)
        path = args.path
        full = path if os.path.isabs(path) else os.path.join(os.path.dirname(st.root), path)
        if not os.path.isfile(full):
            raise HandoffError("후보 파일이 없습니다: %s" % full)
        sha = sha256_file(full)
        cid = args.id or "%s-%s-%s" % (role, _dt.datetime.now().strftime("%Y%m%d-%H%M%S"), sha[:8])

        def fn(d):
            if cid in d["items"]:
                raise HandoffError("후보 ID 중복: %s" % cid)
            for k, v in d["items"].items():
                if v["sha256"] == sha and v["role"] == role:
                    raise HandoffError("동일 SHA의 후보가 이미 있습니다: %s" % k)
            base = args.base
            if base and base not in d["items"]:
                raise HandoffError("기반 후보가 등록되어 있지 않습니다: %s" % base)
            d["items"][cid] = {
                "role": role, "path": path, "sha256": sha, "created_at": now_iso(), "created_by": st.session,
                "base_candidate": base, "inputs": args.input or [],
                "self_test": {"status": "none"}, "independent_review": {"status": "pending"},
                "user_approved": False, "deployed": False, "frozen": True, "note": args.note or "",
            }
            return d
        st.update("candidates", fn)
        if not args.no_set_latest:
            st.update("roles/" + role, lambda d: dict(d, latest_candidate=cid))
        st.journal("candidate_register", role=role, candidate=cid, sha256=sha)
        print("후보 등록: %s  sha256=%s" % (cid, sha))
    elif args.action == "self-test":
        def fn(d):
            c = d["items"].get(args.id)
            if not c:
                raise HandoffError("후보 없음: %s" % args.id)
            st.require_lease(c["role"])
            c["self_test"] = {"status": args.status, "at": now_iso(), "by": st.session, "note": args.note or ""}
            return d
        st.update("candidates", fn)
        print("자체 시험 기록: %s=%s" % (args.id, args.status))
    elif args.action == "review":
        reviewer = args.by.upper()
        p = _project(st)
        if not p["roles"].get(reviewer, {}).get("reviewer"):
            raise HandoffError("역할 %s 는 독립 검수 권한(reviewer)이 없습니다. 자체 시험은 'self-test' 로 기록하세요." % reviewer)
        st.require_lease(reviewer)

        def fn(d):
            c = d["items"].get(args.id)
            if not c:
                raise HandoffError("후보 없음: %s" % args.id)
            if c["role"] == reviewer:
                raise HandoffError("자기 역할의 후보를 독립 검수로 기록할 수 없습니다.")
            v = _candidate_view(st, args.id)
            if v.get("sha_matches") is False and args.status == "pass":
                raise HandoffError("후보 파일이 등록 해시와 다릅니다(고정 후 수정됨). 합격 처리 거부. 새 후보로 다시 등록하세요.")
            c["independent_review"] = {"status": args.status, "by": reviewer, "at": now_iso(), "session": st.session,
                                       "note": args.note or "", "reviewed_sha256": c["sha256"]}
            return d
        st.update("candidates", fn)
        st.journal("candidate_review", candidate=args.id, status=args.status, by=reviewer)
        print("독립 검수 기록: %s=%s (by %s)" % (args.id, args.status, reviewer))
    elif args.action == "set-passed":
        role = args.role.upper()
        st.require_lease(role)
        c = st.load("candidates")["items"].get(args.id)
        if not c:
            raise HandoffError("후보 없음: %s" % args.id)
        if c["role"] != role:
            raise HandoffError("역할 불일치: 후보 %s 는 역할 %s 소유" % (args.id, c["role"]))
        rv = c["independent_review"]
        if rv.get("status") != "pass":
            raise HandoffError("독립 검수 상태가 '%s' 인 후보는 마지막 합격판으로 설정할 수 없습니다 (pass 필요). 검수 보류/대기 후보를 합격으로 승격하지 마세요." % rv.get("status"))
        if rv.get("reviewed_sha256") != c["sha256"]:
            raise HandoffError("검수된 SHA와 후보 SHA가 다릅니다.")
        v = _candidate_view(st, args.id)
        if v.get("sha_matches") is False:
            raise HandoffError("후보 파일이 등록 해시와 달라 합격판 설정을 거부합니다.")
        st.update("roles/" + role, lambda d: dict(d, last_passed_candidate=args.id))
        st.journal("set_passed", role=role, candidate=args.id)
        print("마지막 합격판 설정: %s=%s" % (role, args.id))
    elif args.action == "approve":
        # 사용자 승인: --user-approved 플래그 없이는 거부
        if not args.user_approved:
            raise HandoffError("사용자 승인 기록에는 --user-approved 플래그가 필요합니다. (사용자가 명시적으로 승인한 경우에만 사용)")
        def fn(d):
            c = d["items"].get(args.id)
            if not c:
                raise HandoffError("후보 없음: %s" % args.id)
            c["user_approved"] = True
            c["user_approved_at"] = now_iso()
            c["user_approval_note"] = args.note or ""
            return d
        st.update("candidates", fn)
        st.update("decisions", lambda d: _add_decision(d, st, "후보 %s 사용자 승인: %s" % (args.id, args.note or ""), approves_candidate=args.id))
        print("사용자 승인 기록: %s" % args.id)
    elif args.action == "verify":
        v = _candidate_view(st, args.id)
        print(_label_candidate(v))
        return 0 if v and v.get("sha_matches") else 1
    elif args.action == "chain":
        items = st.load("candidates")["items"]
        cid, seen = args.id, []
        ok = True
        while cid and cid not in seen:
            seen.append(cid)
            c = items.get(cid)
            if not c:
                print("  %s  (등록 없음!)" % cid)
                ok = False
                break
            v = _candidate_view(st, cid)
            flag = "OK" if v.get("sha_matches") else ("파일없음" if v.get("file_exists") is False else "SHA불일치")
            if flag != "OK":
                ok = False
            print("  %s  역할=%s  sha=%s…  검수=%s  [%s]" % (cid, c["role"], c["sha256"][:16], c["independent_review"]["status"], flag))
            cid = c.get("base_candidate")
        return 0 if ok else 1
    elif args.action == "list":
        items = st.load("candidates")["items"]
        for cid in sorted(items):
            print(_label_candidate(_candidate_view(st, cid)))
    return 0


def _add_decision(d, st, text, **extra):
    did = "DEC-%s-%s" % (_dt.datetime.now().strftime("%Y%m%d%H%M%S"), uuid.uuid4().hex[:4])
    rec = {"text": text, "at": now_iso(), "recorded_by": st.session, "user_approved": True}
    rec.update(extra)
    d["items"][did] = rec
    return d


def cmd_decision(st, args):
    if args.action == "list":
        for did, d in sorted(st.load("decisions")["items"].items()):
            print("%s  %s  %s" % (did, d["at"], d["text"]), end="")
            if d.get("approves_task"):
                print("  [작업 승인: %s]" % d["approves_task"], end="")
            print()
        return 0
    if args.action == "add":
        if not args.user_approved:
            raise HandoffError("사용자 결정은 사용자가 명시적으로 승인한 경우에만 --user-approved 와 함께 기록할 수 있습니다. 자동 기록 거부.")
        st.update("decisions", lambda d: _add_decision(d, st, args.text, approves_task=args.approves_task))
        print("사용자 결정 기록 완료")
        return 0
    if args.action in ("edit", "delete"):
        raise HandoffError("기존 사용자 결정은 수정·삭제할 수 없습니다. 변경이 필요하면 새 결정을 추가해 이전 결정을 참조하세요.")
    return 0


# ---- 오류 ----
def cmd_error(st, args):
    if args.action == "add":
        role = args.owner.upper()
        st.require_lease(role)
        eid = args.id or "ERR-%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), uuid.uuid4().hex[:4])
        def fn(d):
            if eid in d["items"]:
                raise HandoffError("오류 ID 중복: %s" % eid)
            d["items"][eid] = {
                "id": eid, "title": args.title, "found_at": now_iso(), "found_by": st.session,
                "owner": role, "affects": [x.upper() for x in (args.affects or [])],
                "basis": args.basis or "", "repro": args.repro or "", "expected": args.expected or "", "actual": args.actual or "",
                "cause": args.cause or "", "status": "open", "fix_files": {}, "verification": "", "unresolved_reason": "", "resume_condition": "",
            }
            return d
        st.update("errors", fn)
        st.journal("error_add", error=eid, owner=role)
        print("오류 기록: %s" % eid)
    elif args.action == "update":
        def fn(d):
            e = d["items"].get(args.id)
            if not e:
                raise HandoffError("오류 없음: %s" % args.id)
            st.require_lease(e["owner"])
            if args.status:
                if args.status == "verified" and not args.verification:
                    raise HandoffError("'verified' 로 바꾸려면 --verification (재시험 결과)이 필요합니다.")
                e["status"] = args.status
            for k in ("cause", "verification", "unresolved_reason", "resume_condition", "repro"):
                v = getattr(args, k, None)
                if v:
                    e[k] = v
            for f in args.fix_file or []:
                e["fix_files"][f] = sha256_file(f) if os.path.isfile(f) else None
            e["updated_at"] = now_iso()
            return d
        st.update("errors", fn)
        print("오류 갱신: %s" % args.id)
    elif args.action == "list":
        for e in _open_errors(st, args.owner.upper() if args.owner else None):
            print("%s [%s] %s\n   재현: %s\n   기대/실제: %s / %s" % (e["id"], e["status"], e["title"], e["repro"], e["expected"], e["actual"]))
    return 0


# ---- 인계 메시지 ----
def cmd_handoff(st, args):
    if args.action == "send":
        frm, to = args.frm.upper(), args.to.upper()
        st.require_lease(frm)
        _role(st, to)
        eid = args.event_id or uuid.uuid4().hex
        cands = st.load("candidates")["items"]
        c = cands.get(args.candidate) if args.candidate else None
        if args.candidate and not c:
            raise HandoffError("후보 없음: %s" % args.candidate)
        # 이벤트 ID 중복 처리 방지
        ev = st.load("events")
        if eid in ev["items"]:
            print("동일 인계 이벤트가 이미 처리되었습니다(중복 무시): %s → %s" % (eid, ev["items"][eid]))
            return 0
        hid = "HO-%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), uuid.uuid4().hex[:4])
        st.update("handoffs", lambda d: _put(d, hid, {
            "id": hid, "from": frm, "to": to, "candidate": args.candidate, "sha256": c["sha256"] if c else None,
            "note": args.note or "", "files": {f: sha256_file(f) for f in (args.file or []) if os.path.isfile(f)},
            "status": "pending", "sent_at": now_iso(), "sent_by": st.session, "event_id": eid}))
        st.update("events", lambda d: _put(d, eid, hid))
        st.journal("handoff_send", handoff=hid, frm=frm, to=to, candidate=args.candidate, event_id=eid)
        print("인계 전송: %s  %s→%s  후보=%s" % (hid, frm, to, args.candidate))
    elif args.action == "accept":
        role = args.role.upper()
        st.require_lease(role)
        def fn(d):
            h = d["items"].get(args.id)
            if not h:
                raise HandoffError("인계 없음: %s" % args.id)
            if h["to"] != role:
                raise HandoffError("이 인계의 수신 역할은 %s 입니다." % h["to"])
            if h["status"] != "pending":
                raise HandoffError("이미 %s 처리된 인계입니다." % h["status"])
            if h.get("candidate"):
                v = _candidate_view(st, h["candidate"])
                if v.get("sha_matches") is False:
                    raise HandoffError("인계된 후보 파일 SHA가 등록 해시와 다릅니다. 보낸 창에 새 고정 후보 등록을 요청하세요.")
            h["status"] = "accepted"
            h["accepted_at"] = now_iso()
            h["accepted_by"] = st.session
            return d
        st.update("handoffs", fn)
        st.journal("handoff_accept", handoff=args.id, role=role)
        print("인계 수락: %s" % args.id)
    elif args.action == "list":
        for hid, h in sorted(st.load("handoffs")["items"].items()):
            print("%s  %s→%s  후보=%s  sha=%s…  %s  %s" % (hid, h["from"], h["to"], h.get("candidate"), (h.get("sha256") or "")[:16], h["status"], h.get("note", "")))
    return 0


def _put(d, key, value):
    d["items"][key] = value
    return d


# ---- 체크포인트 / 역할 설정 ----
def cmd_checkpoint(st, args):
    role = args.role.upper()
    st.require_lease(role)
    files = {}
    for f in args.file or []:
        if not os.path.isfile(f):
            raise HandoffError("체크포인트 파일 없음: %s" % f)
        files[f] = sha256_file(f)
    report = ""
    if args.report_file:
        with open(args.report_file, "r", encoding="utf-8") as fh:
            report = fh.read()
    elif args.report:
        report = args.report

    def fn(d):
        cp = {"id": "CP-%s-%s" % (_dt.datetime.now().strftime("%Y%m%d-%H%M%S"), uuid.uuid4().hex[:4]),
              "at": now_iso(), "session": st.session, "files": files, "note": args.note or "",
              "latest_candidate": d["latest_candidate"], "last_passed_candidate": d["last_passed_candidate"],
              "open_errors": [e["id"] for e in _open_errors(st, role)],
              "tasks": {t["id"]: t["status"] for t in d["tasks"]}}
        d["last_checkpoint"] = cp
        if report:
            d["last_report"] = report
        if args.next_command:
            d["resume"]["command"] = args.next_command
        if args.env:
            d["resume"]["env"] = args.env
        if args.note_resume:
            d["resume"]["notes"] = list(dict.fromkeys(d["resume"]["notes"] + args.note_resume))
        if args.do_not_touch:
            d["resume"]["do_not_touch"] = list(dict.fromkeys(d["resume"]["do_not_touch"] + args.do_not_touch))
        if args.dependency:
            d["dependencies"] = list(dict.fromkeys(d["dependencies"] + args.dependency))
        return d
    new = st.update("roles/" + role, fn, expected_generation=args.expect_gen)
    st.journal("checkpoint", role=role, checkpoint=new["last_checkpoint"]["id"])
    print("체크포인트 기록: %s (세대 %d)" % (new["last_checkpoint"]["id"], new["generation"]))
    if args.release:
        st.release_lease(role)
        print("임대 해제: %s" % role)
    return 0


def cmd_role(st, args):
    role = args.role.upper()
    if args.action == "set-workspace":
        st.require_lease(role)
        st.update("roles/" + role, lambda d: dict(d, workspace=args.value))
        print("작업 영역 설정: %s=%s" % (role, args.value))
    elif args.action == "show":
        print(json.dumps(_role(st, role), ensure_ascii=False, indent=2))
    elif args.action == "gen":
        print(_role(st, role)["generation"])
    return 0


# ---- 보호 파일 매니페스트 ----
def _iter_paths(paths, base):
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(base, p)
        if os.path.isdir(full):
            for dp, dns, fns in os.walk(full):
                dns[:] = [x for x in dns if x not in (".git",)]
                for fn in fns:
                    yield os.path.relpath(os.path.join(dp, fn), base)
        elif os.path.isfile(full):
            yield os.path.relpath(full, base)


def cmd_protect(st, args):
    base = os.path.dirname(st.root)  # 프로젝트 루트(= _HANDOFF 의 부모)
    if args.action == "snapshot":
        items = {}
        for rel in _iter_paths(args.path, base):
            if rel.startswith("_HANDOFF") or ".git" in rel.split(os.sep):
                continue
            items[rel.replace(os.sep, "/")] = {"sha256": sha256_file(os.path.join(base, rel)), "size": os.path.getsize(os.path.join(base, rel))}
        def fn(d):
            d["items"] = items
            d["base"] = base
            d["label"] = args.label or ""
            return d
        st.update("protected", fn, default_factory=_items)
        st.journal("protect_snapshot", count=len(items), label=args.label or "")
        print("보호 매니페스트 %d건 기록 (base=%s)" % (len(items), base))
        return 0
    if args.action == "verify":
        man = st.load("protected")
        changed, missing, ok = [], [], 0
        for rel, meta in sorted(man["items"].items()):
            full = os.path.join(base, rel)
            if not os.path.isfile(full):
                missing.append(rel)
            elif sha256_file(full) != meta["sha256"]:
                changed.append(rel)
            else:
                ok += 1
        print("보호 파일 검증: 일치 %d / 변경 %d / 누락 %d" % (ok, len(changed), len(missing)))
        for r in changed:
            print("  변경됨: %s" % r)
        for r in missing:
            print("  누락: %s" % r)
        return 0 if not changed and not missing else 1
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(prog="handoff.py", description="INVESTMENT MAP 공통 작업 인계 도구")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="_HANDOFF 저장소 경로 (기본: 이 파일의 폴더, 환경변수 HANDOFF_ROOT)")
    ap.add_argument("--session", default=None, help="작업창(세션) ID (환경변수 HANDOFF_SESSION)")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init"); p.add_argument("--force", action="store_true")
    p = sp.add_parser("takeover", help="역할 인계받기(임대 획득 + 브리핑)")
    p.add_argument("role"); p.add_argument("--force", action="store_true"); p.add_argument("--reason", default="")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("status"); p.add_argument("role", nargs="?")
    p = sp.add_parser("heartbeat"); p.add_argument("role"); p.add_argument("--daemon", action="store_true"); p.add_argument("--interval", type=int, default=60)
    p = sp.add_parser("release"); p.add_argument("role")

    p = sp.add_parser("task"); p.add_argument("action", choices=["add", "start", "complete", "block", "reopen"])
    p.add_argument("role"); p.add_argument("id"); p.add_argument("--title", default="")
    p.add_argument("--priority", type=int, default=50); p.add_argument("--requires-approval", action="store_true")
    p.add_argument("--depends-on", nargs="*"); p.add_argument("--command", default="")
    p.add_argument("--evidence", default=""); p.add_argument("--sha-file", nargs="*"); p.add_argument("--allow-direct", action="store_true")
    p.add_argument("--reason", default=""); p.add_argument("--expect-gen", type=int, default=None)

    p = sp.add_parser("candidate"); p.add_argument("action", choices=["register", "self-test", "review", "set-passed", "approve", "verify", "chain", "list"])
    p.add_argument("--role", default=""); p.add_argument("--id", default=""); p.add_argument("--path", default="")
    p.add_argument("--base", default=None); p.add_argument("--input", nargs="*"); p.add_argument("--note", default="")
    p.add_argument("--status", default="", choices=["", "none", "pass", "fail", "hold", "pending"]); p.add_argument("--by", default="")
    p.add_argument("--no-set-latest", action="store_true"); p.add_argument("--user-approved", action="store_true")

    p = sp.add_parser("decision"); p.add_argument("action", choices=["list", "add", "edit", "delete"])
    p.add_argument("--text", default=""); p.add_argument("--approves-task", default=None); p.add_argument("--user-approved", action="store_true")

    p = sp.add_parser("error"); p.add_argument("action", choices=["add", "update", "list"])
    p.add_argument("--id", default=""); p.add_argument("--owner", default=""); p.add_argument("--title", default="")
    p.add_argument("--affects", nargs="*"); p.add_argument("--basis", default=""); p.add_argument("--repro", default="")
    p.add_argument("--expected", default=""); p.add_argument("--actual", default=""); p.add_argument("--cause", default="")
    p.add_argument("--status", default="", choices=["", "open", "fixed_unverified", "verified", "wontfix"])
    p.add_argument("--verification", default=""); p.add_argument("--unresolved-reason", dest="unresolved_reason", default="")
    p.add_argument("--resume-condition", dest="resume_condition", default=""); p.add_argument("--fix-file", nargs="*")

    p = sp.add_parser("handoff"); p.add_argument("action", choices=["send", "accept", "list"])
    p.add_argument("--from", dest="frm", default=""); p.add_argument("--to", default=""); p.add_argument("--role", default="")
    p.add_argument("--id", default=""); p.add_argument("--candidate", default=""); p.add_argument("--note", default="")
    p.add_argument("--file", nargs="*"); p.add_argument("--event-id", default="")

    p = sp.add_parser("checkpoint"); p.add_argument("role")
    p.add_argument("--file", nargs="*"); p.add_argument("--note", default=""); p.add_argument("--report", default=""); p.add_argument("--report-file", default="")
    p.add_argument("--next-command", default=""); p.add_argument("--env", default=""); p.add_argument("--note-resume", nargs="*")
    p.add_argument("--do-not-touch", nargs="*"); p.add_argument("--dependency", nargs="*"); p.add_argument("--release", action="store_true")
    p.add_argument("--expect-gen", type=int, default=None)

    p = sp.add_parser("role"); p.add_argument("action", choices=["set-workspace", "show", "gen"]); p.add_argument("role"); p.add_argument("value", nargs="?")
    p = sp.add_parser("protect"); p.add_argument("action", choices=["snapshot", "verify"]); p.add_argument("--path", nargs="*", default=["."]); p.add_argument("--label", default="")
    return ap


COMMANDS = {"init": cmd_init, "takeover": cmd_takeover, "status": cmd_status, "heartbeat": cmd_heartbeat, "release": cmd_release,
            "task": cmd_task, "candidate": cmd_candidate, "decision": cmd_decision, "error": cmd_error, "handoff": cmd_handoff,
            "checkpoint": cmd_checkpoint, "role": cmd_role, "protect": cmd_protect}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    st = Store(root=args.root, session=args.session)
    try:
        return COMMANDS[args.cmd](st, args) or 0
    except ConflictError as e:
        print("충돌: %s" % e, file=sys.stderr)
        return 3
    except HandoffError as e:
        print("거부: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
