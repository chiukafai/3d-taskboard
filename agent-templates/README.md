# agent 接入模板

**核心约定：不要求任何特定 agent。** 只要求你的 agent 具备下面**任意一种**能力：

| 能力档位 | 能做什么 | 用哪个模板 |
|---|---|---|
| A. 会发 HTTP 请求 | `curl` / `requests` / `fetch` | `curl.sh` · `python-stdlib.py` · `node.mjs` |
| B. 会写文件 | 把任务写进投递箱目录 | `dropbox/` |
| C. 都不太会，但能跑命令 | 会话结束时执行一条命令 | `hook-session-end.sh` · `windows-powershell.ps1` |

---

## 先拿到两个值

```bash
BOARD=http://<运行看板的机器IP>:8787      # 本机就是 http://127.0.0.1:8787
TOKEN=                                    # board.config.json 里 server.token，留空则不用带
```

## 一条任务的字段（只认 title，其余都可省）

| 字段 | 说明 | 取值 |
|---|---|---|
| `title` | **必填** 任务名 | 任意文本 |
| `dept` | 归到哪个部门房间 | `ceo` `cfo` `cto` `cpo` `cmo` `coo` `cro` `meeting`，或中文/别名（`财务`/`技术`/`marketing`…） |
| `status` | 状态 | `todo` `in_progress` `done` `blocked`，或中文（`待办`/`进行中`/`已完成`/`阻塞`） |
| `priority` | 优先级 | `high` `medium` `low`，或 `高`/`中`/`低` |
| `desc` | 说明 | 任意文本 |
| `project` | 项目名 | 不填时默认等于 `source` |
| `source` | **来源 agent 名**（建议都填） | `workbuddy` / `claude-code` / `hermes` / `cursor` … |
| `due` | 截止 | 任意文本 |
| `tags` | 标签 | 数组或逗号分隔 |
| `collaborators` | 跨部门协作 | 部门 id 数组，≥2 个时看板画联动线 |
| `external_id` | 上游唯一编号 | 填了就按它去重；不填按标题去重 |
| `dept_reason` | 你判部门的依据（可选，≤80 字） | 看板详情里会显示，方便人复核 |
| `claim` | **顺手申请接手**（见 SPEC §5） | `{"agent":"你的名字","note":"为什么你能接"}`，或直接写名字字符串 |

> **去重规则**：同一「部门 + 去重键」再录一次 = 更新那条，不会出现重复卡片。
> 所以 agent 可以放心重复上报，状态变了直接再发一次即可。

### 上报前先判「这条归谁」（别省这一步）

没写 `dept` 时引擎会按标题关键词猜，**猜是概率性的**。自己判一次更准：

1. **谁验收 → 就是 `dept`**：报表→`cfo`，接口→`cto`，投放→`cmo`，发货→`coo`，
   需求→`cpo`，合规→`cro`，规划→`ceo`，评审会→`meeting`
2. **谁给料 → 写 `collaborators`**：需要别的部门给数据/审批时填数组
3. **判不出来就别硬编**：不写 `dept`（看板打「部门待核」灰标提醒复核），
   或写最近的那个 + `dept_reason` 说明理由

> 口诀：**`dept` = 谁验收；`collaborators` = 谁给料。**
> 拿不准时宁可写 `collaborators` —— 协作错了只是少条线，归属错了是整条任务进错房间。

看板会把三种情况分开标记，人一眼能看出哪些需要复核：

| 情况 | 看板标记 |
|---|---|
| 显式写了 `dept` | 无标记（信任你的判断），详情显示"上报方判定" |
| 没写，引擎猜到了 | 灰色「**部门待核**」标 |
| 没写且猜不出 | 进「未归类」桶，**不落任何房间** |

---

## 极简 Markdown 行格式（写文件时最省事）

不用 JSON，一行一条，`|` 后面是元数据，会被自动摘出来：

```
[cfo] 月度营收趋势模块联调 | p:high | s:in_progress | desc:对外数据第一优先
- [x] 已完成的事 | dept:meeting | p:high
- [ ] 待办的事 | s:todo | dep:cfo,cto
cfo: 冒号前缀写法也行 | p:low
这是一行裸文本，也照样收
```

