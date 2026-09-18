# -*- coding: utf-8 -*-
"""存储层：SQLite（WAL 模式，支持多进程/多线程读写）。

为什么用 SQLite 而不是直接改 JS 文件
------------------------------------
* 多个 agent 可能**同时**录任务 → 直接改同一个 js 文件必然互相覆盖；
  SQLite 有事务和锁，天然安全。
* 任务需要"改状态、删除、按部门筛选" → 数据库一条 SQL 就够，改文件要全文重写易出错。
* `tasks-data/tasks.js` 变成**导出产物**（给人看/给看板读），不再是人手改的数据源。
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id            TEXT PRIMARY KEY,
  dept          TEXT NOT NULL,
  title         TEXT NOT NULL,
  desc          TEXT DEFAULT '',
  status        TEXT NOT NULL,
  priority      TEXT NOT NULL,
  project       TEXT DEFAULT '',
  source        TEXT DEFAULT '',
  agent         TEXT DEFAULT '',
  external_id   TEXT DEFAULT '',
  dedup_key     TEXT NOT NULL,
  due           TEXT DEFAULT '',
  tags          TEXT DEFAULT '[]',
  collaborators TEXT DEFAULT '[]',
  auto          INTEGER DEFAULT 0,
  session       TEXT,
  dept_source   TEXT DEFAULT '',   -- expert | guessed | none（部门是怎么定的）
  dept_reason   TEXT DEFAULT '',   -- 上游给出归类理由（可选，供人复核）
  assignee      TEXT DEFAULT '',   -- 认领被批准后落定的执行方
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  done_at       TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_tasks_dedup ON tasks(dept, dedup_key);
CREATE INDEX IF NOT EXISTS ix_tasks_dept   ON tasks(dept);
CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status);

-- 认领申请：agent 说「这条我能干」，但**不直接开工**，等人工批准。
-- 为什么单独一张表：一条任务可能被多个 agent 同时看中，得让用户有得选、
-- 也得留下「谁在什么时候申请过、批没批、为什么驳回」的痕迹（纯追加，不覆盖历史）。
CREATE TABLE IF NOT EXISTS claims (
  id         TEXT PRIMARY KEY,
  task_id    TEXT NOT NULL,
  agent      TEXT NOT NULL,
  note       TEXT DEFAULT '',      -- agent 说自己为什么能接、打算怎么做
  status     TEXT NOT NULL,        -- proposed | approved | rejected | withdrawn
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by TEXT DEFAULT '',
  reason     TEXT DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_claims_task_agent ON claims(task_id, agent);
CREATE INDEX IF NOT EXISTS ix_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS ix_claims_task   ON claims(task_id);

CREATE TABLE IF NOT EXISTS ingest_log (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  at        TEXT NOT NULL,
  origin    TEXT NOT NULL,
  filename  TEXT DEFAULT '',
  added     INTEGER DEFAULT 0,
  updated   INTEGER DEFAULT 0,
  skipped   INTEGER DEFAULT 0,
  errors    TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS event_log (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      TEXT NOT NULL,
  actor   TEXT DEFAULT '',
  action  TEXT NOT NULL,
  task_id TEXT DEFAULT '',
  detail  TEXT DEFAULT ''
);
"""


def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


#: 后加的列 → 老库自动补齐（SQLite 的 ADD COLUMN 只能加在最后，这里足够）
_MIGRATIONS = {
    "tasks": [("dept_source", "TEXT DEFAULT ''"), ("dept_reason", "TEXT DEFAULT ''"),
              ("assignee", "TEXT DEFAULT ''")],
}


def claim_id(task_id: str, agent: str) -> str:
    """同一条任务 + 同一个 agent 的申请共用一个 id → 重复申请是"更新"而不是刷屏。"""
    h = hashlib.sha1(("{}|{}".format(task_id, agent)).encode("utf-8")).hexdigest()[:10]
    return "cl-" + h


