# MEMORY.md — workbuddy看板 项目长期记忆

## 关键事实（2026-08-10 确认）

- **目录是 junction**：`E:\AI\Workbuddy\workbuddy看板` 与 `E:\AI\Workbuddy\WPS云同步（workbuddy)\workbuddy看板` 是同一物理目录（cp 报 "same file"）。所有写入只会影响一份文件，无需分别同步。
- **WPS 云占位（Offline 属性）**：`tasks-data/tasks.js`（真实任务数据）在本机为 WPS 云占位文件，内容未本地化，`cat`/Read/python 读取均失败（OSError 22 / Permission denied）；`ls`/`wc`/`attrib` 正常。`office-3d-taskboard.html` 为本地可用（无 O 属性）。若看板显示示例任务，多半是 tasks.js 未"始终保留在此设备"导致加载失败回退 FALLBACK_TASKS。

## 看板任务数据双管线

| 管线 | 触发 | 脚本 | 产物 | 加载方式 |
|------|------|------|------|----------|
| 自动 | task-logger 技能 | `tasks-data/extract-tasks.py` | `tasks-data/tasks.js`（`window.TASK_DATA`） | HTML `loadTasks()` |
| 手动/跨机 | board-export 技能（`/board-export`） | `tasks-data/import_inbox.py` | `tasks-data/inbox_tasks.js`（`window.TASK_INBOX`） | HTML `loadTasks()` 合并 |

- 两条管线**互不覆盖**：`import_inbox.py` 只读 `inbox/*.md`，生成独立 `inbox_tasks.js`，绝不改 `tasks.js`。
- `import_inbox.py` 自动探测 inbox 位置（Win 全角括号 `（workbuddy）`/Mac/工作区兜底），解析 ```board 代码块，归档已处理 `.md` 至 `inbox/_imported/`。
- board-export 技能已安装：`E:\AI\Workbuddy\workbuddy看板\.workbuddy\skills\board-export\SKILL.md`（frontmatter 用 `trigger` 单数列表，非 `triggers`）。

## 技能文件位置

- board_export_skill.md（SSOT）与已安装的 SKILL.md 为同一目录树下的两份（junction 同一文件），改一处即同步。

## 浏览器内导入的 UX 陷阱 (2026-08-10)

看板内 📥 导入按钮走浏览器 `<input webkitdirectory>` → 解析 → **自动下载** inbox_tasks.js 到 `Downloads/`，但浏览器安全限制无法直接写入 `tasks-data/`。

- **典型踩坑**：用户以为"导入完成 = 任务已入看板"，其实文件还在 Downloads 没移动，刷新看不到任务。
- **看板弹窗已优化**（v1.1）：明确显示"接下来要做 2 步"+ 目标路径 + 一键复制按钮 + `<kbd>F5</kbd>` 提示。
- **建议优先用 Python 路径**：`python3 tasks-data/import_inbox.py` 直接写 `tasks-data/inbox_tasks.js`，免移动。Python 解析已用 node 单测 6/6 验证。

## ⚠️ WPS 云同步冲突风险（2026-08-11 确认，重大）

- 本看板项目经 **WPS云同步（workbuddy)** 在 **Mac + Windows 双机**间同步。
- 同步机制为 **last-write-wins**；WPS 对 `.html`/`.js` 等纯文本文件**通常不保留历史版本**（历史版本主要覆盖 WPS 自有文档格式）。
- **致命陷阱**：在任一台机器「仅打开/查看」文件，也可能触发 WPS 把该机**本地旧版**回传云端，覆盖另一台机器更新的修改。2026-08-11 已发生：Mac 本地为 Aug 10 00:20 旧版，仅打开页面即把云端 Windows 早修改覆盖，且云端无解。
- **恢复窗口依赖另一台机器的本地副本**：对方 WPS 尚未把坏版本拉下来前，其本地仍存好版本。处置顺序：立即去另一台 → 复制到非同步区（桌面/U盘）→ 再确认内容。
- **预防约定**：①跨机编辑前确认 WPS 状态=已同步；②只看效果就开副本、不开同步文件；③重要修改后 `zip` 一份到非同步区；④建议项目用 **git** 做版本控制（独立于 WPS，能真正留历史）。
