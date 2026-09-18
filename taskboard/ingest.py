# -*- coding: utf-8 -*-
"""投递箱扫描：把「任何 agent 丢进目录的文件」变成库里的任务。

支持四种文件格式，覆盖从"只会 append 一行"到"能写结构化 JSON"的全部能力档位：

1. `.json`    单个对象 / 对象数组 / {"tasks":[...]}
2. `.jsonl`   一行一个 JSON 对象（最适合 agent 逐条 append，不怕并发写坏文件）
3. `.md`      围栏代码块 ```board（兼容旧格式）或 ```json；也认 `- [ ] 待办` 清单
4. `.txt`     先按 jsonl 试，失败再按 board 行解析

任何格式都可以在开头用 front-matter 声明来源，便于"一眼看出是哪个 agent 录的"：
    ---
    source: claude-code
    project: Hailu-SC-EMS
    ---
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from . import model

SUPPORTED = {".json", ".jsonl", ".ndjson", ".md", ".markdown", ".txt"}

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
_LINE = re.compile(r"^\[([A-Za-z_]{2,12})\]\s+(.*)$")
_CHECK = re.compile(r"^\s*[-*]\s*\[([ xX✓])\]\s+(.*)$")
_BULLET = re.compile(r"^\s*[-*]\s+(?!\[)(.+)$")
_DEPT_PREFIX = re.compile(r"^([A-Za-z_]{2,12}|[\u4e00-\u9fa5]{1,4})\s*[:：]\s*(.+)$")


def _parse_front(text: str):
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"\'')
    return meta, text[m.end():]


def _kv_segments(rest: str) -> dict:
    """解析 board 行里的 ``| p:high | s:done | dep:cfo,cto`` 段。

    别名约定（与任务对象的字段含义保持一致，避免"同一个词两个意思"）：
      * ``dep`` / ``collab`` / ``协作``  → **协作部门**（跨部门联动线，需 ≥2 个）
      * ``dept`` / ``zone`` / ``team`` / ``room`` / ``部门`` → **本条任务的归属部门**
    历史上 ``dept`` 曾被当作协作部门用，容易与任务级 ``dept`` 混淆，已纠正。
    """
    out = {}
    for seg in [s.strip() for s in rest.split("|")][1:]:
        if ":" not in seg:
            continue
        k, v = seg.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k in ("p", "prio", "priority", "优先级"):
            out["priority"] = v
        elif k in ("s", "status", "状态"):
            out["status"] = v
        elif k in ("d", "due", "deadline", "截止"):
            out["due"] = v
        elif k in ("dep", "collab", "collaborators", "协作"):
            out["collaborators"] = v
        elif k in ("dept", "department", "zone", "team", "room", "部门"):
            out["dept"] = v
        elif k in ("desc", "d2", "说明", "备注"):
            out["desc"] = v
        elif k in ("tag", "tags", "标签"):
            out["tags"] = v
        elif k in ("id", "ext", "编号"):
            out["external_id"] = v
        elif k in ("src", "source", "来源"):
            out["source"] = v
        elif k in ("proj", "project", "项目"):
            out["project"] = v
        elif k in ("auto", "自动化"):
            out["auto"] = v
        else:
            out[k] = v
    return out


def _split_title_meta(rest: str) -> tuple:
    """把 ``标题 | p:high | s:done`` 拆成 ``(标题, 元数据字典)``。

    关键点：``|`` 段一律从标题里摘掉。否则 ``- [x] 做完的事 | s:done`` 会把
    ``| s:done`` 留在标题上（曾经的真实 bug），看板上就会出现带管道符的脏标题。
    """
    title = (rest.split("|", 1)[0] or "").strip()
    return title, _kv_segments(rest)


def parse_board_lines(text: str) -> list[dict]:
    """`[dept] 标题 | p:high | s:done` —— 兼容 board-export 旧格式。

    策略：围栏 ```board 里的每一行**默认就是一条任务**（围栏本身已经声明了这件事），
    所以除标题行/分隔行/表格行外的普通文本也照收，避免"写了却没录进去"。
    """
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _LINE.match(line)
        if m:
            title, meta = _split_title_meta(m.group(2))
            d = {"dept": m.group(1), "title": title}
            d.update(meta)
            out.append(d)
            continue
        m = _CHECK.match(raw)
        if m:
            title, meta = _split_title_meta(m.group(2))
            d = {"title": title, "status": "done" if m.group(1).lower() in "x✓" else "todo"}
            d.update(meta)
            if not d["title"]:
                continue                              # `- [x] | s:done` 这种没有标题的行丢掉
            out.append(d)
            continue
        m = _DEPT_PREFIX.match(line)
        if m and model.norm_dept(m.group(1)):
            title, meta = _split_title_meta(m.group(2))
            d = {"dept": m.group(1), "title": title}
            d.update(meta)
            out.append(d)
            continue
        m = _BULLET.match(raw)
        if m:
            title, meta = _split_title_meta(m.group(1))
            d = {"title": title}
            d.update(meta)
            out.append(d)
            continue
        if line[0] in '#>|=*':
            continue                                  # 标题/引用/表格/装饰行，不是任务
        title, meta = _split_title_meta(line)
        d = {"title": title}
        d.update(meta)
        out.append(d)
    return out


def parse_text(name: str, text: str) -> list[dict]:
    meta, body = _parse_front(text)
    ext = Path(name).suffix.lower()
    items: list[dict] = []

    if ext in (".json", ".jsonl", ".ndjson", ".txt"):
        stripped = body.strip()
        if stripped.startswith("{") and ext != ".jsonl":
            try:
                obj = json.loads(stripped)
                items = obj.get("tasks") if isinstance(obj, dict) and "tasks" in obj else (
                    obj if isinstance(obj, list) else [obj])
            except json.JSONDecodeError:
                items = []
        if not items:
            for line in stripped.splitlines():
                line = line.strip().rstrip(",")
                if not line or line in ("[", "]"):
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, list):
                    items.extend(obj)
                elif isinstance(obj, dict):
                    items.append(obj)

    if ext in (".md", ".markdown", ".txt") and not items:
        for fm in re.finditer(r"```(board|json|tasks)\s*\n(.*?)```", body, re.S):
            kind, chunk = fm.group(1), fm.group(2)
            if kind == "board":
                items.extend(parse_board_lines(chunk))
            else:
                try:
                    obj = json.loads(chunk)
                    items.extend(obj.get("tasks") if isinstance(obj, dict) and "tasks" in obj
                                 else (obj if isinstance(obj, list) else [obj]))
                except json.JSONDecodeError:
                    items.extend(parse_board_lines(chunk))
        if not items:
            items = parse_board_lines(body)

    # front-matter 作为默认值注入（单条任务里写了的优先）
    for it in items:
        if isinstance(it, dict):
            for k in ("source", "project", "agent", "dept"):
                if k in meta and not it.get(k):
                    it[k] = meta[k]
            it.setdefault("source", meta.get("source") or Path(name).stem)
    return [i for i in items if isinstance(i, dict)]


def scan_files(inbox: Path, archive: Path):
    """产出 (path, items) 序列，跳过归档区与隐藏文件。"""
    if not inbox.exists():
        return
    arch = archive.resolve()
    for p in sorted(inbox.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        try:
            p.resolve().relative_to(arch)
            continue                                    # 归档区里的文件不再扫
        except ValueError:
            pass
        if p.suffix.lower() not in SUPPORTED:
            continue
        yield p


def apply_claims(store, tasks: list[dict]) -> list[dict]:
    """把任务里附带的 `claim` 字段变成「认领申请」。

    为什么放在上报这一层：只会发一次 HTTP 的 agent 不必再学一个新接口，
    一次 POST 就能"上报 + 申请接手"。但**只是申请**——任务状态不受影响，
    要等人在看板上批准（见 SPEC §5 认领协议）。
    返回每个申请的结果，便于调用方回报。
    """
    out = []
    for t in tasks:
        cl = t.get("claim")
        if not cl or not cl.get("agent"):
            continue
        try:
            res = store.claim_propose(t["id"], cl["agent"], cl.get("note", ""), actor=cl["agent"])
            out.append({"task": t["title"], "agent": cl["agent"], "result": res["result"],
                        "claim_id": res["claim"]["id"]})
        except (KeyError, ValueError, PermissionError) as e:      # noqa: BLE001
            out.append({"task": t["title"], "agent": cl["agent"], "result": "skipped",
                        "error": str(e)})
    return out


def ingest(config, store, origin: str = "scan", dry_run: bool = False) -> dict:
    """扫描投递箱 → 归一化 → 入库 → 归档。返回统计。"""
    config.ensure_dirs()
    total = {"files": 0, "added": 0, "updated": 0, "skipped": 0, "errors": []}
    for path in scan_files(config.inbox_dir, config.archive_dir):
        total["files"] += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            total["errors"].append("{}: 读取失败 {}".format(path.name, e))
            continue
        raw_items = parse_text(path.name, text)
        if not raw_items:
            total["errors"].append("{}: 没解析出任务（检查格式）".format(path.name))
            store.log_ingest(origin, path.name, {"skipped": 1, "errors": ["no tasks parsed"]})
            continue
        tasks, bad = [], []
        for it in raw_items:
            try:
                tasks.append(model.normalize(it, config.defaults, config.limits, config.unassigned_key))
            except ValueError as e:
                bad.append(str(e))
        res = store.add_many(tasks, actor=origin) if not dry_run else {
            "added": len(tasks), "updated": 0, "errors": []}
        total["added"] += res["added"]
        total["updated"] += res["updated"]
        total["skipped"] += len(bad)
        total["errors"] += bad + res["errors"]
        if not dry_run:
            total.setdefault("claims", []).extend(apply_claims(store, tasks))
        store.log_ingest(origin, path.name, {**res, "skipped": len(bad)})
        if not dry_run:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = config.archive_dir / "{}-{}".format(stamp, path.name)
            try:
                shutil.move(str(path), str(dest))
            except OSError:
                pass
    return total
