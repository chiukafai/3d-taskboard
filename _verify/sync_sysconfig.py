# -*- coding: utf-8 -*-
"""把 ~/.workbuddy 里的人格配置文件同步进看板（一键重嵌 + 自动写 mtime）

背景：看板「⚙ 系统配置 · 中控台」面板的人格配置卡片 + 「查看全文」弹窗，
      内容来自 HTML 内嵌的 <script type="text/plain" id="cfg-XXX.md">，
      属于静态快照 → 真实文件改了它不会变，长期必然过期。

用法：
    python _verify/sync_sysconfig.py                      # 同步当前工作区看板（写回 HTML）
    python _verify/sync_sysconfig.py --check              # 只比对不写入
    python _verify/sync_sysconfig.py <另一个html路径>        # 指定目标（如 E 盘主项目副本）

同步内容：
    1) 4 份文件的正文（内嵌副本整体替换为真实文件内容）
    2) SYS_CONFIG_FILES 里每份的 mtime 标注（改为真实文件 mtime）
退出码：0=已是最新/同步成功   1=有差异(--check 模式)   2=出错
"""
import os, re, io, sys, datetime, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOME_WB = os.path.join(os.path.expanduser("~"), ".workbuddy")
FILES = ["SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"]
CHECK_ONLY = "--check" in sys.argv

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
HTML = os.path.abspath(_args[0]) if _args else os.path.join(ROOT, "office-3d-taskboard.html")


def read(p):
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def main():
    if not os.path.exists(HTML):
        print("❌ 找不到", HTML)
        return 2

    html = read(HTML)
    orig = html
    report = []

    for name in FILES:
        real_path = os.path.join(HOME_WB, name)
        if not os.path.exists(real_path):
            report.append((name, "真实文件缺失", 0, 0, 0))
            continue

        real = read(real_path)
        real_clean = real.replace("\r\n", "\n").strip("\n")
        mdate = datetime.datetime.fromtimestamp(
            os.path.getmtime(real_path)).strftime("%Y-%m-%d")

        # ── ① 换正文 ───────────────────────────────────────────────
        pat = re.compile(
            r'(<script type="text/plain" id="cfg-' + re.escape(name) + r'">)(.*?)(</script>)',
            re.S)
        m = pat.search(html)
        if not m:
            report.append((name, "❌ HTML 内找不到该 script 块", 0, 0, 0))
            continue
        old = m.group(2).replace("\r\n", "\n").strip("\n")
        new = "\n" + real_clean + "\n"
        changed = old != real_clean
        html = html[:m.start(2)] + new + html[m.end(2):]

        # ── ② 换 mtime 标注 ────────────────────────────────────────
        # 匹配该文件条目里的 mtime:'YYYY-MM-DD'
        ent = re.compile(
            r"(\{name:'" + re.escape(name) + r"',role:'[^']*',mtime:')[^']*(')")
        m2 = ent.search(html)
        old_m = m2.group(1) if m2 else None
        if m2:
            html = html[:m2.start()] + m2.group(1) + mdate + html[m2.end(2) - 1:]

        # 统计差异
        a, b = old.split("\n"), real_clean.split("\n")
        ratio = 1.0 if a == b else difflib.SequenceMatcher(None, a, b).ratio()
        report.append((name, ("需同步" if CHECK_ONLY else "已更新") if changed else "本就一致",
                       len(old), len(real_clean), mdate))
        report[-1] = report[-1] + (ratio,)

    # ── 输出 ──────────────────────────────────────────────────────
    print("=" * 74)
    print("看板人格配置同步 — " + ("【只检查，不写入】" if CHECK_ONLY else "【写入模式】"))
    print("源: %s" % HOME_WB)
    print("目标: %s" % HTML)
    print("=" * 74)
    print("\n%-13s %-12s %8s %8s %-12s %s" % ("文件", "状态", "旧(看板)", "新(真实)", "真实 mtime", "相似度"))
    print("-" * 74)
    dirty = 0
    for r in report:
        ratio = ("%.2f" % r[5]) if len(r) > 5 else "-"
        if len(r) > 1 and r[1] in ("需同步", "已更新"):
            dirty += 1
        print("%-13s %-12s %8s %8s %-12s %s" % (r[0], r[1], r[2], r[3], r[4], ratio))

    if CHECK_ONLY:
        print("\n结论: %d 份需要同步" % dirty)
        return 1 if dirty else 0

    if html == orig:
        print("\n结论: 看板已与真实配置一致，无需改动 ✅")
        return 0

    write(HTML, html)
    print("\n结论: 已写入 %d 份更新 → %s ✅" % (dirty, HTML))
    print("提示: 同步后请重跑 node _verify/verify_syspanel.mjs 复核面板生效性")
    return 0


if __name__ == "__main__":
    sys.exit(main())
