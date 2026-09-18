# 看板任务上报规范（SPEC）

> **唯一真源。** 任何 AI agent（WorkBuddy / Claude Code / Hermes / Cursor / 自建脚本）
> 只要按本文件做，任务就能进 3D 看板。**不含任何产品专属依赖、不含绝对路径。**
> 改这一份，所有接入方自动跟着变 —— 不用再去改每个 agent 的配置。
>
> 版本 v1.1 · 2026-09-17
> v1.1 新增：§2.5 上报前先判部门 · §5 认领协议（建议认领 + 人工确认）

---

## 0. 只有三个参数是环境相关的

| 参数 | 本机默认 | 远程/容器 |
|---|---|---|
| `看板地址` | `http://127.0.0.1:8787` | `http://<机器IP>:8787` |
| `写令牌` | 空（未启用校验） | `board.config.json` 里 `server.token`，留空则不带 |
| `上报目录` | `<看板目录>/data/inbox/` | 容器里是 `/app/data/inbox/` |

其余全部固定，不需要每个 agent 各配一套。

---

## 1. 两条上报通道，任选其一

### 通道 A — 发 HTTP（推荐，实时）

```
POST {看板地址}/api/tasks
Content-Type: application/json
Authorization: Bearer {写令牌}        ← 令牌为空时删掉这一行

{"title":"任务标题","dept":"cfo","status":"done","priority":"high","source":"你的名字","project":"项目名","desc":"一句话说明"}
```

- 顶层可以直接是数组，一次发多条：`[{...},{...}]`
- 也可以包一层：`{"source":"你的名字","tasks":[{...},{...}]}`
- 返回 `{"ok":true,"added":n,"updated":n,...}`

### 通道 B — 写文件（完全离线也能用）

往 `{上报目录}` 写一个文件，服务端每 30 秒自动扫，处理完归档到 `_imported/`。

支持后缀：`.json` `.jsonl` `.ndjson` `.md` `.markdown` `.txt`

**最推荐 `.jsonl`** —— 一行一个任务对象，追加写不易写坏：

```jsonl
{"title":"月度营收趋势模块联调","dept":"cfo","status":"in_progress","priority":"high","source":"my-agent"}
{"title":"商品图片匹配逻辑归档","dept":"cto","status":"done","source":"my-agent"}
{"title":"这条不写部门，靠关键词自动归类（对账）"}
```

也可以立即收件，不等 30 秒：

```bash
python -m taskboard ingest
```

---

## 2. 字段规范

**`title` 是唯一必填字段。** 其余全可省。

| 字段 | 说明 | 取值 |
|---|---|---|
| `title` | 任务名 | 任意文本 |
| `dept` | 归到哪个房间 | `ceo` `cfo` `cto` `cpo` `cmo` `coo` `cro` `meeting` |
| `status` | 状态 | `todo` `in_progress` `done` `blocked` |
| `priority` | 优先级 | `high` `medium` `low` |
| `source` | **来源 agent 名**（建议必填） | `workbuddy` / `claude-code` / `hermes` … |
| `project` | 项目名 | 不填时默认等于 `source` |
| `desc` | 说明 | 任意文本 |
| `due` | 截止 | 任意文本 |
| `tags` | 标签 | 数组或逗号分隔 |
| `collaborators` | 跨部门协作 | 部门 id 数组，≥2 个时看板画联动线 |
| `external_id` | 上游唯一编号 | 填了就按它去重；不填按标题去重 |

### 别名宽容度（写中文/写错都能认）

| 你写什么 | 识别为 |
|---|---|
| `name` `task` `标题` `summary` `任务` | `title` |
| `zone` `team` `room` `部门` `department` | `dept` |
| `财务` `会计` `对账` `finance` `CFO` | dept `cfo` |
| `营销` `市场` `marketing` `小红书` | dept `cmo` |
| `技术` `研发` `dev` `IT` | dept `cto` |
| `待办` `未开始` `open` `pending` | status `todo` |
| `进行中` `doing` `wip` `state:doing` | status `in_progress` |
| `已完成` `完成` `closed` `resolved` `done:true` | status `done` |
| `阻塞` `卡住` `blocked` `stuck` | status `blocked` |
| `高` `紧急` `urgent:true` `critical` `p0` | priority `high` |
| `dep` `collab` `协作` | **collaborators**（不是 dept） |

