# -*- coding: utf-8 -*-
"""board 行解析器的单元测试 —— 不依赖服务端/浏览器，毫秒级。

为什么单独有这么一个测试：解析器是"agent 写什么都能收"的第一道关口，
一旦把 `| p:high` 之类的元数据漏进标题，看板上就会出现脏标题，
而这种问题在端到端测试里只表现为"标题有点怪"，很容易被忽略。

用法：
    python _verify/test_ingest_parse.py
退出码 0 = 全通过。
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from taskboard.ingest import parse_board_lines  # noqa: E402

fails = 0
cases = 0


def check(label: str, got, want):
    global fails, cases
    cases += 1
    if got == want:
        print("  \u2705 {}".format(label))
    else:
        fails += 1
        print("  \u274c {}\n      得到: {!r}\n      期望: {!r}".format(label, got, want))


def one(line: str) -> dict:
    """解析单行，返回第一条任务。"""
    out = parse_board_lines(line)
    return out[0] if out else {}


print("===== board 行解析器单元测试 =====")


# ---------- 1. 元数据不许漏进标题 ----------
print("\n【1】元数据必须从标题里摘干净")
t = one("[cfo] 月度营收趋势模块联调 | p:high | s:in_progress | desc:对外数据模块第一优先")
check("旧格式 [dept] 标题 + 三段元数据 → 标题", t.get("title"), "月度营收趋势模块联调")
check("  └ 优先级", t.get("priority"), "high")
check("  └ 状态", t.get("status"), "in_progress")
check("  └ 说明", t.get("desc"), "对外数据模块第一优先")
check("  └ 部门", t.get("dept"), "cfo")

t = one("- [x] 已完成的事 | s:done | dept:meeting | p:high")
check("清单行 checkbox → 标题", t.get("title"), "已完成的事")
check("  └ 状态（[x] 也算 done）", t.get("status"), "done")
check("  └ dept: 是归属部门（不是协作）", t.get("dept"), "meeting")
check("  └ 优先级", t.get("priority"), "high")

t = one("- [ ] 未勾选的事 | s:todo")
check("未勾选 → 标题", t.get("title"), "未勾选的事")
check("  └ 状态", t.get("status"), "todo")

t = one("- 普通项目符号 | p:low")
check("普通 bullet → 标题", t.get("title"), "普通项目符号")
check("  └ 优先级", t.get("priority"), "low")

t = one("这是一行裸文本 | s:blocked | tag:紧急,财务")
check("裸文本也收 → 标题", t.get("title"), "这是一行裸文本")
check("  └ 状态", t.get("status"), "blocked")
check("  └ 标签", t.get("tags"), "紧急,财务")

t = one("cfo: 冒号前缀写法 | p:high")
check("cfo: 前缀 → 标题", t.get("title"), "冒号前缀写法")
check("  └ 部门", t.get("dept"), "cfo")

# ---------- 2. 协作部门与归属部门不能混 ----------
print("\n【2】dep: 是协作部门，dept: 是归属部门")
t = one("[cpo] 产品与财务对齐 | dep:cfo,cto | s:todo")
check("dep:cfo,cto → collaborators", t.get("collaborators"), "cfo,cto")
check("  └ dep: 不覆盖 [cpo] 的归属部门", t.get("dept"), "cpo")

t = one("跨部门事项 | 协作:cfo,meeting")
check("中文 协作: 同样生效", t.get("collaborators"), "cfo,meeting")

# ---------- 3. 不产任务的装饰行 ----------
print("\n【3】标题行/表格行/空行不产任务")
check("空文本", parse_board_lines("\n\n   \n"), [])
check("# 一级标题", parse_board_lines("# 本次会话小结"), [])
check("> 引用行", parse_board_lines("> 一段引用"), [])
check("|---|---| 表格分隔", parse_board_lines("|---|---|"), [])

# ---------- 4. 一行只有元数据没有标题 → 丢弃，不要造空卡片 ----------
print("\n【4】空标题行丢弃")
got = parse_board_lines("- [x] | s:done")
check("只有勾选没有标题", got, [])

# ---------- 5. 多行混合 ----------
print("\n【5】多行混合解析")
mixed = parse_board_lines("""[cfo] 甲 | p:high
- [x] 乙 | s:done

| 表头 | 值 |
|---|---|
丙
""")
check("条数", len(mixed), 3)
check("  第1条标题", mixed[0].get("title"), "甲")
check("  第2条标题", mixed[1].get("title"), "乙")
check("  第3条标题", mixed[2].get("title"), "丙")

print("\n===== 结果：{} 项检查，{} =====".format(
    cases, "全部通过 \u2705" if fails == 0 else "{} 项未通过 \u274c".format(fails)))
sys.exit(0 if fails == 0 else 1)
