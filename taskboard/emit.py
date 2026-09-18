# -*- coding: utf-8 -*-
"""导出层：把库里的任务写成看板能直接读的文件。

产物
----
1. `tasks-data/tasks.js`   → `window.TASK_DATA` + `window.TASK_META`（看板 <script> 直接引入）
2. `data/tasks.json`       → 纯 JSON（给别的系统/agent 读，也可当备份）

未归类的任务放在 `_unassigned` 桶里：看板 `loadTasks()` 只认 ZONES 里有的部门键，
所以这个桶不会污染任何房间，但会被中控台按 `session==='standalone'` 收进"记忆派生任务"区。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: 看板 task-card 用到的字段（其余字段留着不删，方便前端以后扩展）
BOARD_FIELDS = ("id", "dept", "status", "priority", "title", "desc", "description", "project",
                "source", "agent", "due", "tags", "collaborators", "auto", "session",
                "external_id", "created_at", "updated_at",
                "dept_source", "dept_reason", "assignee", "claims", "claim_state", "claim_pending")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def _board_task(t: dict) -> dict:
    out = {k: t.get(k) for k in BOARD_FIELDS if t.get(k) not in (None, "", [], {})}
    if t.get("desc"):
        out["description"] = t["desc"]          # 看板兼容两种写法
    out["id"] = t["id"]
    out["status"] = t["status"]
    out["priority"] = t["priority"]
    out["title"] = t["title"]
    return out


def build_payload(store, config) -> dict:
    tasks = store.list(limit=100000)
    order = list(config.departments.keys()) or []
    buckets: dict[str, list] = {k: [] for k in order}
    buckets.setdefault(config.unassigned_key, [])
    for t in tasks:
        key = t["dept"] if t["dept"] in buckets else config.unassigned_key
        if t["dept"].startswith("_"):
            key = config.unassigned_key
        buckets[key].append(_board_task(t))
    # 空桶保留（前端 ZONES 合并时无所谓），保证结构稳定
    stats = store.stats()
    return {
        "generated": _now(),
        "generator": "taskboard",
        "departments": order,
        "unassignedKey": config.unassigned_key,
        "stats": stats,
        "data": buckets,
    }


def _atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(str(tmp), str(path))


def emit(store, config) -> dict:
    """写出两个产物，返回摘要。"""
    payload = build_payload(store, config)
    js = (
        "/* 由 taskboard 自动生成，请勿手改 —— 改数据请走 API 或投递箱 */\n"
        "/* generated: {gen} · total: {total} */\n"
        "window.TASK_DATA = {data};\n"
        "window.TASK_META = {meta};\n"
    ).format(
        gen=payload["generated"],
        total=payload["stats"]["total"],
        data=json.dumps(payload["data"], ensure_ascii=False, indent=1),
        meta=json.dumps({"generated": payload["generated"], "totalTasks": payload["stats"]["total"],
                         "byDept": payload["stats"]["byDept"], "byStatus": payload["stats"]["byStatus"],
                         "bySource": payload["stats"]["bySource"], "generator": "taskboard"},
                        ensure_ascii=False, indent=1),
    )
    _atomic_write(config.emit_js, js)
    _atomic_write(config.emit_json, json.dumps(payload, ensure_ascii=False, indent=1))
    return {"tasksJs": str(config.emit_js), "tasksJson": str(config.emit_json),
            "total": payload["stats"]["total"], "byDept": payload["stats"]["byDept"]}
