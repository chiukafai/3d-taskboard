# 看板任务入站 · 操作手册 v2

> 把任意 Agent 里的待办,**直接生成 .md 任务清单** 落到看板 inbox。
> v2 简化:无需快捷键、无需 capture.py,只需 **3 步**。

---

## 一、3 步上手(0 额外配置)

### Step 1 — Agent 端(每个 Agent 第一次配置一次)

把 Skill 文档装到你的 Agent:
- **WorkBuddy**:`~/.workbuddy/skills/board-export/SKILL.md`(已装 ✅ v2.0.0)
- **Hermes / Codex / 其他**:参照 `board_export_skill.md` 末尾"维护"节

### Step 2 — 直接使用(无需热键、无需 capture)

```
任意 Agent 会话结束前:
  → 输入 /board-export(或"导出待办" / "入库看板" / "to board")
  → Agent 扫描会话 → 生成 .md 文件 → 保存到 inbox/
  → 路径:~/AI Data/WorkBuddy/WPS云同步（workbuddy)/workbuddy看板/inbox/
  → 文件名:任务清单_YYYYMMDD_HHMM.md
```

### Step 3 — 导入到看板

```
1. 打开 inbox/任务清单_*.md,浏览/编辑(不合适直接删)
2. 打开 3D 看板 → 工具栏「📥 导入」
3. 复制"实际导入命令" → 终端粘贴运行
4. 回到看板 → 点"刷新页面"按钮(或 Cmd+R / Ctrl+R)
5. ✅ 新任务出现在对应部门房间
```

---

## 二、生成的 .md 文件长什么样

文件名:`任务清单_20260810_0018.md`

内容:

```markdown
# 任务清单 · 2026-08-10 00:18

> 来源:WorkBuddy(家里 Mac)
> 触发会话:WB 看板配置-001 收尾
> 任务数:3 条
> 提取时间:2026-08-10 00:18:30

---

```board
[cfo] Q3 税务筹划方案 | p:high | d:2026-08-15 | desc:研发加计+加速折旧测算
[cto] WordPress CDN 修复 | p:high | s:blocked | desc:阻塞中,等 Cloudflare 配置确认
[meeting] Q4 预算预审会议 | p:medium | d:2026-09-30 | desc:审各部门预算草案
```
```

**结构**:
- 第 1–7 行:元数据(来源、触发会话、任务数、时间)
- 第 9 行:`---` 分隔线
- 第 10 行起:` ```board ` 代码块内放任务行(每行一条,严格 schema)

**用户可以**:
- 直接看哪几条要入库
- 不想入的删除该行
- 改优先级/截止日/状态,字段格式不变
- 加部门、改部门、合并协作部门

---

## 三、过滤准则(决定什么该入 .md)

每次想捕获时,问自己4 个问题,**至少满足 3 个才入库**:

| # | 判定 | 反例 |
|---|---|---|
| 1 | **有明确动作**(动词开头:做/修/编/审/查/跟/出/设/建/对接) | "了解一下 X"、"讨论一下 Y" |
| 2 | **有具体标的**(不是泛泛而谈) | "看看自动化" vs "修复 WordPress CDN" |
| 3 | **可归到部门**(8 选 1) | 跨部门模糊议题 → 归 `meeting` |
| 4 | **有时限或隐含本季度** | "以后再说" vs "8/15 前完成" |

**反例不入**:闲聊、寒暄、Q&A 答案、灵感(改去 MEMORY.md)、重复任务。

---

## 四、字段约束(每行一条,字段分隔用半角" \| ")

| 字段 | 必填 | 取值 | 备注 |
|------|:----:|------|------|
| `[dept]` | ✅ | `ceo` / `cfo` / `cto` / `cpo` / `cmo` / `coo` / `cro` / `meeting` | 小写,以方括号开头 |
| `title` | ✅ | ≤40 字 | 紧跟部门后,第一个 `\|` 之前 |
| `p:priority` | ❌ | `high` / `medium` / `low` | 默认 `medium` |
| `d:due` | ❌ | `YYYY-MM-DD` | 无截止日可省 |
| `s:status` | ❌ | `todo` / `in_progress` / `blocked` | 默认 `todo` |
| `dep:collaborators` | ❌ | `dept1,dept2` | 多人协作时逗号分隔 |
| `desc:description` | ❌ | 自由文本 | **必须是最后一个字段**,**不含半角 `\|`**(用全角 `｜`) |

---

## 五、文件结构(WPS 同步目录)

```
workbuddy看板/
├── office-3d-taskboard.html       ← 3D 看板(主页)
├── tasks-data/
│   ├── tasks.js                   ← 当前任务数据
│   ├── tasks.js.bak-YYYYMMDD-HHMMSS  ← 每次导入自动备份
│   └── ...
├── board_export_skill.md          ← 单一权威 Skill 文档
├── inbox/                         ← Skill 输出的任务清单(.md)
│   ├── 任务清单_20260810_0018.md  ← 待导入
│   ├── 任务清单_20260810_0930.md  ← 待导入
│   └── processed/                 ← 已处理的归档(带时间戳前缀)
│       └── 20260810-1045_任务清单_20260810_0018.md
├── import_inbox.py                ← 校验+合并脚本
└── board_capture_guide.md         ← 本文档
```

---

## 六、import_inbox.py 用法

```bash
# 默认:扫描 inbox/ 下所有 .md,合并后归档
python3 import_inbox.py

