---
name: board-export
display_name: 任务入看板
description: 扫描会话产出可导入 3D 看板的任务清单。聚焦 Kingsley 角色（财务总监 + 营销），多轮动作识别与多目的拆解，确保所有执行都生成可入看板的项。触发词：/board-export、/导出待办、/入库看板、/to-board。
description_zh: 任务入看板：扫描当前会话，把识别到的动作/待办按规则聚合拆解，生成 任务清单_YYYYMMDD_HHMM.md 保存到 3D 看板 inbox/ 目录（Windows：E:\AI\Workbuddy\WPS云同步（workbuddy)\workbuddy看板\inbox\；Mac：~/AI Data/WorkBuddy/WPS云同步（workbuddy)/workbuddy看板/inbox/），供 import_inbox.py 导入 3D 任务看板。触发词：/board-export、/导出待办、/入库看板、/to-board、导出待办、任务入看板、任务清单。
version: 3.2.0
author: Kingsley
single_source_of_truth: WPS云同步/workbuddy看板/board_export_skill.md
changelog: |
  v3.2.0 (2026-08-11) — 新增 description_zh 适配千问办公触发；新增千问办公副本 ~/.qwenworkcn/skills/board-export/
  v3.1.0 (2026-08-11) — 结构精简（规则不变）：合并冗余章节、删除历史叙述；status 取值补充 done；修正 Windows 导入命令为 python；明确两处同步副本
  v3.0.0 (2026-08-10) — 删除"时限"筛选；新增多轮动作识别与多目的处理；强化强制产出
  v2.0.0 (2026-08-10) — 改为生成完整 .md 文件保存到 inbox/
trigger: ["/board-export", "/导出待办", "/入库看板", "/to-board"]
---

# 任务导出至 3D 看板

扫描本会话**全部对话**，基于 **Kingsley 角色（财务总监 + 市场营销）**视角识别动作与目的，按规则聚合或拆解，生成完整 .md 保存到 inbox/。

## 一、核心原则

1. **强制产出**：所有执行都生成可入看板项；只有经反思确认"零信号"才回复"无任务"。
2. **角色对焦**：任务必须映射 Kingsley 实际工作面（见下表）。
3. **可执行优先**：每条必须是部门房间可承接的具体动作，不泛泛而谈。

| Kingsley 工作面 | 主部门 | 典型任务 |
|---|---|---|
| 财务管理 | `cfo` | 预算、报表、税务、现金流、ROI、风险、建模 |
| 市场营销 | `cmo` | 小红书/公众号内容、投放、品牌、商品目录 |
| 内容产品 | `cpo` | 报告模板、多平台阅读体验 |
| 跨部门 | `meeting` | 评审、预审、对齐、季度复盘 |

## 二、输出规范

**保存路径**（`import_inbox.py` 会自动探测，无需严格匹配）：

| 平台 | 路径 |
|---|---|
| Windows | `E:\AI\Workbuddy\WPS云同步（workbuddy)\workbuddy看板\inbox\`（括号为**全角**） |
| Mac | `~/AI Data/WorkBuddy/WPS云同步（workbuddy)/workbuddy看板/inbox/` |

**文件名**：`任务清单_YYYYMMDD_HHMM.md`（24 小时制），如 `任务清单_20260810_1130.md`。

**完整样例**：

````markdown
# 任务清单 · 2026-08-10 11:30

> 来源:WorkBuddy(家里 Mac)
> 触发会话:WB 看板配置收尾
> 任务数:3 条
> 提取时间:2026-08-10 11:30:00

---

```board
[cfo] Q3 税务筹划方案 | p:high | d:2026-08-15 | desc:研发加计+加速折旧测算,CFO 会议输出文档
[cto] WordPress CDN 修复 | p:high | s:blocked | desc:阻塞中,等 Cloudflare 配置确认
[meeting] Q4 预算预审会议 | p:medium | dep:cfo,ceo | desc:审各部门预算草案
```
````

解析脚本只认 ` ```board ` 代码块：**任务行必须在代码块内**，块外不算。

## 三、识别规则

### 3.1 三条筛选（须同时满足）

1. 有明确动作（动词或动作信号词）——反例："了解一下 X"。
2. 有具体标的——反例："看看自动化"（无对象）vs "修复 WordPress CDN"（有对象）。
3. 可归到 8 部门之一——跨部门模糊议题归 `meeting`。

### 3.2 动作信号词（5 类）

| 类型 | 例词 | 含义 |
|---|---|---|
| 完成态 | 修复、编写、提交、上线、发布、敲定 | 已完成，可标 `s:done` |
| 执行态 | 推进、跟进、协调、对齐、推动 | 持续性任务 |
| 决策态 | 决定、选定、采纳、批准 | 决策型任务 |
| 未来态 | 计划、准备、安排、待、将要 | 待办任务 |
| 责任态 | 负责、主导、统筹、对接、收口 | 责任型任务 |

