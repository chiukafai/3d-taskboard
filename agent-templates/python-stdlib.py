#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只用标准库的接入客户端 —— 任何 Python 环境直接跑，不需要 pip install。

用法
----
  # 命令行录一条
  python python-stdlib.py add "月度营收联调" --dept cfo --status in_progress --priority high

  # 批量：把一个 JSON 文件里的任务全灌进去
  python python-stdlib.py bulk tasks.json

  # 看板里有啥
  python python-stdlib.py ls --dept cfo

  # 改状态 / 删掉
  python python-stdlib.py set cfo-1a2b3c4d5e status=done
  python python-stdlib.py rm  cfo-1a2b3c4d5e

  # 当作库用（在别的 agent 脚本里 import）
  from importlib import import_module
  tb = import_module("python-stdlib")          # 或把本文件改名 taskboard_client.py
  tb.record("任务标题", dept="cfo", source="claude-code")
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BOARD = os.environ.get("BOARD_URL", "http://127.0.0.1:8787").rstrip("/")
TOKEN = os.environ.get("BOARD_TOKEN", "")


def _call(method: str, path: str, body=None, timeout=8):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BOARD + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit("接口返回 {}：{}".format(e.code, e.read().decode("utf-8", "replace")))
    except urllib.error.URLError as e:
        raise SystemExit("连不上 {}（看板服务没起？）：{}".format(BOARD, e.reason))


def record(title: str, **kw):
    """录一条任务。返回接口响应 dict。"""
    kw["title"] = title
    return _call("POST", "/api/tasks", kw)


def record_many(items):
    return _call("POST", "/api/tasks", {"tasks": items})


def main():
    global BOARD
    ap = argparse.ArgumentParser(description="看板任务接入客户端（零依赖）")
    ap.add_argument("--board", default=BOARD, help="服务地址，默认 %(default)s")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="录一条")
    a.add_argument("title")
    for f in ("dept", "status", "priority", "desc", "project", "source", "due", "external_id",
              "dept_reason", "collaborators", "claim"):
        a.add_argument("--" + f, default=None,
                       help="--claim 填你的名字 = 顺手申请接手（见 SPEC §5）" if f == "claim" else None)

    b = sub.add_parser("bulk", help="批量导入 JSON 文件")
    b.add_argument("file")

    l = sub.add_parser("ls", help="列出任务")
    l.add_argument("--dept"); l.add_argument("--status"); l.add_argument("--source")

    s = sub.add_parser("set", help="改字段")
    s.add_argument("id"); s.add_argument("pairs", nargs="+")

    r = sub.add_parser("rm", help="删除")
    r.add_argument("ids", nargs="+")

    sub.add_parser("stats", help="统计")
    args = ap.parse_args()

    BOARD = args.board.rstrip("/")

    if args.cmd == "add":
        kw = {k: v for k, v in vars(args).items() if k not in ("cmd", "title", "board") and v is not None}
        out = record(args.title, **kw)
    elif args.cmd == "bulk":
        with open(args.file, encoding="utf-8") as f:
            obj = json.load(f)
        items = obj.get("tasks", obj) if isinstance(obj, dict) else obj
        out = record_many(items)
    elif args.cmd == "ls":
        q = "&".join("{}={}".format(k, v) for k, v in
                     (("dept", args.dept), ("status", args.status), ("source", args.source)) if v)
        out = _call("GET", "/api/tasks" + ("?" + q if q else ""))
        for t in out["tasks"]:
            print("{:<16} {:<8} {:<12} {:<12} {}".format(
                t["id"], t["dept"], t["status"], t.get("source") or "-", t["title"]))
        print("共 {} 条".format(out["count"]))
        return
    elif args.cmd == "set":
        fields = {}
        for p in args.pairs:
            k, _, v = p.partition("=")
            fields[k] = [x for x in v.split(",") if x] if k in ("tags", "collaborators") else v
        out = _call("PATCH", "/api/tasks/" + args.id, fields)
    elif args.cmd == "rm":
        out = {"deleted": sum(1 for i in args.ids
                              if _call("DELETE", "/api/tasks/" + i).get("deleted"))}
    else:
        out = _call("GET", "/api/summary")

    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