# 预览(不写不归档)
python3 import_inbox.py --dry-run

# 处理单个文件
python3 import_inbox.py --file inbox/任务清单_20260810_0018.md

# 不归档(默认归档到 processed/)
python3 import_inbox.py --no-archive

# 保留原文件(等同 --no-archive,语义别名)
python3 import_inbox.py --keep
```

**自动做的事**:
- 校验每条任务(部门、字段、格式)
- 去重(完全相等 + 子串 ≥80% 相似)
- 备份 `tasks.js` → `tasks.js.bak-YYYYMMDD-HHMMSS`
- 合并入 `tasks.js`,自动分配新 id
- 归档已处理的 .md → `inbox/processed/`

---

## 七、Win/Mac 路径差异

| 平台 | inbox 路径 |
|------|------------|
| Mac(家里) | `~/AI Data/WorkBuddy/WPS云同步（workbuddy)/workbuddy看板/inbox/` |
| Windows(公司) | `%USERPROFILE%\AI Data\WorkBuddy\WPS云同步(workbuddy)\workbuddy看板\inbox\` |

> 路径里的中文括号 Win 是**半角**,Mac 是**全角**——WPS 会自动转换。

**import 命令**:
- Mac:`python3 ~/AI Data/.../import_inbox.py`
- Win:`python %USERPROFILE%\AI Data\...\import_inbox.py`

---

## 八、常见问题

| 症状 | 可能原因 | 处理 |
|---|---|---|
| Agent 输出代码块没生成文件 | Agent 没有文件写权限 | 改用"降级方案":Agent 输出完整 .md 到聊天,你手动复制保存到 inbox/ |
| 导入时报"未知部门" | .md 里的部门代码不在 8 个里 | 检查 `[xxx]` 是否拼错(ceo/cfo/cto/cpo/cmo/coo/cro/meeting) |
| desc 报错 | desc 字段里出现半角 `\|` | 改用全角 `｜`,或挪到不需分隔的字段 |
| 任务标题重复 | 与 tasks.js 已有任务标题完全相同 | 改名或合并(导入脚本自动跳过重复) |
| inbox 文件没归档 | 加了 `--keep` 或 `--no-archive` | 默认下次会归档 |
| 看板不显示新任务 | 浏览器缓存了旧 tasks.js | Cmd+R / Ctrl+R 强制刷新 |

---

## 九、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-08-10 | 重构:Skill 直接生成 .md 文件到 inbox/,删除 capture.py / capture_input.py / board_inbox.md |
| 1.0.0 | 2026-08-10 | 初版:capture.py + board_inbox.md + 快捷键(已废弃) |