> ⚠️ `dept:` 与 `dep:` 只差一个字母：前者「这条归谁」，后者「要和谁协作」。写混不报错，只是归类不对。

### 行内 Markdown 写法（写 `.md` / `.txt` 时最省事）

```
[cfo] 月度营收趋势模块联调 | p:high | s:in_progress | desc:对外数据第一优先
- [x] 已完成的事 | dept:meeting | p:high          ← [x] = 已完成
- [ ] 待办的事 | s:todo | dep:cfo,cto             ← [ ] = 待办
cfo: 冒号前缀写法也行 | p:low
这是一行裸文本，也照样收成任务
```

`.md` 开头的 front-matter 会作为该文件内所有任务的默认值：

```markdown
---
source: hermes
project: Hailu-SC-EMS
dept: cfo
---
```

单条任务自己写了同名字段则以单条为准。

---

## 2.5 上报前先判「这条归谁」——比事后被猜准得多

引擎在你没写 `dept` 时会按标题关键词猜（**猜是概率性的**）。你自己判一次更准，
而且判错的责任清楚：看板会把你判的和引擎猜的**用不同标记区分开**，人一眼能看出哪些需要复核。

### 三步判别法

**第 1 步 · 谁验收 → 就是 `dept`。**
问自己：这件事做完，是**谁拍板说"行"**？

| 做完谁验收 | 写 |
|---|---|
| 财务报表 / 对账 / 成本 / 资金 | `cfo` |
| 接口 / 部署 / 代码 / 数据 | `cto` |
| 投放 / 文案 / 品牌 / 活动 | `cmo` |
| 发货 / 物流 / 库存 / 采购 | `coo` |
| 需求 / 原型 / 功能设计 | `cpo` |
| 合规 / 合同 / 审计 / 风控 | `cro` |
| 年度规划 / 投资 / 董事会决议 | `ceo` |
| 跨部门评审会 / 例会 | `meeting` |

**第 2 步 · 谁给料 → 写进 `collaborators`。**
需要别的部门提供数据、审批或接口时填部门数组，如 `"collaborators":["cfo","cto"]`。
≥2 个时看板会画联动线（纯视觉提示，不会自动通知对方）。

**第 3 步 · 判不出来就别硬编。**
两种处理都行：
- **不写 `dept`** → 引擎按关键词猜，看板上打「**部门待核**」灰标，提醒人复核；
- **写最近的那个部门 + 用 `dept_reason` 说明理由**（≤80 字），看板详情里能看到。

```json
{"title":"仓库温控设备巡检","dept":"coo","dept_reason":"由运营验收，技术只提供传感器数据","source":"my-agent"}
```

> **判别口诀：`dept` = 谁验收；`collaborators` = 谁给料。**
> 拿不准时，宁可写 `collaborators`，也别乱写 `dept` ——
> 协作错了只是少一条线，归属错了是**整条任务进错房间**。

### 你的判断和引擎的猜测，看板怎么区分

| 情况 | 看板标记 |
|---|---|
| 你显式写了 `dept` | 无标记（信任你的判断），详情里显示"上报方判定" |
| 你没写，引擎猜到了 | 灰色「**部门待核**」标 + 鼠标悬停显示猜的依据 |
| 你没写且猜不出 | 进「未归类」桶，**不落任何房间**（在 ⚙ 系统设置 → 记忆派生任务 可见） |
| 你写了但引擎认不出（如写了不存在的部门名） | 同「部门待核」，不会静默丢掉 |

---

## 3. 三条纪律

1. **未完成的也要记。** 不要只报成功的事。没做完用 `in_progress`，卡住的用 `blocked`。
2. **重复上报不会变两条。** 系统按「部门 + 标题（或 external_id）」去重，重复上报 = 更新，任务 id 稳定不变。**所以状态变了直接再报一次即可。**
3. **一次会话尽量 3 条以内**（合并同类项）。只有标题没把握时才补 `desc`。不要为凑数硬造任务。

会话收尾时，用一句话汇报上报了几条、有没有失败。

---

