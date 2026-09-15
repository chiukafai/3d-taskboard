# -*- coding: utf-8 -*-
"""3D 俯视剪影 vs plan_v4 期望轮廓 —— 并排 ASCII 对比（人眼可直接读）
图例： '# '=两者都有   'O '=只在渲染里(多出)   'X '=只在期望里(缺失)   '..'=都没有
"""
import json, os
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN = json.load(open(os.path.join(HERE, "gen3d_v4.json"), encoding="utf-8"))

IM = Image.open(os.path.join(ROOT, "_shots", "p0_silhouette.png")).convert("RGB")
W, H = IM.size
a = np.asarray(IM).astype(np.int16)

CX, CZ, HW, HH = 14.8, 10.8, 15.8, 11.8
GRID = 0.38
xs = np.arange(GRID / 2, 29.6, GRID)
zs = np.arange(GRID / 2, 21.6, GRID)

# 期望掩码：建筑垫层(外扩 0.3) ∪ 前庭 ∪ 东南侧庭 ∪ 入口步道
pads = [tuple(r) for r in GEN["pad_rects"]]
c = GEN["court"]; y = (26.2, 12.6, 29.6, 19.0); walk = (6.5, 1.4, 9.5, 5.6)


def exp_at(x, z):
    for (x1, z1, x2, z2) in list(pads) + [c, y, walk]:
        if x1 - 1e-6 <= x <= x2 + 1e-6 and z1 - 1e-6 <= z <= z2 + 1e-6:
            return True
    return False


def obs_at(x, z):
    u = int(round((x - (CX - HW)) / (2 * HW) * W))
    v = int(round((z - (CZ - HH)) / (2 * HH) * H))
    u = min(max(u, 0), W - 1); v = min(max(v, 0), H - 1)
    return bool(a[v, u].sum() > 24)


only_obs = only_exp = both = 0
lines = []
for z in zs:
    row = ""
    for x in xs:
        o, e = obs_at(x, z), exp_at(x, z)
        if o and e: row += "# "; both += 1
        elif o:     row += "O "; only_obs += 1
        elif e:     row += "X "; only_exp += 1
        else:       row += ". "
    lines.append(f"{z:5.1f} {row}")

print("       x: 0.19 → 29.41（每列 0.38m，共 %d 列）" % len(xs))
print("       " + "".join(str((i // 10) % 10) if i % 10 == 0 else " " for i in range(len(xs))))
for ln in lines:
    print(ln)

tot = both + only_obs + only_exp
print(f"\n重合 {both}   渲染多出 {only_obs}   渲染缺失 {only_exp}   "
      f"IoU = {both/(both+only_obs+only_exp)*100:.1f}%")
print("""
读数提示：
  · 若 'O' 集中在「屋顶/雨棚投影」或「实体家具伸到室外」→ 渲染多出属正常
  · 若 'X' 成片出现在某个房间位置 → 该房间没被建出来（严重）
""")
