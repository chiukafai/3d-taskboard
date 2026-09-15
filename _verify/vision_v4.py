# -*- coding: utf-8 -*-
"""视觉复核：把 3D 正交俯视图的建筑轮廓与 plan_v4 几何做定量比对

思路：3D 俯视图里"建筑（含 0.3m 垫层）"与"室外草地"颜色差异明显 →
      按颜色阈值提取轮廓掩码 → 与脚本按同一正交取景算出的期望掩码比 IoU。
"""
import json, os, sys
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = json.load(open(os.path.join(HERE, "plan_v4.json"), encoding="utf-8"))
GEN = json.load(open(os.path.join(HERE, "gen3d_v4.json"), encoding="utf-8"))

IMG = os.path.join(ROOT, "_shots", "p0_silhouette.png")
im = Image.open(IMG).convert("RGB")
Wp, Hp = im.size
a = np.asarray(im).astype(np.int16)
print(f"俯视图 {Wp}×{Hp}")

# 正交相机取景：中心 (14.8,10.8)，半宽 15.8 / 半高 11.8
CX, CZ, HW, HH = 14.8, 10.8, 15.8, 11.8
# cam.up=(0,0,-1) 看向 -Y → 屏幕右 = +X，屏幕上 = -Z（即北在上）
# 图像 px 0..Wp ↔ x CX-HW..CX+HW ；py 0..Hp ↔ z CZ-HH..CZ+HH


def to_px(x, z, pad_px=0):
    return ((x - (CX - HW)) / (2 * HW) * Wp, (z - (CZ - HH)) / (2 * HH) * Hp)


# ── 期望掩码：建筑（含垫层）＝ 房间∪公共区 膨胀 0.3m ──
N = 600
xs = np.linspace(CX - HW, CX + HW, N)
zs = np.linspace(CZ - HH, CZ + HH, int(N * (2 * HH) / (2 * HW)))
Zg, Xg = np.meshgrid(zs, xs, indexing="ij")
exp = np.zeros_like(Xg, dtype=bool)
for (x1, z1, x2, z2) in GEN["pad_rects"]:
    exp |= (Xg >= x1) & (Xg <= x2) & (Zg >= z1) & (Zg <= z2)
# 室外铺装：前庭 / 东南侧庭（也会偏离草地色）
pave = np.zeros_like(Xg, dtype=bool)
c = GEN["court"]
pave |= (Xg >= c[0]) & (Xg <= c[2]) & (Zg >= c[1]) & (Zg <= c[3])
y = [26.2, 12.6, 29.6, 19.0]
pave |= (Xg >= y[0]) & (Xg <= y[2]) & (Zg >= y[1]) & (Zg <= y[3])
exp_all = exp | pave

# ── 实测掩码：剪影渲染（纯黑背景 + 关灯 + 隐藏草地）→ 非黑即建筑 ──
d = a.sum(axis=2)
mask = d > 24
print("剪影掩码像素占比 %.2f%%" % (100.0 * mask.mean()))

# 缩放到与 exp 同网格
mimg = Image.fromarray((mask * 255).astype(np.uint8)).resize((Xg.shape[1], Xg.shape[0]), Image.BILINEAR)
obs = np.asarray(mimg) > 128

inter = (obs & exp_all).sum()
union = (obs | exp_all).sum()
iou = inter / max(union, 1)
print(f"\n建筑+室外铺装 轮廓 IoU = {iou*100:.1f}%   （观察 {obs.sum()} 格 / 期望 {exp_all.sum()} 格）")

# ── 逐行/逐列占用率相关性 ──
ro = obs.mean(axis=1); re = exp_all.mean(axis=1)
co = obs.mean(axis=0); ce = exp_all.mean(axis=0)
print(f"行方向（南北）剖面相关 = {np.corrcoef(ro, re)[0,1]*100:.1f}%")
print(f"列方向（东西）剖面相关 = {np.corrcoef(co, ce)[0,1]*100:.1f}%")

# ── 关键特征点抽查（在实测掩码上打点，看是否为"建筑"） ──
print("\n关键特征点（实测掩码 1=有实体）:")
pts = [
    ("CMO 营销中心 (19.7,4.3)", 19.7, 4.3, True),
    ("CTO 技术中心 (26.7,5.1)", 26.7, 5.1, True),
    ("西北入口前庭(空场) (3.3,2.8)", 3.3, 2.8, True),
    ("圆厅/接待厅 (9.4,10.8)", 9.4, 10.8, True),
    ("主廊东段 (24.0,10.0)", 24.0, 10.0, True),
    ("蛇形支廊 A2 (8.8,13.5)", 8.8, 13.5, True),
    ("蛇形支廊 A3 (10.0,18.5)", 10.0, 18.5, True),
    ("CEO 东侧空地(应空) (28.0,17.0)", 28.0, 17.0, True),
    ("A2/COO 之间凹口(应空) (10.8,14.5)", 10.8, 14.5, False),
    ("北侧 CRO 上方空地(应空) (12.0,1.5)", 12.0, 1.5, False),
    ("CTO 北侧退台空地(应空) (27.0,0.6)", 27.0, 0.6, False),
    ("CFO 西侧退台空地(应空) (1.0,19.0)", 1.0, 19.0, False),
]
ok = 0
for name, x, z, want in pts:
    u = int(round((x - (CX - HW)) / (2 * HW) * Xg.shape[1] - 0.5))
    v = int(round((z - (CZ - HH)) / (2 * HH) * Xg.shape[0] - 0.5))
    if not (0 <= u < Xg.shape[1] and 0 <= v < Xg.shape[0]):
        print(f"   {name:34s} 超出取景范围")
        continue
    got = bool(obs[v, u])
    good = got == want
    ok += good
    print(f"   {name:34s} 实测={'有实体' if got else '空'}  期望={'有实体' if want else '空'}  {'✅' if good else '❌'}")
print(f"\n   特征点命中 {ok}/{len(pts)}")
sys.exit(0 if (iou > 0.90 and ok == len(pts)) else 1)
