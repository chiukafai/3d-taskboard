#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""认领助手 —— 给「会跑命令」的 agent 用的一站式脚本（纯标准库，无需 pip）。

对应 SPEC.md §5 认领协议。它只做一件事：把"申请→等批→取活→回报"这套
一来一回的交互，收敛成几条不会写错的命令。

⚠️ 记住底线：**这个脚本不会替你开工。** 只有 `queue` 列出来的任务才是
   人已批准的。`ask` 提交的申请只是"待批"，那时别动手。

用法
----
    # 看有哪些活可以接（默认只看自己部门未开工的）
    python claim-poll.py ask  --agent claude-code --dept cfo

    # 提申请（任务状态不变，等人批准）
    python claim-poll.py claim cpo-abc123 --agent claude-code --note "原型评审我熟"

    # 查自己的申请批了没
    python claim-poll.py state --agent claude-code

    # 取「已批准、可以开工」的活
    python claim-poll.py queue --agent claude-code

    # 不想接了 / 干完了
    python claim-poll.py withdraw cl-xxxx --agent claude-code
    python claim-poll.py report cpo-abc123 --status done --agent claude-code

看板地址：用 --board 指定，或设环境变量 BOARD（默认 http://127.0.0.1:8787）
令牌：   用 --token 指定，或设环境变量 BOARD_TOKEN（服务端没开校验就留空）
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

STATE_LABEL = {
    "proposed": "待批（别开工，等人批准）",
    "approved": "已批准（可以开工）",
    "rejected": "被驳回（停手，别重试）",
    "withdrawn": "已撤回",
}


def call(board, token, method, path, body=None):
    url = board.rstrip("/") + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return {"ok": False, "http": e.code, **json.loads(raw)}
        except ValueError:
            return {"ok": False, "http": e.code, "error": raw[:200]}
    except urllib.error.URLError as e:
        return {"ok": False, "error": "连不上看板 {}：{}".format(url, e.reason)}


def dump(obj, as_json):
    """打印并返回 0 —— 这样调用处可以直接 `return dump(...)`。"""
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=1))
    else:
        print(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1))
    return 0


def fail(r, as_json, msg="失败"):
    print("{}：{}".format(msg, r.get("error") or r), file=sys.stderr)
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    return 1


def cmd_ask(a):
    q = "/api/tasks?status=todo&claim=none"
    if a.dept:
        q += "&dept=" + urllib.parse.quote(a.dept)
    if a.limit:
        q += "&limit=%d" % a.limit
    r = call(a.board, a.token, "GET", q)
    if not r.get("ok"):
        return fail(r, a.json, "读取失败")
    tasks = r["tasks"]
    if a.json:
        return dump({"ok": True, "count": len(tasks), "tasks": tasks}, True)
    if not tasks:
        print("（没有可接的活）")
        return 0
    print("可以接的活（%d 条）：" % len(tasks))
    for t in tasks:
        print("  %-16s %-7s %-6s %s" % (t["id"], t["dept"], t["priority"], t["title"][:40]))
    print("\n下一步：claim <任务id> --agent %s --note \"为什么你能接\"" % (a.agent or "你"))
    print("提醒：提交后只是「待批」，任务仍是待办 —— 别开工，等人批准。")
    return 0


def cmd_claim(a):
    if not a.agent:
        print("必须给 --agent（你是谁）", file=sys.stderr)
        return 2
    r = call(a.board, a.token, "POST", "/api/tasks/%s/claim" % urllib.parse.quote(a.task),
             {"agent": a.agent, "note": a.note or ""})
    if not r.get("ok"):
        print("申请失败：%s" % (r.get("error") or r), file=sys.stderr)
        if r.get("http") == 409:
            print("→ 这条已被别人认领了，换一条吧。", file=sys.stderr)
        return 1
    if a.json:
        return dump(r, True)
    print("已提交申请：%s → %s" % (r["claim"]["id"], r["claim"]["status"]))
    print("⚠️ 任务状态**没有改变**。请**不要开工**，等人在看板上批准。")
    print("   之后用 `state --agent %s` 查结果，或用 `queue --agent %s` 取已批准的活。" % (a.agent, a.agent))
    return 0


