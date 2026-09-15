# -*- coding: utf-8 -*-
"""把 office3d-assets/models 全部 10 类 GLB 打包成 all-models.js（base64 内嵌）。

看板以 file:// 打开时无法 fetch 外部模型，script 标签是唯一通道。
输出 window.OFFICE_MODELS（9 类），并向下兼容 window.CFO_MODELS。
"""
import base64, io, os, json

SRC = r"E:/AI/Workbuddy/office3d-assets/models"
DST = r"C:/Users/Perfect/Desktop/3d-taskboard-main/all-models.js"
# office_desk 已从包中移除：8 间房 SHOW 布局 0 引用（省 ~400KB base64 解析）
KEYS = ["exec_desk", "exec_chair", "office_chair", "office_monitor",
        "sofa", "coffee_table", "filing_cabinet", "plant_potted", "laptop"]

parts = []
total = 0
for k in KEYS:
    p = os.path.join(SRC, k + ".glb")
    if not os.path.exists(p):
        print("[WARN] missing", k)
        continue
    raw = open(p, "rb").read()
    b64 = base64.b64encode(raw).decode("ascii")
    total += len(raw)
    parts.append('  %s: "%s",' % (k, b64))
    print("[EMBED] %-16s %7.0f KB -> b64 %7.0f KB" % (k, len(raw) / 1024, len(b64) / 1024))

out = [
    "// 办公高清模型包（自动生成：源 office3d-assets/models，9 类）",
    "// base64 内嵌 GLB —— 看板以 file:// 打开时无法 fetch 外部模型，script 标签是唯一通道",
    "window.OFFICE_MODELS = {",
    "\n".join(parts),
    "};",
    "// 向下兼容：CFO 样板房旧代码引用 window.CFO_MODELS",
    "window.CFO_MODELS = window.OFFICE_MODELS;",
    "",
]
io.open(DST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("[DONE] %s  (源合计 %.1f MB, 输出 %.1f MB, %d 类)" %
      (DST, total / 1048576, os.path.getsize(DST) / 1048576, len(parts)))
