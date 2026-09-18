# -*- coding: utf-8 -*-
"""对比看板内嵌的人格配置副本 与 ~/.workbuddy 真实文件
用法: python _verify/cmp_sysconfig.py
"""
import os, re, sys, difflib, hashlib, datetime, io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "office-3d-taskboard.html")
HOME_WB = os.path.join(os.path.expanduser("~"), ".workbuddy")

FILES = ["SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"]


def read_html():
    with io.open(HTML, encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_embedded(html, name):
    """抓 <script type="text/plain" id="cfg-NAME"> ... </script> 的内文"""
    pat = re.compile(
        r'<script type="text/plain" id="cfg-' + re.escape(name) + r'">(.*?)</script>',
        re.S)
    m = pat.search(html)
    return m.group(1) if m else None


def norm(s):
    """统一换行 + 去首尾空行（浏览器 innerHTML 会吃掉首尾空白）"""
    if s is None:
        return None
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip("\n")


def main():
    html = read_html()
    print("=" * 78)
    print("看板内嵌人格配置  vs  ~/.workbuddy 真实文件")
    print("看板文件: %s" % HTML)
    print("生成时间: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 78)

    rows = []
    for name in FILES:
        real_path = os.path.join(HOME_WB, name)
        emb = norm(extract_embedded(html, name))
        real = None
        mtime = None
        if os.path.exists(real_path):
            with io.open(real_path, encoding="utf-8", errors="replace") as f:
                real = norm(f.read())
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(real_path))

        if emb is None:
            rows.append((name, "缺失", "-", "-", "-",
                         "看板内 <script id=cfg-%s> 不存在" % name, None, None, None, None))
            continue

        if real is None:
            rows.append((name, "文件不存在", len(emb), 0, "-",
                         "本机 ~/.workbuddy 无此文件", emb, None, None, None))
            continue

        # 行级差异
        a, b = emb.split("\n"), real.split("\n")
        if a == b:
            same = True
            ratio = 1.0
            added, removed = 0, 0
        else:
            same = False
            sm = difflib.SequenceMatcher(None, a, b)
            ratio = sm.ratio()
            added = removed = 0
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag in ("replace", "delete"):
                    removed += i2 - i1
                if tag in ("replace", "insert"):
                    added += j2 - j1
        rows.append((name, "一致" if same else "不一致", len(emb), len(real),
                     "%.2f" % ratio, "%s%d 行 / +%d 行" % ("" if same else "改动 ", removed, added),
                     emb, (real, mtime, added, removed, a, b), None, None))

    print("\n%-13s %-9s %8s %8s %7s  %s" % ("文件", "状态", "看板字符", "真实字符", "相似度", "说明"))
    print("-" * 78)
    for r in rows:
        print("%-13s %-9s %8s %8s %7s  %s" % (r[0], r[1], r[2], r[3], r[4], r[5]))

    # 真实文件 mtime
    print("\n【真实文件修改时间】")
    for name in FILES:
        p = os.path.join(HOME_WB, name)
        if os.path.exists(p):
            st = os.stat(p)
            print("  %-13s %s   %6d bytes" % (
                name,
                datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                st.st_size))

    # 详细差异首位
    print("\n" + "=" * 78)
    for r in rows:
        if r[7] is None:
            continue
        name = r[0]
        real, mtime, added, removed, a, b = r[7]
        if a == b:
            continue
        print("\n【%s】看板副本 vs 真实文件 —— 差异明细" % name)
        d = list(difflib.unified_diff(a, b, lineterm="", n=1,
                                      fromfile="看板内嵌", tofile="真实 " + name))
        for line in d[:60]:
            print("   " + line[:150])
        if len(d) > 60:
            print("   ... (共 %d 行 diff，已截断)" % len(d))
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