## 4. 两个已知边界（照实说，别让 agent 误以为能做到）

1. **没有"自动派活"。** 上报只是「记下来」。看板不会自动把任务转给别的部门，也不会自动触发别的 agent。
   想让 agent 主动接活，走 §5 的**认领协议**——那是"agent 提申请、人来批"，不是自动调度。
2. **部门归类是「猜」的。** 没写 `dept` 时按标题关键词猜，猜不出进「未归类」桶（在 ⚙ 系统设置 → 记忆派生任务 里可见），
   **不会**自动落到某个房间。想要确定性归类，就按 §2.5 显式写 `dept`。

---

## 5. 认领协议（A+B 中间态：建议认领 + 人工确认）

> **可选功能。** 只想"上报"的 agent 看完 §1 §2 就够了，不用读这节。
> 读这节的前提：你希望**主动接手**别人的待办任务，而不是等人派活。

### ⚠️ 唯一的铁律

**你只能"申请"，不能自己开工。** 任务状态的推进权在人手里。
你提申请之后任务**仍是 `todo`**，此时**不要开始干活**——真开工了人也不知道，等于白干。

### 5.1 三步

**① 看有哪些活可以接**

```
GET {看板地址}/api/tasks?status=todo&dept=<你团队的部门>&claim=none
```

`claim=none` 表示"还没人申请接手"。返回 `{"ok":true,"count":n,"tasks":[{id,title,...}]}`。

**② 提申请（任务状态不变，只是登记意向）**

```
POST {看板地址}/api/tasks/<任务id>/claim
Content-Type: application/json

{"agent":"你的名字","note":"为什么你能接 / 打算怎么做"}
```

返回 `{"ok":true,"result":"proposed","claim":{"id":"cl-xxxx","status":"proposed"}}`。

也可以**在上报任务的同时顺手申请**（一次请求搞定，少学一个接口）：

```json
{"title":"...", "dept":"cfo", "source":"my-agent", "claim":{"agent":"my-agent","note":"我能接"}}
```

`claim` 也可以直接写字符串：`"claim":"my-agent"`。

**③ 等批准后取活**

```
GET {看板地址}/api/queue?agent=你的名字
```

**只有出现在这个列表里的任务才是"已批准、可以开工"的。** 干完仍按 §1 正常上报 `status:done`。

### 5.2 你的申请处于什么状态，你该做什么

| 状态 | 含义 | 你的动作 |
|---|---|---|
| `proposed` | 等人工批 | **什么都别做**（别开工）。下次会话再来查一次即可 |
| `approved` | 已放行 | 开工；完成后上报 `status:done` |
| `rejected` | 被驳回 | 停手，**不要重试**。`reason` 字段里有原因 |
| `withdrawn` | 你自己撤回的 | — |

查自己的申请状态：`GET {看板地址}/api/claims?agent=你的名字`
不想接了：`POST {看板地址}/api/claims/<认领id>/withdraw  {"agent":"你的名字"}`

### 5.3 六条规则

1. **一条任务只会被批准给一个 agent。** 已被别人拿下后再申请 → `409`，据此判断"这活被抢了"。
2. **多个 agent 申请同一条 = 正常。** 人会挑一个，其余自动驳回（`reason: "已被 xxx 认领"`）。
3. **重复申请是"更新"，不会刷屏**（同任务 + 同 agent 共用一个认领 id）。
4. **已批准的申请再报一次不会退回待批** —— 人批过的，不能被 agent 自己改回去。
5. **人可以撤销批准**，任务会退回 `todo`。别把"批准"当永久授权。
6. **已完成（`done`）的任务不能再申请**。

### 5.4 只会写文件的 agent 怎么用

能往投递箱写文件的话，把 `claim` 放进任务对象即可（服务端收件时自动登记申请）：

```jsonl
{"title":"供应商账期重谈","dept":"cfo","status":"todo","source":"file-only-agent","claim":{"agent":"file-only-agent","note":"从投递箱申请"}}
```

但**后续的"查状态 / 取队列"仍要能发 HTTP** —— 认领是一来一回的交互，
写文件这种方式只适合单向提交，不适合等回音。完全不能联网的 agent 请走 §1 纯上报。
