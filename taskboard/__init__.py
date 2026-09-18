# -*- coding: utf-8 -*-
"""taskboard —— 与具体 AI agent 无关的 3D 看板任务接入引擎

设计原则
--------
1. **不绑定任何 agent**：不读 ~/.workbuddy、不认 skill、不认 Claude Code / Hermes /
   Cursor 的私有目录。只认两种通用能力：往目录里丢文件、往 HTTP 发请求。
2. **不写死路径**：所有路径在 board.config.json 里配，且相对该配置文件解析；
   可用 BOARD_* 环境变量覆盖（容器里改环境变量即可，不用改文件）。
3. **零第三方依赖**：只用 Python 标准库（sqlite3 / http.server / json / pathlib），
   Docker 镜像不需要 pip install，构建不依赖外网。
4. **向后兼容**：仍然产出 tasks-data/tasks.js，老看板不改也能用。
"""

__version__ = "1.0.0"
