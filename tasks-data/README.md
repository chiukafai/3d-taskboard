# 3D 办公室任务看板 — 迁移指南

## 文件清单

看板由两部分组成：看板文件 + 数据管道，全部存放在一个 workspace 目录下。

```
/Users/chiukingsley/WorkBuddy/2026-07-27-23-18-18/
├── office-3d-taskboard.html          ← ���板主文件（双击打开）
└── tasks-data/                        ← 数据管道目录
    ├── tasks.js                       ← 任务数据（60+ 条真实任务，JSON 格式）
    ├── keymap.json                    ← 关键词→部门映射规则
    └── extract-tasks.py               ← 自动提取脚本（从记忆文件生成 tasks.js）
```

此外，task-logger 集成依赖：

```
~/.workbuddy/skills/task-logger/SKILL.md  ← 任务记录 Skill（已更新，步骤 8 自动同步看板）
~/.workbuddy/task_log.md                  ← 全局任务日志（数据源）
~/.workbuddy/memory/CONTEXT_INDEX.md      ← 上下文索引（数据源）
```

## 迁移到其他机器

### 前提条件
- 目标机器已安装 WorkBuddy
- 目标机器的 `~/.workbuddy/task_log.md` 和 `CONTEXT_INDEX.md` 已存在（WorkBuddy 会自动生成）

### 步骤

**1. 复制看板文件夹**

将整个 workspace 目录复制到目标机器的任意位置：

```bash
# 在源机器打包
cd /Users/chiukingsley/WorkBuddy
zip -r office-taskboard.zip 2026-07-27-23-18-18/

# 传输到目标机器后解压
unzip office-taskboard.zip -d ~/WorkBuddy/
```

**2. 首次运行数据提取**

在目标机器上运行一次提取脚本，生成该账号的任务数据：

```bash
cd ~/WorkBuddy/2026-07-27-23-18-18/tasks-data
python3 extract-tasks.py
```

这会从目标机器的 `~/.workbuddy/task_log.md` 和 `CONTEXT_INDEX.md` 提取任务，自动按关键词分类到各部门。

**3. 打开看板**

```bash
open ~/WorkBuddy/2026-07-27-23-18-18/office-3d-taskboard.html
```

或直接双击文件。

**4. （可选）启用自动同步**

确保 task-logger skill 已启用（`~/.workbuddy/skills/task-logger/SKILL.md` 中 `disable: false`）。

之后每次在 WorkBuddy 中说「记录任务」，task-logger 会：
1. 写入 task_log.md
2. 自动运行 `extract-tasks.py` 更新 `tasks.js`
3. 刷新看板即可看到最新任务

## 在非 WorkBuddy 环境中使用

如果目标机器没有 WorkBuddy（没有 `~/.workbuddy/` 目录结构）：

1. 复制看板文件夹
2. **跳过** extract-tasks.py（没有数据源无法运行）
3. 看板会使用 `tasks.js` 中已有的示例/历史数据
4. 手动编辑 `tasks-data/tasks.js` 添加任务
5. 直接双击 `office-3d-taskboard.html` 打开

看板文件是纯 HTML，**不依赖 WorkBuddy**，任何现代浏览器都能打开。

## 文件依赖关系

```
记录任务 (WorkBuddy 对话)
    │
    ▼
task-logger skill
    │
    ├──→ task_log.md ─────────────────┐
    │                                  │
    └──→ 运行 extract-tasks.py ────────┤
                                       ▼
                              tasks-data/tasks.js
                                       │
                                       ▼
                          office-3d-taskboard.html
                              (浏览器打开)
```

## 注意事项

- `tasks.js` 是**本地数据文件**，修改后刷新看板即可看到变化
- `extract-tasks.py` 只依赖 Python 3 标准库，无需安装任何包
- 如果关键词映射不准确，编辑 `keymap.json` 调整规则
- 看板 HTML 依赖 CDN 加载 Three.js，首次加载需联网（之后浏览器缓存）
