# -*- coding: utf-8 -*-
"""命令行入口：`python -m taskboard <命令> [参数]`

命令
----
  init                     生成一份配置文件骨架 + 目录 + 投递示例
  serve                    起 HTTP 服务（看板 + API），并自动扫描投递箱
  ingest [文件...]          扫描 data/inbox 收件（不给文件就扫整个目录）
  add  '<json>'            直接录一条（也支持从管道读 JSON）
  ls   [--dept --status]   列出任务
  set  <id> k=v ...        改字段（如 status=done priority=high）
  rm   <id> [<id>...]      删除
  export                   只重新导出 tasks.js / tasks.json
  seed-demo                灌入一批演示任务（看清效果用，可一键清掉）
  clear --source=<来源>     按来源/部门删任务（防误删，必须带条件）
  stats                    统计
  doctor                   自检：配置、路径、依赖是否就绪

认领（A+B 中间态：agent 提建议、人拍板）
  claim  <任务id> --agent=<名字> [--note=...]    登记「我想干这条」（不动任务状态）
  claims [--status=proposed] [--task=<id>]      看认领申请
  approve <认领id> [--by=<谁批的>]                批准 → 任务转 in_progress 并落定执行方
  reject  <认领id> [--reason=...]                驳回
  withdraw <认领id> --agent=<名字>                agent 自己撤回
  queue  --agent=<名字>                          取「已批准、可以开工」的队列
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config as config_mod
from . import emit, ingest as ingest_mod
from .model import normalize
from .store import Store


def _args(argv):
    opts, rest = {}, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k = a[2:]
            if "=" in k:
                k, v = k.split("=", 1)
            else:
                v = True
                if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                    v, i = argv[i + 1], i + 1
            opts[k] = v
        else:
            rest.append(a)
        i += 1
    return opts, rest


def _load(opts):
    cfg = config_mod.load(opts.get("config") if isinstance(opts.get("config"), str) else None)
    cfg.ensure_dirs()
    return cfg, Store(cfg.db_file)


def _out(o):
    print(json.dumps(o, ensure_ascii=False, indent=1))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, opts, rest = argv[0], *_args(argv[1:])

    if cmd == "init":
        return _cmd_init(opts)
    if cmd == "doctor":
        return _cmd_doctor(opts)

    cfg, store = _load(opts)

    if cmd == "serve":
        if not opts.get("no-scan"):
            res = ingest_mod.ingest(cfg, store, origin="startup")
            if res["files"]:
                print("[startup] 收件 {} 个文件 → +{added} ~{updated}".format(**res, files=res["files"]))
        emit.emit(store, cfg)
        from .server import serve as _serve
        _serve(cfg, store, quiet=bool(opts.get("quiet")))
        return 0

    if cmd in ("ingest", "import"):
        total = {"files": 0, "added": 0, "updated": 0, "skipped": 0, "errors": []}
        if rest:
            tmp_inbox = cfg.inbox_dir
            for f in rest:
                p = Path(f).expanduser().resolve()
                if not p.exists():
                    total["errors"].append("找不到文件: {}".format(p))
                    continue
                dst = tmp_inbox / p.name
                if p != dst:
                    dst.write_bytes(p.read_bytes())
        total = ingest_mod.ingest(cfg, store, origin="cli", dry_run=bool(opts.get("dry-run")))
        if not opts.get("dry-run"):
            emit.emit(store, cfg)
        _out({"ok": True, **total})
        return 0

    if cmd == "add":
        payload = " ".join(rest) if rest else sys.stdin.read()
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as e:
            print("JSON 解析失败:", e, file=sys.stderr)
            return 2
        items = obj if isinstance(obj, list) else (obj.get("tasks") if isinstance(obj, dict) and "tasks" in obj else [obj])
        norm, bad = [], []
        for it in items:
            try:
                norm.append(normalize(it, cfg.defaults, cfg.limits, cfg.unassigned_key))
            except ValueError as e:
                bad.append(str(e))
        res = store.add_many(norm, actor="cli")
        claims = ingest_mod.apply_claims(store, norm)
        summary = emit.emit(store, cfg)
        _out({"ok": True, **res, "rejected": bad, "ids": [t["id"] for t in norm],
              "claims": claims, "total": summary["total"]})
        return 0 if (res["added"] + res["updated"]) else 1

    if cmd == "ls":
        tasks = store.list(dept=opts.get("dept") if isinstance(opts.get("dept"), str) else None,
                           status=opts.get("status") if isinstance(opts.get("status"), str) else None,
                           source=opts.get("source") if isinstance(opts.get("source"), str) else None,
                           agent=opts.get("agent") if isinstance(opts.get("agent"), str) else None,
                           claim=opts.get("claim") if isinstance(opts.get("claim"), str) else None)
        if opts.get("json"):
            _out({"ok": True, "count": len(tasks), "tasks": tasks})
            return 0
        print("{:<16} {:<6} {:<9} {:<12} {:<10} {}".format("id", "dept", "status", "source", "认领", "title"))
        for t in tasks:
            marker = {"approved": "✋ " + t.get("assignee", ""), "pending": "🔔 待批"}.get(
                t.get("claim_state"), "—")
            print("{:<16} {:<6} {:<9} {:<12} {:<10} {}".format(
                t["id"], t["dept"], t["status"], t["source"] or "-", marker, t["title"][:36]))
        print("共 {} 条".format(len(tasks)))
        return 0

    if cmd == "set":
        if not rest:
            print("用法: set <id> status=done priority=high", file=sys.stderr)
            return 2
        tid, pairs = rest[0], rest[1:]
        fields = {}
        for p in pairs:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "tags" or k == "collaborators":
                v = [x for x in v.replace("，", ",").split(",") if x]
            elif k == "auto":
                v = v.lower() in ("1", "true", "yes", "on")
            fields[k] = v
        t = store.patch(tid, fields, actor="cli")
        if t is None:
            print("找不到任务:", tid, file=sys.stderr)
            return 1
        emit.emit(store, cfg)
        _out({"ok": True, "task": t})
        return 0

    if cmd == "rm":
        n = 0
        for tid in rest:
            n += 1 if store.delete(tid, actor="cli") else 0
        emit.emit(store, cfg)
        _out({"ok": True, "deleted": n})
        return 0

    # ---------------- 认领（A+B 中间态） ----------------
    if cmd == "claim":
        if not rest or not opts.get("agent"):
            print("用法: claim <任务id> --agent=<名字> [--note=说明]", file=sys.stderr)
            return 2
        try:
            res = store.claim_propose(rest[0], str(opts["agent"]), str(opts.get("note") or ""),
                                      actor=str(opts["agent"]))
        except KeyError:
            print("找不到任务:", rest[0], file=sys.stderr)
            return 1
        except (ValueError, PermissionError) as e:
            print("认领失败:", e, file=sys.stderr)
            return 1
        emit.emit(store, cfg)
        _out({"ok": True, **res,
              "下一步": "等人在看板上点「批准」。批准后跑 `queue --agent={}` 取活。".format(opts["agent"])})
        return 0

    if cmd == "claims":
        rows = store.claims_list(status=opts.get("status") if isinstance(opts.get("status"), str) else None,
                                 task_id=opts.get("task") if isinstance(opts.get("task"), str) else None,
                                 agent=opts.get("agent") if isinstance(opts.get("agent"), str) else None)
        if opts.get("json"):
            _out({"ok": True, "count": len(rows), "claims": rows})
            return 0
        if not rows:
            print("（没有认领申请）")
            return 0
        print("{:<14} {:<14} {:<10} {:<20} {}".format("认领id", "agent", "状态", "任务id", "说明"))
        for c in rows:
            print("{:<14} {:<14} {:<10} {:<20} {}".format(
                c["id"], c["agent"], c["status"], c["task_id"], (c["note"] or "")[:24]))
        print("共 {} 条".format(len(rows)))
        return 0

    if cmd in ("approve", "reject"):
        if not rest:
            print("用法: {} <认领id> [--by=谁] [--reason=...]".format(cmd), file=sys.stderr)
            return 2
        try:
            res = store.claim_decide(rest[0], cmd == "approve",
                                     by=str(opts.get("by") or "cli"),
                                     reason=str(opts.get("reason") or ""))
        except KeyError:
            print("找不到认领申请:", rest[0], file=sys.stderr)
            return 1
        except (ValueError, PermissionError) as e:
            print("处理失败:", e, file=sys.stderr)
            return 1
        emit.emit(store, cfg)
        _out({"ok": True, **res})
        return 0

    if cmd == "withdraw":
        if not rest:
            print("用法: withdraw <认领id> [--agent=名字]", file=sys.stderr)
            return 2
        try:
            res = store.claim_withdraw(rest[0], agent=str(opts.get("agent") or ""))
        except KeyError:
            print("找不到认领申请:", rest[0], file=sys.stderr)
            return 1
        except PermissionError as e:
            print("撤回失败:", e, file=sys.stderr)
            return 1
        emit.emit(store, cfg)
        _out({"ok": True, **res})
        return 0

    if cmd == "queue":
        agent = opts.get("agent")
        if not agent:
            print("用法: queue --agent=<名字>", file=sys.stderr)
            return 2
        rows = store.claims_list(status="approved", agent=str(agent))
        tasks = []
        for c in rows:
            t = store.get(c["task_id"])
            if t:
                t["claim_id"] = c["id"]
                tasks.append(t)
        if opts.get("json"):
            _out({"ok": True, "agent": agent, "count": len(tasks), "tasks": tasks})
            return 0
        if not tasks:
            print("（{} 暂无已批准的认领）".format(agent))
            return 0
        print("{:<16} {:<8} {:<9} {:<6} {}".format("任务id", "部门", "状态", "优先", "标题"))
        for t in tasks:
            print("{:<16} {:<8} {:<9} {:<6} {}".format(
                t["id"], t["dept"], t["status"], t["priority"], t["title"][:36]))
        print("共 {} 条可开工".format(len(tasks)))
        return 0

    if cmd == "export":
        _out({"ok": True, **emit.emit(store, cfg)})
        return 0

    if cmd in ("seed-demo", "demo"):
        demo = _demo_tasks()
        norm = [normalize(t, cfg.defaults, cfg.limits, cfg.unassigned_key) for t in demo]
        res = store.add_many(norm, actor="seed-demo")
        # 顺手造一条「待批认领」，这样一打开看板就能看到 A+B 中间态长什么样
        try:
            pic = next(t for t in norm if t["title"].startswith("新版产品原型"))
            store.claim_propose(pic["id"], "demo-agent", "原型评审我熟，可以接手", actor="seed-demo")
        except Exception:                                         # noqa: BLE001
            pass
        summary = emit.emit(store, cfg)
        _out({"ok": True, **res, "total": summary["total"],
              "提示": "演示数据已写入（含 1 条待批认领，看板左下角会亮 🔔）。"
                      "清掉它们：python -m taskboard clear --source demo"})
        return 0

    if cmd == "clear":
        src, dept = opts.get("source"), opts.get("dept")
        ids = [t["id"] for t in store.list(source=src, dept=dept)] if (src or dept) else []
        if ids:
            for i in ids:
                store.delete(i, actor="cli")
            emit.emit(store, cfg)
            _out({"ok": True, "deleted": len(ids), "filter": {"source": src, "dept": dept}})
            return 0
        if opts.get("all"):
            n = store.clear(None, actor="cli")
            emit.emit(store, cfg)
            _out({"ok": True, "deleted": n})
            return 0
        print("拒绝无条件清空：请加 --source=<来源> 或 --dept=<部门>，或显式 --all=1", file=sys.stderr)
        return 2

    if cmd == "stats":
        _out({"ok": True, **store.stats()})
        return 0

    print("未知命令:", cmd, file=sys.stderr)
    print(__doc__)
    return 2


def _demo_tasks():
    """演示数据：故意覆盖「不同 agent 的不同写法」，让人一眼看懂接入有多宽松。"""
    return [
        {"title": "月度营收趋势模块联调", "dept": "cfo", "status": "in_progress", "priority": "high",
         "project": "Hailu-SC-EMS", "source": "demo", "desc": "对外数据模块第一优先"},
        {"name": "商品图片模糊匹配逻辑归档", "zone": "技术", "state": "done", "source": "demo"},
        {"title": "小红书 9 月投放复盘", "部门": "营销", "状态": "待办", "优先级": "中", "source": "demo"},
        {"title": "发货单生成软件需求收敛", "dept": "coo", "status": "blocked", "source": "demo",
         "desc": "等业务计划模板定稿"},
        {"title": "周五部门例会复盘", "dept": "meeting", "source": "demo", "due": "2026-09-19"},
        {"title": "季度合规抽查材料准备", "dept": "cro", "status": "todo", "priority": "high", "source": "demo"},
        {"title": "新版产品原型评审", "dept": "cpo", "urgent": True, "source": "demo"},
        {"title": "小红书投放素材整理", "source": "demo"},          # 没写部门 → 被猜成 cmo，看板会打「部门待核」
        {"title": "仓库温控设备巡检", "dept": "coo", "source": "demo",
         "dept_reason": "由运营验收，技术只提供传感器数据"},        # 显式判部门 + 说明理由
        {"title": "这件事没写部门，会被放进未归类", "source": "demo"},
    ]


# ---------------- init / doctor ----------------
TEMPLATE_CONFIG = {
    "_说明": "唯一配置文件。所有相对路径相对本文件解析；可用 BOARD_DATA_DIR / BOARD_PORT / BOARD_TOKEN 等环境变量覆盖。",
    "paths": {
        "dataDir": "data",
        "dbFile": "data/taskboard.db",
        "inboxDir": "data/inbox",
        "archiveDir": "data/inbox/_imported",
        "emitJs": "tasks-data/tasks.js",
        "emitJson": "data/tasks.json",
        "boardHtml": "office-3d-taskboard.html",
        "staticRoot": ".",
    },
    "server": {"host": "0.0.0.0", "port": 8787, "token": "", "cors": "*", "autoIngestSec": 30},
    "defaults": {"status": "todo", "priority": "medium", "project": "未归类"},
    "unassignedKey": "_unassigned",
    "departments": {
        "ceo": "CEO 战略办公室", "cfo": "CFO 财务中心", "cto": "CTO 技术中心", "cpo": "CPO 产品设计室",
        "cmo": "CMO 营销中心", "coo": "COO 运营中心", "cro": "CRO 风控中心", "meeting": "战略会议室",
    },
    "aliases": {
        "财务": "cfo", "对账": "cfo", "营销": "cmo", "技术": "cto", "运营": "coo",
        "风控": "cro", "产品": "cpo", "战略": "ceo", "会议": "meeting",
    },
    "limits": {"title": 80, "desc": 400, "project": 40},
}

SAMPLE_INBOX = """---
source: 你的agent名字
project: 我的项目
---