class Store:
    def __init__(self, db_file: Path):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._conn() as c:
            c.executescript(SCHEMA)
            self._migrate(c)

    def _migrate(self, c: sqlite3.Connection):
        for table, cols in _MIGRATIONS.items():
            have = {r["name"] for r in c.execute("PRAGMA table_info({})".format(table))}
            for name, ddl in cols:
                if name not in have:
                    c.execute("ALTER TABLE {} ADD COLUMN {} {}".format(table, name, ddl))

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.db_file), timeout=15, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA busy_timeout=15000")
        return c

    # ---------------- 写入 ----------------
    def upsert(self, t: dict, actor: str = "") -> str:
        """按 (dept, dedup_key) 唯一键写入；已存在则更新。返回 'added' 或 'updated'。"""
        now = now_iso()
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT id, status FROM tasks WHERE dept=? AND dedup_key=?",
                (t["dept"], t["dedup_key"])).fetchone()
            done_at = now if t["status"] == "done" else None
            if row:
                c.execute(
                    """UPDATE tasks SET id=?, title=?, desc=?, status=?, priority=?, project=?,
                       source=?, agent=?, external_id=?, due=?, tags=?, collaborators=?, auto=?,
                       session=?, dept_source=?, dept_reason=?, updated_at=?, done_at=COALESCE(?, done_at)
                       WHERE id=?""",
                    (t["id"], t["title"], t["desc"], t["status"], t["priority"], t["project"],
                     t["source"], t["agent"], t["external_id"], t["due"],
                     json.dumps(t["tags"], ensure_ascii=False),
                     json.dumps(t["collaborators"], ensure_ascii=False),
                     1 if t["auto"] else 0, t.get("session"),
                     t.get("dept_source", ""), t.get("dept_reason", ""),
                     now, done_at, row["id"]))
                c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                          (now, actor, "update", t["id"], t["title"]))
                return "updated"
            c.execute(
                """INSERT INTO tasks(id,dept,title,desc,status,priority,project,source,agent,
                   external_id,dedup_key,due,tags,collaborators,auto,session,
                   dept_source,dept_reason,created_at,updated_at,done_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (t["id"], t["dept"], t["title"], t["desc"], t["status"], t["priority"], t["project"],
                 t["source"], t["agent"], t["external_id"], t["dedup_key"], t["due"],
                 json.dumps(t["tags"], ensure_ascii=False),
                 json.dumps(t["collaborators"], ensure_ascii=False),
                 1 if t["auto"] else 0, t.get("session"),
                 t.get("dept_source", ""), t.get("dept_reason", ""), now, now, done_at))
            c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                      (now, actor, "add", t["id"], t["title"]))
            return "added"

    def add_many(self, tasks: list[dict], actor: str = "") -> dict:
        res = {"added": 0, "updated": 0, "errors": []}
        for t in tasks:
            try:
                r = self.upsert(t, actor)
                res[r] += 1
            except Exception as e:                                  # noqa: BLE001
                res["errors"].append("{}: {}".format(t.get("title", "?"), e))
        return res

    def patch(self, task_id: str, fields: dict, actor: str = "") -> dict | None:
        allow = ("title", "desc", "status", "priority", "project", "source", "agent",
                 "due", "tags", "collaborators", "auto", "dept", "assignee",
                 "dept_source", "dept_reason")
        sets, vals = [], []
        for k, v in fields.items():
            if k not in allow:
                continue
            if k in ("tags", "collaborators"):
                v = json.dumps(v if isinstance(v, list) else [str(v)], ensure_ascii=False)
            if k == "auto":
                v = 1 if v else 0
            sets.append("{}=?".format(k))
            vals.append(v)
        if not sets:
            return self.get(task_id)
        now = now_iso()
        if fields.get("status") == "done":
            sets.append("done_at=?")
            vals.append(now)
        sets.append("updated_at=?")
        vals.append(now)
        vals.append(task_id)
        with self._lock, self._conn() as c:
            cur = c.execute("UPDATE tasks SET {} WHERE id=?".format(",".join(sets)), vals)
            if cur.rowcount:
                c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                          (now, actor, "patch", task_id, json.dumps(fields, ensure_ascii=False)))
        return self.get(task_id)

    # ---------------- 认领（A+B 中间态：建议认领 + 人工确认） ----------------
    #
    # 流程：agent 看中某条待办 → claim_propose() 只**登记意向**，不动任务状态；
    #       人在看板上点「批准」→ claim_decide(approve) 才把任务标成 in_progress
    #       并把 assignee 落定；被驳回的申请留在表里当审计痕迹，不删。
    # 为什么不让 agent 直接改状态：那样人工审核关口就没了，任务会被悄悄领走。
    def claim_propose(self, task_id: str, agent: str, note: str = "", actor: str = "") -> dict:
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        agent = (agent or "").strip()[:40]
        if not agent:
            raise ValueError("缺少 agent（谁在认领）")
        if task["status"] == "done":
            raise ValueError("任务已完成，无需认领")
        cid, now = claim_id(task_id, agent), now_iso()
        with self._lock, self._conn() as c:
            other = c.execute(
                "SELECT agent FROM claims WHERE task_id=? AND status='approved' AND agent<>?",
                (task_id, agent)).fetchone()
            if other:
                raise PermissionError("该任务已被 {} 认领".format(other["agent"]))
            row = c.execute("SELECT status FROM claims WHERE id=?", (cid,)).fetchone()
            if row and row["status"] == "approved":
                # 已批准：只更新说明，**绝不退回待批**——否则 agent 等于能自己撤销批准，
                # 人工关口就被绕过去了（曾经真出现过这个 bug）。
                c.execute("UPDATE claims SET note=? WHERE id=?", (note[:200], cid))
                res = "already_approved"
            elif row:
                # 待批/被驳回 → 再次申请：更新内容并重新回到「待批」
                res = "updated" if row["status"] == "proposed" else "reproposed"
                c.execute("""UPDATE claims SET note=?, status='proposed', created_at=?,
                             decided_at=NULL, decided_by='', reason='' WHERE id=?""",
                          (note[:200], now, cid))
            else:
                res = "proposed"
                c.execute("""INSERT INTO claims(id,task_id,agent,note,status,created_at)
                             VALUES(?,?,?,?,'proposed',?)""", (cid, task_id, agent, note[:200], now))
            c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                      (now, actor or agent, "claim_propose", task_id, agent))
        return {"result": res, "claim": self.get_claim(cid)}

    def get_claim(self, cid: str) -> dict | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM claims WHERE id=?", (cid,)).fetchone()
            return dict(r) if r else None

    def claims_list(self, status: str | None = None, agent: str | None = None,
                    task_id: str | None = None, limit: int = 500) -> list[dict]:
        sql, args = "SELECT * FROM claims WHERE 1=1", []
        if status:
            sql += " AND status=?"
            args.append(status)
        if agent:
            sql += " AND agent=?"
            args.append(agent)
        if task_id:
            sql += " AND task_id=?"
            args.append(task_id)
        sql += " ORDER BY CASE status WHEN 'proposed' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END," \
               " created_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [dict(r) for r in c.execute(sql, args).fetchall()]

    def claim_decide(self, cid: str, approve: bool, by: str = "board", reason: str = "") -> dict:
        """批准/驳回一条认领申请。批准 = 任务进入进行中并落定执行方。"""
        now = now_iso()
        with self._lock, self._conn() as c:
            row = c.execute("SELECT * FROM claims WHERE id=?", (cid,)).fetchone()
            if row is None:
                raise KeyError(cid)
            if row["status"] not in ("proposed", "approved"):
                raise ValueError("该申请已是 {} 状态，无需再处理".format(row["status"]))
            task_id, agent = row["task_id"], row["agent"]
            was_approved = row["status"] == "approved"
            if approve:
                c.execute("""UPDATE claims SET status='approved', decided_at=?, decided_by=?, reason=''
                             WHERE id=?""", (now, by[:40], cid))
                trow = c.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
                if trow is not None:
                    new_status = trow["status"] if trow["status"] in ("in_progress", "done") else "in_progress"
                    c.execute("UPDATE tasks SET assignee=?, status=?, updated_at=? WHERE id=?",
                              (agent, new_status, now, task_id))
                # 同一条任务的其它待批申请自动驳回（避免两位 agent 同时开工）
                c.execute("""UPDATE claims SET status='rejected', decided_at=?, decided_by=?, reason=?
                             WHERE task_id=? AND status='proposed' AND id<>?""",
                          (now, by[:40], "已被 {} 认领".format(agent), task_id, cid))
            else:
                c.execute("UPDATE claims SET status='rejected', decided_at=?, decided_by=?, reason=? WHERE id=?",
                          (now, by[:40], reason[:120] or ("看板撤销认领" if was_approved else ""), cid))
                cur = c.execute("SELECT assignee, status FROM tasks WHERE id=?", (task_id,)).fetchone()
                if cur is not None and cur["assignee"] == agent:
                    # 撤销已批准的认领 → 退回待办，别让任务停在"进行中但没人干"
                    back = "todo" if (was_approved and cur["status"] == "in_progress") else cur["status"]
                    c.execute("UPDATE tasks SET assignee='', status=?, updated_at=? WHERE id=?",
                              (back, now, task_id))
            c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                      (now, by[:40], "claim_approve" if approve else "claim_reject", task_id,
                       "{} ({})".format(agent, reason[:60])))
        return {"claim": self.get_claim(cid), "task": self.get(task_id)}

    def claim_withdraw(self, cid: str, agent: str = "") -> dict:
        now = now_iso()
        with self._lock, self._conn() as c:
            row = c.execute("SELECT * FROM claims WHERE id=?", (cid,)).fetchone()
            if row is None:
                raise KeyError(cid)
            if agent and row["agent"] != agent:
                raise PermissionError("只能撤回自己的申请")
            c.execute("""UPDATE claims SET status='withdrawn', decided_at=?, decided_by=?, reason=?
                         WHERE id=?""", (now, agent or row["agent"], "agent 主动撤回", cid))
            c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                      (now, agent or row["agent"], "claim_withdraw", row["task_id"], row["agent"]))
        return {"claim": self.get_claim(cid)}

    def _claims_by_task(self, c: sqlite3.Connection) -> dict:
        out: dict[str, list] = {}
        for r in c.execute("SELECT * FROM claims WHERE status IN ('proposed','approved')"):
            out.setdefault(r["task_id"], []).append(dict(r))
        return out

    @staticmethod
    def annotate_claims(t: dict, claims: list) -> dict:
        """把认领状态挂到任务上，供看板显示徽标/按钮。"""
        approved = [c for c in claims if c["status"] == "approved"]
        pending = [c for c in claims if c["status"] == "proposed"]
        t["claims"] = [{"id": c["id"], "agent": c["agent"], "status": c["status"],
                        "note": c["note"], "reason": c.get("reason", ""),
                        "created_at": c["created_at"]} for c in (pending + approved)]
        t["claim_state"] = "approved" if approved else ("pending" if pending else "none")
        t["claim_pending"] = len(pending)
        t["claim_agent"] = approved[0]["agent"] if approved else (pending[0]["agent"] if pending else "")
        return t

    def claim_stats(self) -> dict:
        with self._conn() as c:
            rows = c.execute("SELECT status, COUNT(*) n FROM claims GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}

    def delete(self, task_id: str, actor: str = "") -> bool:
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM claims WHERE task_id=?", (task_id,))   # 任务没了，申请也无意义
            cur = c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            if cur.rowcount:
                c.execute("INSERT INTO event_log(at,actor,action,task_id,detail) VALUES(?,?,?,?,?)",
                          (now_iso(), actor, "delete", task_id, ""))
            return cur.rowcount > 0

    def clear(self, dept: str | None = None, actor: str = "") -> int:
        with self._lock, self._conn() as c:
            if dept:
                c.execute("DELETE FROM claims WHERE task_id IN (SELECT id FROM tasks WHERE dept=?)", (dept,))
                cur = c.execute("DELETE FROM tasks WHERE dept=?", (dept,))
            else:
                c.execute("DELETE FROM claims")
                cur = c.execute("DELETE FROM tasks")
            c.execute("INSERT INTO event_log(at,actor,action,detail) VALUES(?,?,?,?)",
                      (now_iso(), actor, "clear", "dept={}".format(dept or "*")))
            return cur.rowcount

    # ---------------- 读取 ----------------
    def _row_to_task(self, r: sqlite3.Row) -> dict:
        t = dict(r)
        t["tags"] = json.loads(t.get("tags") or "[]")
        t["collaborators"] = json.loads(t.get("collaborators") or "[]")
        t["auto"] = bool(t.get("auto"))
        if not t.get("session"):
            t["session"] = "standalone" if t["dept"].startswith("_") else None
        return t

    def get(self, task_id: str) -> dict | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not r:
                return None
            t = self._row_to_task(r)
            claims = [dict(x) for x in c.execute(
                "SELECT * FROM claims WHERE task_id=? AND status IN ('proposed','approved')",
                (task_id,)).fetchall()]
        return self.annotate_claims(t, claims)

    def list(self, dept: str | None = None, status: str | None = None,
             source: str | None = None, agent: str | None = None,
             claim: str | None = None, limit: int = 2000) -> list[dict]:
        """``claim``: none | pending | approved —— 按认领状态筛（A+B 流程用得上）。"""
        sql, args = "SELECT * FROM tasks WHERE 1=1", []
        if dept:
            sql += " AND dept=?"
            args.append(dept)
        if status:
            sql += " AND status=?"
            args.append(status)
        if source:
            sql += " AND source=?"
            args.append(source)
        if agent:
            sql += " AND (assignee=? OR agent=? OR source=?)"
            args += [agent, agent, agent]
        if claim == "approved":
            sql += " AND assignee<>''"
        elif claim == "pending":
            sql += " AND assignee='' AND id IN (SELECT task_id FROM claims WHERE status='proposed')"
        elif claim == "none":
            sql += " AND assignee='' AND id NOT IN (SELECT task_id FROM claims WHERE status='proposed')"
        sql += " ORDER BY CASE status WHEN 'blocked' THEN 0 WHEN 'in_progress' THEN 1 " \
               "WHEN 'todo' THEN 2 ELSE 3 END, CASE priority WHEN 'high' THEN 0 " \
               "WHEN 'medium' THEN 1 ELSE 2 END, updated_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            rows = [self._row_to_task(r) for r in c.execute(sql, args).fetchall()]
            cmap = self._claims_by_task(c)
        for t in rows:
            self.annotate_claims(t, cmap.get(t["id"], []))
        return rows

    def stats(self) -> dict:
        with self._conn() as c:
            by_dept = {r["dept"]: r["n"] for r in
                       c.execute("SELECT dept, COUNT(*) n FROM tasks GROUP BY dept")}
            by_status = {r["status"]: r["n"] for r in
                         c.execute("SELECT status, COUNT(*) n FROM tasks GROUP BY status")}
            by_source = {r["source"] or "(未标注)": r["n"] for r in
                         c.execute("SELECT source, COUNT(*) n FROM tasks GROUP BY source")}
            total = c.execute("SELECT COUNT(*) n FROM tasks").fetchone()["n"]
            cs = {r["status"]: r["n"] for r in
                  c.execute("SELECT status, COUNT(*) n FROM claims GROUP BY status")}
            guessed = c.execute("SELECT COUNT(*) n FROM tasks WHERE dept_source='guessed'").fetchone()["n"]
            unassigned = c.execute("SELECT COUNT(*) n FROM tasks WHERE dept LIKE '\\_%' ESCAPE '\\'"
                                   ).fetchone()["n"]
        return {"total": total, "byDept": by_dept, "byStatus": by_status, "bySource": by_source,
                "claims": {"proposed": cs.get("proposed", 0), "approved": cs.get("approved", 0),
                           "rejected": cs.get("rejected", 0)},
                "deptGuessed": guessed, "unassigned": unassigned}

    def log_ingest(self, origin: str, filename: str, res: dict):
        with self._lock, self._conn() as c:
            c.execute("""INSERT INTO ingest_log(at,origin,filename,added,updated,skipped,errors)
                         VALUES(?,?,?,?,?,?,?)""",
                      (now_iso(), origin, filename, res.get("added", 0), res.get("updated", 0),
                       res.get("skipped", 0), json.dumps(res.get("errors", []), ensure_ascii=False)))

    def recent_events(self, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM event_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
