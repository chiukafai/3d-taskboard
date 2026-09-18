# -*- coding: utf-8 -*-
"""HTTP 服务：一个进程同时干三件事

1. **看板静态服务**     GET /            → 直接看 3D 看板（浏览器随时打开）
2. **任务写入接口**     POST /api/tasks  → 任何 agent 一行 curl 就能录任务
3. **任务读取接口**     GET /api/tasks   → 给别的系统/脚本读

只用标准库 http.server，不需要 pip install。任何写操作完成后会**立即重新导出**
tasks-data/tasks.js，所以看板刷新即见，不存在"数据写了但看板没更新"。
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from . import emit, ingest
from .model import normalize

MAX_BODY = 4 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    server_version = "taskboard/1.0"
    config = None
    store = None

    # ---------------- 基础 ----------------
    def log_message(self, fmt, *args):                       # noqa: A003
        if self.server.quiet:                                # type: ignore[attr-defined]
            return
        print("[{}] {}".format(self.address_string(), fmt % args), flush=True)

    def _cors(self):
        origin = self.config.cors or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def handle_one_request(self):
        """任何未预期的异常都转成 JSON 错误，不要让连接被直接掐断（客户端会看到 'other side closed'）。"""
        try:
            super().handle_one_request()
        except Exception as e:                                # noqa: BLE001
            print("[error]", repr(e), flush=True)
            try:
                self._err(500, "服务器内部错误：{}".format(e))
            except Exception:                                 # noqa: BLE001
                pass

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8"))

    def _err(self, code: int, msg: str, **extra):
        self._json({"ok": False, "error": msg, **extra}, code)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        if n > MAX_BODY:
            raise ValueError("body too large")
        raw = self.rfile.read(n)
        if not raw.strip():
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # 也接受 x-www-form-urlencoded / 纯文本一行一条
            text = raw.decode("utf-8", "replace").strip()
            try:
                from urllib.parse import parse_qs
                q = parse_qs(text)
                if q:
                    return {k: v[0] for k, v in q.items()}
            except Exception:                                # noqa: BLE001
                pass
            return {"_raw": text}

    def _authorized(self) -> bool:
        if not self.config.token:
            return True
        hdr = self.headers.get("Authorization") or ""
        if hdr.lower().startswith("bearer "):
            return secrets.compare_digest(hdr[7:].strip(), self.config.token)
        q = parse_qs(urlparse(self.path).query)
        return secrets.compare_digest((q.get("token") or [""])[0], self.config.token)

    def _reemit(self):
        try:
            return emit.emit(self.store, self.config)
        except OSError as e:
            print("[emit] 导出失败:", e, flush=True)
            return {}

    def _denied(self, path: str) -> bool:
        """静态托管时的黑名单。

        看板真正会拉的只有 ``.html / .js / 模型文件``，其余一并封掉——
        尤其是任务清单(``inbox/*.md``)、截图(``_shots/``)、备份(``*.bak``)、
        数据库、引擎源码与配置，都不应因为托管看板而暴露到局域网。
        列表项以 ``/`` 开头的按**前缀**匹配；其余按**子串**匹配
        （因为备份名常是 ``xxx.html.bak_pre_zfight`` 这种把 .bak 放中间的形态）。
        """
        deny = self.config.raw.get("server", {}).get("deny") or [
            "/data/", "/taskboard/", "/.workbuddy/", "/.git/", "/_verify/", "/node_modules/",
            "/inbox/", "/_shots/", "/agent-templates/",
            "/board.config.json", "/Dockerfile", "/docker-compose.yml", "/.dockerignore",
            ".bak", ".db", ".db-wal", ".db-shm", ".py", ".md", ".pyc", ".env", ".log"]
        low = path.lower()
        for d in deny:
            d = str(d).lower()
            if not d:
                continue
            if d.startswith("/"):
                if low == d.rstrip("/") or low.startswith(d):
                    return True
            elif d in low:
                return True
        return False

    # ---------------- 路由 ----------------
    def _inject_hint(self, path: str) -> bool:
        """给本服务托管的 HTML 注入数据源提示。

        为什么需要：看板要能"自动"找到 API，但不能靠盲探测——在普通静态服务器
        （如 ``python -m http.server``）上盲探测只会换来一串 404 控制台噪声。
        所以改成"谁托管谁知道"：只有 taskboard 自己托管的页面会被注入
        ``window.__BOARD_API_HINT``，静态打开的页面没有该变量 → 一个请求都不发。
        页面里若已有 ``__BOARD_API_HINT``（例如本地手改过）则不重复注入。
        """
        if not path.lower().endswith((".html", ".htm")):
            return False
        root = os.path.normpath(str(self.config.static_root))
        target = os.path.normpath(os.path.join(root, (path.lstrip("/") or "index.html")))
        if not target.startswith(root) or not os.path.isfile(target):
            return False
        try:
            with open(target, "rb") as f:
                html = f.read().decode("utf-8", "replace")
        except OSError:
            return False
        if "window.__BOARD_API_HINT=location.origin" in html:
            return False                                     # 已注入过，交给静态通道
        hint = ("<script>window.__BOARD_API_HINT=location.origin;"
                "window.__BOARD_POLL={};</script>").format(int(self.config.raw.get(
                    "server", {}).get("boardPollSec") or 20))
        if "</head>" in html:
            html = html.replace("</head>", hint + "</head>", 1)
        else:
            html = hint + html
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        return True

    def do_OPTIONS(self):                                     # noqa: N802
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):                                         # noqa: N802
        path = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)

        if not path.startswith("/api/") and self._denied(path):
            return self._err(403, "该路径不对外提供（数据库/引擎/记忆等内部文件）")

        if not path.startswith("/api/") and self._inject_hint(path):
            return

        if path == "/api/health":
            return self._json({"ok": True, "service": "taskboard", "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "tasks": self.store.stats()["total"],
                               "authRequired": bool(self.config.token)})
        if path == "/api/config":
            return self._json(self.config.redacted())
        if path == "/api/summary":
            return self._json({"ok": True, **self.store.stats()})
        if path == "/api/events":
            return self._json({"ok": True, "events": self.store.recent_events(int((q.get("limit") or ["50"])[0]))})
        if path == "/api/tasks":
            tasks = self.store.list(
                dept=(q.get("dept") or [None])[0],
                status=(q.get("status") or [None])[0],
                source=(q.get("source") or [None])[0],
                agent=(q.get("agent") or [None])[0],
                claim=(q.get("claim") or [None])[0],
                limit=int((q.get("limit") or ["2000"])[0]))
            return self._json({"ok": True, "count": len(tasks), "tasks": tasks})

        # ---- 认领（A+B 中间态）----
        if path == "/api/claims":
            claims = self.store.claims_list(
                status=(q.get("status") or [None])[0],
                agent=(q.get("agent") or [None])[0],
                task_id=(q.get("task") or [None])[0],
                limit=int((q.get("limit") or ["500"])[0]))
            return self._json({"ok": True, "count": len(claims), "claims": claims})
        if path == "/api/queue":
            """agent 的工作队列：已被批准的认领（= 可以开工了）。"""
            agent = (q.get("agent") or [None])[0]
            if not agent:
                return self._err(400, "缺少 ?agent=<名字>")
            rows = [c for c in self.store.claims_list(status="approved", agent=agent, limit=500)]
            tasks = []
            for c in rows:
                t = self.store.get(c["task_id"])
                if t:
                    t["claim_id"] = c["id"]
                    t["claim_note"] = c["note"]
                    t["claim_decided_at"] = c["decided_at"]
                    tasks.append(t)
            return self._json({"ok": True, "agent": agent, "count": len(tasks), "tasks": tasks})
        if path in ("/api/tasks.json", "/api/board.json"):
            return self._json(emit.build_payload(self.store, self.config))
        if path == "/api/tasks.js":
            payload = emit.build_payload(self.store, self.config)
            js = ("window.TASK_DATA = {};\nwindow.TASK_META = {};\n").format(
                json.dumps(payload["data"], ensure_ascii=False),
                json.dumps({"generated": payload["generated"], "totalTasks": payload["stats"]["total"],
                            "byDept": payload["stats"]["byDept"], "bySource": payload["stats"]["bySource"],
                            "generator": "taskboard"}, ensure_ascii=False))
            return self._send(200, js.encode("utf-8"), "application/javascript; charset=utf-8")

        return super().do_GET()

    def do_HEAD(self):                                        # noqa: N802
        return self.do_GET()

    def do_POST(self):                                        # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/"):
            return self._err(404, "not found")
        if not self._authorized():
            return self._err(401, "缺少或错误的 token（Authorization: Bearer <token>）")

        if path == "/api/ingest":
            res = ingest.ingest(self.config, self.store, origin="api")
            self._reemit()
            return self._json({"ok": True, **res})

        if path in ("/api/tasks", "/api/tasks/bulk"):
            try:
                body = self._body()
            except ValueError as e:
                return self._err(413, str(e))
            # 顶层可以直接是数组（最省事：POST 一个 [{...},{...}]）
            if isinstance(body, list):
                items, actor = body, "api"
            else:
                items = body.get("tasks") if "tasks" in body else body.get("items")
                if items is None:
                    items = [body]
                actor = body.get("source") or body.get("agent") or "api"
            if isinstance(items, dict):
                items = [items]
            if not isinstance(items, list):
                return self._err(400, "tasks 必须是数组")

            norm, bad = [], []
            for it in items:
                try:
                    norm.append(normalize(it, self.config.defaults, self.config.limits,
                                          self.config.unassigned_key))
                except ValueError as e:
                    bad.append({"input": it, "error": str(e)})
            res = self.store.add_many(norm, actor=actor)
            # 顺带支持「上报 + 申请接手」一次完成（见 SPEC §5 认领协议）
            claims = ingest.apply_claims(self.store, norm)
            self.store.log_ingest("api", "", {"added": res["added"], "updated": res["updated"],
                                              "skipped": len(bad), "errors": [b["error"] for b in bad]})
            summary = self._reemit()
            return self._json({"ok": bool(res["added"] + res["updated"]) or not bad,
                               "added": res["added"], "updated": res["updated"],
                               "rejected": bad, "ids": [t["id"] for t in norm],
                               "claims": claims,
                               "note": "claims 里的申请处于「待批」，任务状态不变；要开工等人批准。",
                               "total": summary.get("total")}, 200)

        if path == "/api/seed":                               # 一次性灌入一组任务
            return self.do_POST_tasks_alias()

        # ---- 认领（A+B 中间态）----
        # 设计要点：agent 的 POST 只**登记意向**（proposed），绝不直接改任务状态；
        # 只有人在看板上点「批准」才会真正把任务推进到 in_progress。
        if path.startswith("/api/tasks/") and path.endswith("/claim"):
            task_id = path[len("/api/tasks/"):-len("/claim")]
            try:
                body = self._body()
            except ValueError as e:
                return self._err(413, str(e))
            agent = str(body.get("agent") or body.get("source") or "").strip()
            note = str(body.get("note") or body.get("desc") or "")
            try:
                res = self.store.claim_propose(task_id, agent, note, actor=agent or "api")
            except KeyError:
                return self._err(404, "任务不存在: " + task_id)
            except PermissionError as e:
                return self._err(409, str(e))
            except ValueError as e:
                return self._err(400, str(e))
            self._reemit()
            return self._json({"ok": True, **res})

        if path.startswith("/api/claims"):
            parts = path[len("/api/claims"):].strip("/").split("/")
            cid = parts[0] if parts and parts[0] else ""
            action = parts[1] if len(parts) > 1 else ""
            if not cid:
                return self._err(400, "缺少认领 id")
            try:
                body = self._body()
            except ValueError as e:
                return self._err(413, str(e))
            by = str(body.get("by") or body.get("agent") or "api")
            try:
                if action == "approve":
                    res = self.store.claim_decide(cid, True, by=by)
                elif action == "reject":
                    res = self.store.claim_decide(cid, False, by=by, reason=str(body.get("reason") or ""))
                elif action == "withdraw":
                    res = self.store.claim_withdraw(cid, agent=str(body.get("agent") or ""))
                else:
                    return self._err(400, "未知动作（可用 approve / reject / withdraw）: " + action)
            except KeyError:
                return self._err(404, "认领申请不存在: " + cid)
            except (ValueError, PermissionError) as e:
                return self._err(409, str(e))
            self._reemit()
            return self._json({"ok": True, **res})

        return self._err(404, "not found")

    def do_POST_tasks_alias(self):                            # noqa: N802
        return self._err(400, "请用 POST /api/tasks")

    def do_PATCH(self):                                       # noqa: N802
        return self._mutate_one("patch")

    def do_PUT(self):                                         # noqa: N802
        return self._mutate_one("put")

    def _mutate_one(self, mode: str):
        path = urlparse(self.path).path
        if not path.startswith("/api/tasks/"):
            return self._err(404, "not found")
        if not self._authorized():
            return self._err(401, "缺少或错误的 token")
        task_id = path[len("/api/tasks/"):]
        try:
            body = self._body()
        except ValueError as e:
            return self._err(413, str(e))
        if mode == "put":
            try:
                t = normalize(body, self.config.defaults, self.config.limits, self.config.unassigned_key)
            except ValueError as e:
                return self._err(400, str(e))
            self.store.delete(task_id, actor="api")
            r = self.store.upsert(t, actor="api")
            self._reemit()
            return self._json({"ok": True, "result": r, "task": self.store.get(t["id"])})
        updated = self.store.patch(task_id, body, actor="api")
        if updated is None:
            return self._err(404, "任务不存在: " + task_id)
        self._reemit()
        return self._json({"ok": True, "task": updated})

    def do_DELETE(self):                                      # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/tasks"):
            return self._err(404, "not found")
        if not self._authorized():
            return self._err(401, "缺少或错误的 token")
        if path == "/api/tasks":                              # 清空（需 ?dept= 限定或用 ?all=1）
            q = parse_qs(urlparse(self.path).query)
            if not q.get("all") and not q.get("dept"):
                return self._err(400, "拒绝清空全部：请加 ?dept=cfo 或显式 ?all=1")
            n = self.store.clear((q.get("dept") or [None])[0], actor="api")
            self._reemit()
            return self._json({"ok": True, "deleted": n})
        task_id = path[len("/api/tasks/"):]
        ok = self.store.delete(task_id, actor="api")
        self._reemit()
        return self._json({"ok": ok, "deleted": 1 if ok else 0}, 200 if ok else 404)


def _auto_ingest_loop(config, store, stop: threading.Event, quiet: bool):
    while not stop.wait(max(config.auto_ingest_sec, 5)):
        try:
            res = ingest.ingest(config, store, origin="auto")
            if res["added"] or res["updated"]:
                emit.emit(store, config)
                if not quiet:
                    print("[auto-ingest] +{} ~{} ({} 文件)".format(
                        res["added"], res["updated"], res["files"]), flush=True)
        except Exception as e:                                # noqa: BLE001
            print("[auto-ingest] 出错:", e, flush=True)


def serve(config, store, quiet: bool = False):
    config.ensure_dirs()
    Handler.config = config
    Handler.store = store
    handler = partial(Handler, directory=str(config.static_root))
    httpd = ThreadingHTTPServer((config.host, config.port), handler)
    httpd.daemon_threads = True
    httpd.quiet = quiet                                       # type: ignore[attr-defined]

    stop = threading.Event()
    if config.auto_ingest_sec > 0:
        threading.Thread(target=_auto_ingest_loop, args=(config, store, stop, quiet),
                         daemon=True).start()

    print("=" * 66, flush=True)
    print(" taskboard 已启动", flush=True)
    print(" 看板      http://{}:{}/".format(_display_host(config.host), config.port), flush=True)
    print(" 健康检查  http://{}:{}/api/health".format(_display_host(config.host), config.port), flush=True)
    print(" 数据文件  {}".format(config.db_file), flush=True)
    print(" 导出产物  {}".format(config.emit_js), flush=True)
    print(" 写权限    {}".format("需要 Bearer token" if config.token else "未设 token（内网可不开）"), flush=True)
    print(" 自动收件  {} 秒扫描一次 inbox".format(config.auto_ingest_sec or "已关闭"), flush=True)
    print("=" * 66, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[taskboard] 收到中断，退出", flush=True)
    finally:
        stop.set()
        httpd.server_close()


def _display_host(h: str) -> str:
    return "127.0.0.1" if h in ("0.0.0.0", "::", "") else h