```board
[cfo] 示例：把这条换成真实任务 | p:high | s:in_progress | desc:说明写这里
[cto] 示例：未完成的任务也照录 | p:medium
[meeting] 示例：已完成的任务 | s:done
```
"""


def _cmd_init(opts) -> int:
    root = Path(opts.get("dir") or Path.cwd()).expanduser().resolve()
    cfg_path = root / config_mod.DEFAULT_FILENAME
    wrote = []
    if not cfg_path.exists() or opts.get("force"):
        cfg_path.write_text(json.dumps(TEMPLATE_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        wrote.append(str(cfg_path))
    cfg = config_mod.load(str(cfg_path))
    cfg.ensure_dirs()
    sample = cfg.inbox_dir / "示例-删掉我.md"
    if not sample.exists():
        sample.write_text(SAMPLE_INBOX, encoding="utf-8")
        wrote.append(str(sample))
    emit.emit(Store(cfg.db_file), cfg)
    _out({"ok": True, "config": str(cfg.path), "created": wrote,
          "inbox": str(cfg.inbox_dir), "emitJs": str(cfg.emit_js)})
    print("\n下一步：\n  1) python -m taskboard serve      # 起服务，浏览器开 http://127.0.0.1:8787/")
    return 0


def _cmd_doctor(opts) -> int:
    import os
    import platform
    import sqlite3
    cfg = config_mod.load(opts.get("config") if isinstance(opts.get("config"), str) else None)
    missing, rows = [], []
    for k, p in cfg.paths.items():
        if k in ("dataDir", "staticRoot"):
            continue
        parent = p if p.is_dir() else p.parent
        # 找到最近一个已存在的祖先，判断能否创建
        probe, needed = parent, []
        while not probe.exists() and probe != probe.parent:
            needed.append(str(probe))
            probe = probe.parent
        creatable = probe.exists() and os.access(str(probe), os.W_OK)
        state = "√ 已存在" if p.exists() else ("√ 待创建" if creatable else "× 父目录不可写")
        rows.append((k, state, str(p)))
        if not p.exists() and creatable:
            missing.extend(needed)
    missing = list(dict.fromkeys(missing))
    ok = cfg.board_html.exists()
    print("taskboard 自检")
    print("  配置文件 : {}".format(cfg.path or "(使用内置默认值，未找到 board.config.json)"))
    print("  Python   : {} {}".format(platform.python_version(), platform.system()))
    print("  SQLite   : {}".format(sqlite3.sqlite_version))
    print("  看板 HTML: {}".format("√ 存在" if ok else "× 找不到 " + str(cfg.board_html)))
    print("  服务地址 : {}:{}".format(cfg.host, cfg.port))
    print("  写 token : {}".format("已设置" if cfg.token else "未设置"))
    print("  配置来源 : {}".format(", ".join(k for k in cfg.paths)))
    for k, state, path in rows:
        print("  {:<10} {:<12} {}".format(k, state, path))
    if missing:
        print("\n  首次运行会自动创建：")
        for m in missing:
            print("    -", m)
    print("\n结论：", "可以开工" if ok else "看板 HTML 路径需在配置里指对")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
