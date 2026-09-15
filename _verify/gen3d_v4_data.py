# -*- coding: utf-8 -*-
"""v4 平面图 → 3D 看板数据（ZONES / 公共区地板 / 公共区外墙段）

思路（与 floorplan-svg-generator 技能的栅格法一致）：
  1) 直接复用 plan_v4.json 的房间矩形与公共区矩形，1:1 当作 three.js 世界坐标
     （平面图 z 向下=南，看板相机在 +Z 看向 -Z，方向天然一致 → 无需翻转）
  2) 公共区地板：对公共区做「贪心最大矩形分解」→ 得到互不重叠的地板矩形，避免 z-fighting
  3) 公共区外墙：沿用栅格边界法。边界段若「内侧格」属于房间则该房间自己会建墙 → 跳过；
     只有内侧格属于公共区(PUB)时才需要另建外墙。门洞再单独开槽。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, "plan_v4.json"), encoding="utf-8"))
G = 0.1
EX, EZ = PLAN["envelope"]
W, H = int(round(EX / G)), int(round(EZ / G))

# ---------- 1) ZONES ----------
# doorWall 映射：平面图 S 墙(南,+z) = 看板 front；N 墙(北,-z) = back；E 墙(东,+x) = right；W = left
WALLMAP = {"S": "front", "N": "back", "E": "right", "W": "left"}
DOORS = {d[0]: (d[1], d[2], d[3]) for d in PLAN["doors"]}

# 看板既有的部门身份色 / 地毯色（保持不变，只换布局）
STYLE = {
    "CPO": ("cpo",     "CPO 产品设计室", "#b08060", "#885840"),
    "MT":  ("meeting", "战略会议室",     "#706898", "#504870"),
    "CFO": ("cfo",     "CFO 财务中心",   "#5a8070", "#406050"),
    "CRO": ("cro",     "CRO 风控中心",   "#8a5858", "#604040"),
    "CMO": ("cmo",     "CMO 营销中心",   "#b89850", "#907038"),
    "CTO": ("cto",     "CTO 技术中心",   "#485c48", "#304030"),
    "COO": ("coo",     "COO 运营中心",   "#647080", "#4a5460"),
    "CEO": ("ceo",     "CEO 战略办公室", "#5a6880", "#445060"),
}

zones = []
for r in PLAN["rooms"]:
    k = r["key"]
    zid, name, color, carpet = STYLE[k]
    wall, coord, pos = DOORS[k]
    cx = round((r["x1"] + r["x2"]) / 2, 2)
    cz = round((r["z1"] + r["z2"]) / 2, 2)
    zones.append(dict(id=zid, key=k, name=name, color=color, carpet=carpet,
                      cx=cx, cz=cz, w=round(r["w"], 2), d=round(r["d"], 2),
                      rect=(r["x1"], r["z1"], r["x2"], r["z2"]),
                      doorWall=WALLMAP[wall], doorPos=round(pos, 2)))

# ---------- 2) 栅格归属 ----------
owner = [[None] * W for _ in range(H)]


def fill(x1, z1, x2, z2, tag):
    for j in range(int(round(z1 / G)), int(round(z2 / G))):
        for i in range(int(round(x1 / G)), int(round(x2 / G))):
            if 0 <= i < W and 0 <= j < H:
                owner[j][i] = tag


for z in zones:
    fill(*z["rect"], z["id"])
pub_mask = [[False] * W for _ in range(H)]
for (x1, z1, x2, z2) in PLAN["public"]:
    for j in range(int(round(z1 / G)), int(round(z2 / G))):
        for i in range(int(round(x1 / G)), int(round(x2 / G))):
            if owner[j][i] is None:
                owner[j][i] = "PUB"
                pub_mask[j][i] = True
lcx, lcz, lr = PLAN["lobby"]
for j in range(H):
    for i in range(W):
        if ((i + .5) * G - lcx) ** 2 + ((j + .5) * G - lcz) ** 2 <= lr * lr:
            if owner[j][i] is None:
                owner[j][i] = "PUB"
                pub_mask[j][i] = True

# ---------- 3) 公共区地板：贪心最大矩形分解 ----------
def greedy_rects(mask):
    m = [row[:] for row in mask]
    rects = []

    def largest():
        best = (0, None)
        heights = [0] * W
        for j in range(H):
            for i in range(W):
                heights[i] = heights[i] + 1 if m[j][i] else 0
            st = []
            for i in range(W + 1):
                cur = heights[i] if i < W else 0
                start = i
                while st and st[-1][1] >= cur:
                    s, h = st.pop()
                    area = h * (i - s)
                    if area > best[0]:
                        best = (area, (s, j - h + 1, i - s, h))
                    start = s
                st.append((start, cur))
        return best

    while True:
        area, rc = largest()
        if not area:
            break
        x0, z0, ww, hh = rc
        rects.append((x0 * G, z0 * G, (x0 + ww) * G, (z0 + hh) * G))
        for j in range(z0, z0 + hh):
            for i in range(x0, x0 + ww):
                m[j][i] = False
    return rects


pub_floors = greedy_rects(pub_mask)

# ---------- 3b) 建筑垫层：整栋外轮廓膨胀 3 格(0.3m) → 分解（凹口不会被填平） ----------
inside_mask = [[owner[j][i] is not None for i in range(W)] for j in range(H)]
pad_mask = [[False] * W for _ in range(H)]
R = 3
for j in range(H):
    for i in range(W):
        if not inside_mask[j][i]:
            continue
        for jj in range(max(0, j - R), min(H, j + R + 1)):
            for ii in range(max(0, i - R), min(W, i + R + 1)):
                pad_mask[jj][ii] = True
pad_rects = greedy_rects(pad_mask)
pad_rects = [(round(x1, 1), round(z1, 1), round(x2, 1), round(z2, 1)) for (x1, z1, x2, z2) in pad_rects]


# ---------- 4) 公共区外墙段（内侧格为 PUB 才建） ----------
def is_in(j, i):
    return 0 <= i < W and 0 <= j < H and owner[j][i] is not None


raw = []   # (o, k, s, e, inside_j, inside_i)
for j in range(H):
    for i in range(W):
        if not is_in(j, i):
            continue
        if not is_in(j - 1, i):
            raw.append(("h", j, i, i + 1, j, i))
        if not is_in(j + 1, i):
            raw.append(("h", j + 1, i, i + 1, j, i))
        if not is_in(j, i - 1):
            raw.append(("v", i, j, j + 1, j, i))
        if not is_in(j, i + 1):
            raw.append(("v", i + 1, j, j + 1, j, i))

# 按键分组 → 按内侧归属切段 → 合并相邻同归属段
from collections import defaultdict
bucket = defaultdict(list)
for o, k, s, e, ij, ii in raw:
    bucket[(o, k)].append((s, e, owner[ij][ii]))

segs = []
for (o, k), lst in bucket.items():
    lst.sort()
    cur = None
    for s, e, own in lst:
        if cur and cur[2] == own and s <= cur[1]:
            cur = (cur[0], max(cur[1], e), own)
        else:
            if cur:
                segs.append((o, k) + cur)
            cur = (s, e, own)
    if cur:
        segs.append((o, k) + cur)

pub_walls = [(o, k, s, e) for (o, k, s, e, own) in segs if own == "PUB"]

# ---------- 5) 输出 ----------
print("=== ZONES ===")
for z in zones:
    print(f"  {z['id']:8s} cx={z['cx']:5.1f} cz={z['cz']:5.1f} w={z['w']:4.1f} d={z['d']:4.1f} "
          f"door={z['doorWall']:5s} pos={z['doorPos']:5.1f}")
print(f"\n=== 公共区地板 {len(pub_floors)} 块 ===")
for (x1, z1, x2, z2) in pub_floors:
    print(f"  x {x1:5.1f}~{x2:5.1f}   z {z1:5.1f}~{z2:5.1f}   ({x2-x1:.1f} x {z2-z1:.1f})")
print(f"\n=== 公共区外墙 {len(pub_walls)} 段 ===")
for (o, k, s, e) in pub_walls:
    if o == "h":
        print(f"  H  z={k*G:5.1f}   x {s*G:5.1f}~{e*G:5.1f}  (长 {(e-s)*G:.1f})")
    else:
        print(f"  V  x={k*G:5.1f}   z {s*G:5.1f}~{e*G:5.1f}  (长 {(e-s)*G:.1f})")
print("\n=== 圆厅 ===", PLAN["lobby"], " 前庭", PLAN["court"], " 主入口", PLAN["entry"])
print(f"\n=== 建筑垫层 {len(pad_rects)} 块（外扩 0.3m） ===")
for (x1, z1, x2, z2) in pad_rects:
    print(f"  x {x1:5.1f}~{x2:5.1f}   z {z1:5.1f}~{z2:5.1f}")

json.dump(dict(zones=zones, pub_floors=pub_floors, pub_walls=pub_walls, pad_rects=pad_rects,
               lobby=PLAN["lobby"], court=PLAN["court"], entry=PLAN["entry"],
               envelope=PLAN["envelope"]),
          open(os.path.join(HERE, "gen3d_v4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n→ 已写出 _verify/gen3d_v4.json")
