# -*- coding: utf-8 -*-
"""配置加载：board.config.json + BOARD_* 环境变量覆盖。

规则
----
* 所有路径字段都相对 **配置文件所在目录** 解析 → 目录整体搬到哪台机器都能跑。
* 环境变量优先级最高（容器/CI 里最方便）：
    BOARD_CONFIG    配置文件路径（默认：进程工作目录 → 逐级向上找 board.config.json）
    BOARD_DATA_DIR  整个数据目录（会覆盖 db / inbox / archive 的默认相对位置）
    BOARD_HOST / BOARD_PORT / BOARD_TOKEN / BOARD_POLL
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_FILENAME = "board.config.json"

#: 内置兜底值 —— 即使没有配置文件也能跑起来
BUILTIN = {
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
    "defaults": {"status": "todo", "priority": "medium", "project": "未归类", "projectFrom": "source"},
    "unassignedKey": "_unassigned",
    "departments": {},
    "aliases": {},
    "limits": {"title": 80, "desc": 400, "project": 40},
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def find_config(start: Path | None = None) -> Path | None:
    """从 start（默认 cwd）逐级向上找 board.config.json。"""
    env = os.environ.get("BOARD_CONFIG")
    if env:
        p = Path(env).expanduser().resolve()
        return p if p.exists() else None
    here = (start or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        p = d / DEFAULT_FILENAME
        if p.exists():
            return p
    return None


class Config:
    """读好的配置对象。属性即配置项，路径全部已解析为绝对 Path。"""

    def __init__(self, path: Path | None = None, raw: dict | None = None):
        self.path = path
        file_raw = {}
        if raw is None and path and path.exists():
            with open(path, "r", encoding="utf-8") as f:
                file_raw = json.load(f)
        elif raw is not None:
            file_raw = raw
        self.raw = _deep_merge(BUILTIN, file_raw)

        # 配置文件所在目录 = 所有相对路径的锚点
        self.root = (path.parent if path else Path.cwd()).resolve()

        self._apply_env()
        self._resolve_paths()

    # ---------- 内部 ----------
    def _apply_env(self):
        env = os.environ
        if env.get("BOARD_DATA_DIR"):
            d = env["BOARD_DATA_DIR"]
            self.raw["paths"]["dataDir"] = d
            self.raw["paths"]["dbFile"] = str(Path(d) / "taskboard.db")
            self.raw["paths"]["inboxDir"] = str(Path(d) / "inbox")
            self.raw["paths"]["archiveDir"] = str(Path(d) / "inbox" / "_imported")
            self.raw["paths"]["emitJson"] = str(Path(d) / "tasks.json")
        srv = self.raw["server"]
        for key in ("host", "port", "token"):
            v = env.get("BOARD_" + key.upper())
            if v:
                srv[key] = int(v) if key == "port" else v
        if env.get("BOARD_POLL"):
            srv["clientPollSec"] = int(env["BOARD_POLL"])
        if env.get("BOARD_CORS"):
            srv["cors"] = env["BOARD_CORS"]

    def _resolve_paths(self):
        p = self.raw["paths"]
        self.paths = {k: (self.root / v).resolve() for k, v in p.items()}
        srv = self.raw["server"]
        self.host = srv.get("host", "0.0.0.0")
        self.port = int(srv.get("port", 8787))
        self.token = (srv.get("token") or "").strip()
        self.cors = srv.get("cors", "*")
        self.auto_ingest_sec = int(srv.get("autoIngestSec") or 0)
        self.client_poll_sec = int(srv.get("clientPollSec") or 20)
        self.defaults = self.raw.get("defaults") or {}
        self.limits = self.raw.get("limits") or {}
        self.departments = self.raw.get("departments") or {}
        self.aliases = self.raw.get("aliases") or {}
        self.unassigned_key = self.raw.get("unassignedKey") or "_unassigned"

    # ---------- 对外 ----------
    @property
    def db_file(self) -> Path:
        return self.paths["dbFile"]

    @property
    def inbox_dir(self) -> Path:
        return self.paths["inboxDir"]

    @property
    def archive_dir(self) -> Path:
        return self.paths["archiveDir"]

    @property
    def emit_js(self) -> Path:
        return self.paths["emitJs"]

    @property
    def emit_json(self) -> Path:
        return self.paths["emitJson"]

    @property
    def board_html(self) -> Path:
        return self.paths["boardHtml"]

    @property
    def static_root(self) -> Path:
        return self.paths["staticRoot"]

    def ensure_dirs(self):
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.emit_js.parent.mkdir(parents=True, exist_ok=True)
        self.emit_json.parent.mkdir(parents=True, exist_ok=True)

    def redacted(self) -> dict:
        """给 /api/config 用：token 打码。"""
        out = json.loads(json.dumps(self.raw))
        if out.get("server", {}).get("token"):
            out["server"]["token"] = "***"
        out["_resolved"] = {k: str(v) for k, v in self.paths.items()}
        out["_configFile"] = str(self.path) if self.path else "(builtin)"
        return out


def load(path: str | Path | None = None) -> Config:
    if path:
        p = Path(path).expanduser().resolve()
    else:
        p = find_config()
    return Config(p if p and Path(p).exists() else None)