**不算动作**：状态动词（是/有/在）；思考与询问动词（想/觉得/考虑/了解/看看）——但紧跟明确动作时计入（如"决定做 X"、"了解并修复"）。

### 3.3 多轮链路（4 类）

| 模式 | 链路 |
|---|---|
| A | 建议 → 同意 → 已落地 |
| B | 出问题 → 查原因 → 修复 |
| C | 探索 → 对比 → 选定 |
| D | 建议 → 反馈调整 → 定稿 |

**要求**：捕获**最终决策/动作**，忽略中间被否决的方案。

### 3.4 聚合与拆分

- **默认聚合**：按主部门合成一条任务，协作部门记入 `dep:`（如财务+营销 → 一条，`dep:cfo,cmo`）。
- **100% 完全独立才拆**：两事核心目的互不相关、分属不同部门且需分别跟踪（如同一会话里"修复 CDN"和"双 11 投放"）→ 拆；同一事的不同阶段（调研→方案→落地）→ 合。

## 四、字段约束

每行一条，字段用半角 ` | ` 分隔：

| 字段 | 必填 | 取值 |
|---|:-:|---|
| `[dept]` | ✅ | 8 选 1（见第五节），小写方括号开头 |
| `title` | ✅ | ≤40 字，紧跟部门 |
| `p:priority` | ❌ | high/medium/low，默认 medium |
| `d:due` | ❌ | YYYY-MM-DD |
| `s:status` | ❌ | todo/in_progress/blocked/done，默认 todo |
| `dep:` | ❌ | dept1,dept2（跨部门时填） |
| `desc:` | ❌ | **必须最后一个字段**，不含半角 `|`（用全角 ｜） |

## 五、部门归纳

| ID | 适配场景 |
|---|---|
| `ceo` | 战略、方向、OKR、跨部门协调、复盘 |
| `cfo` | 财务、预算、税务、现金流、ROI、风险、建模 |
| `cto` | 系统、技术、自动化、运维、CDN、Skill、配置 |
| `cpo` | 产品、设计、模板、UI/UX、阅读体验 |
| `cmo` | 内容、小红书/公众号/抖音/微博、投放、品牌、商品 |
| `coo` | SOP、流程、周报、看板、排期、交付 |
| `cro` | 安全、合规、审计、风险、隐私、应急 |
| `meeting` | 跨部门会议、评审、预审、对齐 |

- 涉及 2+ 部门 → 主部门 + `dep:`（例：投放 ROI 复盘 → 主 `cmo`，`dep:cmo,cfo`）。
- 主题模糊 → `meeting`；完全无法判断 → `cto` 兜底。

## 六、严格禁止

- 任务行散落在代码块外。
- 输出无法归到 8 部门的"任务"。
- 描述里出现半角 `|`（解析器拒绝整行）。
- 明明识别到信号词却跳过不产出（违反强制产出）。
- 把多个完全独立事项硬塞进一条任务的 `dep:`（应拆分）。

## 七、保存后回复

**有任务**（只允许一句话）：

```
已生成 inbox/任务清单_YYYYMMDD_HHMM.md（N 条）。
如需修改直接编辑该文件；确认后运行导入（Windows: python tasks-data/import_inbox.py；Mac: python3 tasks-data/import_inbox.py），或用看板 📥 导入按钮。
```

**无任务**（须经反思确认零信号）：

```
本会话经反思后确认无符合条件的新待办。
（如有遗漏请明确指出"把 X 入看板"）
```

## 八、无写权限降级

把完整 .md（头部 + 代码块）输出到聊天 → 请用户保存为 `<inbox 路径>/任务清单_YYYYMMDD_HHMM.md` → 用户自行跑 import。

## 九、维护

- **唯一权威源（SSOT）**：`WPS云同步/workbuddy看板/board_export_skill.md`。
- **三处同步副本**（内容须与 SSOT 完全一致）：
  1. 看板目录 `.workbuddy/skills/board-export/SKILL.md`（WorkBuddy 项目级）
  2. 用户级 `~/.workbuddy/skills/board-export/SKILL.md`（WorkBuddy 用户级，会被 WorkBuddy 扫描）
  3. 千问办公用户级 `~/.qwenworkcn/skills/board-export/SKILL.md`（千问办公技能目录，靠 description/description_zh 触发）
- **修改流程**：改 SSOT → 同步三处副本 → 测试一次 Skill 验证。
- **版本规则**：frontmatter `version` 递增——大改升 major，字段新增升 minor，文案修订升 patch。

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| 3.2.0 | 2026-08-11 | 新增 description_zh（千问办公中文触发）；新增千问办公副本 ~/.qwenworkcn/skills/ |
| 3.1.0 | 2026-08-11 | 结构精简（规则不变）；status 补 done；修正 Windows 导入命令；明确两处同步副本 |
| 3.0.0 | 2026-08-10 | 删除时限筛选；多轮动作识别（5 类信号词 + 4 类链路）；多目的处理；强化强制产出 |
| 2.0.0 | 2026-08-10 | 改为生成 .md 文件保存到 inbox/ |
