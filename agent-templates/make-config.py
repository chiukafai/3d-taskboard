#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键生成 agent 配置 —— 省掉手抄那段 48 行 prompt。

用法：
    python make-config.py                          # 交互式问 3 个问题
    python make-config.py --source hermes --project Hailu-SC-EMS
    python make-config.py --source claude-code --ip 192.168.1.9 --dry-run

产出（写到 ./生成配置/ 下）：
    粘贴.txt     直接复制进任何 agent 的对话框/指令栏（含一行版、六行版）
    AGENTS.md    项目级规则文件，放项目根目录，支持 AGENTS.md 的 agent 会自动读
    CLAUDE.md    同上，给 Claude Code 用（内容一致）
    .cursorrules 同上，给 Cursor 用（内容一致）

只用 Python 标准库，不装任何包。
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "生成配置"
SPEC = HERE / "SPEC.md"
DEFAULT_PORT = 8787


def spec_one_liner(ip, port, source):
    return (
        f"任务上报规则见 {SPEC}，每次会话结束前按它上报，"
        f"看板地址 http://{ip}:{port}，source 填 {source}。"
    )


def spec_six_liner(ip, port, source):
    return f"""【任务上报规则】本会话完成或推进的每件事都要上报到 3D 看板。
地址：POST http://{ip}:{port}/api/tasks
字段：{{"title":"必填","dept":"cfo|cto|cmo|ceo|cpo|coo|cro|meeting","status":"todo|in_progress|done|blocked","priority":"high|medium|low","source":"{source}","desc":"一句话","dept_reason":"判部门的依据（可选）"}}
判部门：dept = 谁验收（报表→cfo 接口→cto 投放→cmo 发货→coo 需求→cpo 合规→cro 规划→ceo 评审会→meeting）；谁给料写进 collaborators 数组；判不出来就别写 dept（系统猜，看板会打「部门待核」标）。
未完成的也要报（用 in_progress）；卡住的用 blocked。重复上报=更新，不会变两条。一次会话最多报 3 条。
若 HTTP 不通，改往 {HERE.parent / 'data' / 'inbox'} 写 .jsonl 文件（一行一个任务对象），服务恢复后自动收。
（可选）想主动接活：POST http://{ip}:{port}/api/tasks/<任务id>/claim body {{"agent":"{source}","note":"我能接"}} —— 只是申请，等人批准；批准后 GET http://{ip}:{port}/api/queue?agent={source} 取活。详见 SPEC.md §5。"""


def spec_rules_md(ip, port, source):
    return f"""# 任务上报规则

> 由 `agent-templates/make-config.py` 生成 · 规范真源：`{SPEC}`
> 看板地址 `http://{ip}:{port}` · 来源名 `{source}`

## 你要做的事

本会话里**完成或推进了**任何一件事，都要上报到 3D 看板。
**未完成的也要报** —— 没做完用 `in_progress`，卡住的用 `blocked`。

## 上报方式（按你自身能力挑一种）

### 1. 能发 HTTP 请求

```
POST http://{ip}:{port}/api/tasks
Content-Type: application/json

{{"title":"任务标题","dept":"cfo","status":"done","priority":"high","source":"{source}","project":"项目名","desc":"一句话说明"}}
```

多条一次发：顶层换成数组 `[{{...}},{{...}}]`。

### 2. 能写文件（离线也能用）

往 `{HERE.parent / 'data' / 'inbox'}` 写一个 `.jsonl` 文件，一行一个任务对象（字段同上）。
可选后缀：`.json` `.jsonl` `.ndjson` `.md` `.markdown` `.txt`
服务端每 30 秒自动扫，处理完归档，不会重复处理。

### 3. 会跑命令

```bash
python -c "import json,urllib.request as u;r=u.Request('http://{ip}:{port}/api/tasks',json.dumps([{{'title':'标题','dept':'cfo','status':'done','source':'{source}'}}]).encode(),{{'Content-Type':'application/json'}},method='POST');print(u.urlopen(r).read().decode())"
```

## 字段速查

| 字段 | 说明 |
|---|---|
| `title` | **必填**，任务名 |
| `dept` | `ceo` `cfo` `cto` `cpo` `cmo` `coo` `cro` `meeting` |
| `status` | `todo` / `in_progress` / `done` / `blocked` |
| `priority` | `high` / `medium` / `low` |
| `source` | 固定填 `{source}` |
| `project` | 项目名 |
| `desc` | 一句话说明 |
| `dept_reason` | 可选，一句话说明你判部门的依据（人会在看板上看到） |
| `collaborators` | 需要别的部门配合时填部门数组，如 `["cfo","cto"]` |

写中文也认：`财务`→cfo、`营销`→cmo、`进行中`→in_progress、`已完成`→done、`高`→high。
⚠️ `dep:`（协作）和 `dept:`（归属）不是一回事，别写混。

## 上报前先判「这条归谁」（别省这一步）

引擎在你没写 `dept` 时会按标题关键词猜，**猜是概率性的**。你自己判一次更准：

1. **谁验收 → 就是 `dept`。** 做完这件事是谁拍板说"行"？
   财务报表→`cfo`；接口部署→`cto`；投放文案→`cmo`；发货库存→`coo`；
   需求原型→`cpo`；合规合同→`cro`；年度规划→`ceo`；跨部门评审会→`meeting`
2. **谁给料 → 写 `collaborators`。** 需要别的部门提供数据/审批/接口时填数组。
3. **判不出来就别硬编。** 要么**不写 `dept`**（系统猜，看板打「部门待核」灰标提醒人复核），
   要么写最近的那个部门 + 用 `dept_reason` 说明理由（≤80 字）。

> 口诀：**`dept` = 谁验收；`collaborators` = 谁给料。**
> 拿不准时宁可写 `collaborators` —— 协作错了只是少条线，归属错了是整条任务进错房间。

## 三条纪律

1. **未完成的也要记**，不要只记成功的事。
2. **重复上报 = 更新**，不会变两条。状态变了直接再报一次。
3. **一次会话最多 3 条**，合并同类项，不要为凑数硬造任务。

## 边界（别误以为能做到）

- 看板**不会自动派活** —— 它只做「记录 + 展示 + 改状态」。上报不会自动触发别的部门或别的 agent。
- 想主动接活请用**认领协议**：你只能提申请，**人不批准就不能开工**（详见 `{SPEC}` §5）。
- 部门归类是**猜**的。想要确定性归类就按上面三步显式写 `dept`。

会话收尾时用一句话汇报：报了几条、有没有失败。
"""