| 行内写法 | 含义 |
|---|---|
| `[cfo] 标题` / `cfo: 标题` | 归属部门 |
| `- [ ]` / `- [x]` / `- ` / 裸文本 | 都会被收成任务（`[x]` = 已完成） |
| `p:` `prio:` `priority:` `优先级:` | 优先级 |
| `s:` `status:` `状态:` | 状态 |
| `dept:` `zone:` `team:` `room:` `部门:` | **归属部门** |
| `dep:` `collab:` `协作:` | **协作部门**（≥2 个看板会画跨部门联动线） |
| `desc:` `说明:` `备注:` | 说明 |
| `due:` `截止:` | 截止 |
| `tag:` `标签:` | 标签 |
| `id:` `编号:` | 上游唯一编号（按它去重） |
| `src:` `source:` `来源:` | 来源 agent 名 |
| `proj:` `项目:` | 项目名 |

> ⚠️ 注意 `dept:` 与 `dep:` 是**两个不同字段**：前者指"这条任务归谁"，
> 后者指"要和谁协作"。写混了不会报错，但归类会不对。

---

## 各模板

- `curl.sh` —— 一行命令，最通用
- `python-stdlib.py` —— 不装任何包，可被任何 Python 环境调用；也可直接当图书管理员用（批量导入）
- `node.mjs` —— Node 环境
- `hook-session-end.sh` —— 挂到任意 agent 的"会话结束"钩子上
- `windows-powershell.ps1` —— Windows 原生
- `dropbox/` —— 完全离线：把文件丢进 `data/inbox/` 就行
- `claim-poll.py` —— ⭐ **认领助手**（SPEC §5）：`ask` 看可接的活 / `claim` 提申请 / `queue` 取已批准的活 / `report` 回报。给"会跑命令"的 agent 用
- `any-agent-prompt.md` —— 完整版指令，贴进任意 agent 的指令里（含判部门三步法 + 认领协议，不想用就删那节）
- **`SPEC.md`** —— ⭐ **规则唯一真源**。字段、别名、两条通道、判部门、认领协议、纪律全在这。改它，所有接入方跟着变
- **`粘贴用的短口令.md`** —— 一行版 / 六行版短口令（觉得完整版太长就用这个）
- **`make-config.py`** —— 一键生成配置（省掉手抄）。跑完在 `生成配置/` 拿到可直接落地的 `AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `粘贴.txt`
- `一键生成配置.bat` —— 上面那步的双击版（不用打命令）
- `录入任务.bat` —— 双击手动补一条任务

> ⚠️ 两个 `.bat` 是给"不想打命令"的场景准备的：逻辑为标准 cmd 写法（CRLF 换行、UTF-8 + `chcp 65001`），
> 但**未在真实双击环境下实测**（当前开发环境不允许调用 cmd.exe）。双击若没反应，
> 请改用 `python claim-poll.py` / `python make-config.py`，或直接让 WorkBuddy 代做。

---

## 想让它主动接活？用认领协议（SPEC §5）

**核心纪律：agent 只能提申请，人不批准就不能开工。**

| 步骤 | 命令（`claim-poll.py`） | 说明 |
|---|---|---|
| ① 看有哪些活 | `ask --agent 你的名字 --dept cfo` | 列 `todo` 且没人申请的 |
| ② 提申请 | `claim <任务id> --agent 你的名字 --note "我能接"` | 任务**状态不变**，只是登记意向 |
| ③ 查批没批 | `state --agent 你的名字` | `proposed` / `approved` / `rejected` |
| ④ 取已批准的活 | `queue --agent 你的名字` | **只有这里列出的才能开工** |
| ⑤ 干完回报 | `report <任务id> --status done --agent 你的名字` | |
| ✕ 不想接了 | `withdraw <认领id> --agent 你的名字` | |

也可以在上报任务时顺手申请（一次请求）：

```json
{"title":"供应商账期重谈","dept":"cfo","source":"my-agent","claim":{"agent":"my-agent","note":"我能接"}}
```

人批准后会**自动驳回同一条任务的其它申请**（reason 写明"已被 xxx 认领"）。

---

## 怎么装最省事（按省力排序）

| 你的 agent | 推荐做法 |
|---|---|
| **WorkBuddy** | 已经装好技能了 —— 直接说「**记到看板**」，不用贴任何东西 |
| 支持持久配置的（Claude Code / Cursor / Hermes） | 跑 `python make-config.py`（或双击 `一键生成配置.bat`），把生成的 `AGENTS.md` / `CLAUDE.md` / `.cursorrules` 复制到项目根。**装一次，永久免贴** |
| 临时用一次 | 复制 `粘贴用的短口令.md` 里的**一行版**（指向 `SPEC.md`） |
| 读不了本地文件 | 复制**六行版**（自带全部信息） |

> 📌 **完整版指令是"装一次"的东西，不是每次会话都要贴。** 这是最常见的误解。
