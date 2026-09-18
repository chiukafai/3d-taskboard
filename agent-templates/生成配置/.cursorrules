# 任务上报规则

> 由 `agent-templates/make-config.py` 生成 · 规范真源：`C:\Users\Perfect\Desktop\3d-taskboard-main\agent-templates\SPEC.md`
> 看板地址 `http://127.0.0.1:8787` · 来源名 `hermes`

## 你要做的事

本会话里**完成或推进了**任何一件事，都要上报到 3D 看板。
**未完成的也要报** —— 没做完用 `in_progress`，卡住的用 `blocked`。

## 上报方式（按你自身能力挑一种）

### 1. 能发 HTTP 请求

```
POST http://127.0.0.1:8787/api/tasks
Content-Type: application/json

{"title":"任务标题","dept":"cfo","status":"done","priority":"high","source":"hermes","project":"项目名","desc":"一句话说明"}
```

多条一次发：顶层换成数组 `[{...},{...}]`。

### 2. 能写文件（离线也能用）

往 `C:\Users\Perfect\Desktop\3d-taskboard-main\data\inbox` 写一个 `.jsonl` 文件，一行一个任务对象（字段同上）。
可选后缀：`.json` `.jsonl` `.ndjson` `.md` `.markdown` `.txt`
服务端每 30 秒自动扫，处理完归档，不会重复处理。

### 3. 会跑命令

```bash
python -c "import json,urllib.request as u;r=u.Request('http://127.0.0.1:8787/api/tasks',json.dumps([{'title':'标题','dept':'cfo','status':'done','source':'hermes'}]).encode(),{'Content-Type':'application/json'},method='POST');print(u.urlopen(r).read().decode())"
```

## 字段速查

| 字段 | 说明 |
|---|---|
| `title` | **必填**，任务名 |
| `dept` | `ceo` `cfo` `cto` `cpo` `cmo` `coo` `cro` `meeting`；不写则按标题关键词自动猜 |
| `status` | `todo` / `in_progress` / `done` / `blocked` |
| `priority` | `high` / `medium` / `low` |
| `source` | 固定填 `hermes` |
| `project` | 项目名（本项目填 `Hailu-SC-EMS`） |
| `desc` | 一句话说明 |
| `collaborators` | 需要别的部门配合时填部门数组，如 `["cfo","cto"]` |

写中文也认：`财务`→cfo、`营销`→cmo、`进行中`→in_progress、`已完成`→done、`高`→high。
⚠️ `dep:`（协作）和 `dept:`（归属）不是一回事，别写混。

## 三条纪律

1. **未完成的也要记**，不要只记成功的事。
2. **重复上报 = 更新**，不会变两条。状态变了直接再报一次。
3. **一次会话最多 3 条**，合并同类项，不要为凑数硬造任务。

## 边界（别误以为能做到）

- 看板**不会自动派活** —— 它只做「记录 + 展示 + 改状态」。上报不会自动触发别的部门或别的 agent。
- 部门归类是**猜**的。想要确定性归类就显式写 `dept`。

会话收尾时用一句话汇报：报了几条、有没有失败。
