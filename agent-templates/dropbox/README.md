# 投递箱（完全离线，不需要网络）

只要你的 agent **能往目录里写文件**，就能录任务 —— 连 HTTP 都不用会。

把文件放进：

```
<看板目录>/data/inbox/
```

服务端每 **30 秒**扫一次（`board.config.json` 里的 `server.autoIngestSec`），
处理完会把文件挪到 `data/inbox/_imported/` 存档，不会重复处理。

也可以手动立即收件：

```bash
python -m taskboard ingest
```

---

## 支持的文件格式（四选一）

### 1. `.jsonl` —— **最推荐给 agent 用**

一行一个 JSON 对象，追加写不容易写坏，天然适合 agent 边干边记：

```jsonl
{"title":"月度营收趋势模块联调","dept":"cfo","status":"in_progress","priority":"high","source":"my-agent"}
{"title":"商品图片匹配逻辑归档","dept":"cto","status":"done","source":"my-agent"}
{"title":"这条不写部门，靠关键词自动归类（对账）"}
```

### 2. `.json` —— 结构化

```json
[
  {"title": "小红书 9 月投放复盘", "dept": "marketing", "status": "待办", "priority": "中"},
  {"title": "发货单需求收敛", "zone": "ops", "state": "doing", "urgent": true}
]
```

或 `{"tasks": [ ... ]}` 包一层也行。

### 3. `.md` —— 人也能读，agent 也好写

```markdown
---
source: claude-code
project: Hailu-SC-EMS
---

## 本次会话

```board
[cfo] 月度营收趋势模块联调 | p:high | s:in_progress | desc:对外数据模块第一优先
[cto] 图片匹配逻辑归档 | s:done
[meeting] 周五例会复盘
```

```json
[{"title":"另一条走 JSON 也行","dept":"cmo"}]
```

- [ ] 清单写法：未勾选 = 待办
- [x] 已勾选 = 已完成
```

### 4. `.txt` —— 兜底

先按 JSONL 试，不行再按上面的 `[dept] 标题` / 清单行解析。

---

## front-matter 的作用

文件开头那三行 `---` 之间的内容会作为**默认值**注入到该文件里的每条任务：

```markdown
---
source: hermes          # 这个文件里所有任务的来源都记为 hermes
project: 我的项目         # 都归到这个项目
dept: cfo               # 都没写部门时默认归财务
---
```

单条任务里自己写了同名字段，则以单条为准。

---

## 别名宽容度（写错不了）

| 你写什么 | 会被识别为 |
|---|---|
| `财务` `会计` `对账` `finance` `CFO` | 部门 `cfo` |
| `marketing` `营销` `市场` `小红书` | 部门 `cmo` |
| `已完成` `完成` `done` `closed` `resolved` | 状态 `done` |
| `进行中` `doing` `wip` `state:doing` | 状态 `in_progress` |
| `阻塞` `卡住` `blocked` `stuck` | 状态 `blocked` |
| `高` `紧急` `urgent:true` `critical` | 优先级 `high` |
| `name` `title` `任务` `标题` `summary` | 任务名 |
| `zone` `team` `room` `dept` `部门` | 部门字段 |
| `dep` `collab` `协作` | **协作部门**（行内 `dep:cfo,cto`，≥2 个画跨部门联动线） |

字段名也认大小写混写。**实在认不出来也不会报错**——会放进"未归类"，
在 ⚙ 系统设置 → 记忆派生任务 里能看到，你可以之后手动归位。

> ⚠️ `dept:` 与 `dep:` 只差一个字母但含义不同：`dept:` 是"这条归谁"，
> `dep:` 是"要和谁协作"。写混了不报错，只是归类会不对。

### 行内元数据会被自动摘出标题

`- [x] 做完的事 | s:done | p:high` → 标题是「做完的事」，状态 done，优先级 high。
`|` 段不会留在标题上，也不会造出空任务（`- [x] | s:done` 这种没标题的行会被丢弃）。

---

## 判部门：能写就写，别全靠猜

没写 `dept` 时引擎按标题关键词猜，**猜是概率性的**。三条原则：

1. **谁验收 → 就是 `dept`**（报表→cfo、接口→cto、投放→cmo、发货→coo、需求→cpo、合规→cro、规划→ceo、评审会→meeting）
2. **谁给料 → 写 `dep:`**（行内）或 `collaborators`（JSON），指要和谁协作
3. **判不出来就别硬编**：不写 `dept`（看板会打「部门待核」灰标提醒复核），
   或写最近的那个 + `dept_reason` 说明理由

```jsonl
{"title":"仓库温控设备巡检","dept":"coo","dept_reason":"由运营验收，技术只提供传感器数据","source":"my-agent"}
```

---

## 顺带申请接手（可选）

写文件时把 `claim` 放进任务对象，服务端收件时**顺便登记认领申请**：

```jsonl
{"title":"供应商账期重谈","dept":"cfo","status":"todo","source":"file-only-agent","claim":{"agent":"file-only-agent","note":"我能接"}}
```

⚠️ 两点必须清楚：

- **这只是申请，任务状态不变**（仍是 `todo`）。要等人在看板上批准才能开工。
- **"查批没批 / 取已批准的活"仍要能发 HTTP** —— 认领是一来一回的交互，
  写文件这种单向通道只能提交申请，收不到回音。完全不能联网的 agent 请不要用认领，
  走正常上报即可（见 `SPEC.md` §1、§5.4）。