def ask(prompt, default="", allow_empty=True):
    tip = f"{prompt}"
    if default:
        tip += f" [{default}]"
    tip += "："
    try:
        val = input(tip).strip()
    except EOFError:
        val = ""
    if not val:
        if default or allow_empty:
            return default
        print("  这一项不能为空，请重试。")
        return ask(prompt, default, allow_empty)
    return val


def main():
    ap = argparse.ArgumentParser(description="一键生成 agent 配置")
    ap.add_argument("--source", help="来源 agent 名，如 workbuddy / claude-code / hermes")
    ap.add_argument("--ip", default="127.0.0.1", help="看板所在机器 IP（默认 127.0.0.1）")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口（默认 {DEFAULT_PORT}）")
    ap.add_argument("--project", default="", help="项目名（可留空）")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    print("=" * 62)
    print(" 生成 agent 任务上报配置（省掉手抄 prompt）")
    print("=" * 62)
    print()

    source = args.source or ask("① 你的来源名（用于区分任务从哪来）", "my-agent")
    ip = args.ip or ask("② 看板所在机器 IP（本机直接回车）", "127.0.0.1")
    port = args.port or DEFAULT_PORT
    project = args.project or ask("③ 项目名（可留空）", "")

    print()
    print("-" * 62)
    print(" 即将生成：")
    print(f"   看板地址   http://{ip}:{port}")
    print(f"   来源名     {source}")
    print(f"   项目名     {project or '(未填)'}")
    print(f"   输出目录   {OUT}")
    print("-" * 62)
    print()

    if args.dry_run:
        print("【--dry-run】只预览，不写文件。")
        print()
        print(spec_one_liner(ip, port, source))
        print()
        return 0

    OUT.mkdir(parents=True, exist_ok=True)

    paste = f"""# 复制下面任意一段，贴进 agent 的指令配置里（装一次即可，不用每次会话都贴）

## ① 一行版（最省事 · 前提：那个 agent 能读本地文件）

{spec_one_liner(ip, port, source)}

## ② 六行版（agent 读不了本地文件时用 · 自带全部信息）

{spec_six_liner(ip, port, source)}

## ③ 装到哪里（从此永久免贴）

| agent | 写进哪里 |
|---|---|
| Claude Code | 项目根 `CLAUDE.md` 或全局 `~/.claude/CLAUDE.md` |
| Cursor | 项目根 `.cursorrules` 或 `.cursor/rules/*.mdc` |
| Hermes / 自建 agent | 其 system prompt 字段 |
| 支持 AGENTS.md 的 | 项目根 `AGENTS.md` |
| WorkBuddy | 已装成技能：说「记到看板」即可 |

本目录已生成 `AGENTS.md` / `CLAUDE.md` / `.cursorrules`（内容相同），直接复制到目标位置即可。

项目名：{project or '(未填)'}
生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    rules = spec_rules_md(ip, port, source)
    if project:
        rules = rules.replace("`project` | 项目名", f"`project` | 项目名（本项目填 `{project}`）")

    (OUT / "粘贴.txt").write_text(paste, encoding="utf-8")
    (OUT / "AGENTS.md").write_text(rules, encoding="utf-8")
    (OUT / "CLAUDE.md").write_text(rules, encoding="utf-8")
    (OUT / ".cursorrules").write_text(rules, encoding="utf-8")

    print("已生成：")
    for name in ("粘贴.txt", "AGENTS.md", "CLAUDE.md", ".cursorrules"):
        p = OUT / name
        print(f"  {name:<16} {p.stat().st_size:>5} 字节")
    print()
    print(f"目录：{OUT}")
    print()
    print("下一步：")
    print("  · 想最快生效 → 打开 粘贴.txt，复制【一行版】贴进那个 agent 的指令配置")
    print("  · 想零手工     → 把 AGENTS.md / CLAUDE.md / .cursorrules 复制到项目根目录")
    return 0


if __name__ == "__main__":
    sys.exit(main())