def cmd_state(a):
    if not a.agent:
        print("必须给 --agent", file=sys.stderr)
        return 2
    r = call(a.board, a.token, "GET", "/api/claims?agent=" + urllib.parse.quote(a.agent))
    if not r.get("ok"):
        return fail(r, a.json, "读取失败")
    rows = r["claims"]
    if a.json:
        return dump({"ok": True, "count": len(rows), "claims": rows}, True)
    if not rows:
        print("（你还没有提交过申请）")
        return 0
    print("你的申请（%d 条）：" % len(rows))
    for c in rows:
        print("  %-14s %-9s %s" % (c["id"], c["status"], c["task_id"]))
        print("      %s" % STATE_LABEL.get(c["status"], c["status"]))
        if c.get("reason"):
            print("      原因：%s" % c["reason"])
    return 0


def cmd_queue(a):
    if not a.agent:
        print("必须给 --agent", file=sys.stderr)
        return 2
    r = call(a.board, a.token, "GET", "/api/queue?agent=" + urllib.parse.quote(a.agent))
    if not r.get("ok"):
        return fail(r, a.json, "读取失败")
    tasks = r["tasks"]
    if a.json:
        return dump({"ok": True, "count": len(tasks), "tasks": tasks}, True)
    if not tasks:
        print("（暂时没有已批准给你的活。先 ask 看有哪些可以接）")
        return 0
    print("✅ 已批准、可以开工（%d 条）：" % len(tasks))
    for t in tasks:
        print("  %-16s %-7s %s" % (t["id"], t["dept"], t["title"][:40]))
        if t.get("desc"):
            print("      %s" % t["desc"][:70])
    print("\n干完记得回报：report <任务id> --status done --agent %s" % a.agent)
    return 0


def cmd_withdraw(a):
    r = call(a.board, a.token, "POST", "/api/claims/%s/withdraw" % urllib.parse.quote(a.claim_id),
             {"agent": a.agent or ""})
    if not r.get("ok"):
        return fail(r, a.json, "撤回失败")
    print("已撤回：%s" % r["claim"]["id"])
    return 0


def cmd_report(a):
    if not a.agent:
        print("必须给 --agent", file=sys.stderr)
        return 2
    patch = {"status": a.status}
    if a.note:
        patch["desc"] = a.note
    r = call(a.board, a.token, "PATCH", "/api/tasks/" + urllib.parse.quote(a.task), patch)
    if not r.get("ok"):
        return fail(r, a.json, "回报失败")
    t = r["task"]
    print("已回报：%s → %s" % (t["title"], t["status"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description="看板认领助手（SPEC §5）")
    ap.add_argument("--board", default=os.environ.get("BOARD", "http://127.0.0.1:8787"))
    ap.add_argument("--token", default=os.environ.get("BOARD_TOKEN", ""))
    ap.add_argument("--json", action="store_true", help="输出 JSON（给程序读）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ask", help="看有哪些活可以接")
    p.add_argument("--agent", default="", help="你的名字（可选，仅用于提示语）")
    p.add_argument("--dept", default="", help="只看某个部门（如 cfo）")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_ask)

    p = sub.add_parser("claim", help="提申请（只是申请，等人批准）")
    p.add_argument("task")
    p.add_argument("--agent", required=True)
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_claim)

    p = sub.add_parser("state", help="查自己的申请批了没")
    p.add_argument("--agent", required=True)
    p.set_defaults(fn=cmd_state)

    p = sub.add_parser("queue", help="取已批准、可以开工的活")
    p.add_argument("--agent", required=True)
    p.set_defaults(fn=cmd_queue)

    p = sub.add_parser("withdraw", help="撤回申请")
    p.add_argument("claim_id")
    p.add_argument("--agent", default="")
    p.set_defaults(fn=cmd_withdraw)

    p = sub.add_parser("report", help="回报进度 / 完成")
    p.add_argument("task")
    p.add_argument("--status", default="done",
                   choices=["todo", "in_progress", "done", "blocked"])
    p.add_argument("--agent", required=True)
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
