# -*- coding: utf-8 -*-
"""平面图 v4 —— 完全非对称：几何计算 + 冲突校验 + 对称性检测 → plan_v4.json"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plan_v4.json")
G = 0.1
EX, EZ = 29.6, 21.6          # 包络 29.6 x 21.6

# key, 中文, 英文, x1, z1, x2, z2, 配色
ROOMS = [
    ("CPO", "产品设计室", "Product",        0.0,  5.6,  6.6, 11.0, "#6FB98F"),
    ("MT",  "战略会议室", "Meeting Room",   1.0, 11.0,  7.4, 16.4, "#9C8AA5"),
    ("CFO", "财务中心",   "Finance",        2.2, 16.4,  8.6, 21.6, "#C97B84"),
    ("CRO", "风控中心",   "Risk Control",   9.4,  3.6, 15.6,  8.6, "#8E7CC3"),
    ("CMO", "营销中心",   "Marketing",     15.6,  0.0, 23.8,  8.6, "#E08A5B"),
    ("CTO", "技术中心",   "Technology",    23.8,  1.6, 29.6,  8.6, "#5B8FB9"),
    ("COO", "运营中心",   "Operations",    11.4, 11.6, 19.4, 19.4, "#D9A441"),
    ("CEO", "战略办公室", "Executive",     19.4, 12.4, 26.0, 19.0, "#7A8FA6"),
]

# 公共：西翼蛇形楼梯廊 A1→A2→A3 + 东西主廊 B1(北)/B2(南移) + 中央枢纽
PUBLIC = [
    (6.6,  5.6,  9.4, 11.0),   # A1
    (7.4, 11.0, 10.2, 16.4),   # A2
    (8.6, 16.4, 11.4, 21.6),   # A3
    (9.4,  8.6, 19.4, 11.6),   # B1
    (19.4, 8.6, 29.4, 12.4),   # B2（东段向南加宽 1.4m，形成单侧放大）
    (7.4,  8.6, 11.4, 13.0),   # 中央枢纽
]
LOBBY = (9.4, 10.8, 1.9)                  # 接待厅圆，偏心（包络中心 x=14.8）
COURT = (0.0, 0.0, 6.6, 5.6)              # 西北入口前庭（无顶）
ENTRY = (8.0, 5.6)                        # 主入口：A1 北端，朝北前庭

DOORS = [
    ("CPO", "E",  6.6,  8.0), ("MT", "E", 7.4, 13.6), ("CFO", "E", 8.6, 19.0),
    ("CRO", "S",  8.6, 12.6), ("CMO", "S", 8.6, 17.6), ("CTO", "S", 8.6, 26.4),
    ("COO", "N", 11.6, 15.2), ("CEO", "N", 12.4, 22.6),
]

W, H = int(round(EX / G)), int(round(EZ / G))
owner = [[None] * W for _ in range(H)]
conflicts = []


def paint(x1, z1, x2, z2, tag):
    a = max(0, int(round(x1 / G))); b = min(W, int(round(x2 / G)))
    c = max(0, int(round(z1 / G))); d = min(H, int(round(z2 / G)))
    for j in range(c, d):
        row = owner[j]
        for i in range(a, b):
            if row[i] is None:
                row[i] = tag
            elif row[i] != tag:
                conflicts.append((row[i], tag, round(i * G, 1), round(j * G, 1)))


rlist = []
for (k, cn, en, x1, z1, x2, z2, col) in ROOMS:
    paint(x1, z1, x2, z2, k)
    rlist.append(dict(key=k, cn=cn, en=en, x1=x1, z1=z1, x2=x2, z2=z2, color=col,
                      w=round(x2 - x1, 2), d=round(z2 - z1, 2),
                      area=round((x2 - x1) * (z2 - z1), 1)))

pub = set()
for (x1, z1, x2, z2) in PUBLIC:
    for j in range(int(round(z1 / G)), int(round(z2 / G))):
        for i in range(int(round(x1 / G)), int(round(x2 / G))):
            pub.add((i, j))
cx, cz, r = LOBBY
for j in range(H):
    for i in range(W):
        if ((i + .5) * G - cx) ** 2 + ((j + .5) * G - cz) ** 2 <= r * r:
            pub.add((i, j))
pub_hit = 0
for (i, j) in pub:
    if owner[j][i] is None:
        owner[j][i] = "PUB"
    else:
        pub_hit += 1
        conflicts.append((owner[j][i], "PUB", round(i * G, 1), round(j * G, 1)))

room_area = sum(x["area"] for x in rlist)
pub_area = len(pub) * G * G
inside = [[owner[j][i] is not None for i in range(W)] for j in range(H)]
foot = sum(1 for j in range(H) for i in range(W) if inside[j][i]) * G * G

# ---- 对称性检测 A：面积镜像重合度 ----
def mirror(axis):
    same = tot = 0
    for j in range(H):
        for i in range(W):
            if inside[j][i]:
                tot += 1
                if (inside[j][W - 1 - i] if axis == "x" else inside[H - 1 - j][i]):
                    same += 1
    return 100.0 * same / max(tot, 1)


# ---- 对称性检测 B：房间级镜像自洽（有几间房镜像后还落在自己身上）----
def owner_at(x, z):
    i, j = int(x / G), int(z / G)
    return owner[j][i] if 0 <= i < W and 0 <= j < H else None


self_sym = []
for rm in rlist:
    ccx = (rm["x1"] + rm["x2"]) / 2
    ccz = (rm["z1"] + rm["z2"]) / 2
    hit_x = owner_at(EX - ccx, ccz)
    hit_z = owner_at(ccx, EZ - ccz)
    self_sym.append(dict(key=rm["key"], mirror_x=hit_x, mirror_z=hit_z,
                         same_x=hit_x == rm["key"], same_z=hit_z == rm["key"]))

# ---- 外轮廓：栅格边界 → 合并共线 → 线段列表 ----
def boundary_runs():
    segs_h, segs_v = [], []
    for j in range(H):
        for i in range(W):
            if not inside[j][i]:
                continue
            if j == 0 or not inside[j - 1][i]:
                segs_h.append((j, i, i + 1))
            if j == H - 1 or not inside[j + 1][i]:
                segs_h.append((j + 1, i, i + 1))
            if i == 0 or not inside[j][i - 1]:
                segs_v.append((i, j, j + 1))
            if i == W - 1 or not inside[j][i + 1]:
                segs_v.append((i + 1, j, j + 1))
    hb, vb = {}, {}
    for key, s, e in segs_h:
        hb.setdefault(key, []).append((s, e))
    for key, s, e in segs_v:
        vb.setdefault(key, []).append((s, e))
    # 合并同一直线上首尾相接的段
    merged = []
    for o, buckets in (("h", hb), ("v", vb)):
        for k, rs in buckets.items():
            rs.sort()
            s, e = rs[0]
            for a, b in rs[1:]:
                if a <= e:
                    e = max(e, b)
                else:
                    merged.append(dict(o=o, k=k, s=s, e=e))
                    s, e = a, b
            merged.append(dict(o=o, k=k, s=s, e=e))
    return merged


runs = boundary_runs()
door_ck = []
for (k, wall, coord, pos) in DOORS:
    rm = next(x for x in rlist if x["key"] == k)
    if wall in ("S", "N"):
        on = abs(coord - (rm["z2"] if wall == "S" else rm["z1"])) < 1e-6 and rm["x1"] + .6 < pos < rm["x2"] - .6
        pr = (pos, coord + (0.35 if wall == "S" else -0.35))
    else:
        on = abs(coord - (rm["x2"] if wall == "E" else rm["x1"])) < 1e-6 and rm["z1"] + .6 < pos < rm["z2"] - .6
        pr = (coord + (0.35 if wall == "E" else -0.35), pos)
    i2, j2 = int(pr[0] / G), int(pr[1] / G)
    ok = 0 <= i2 < W and 0 <= j2 < H and owner[j2][i2] == "PUB"
    door_ck.append(dict(room=k, wall=wall, pos=pos, on_wall=bool(on), to_public=bool(ok)))

rep = dict(rooms=rlist, public=PUBLIC, lobby=LOBBY, court=COURT, entry=ENTRY,
           doors=DOORS, runs=runs, room_area=round(room_area, 1),
           public_area=round(pub_area, 1), indoor=round(room_area + pub_area, 1),
           footprint=round(foot, 1), envelope=[EX, EZ],
           sym_x=round(mirror("x"), 1), sym_z=round(mirror("z"), 1),
           self_sym=self_sym,
           north_faces=sorted({x["z1"] for x in rlist if x["z1"] < 9}),
           south_faces=sorted({x["z2"] for x in rlist if x["z2"] > 11}),
           west_faces=sorted({x["x1"] for x in rlist}),
           east_faces=sorted({x["x2"] for x in rlist}))
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)

print("重叠冲突        :", len(conflicts), conflicts[:4])
print("公共压房间      :", pub_hit)
print("房间面积合计    : %.1f m2" % room_area)
print("公共面积合计    : %.1f m2" % pub_area)
print("室内合计        : %.1f m2   外轮廓占地 %.1f m2   包络 %.1fx%.1f=%.1f"
      % (room_area + pub_area, foot, EX, EZ, EX * EZ))
print("覆盖率          : %.1f%%    公共占比 %.1f%%"
      % (100 * foot / (EX * EZ), 100 * pub_area / (room_area + pub_area)))
print("镜像重合度(面积): 左右 %.1f%%  上下 %.1f%%" % (mirror("x"), mirror("z")))
print("镜像自洽(房间级): 左右命中 %d/8  上下命中 %d/8"
      % (sum(1 for s in self_sym if s["same_x"]), sum(1 for s in self_sym if s["same_z"])))
print("北墙 z          :", rep["north_faces"])
print("南墙 z          :", rep["south_faces"])
print("西墙 x          :", rep["west_faces"])
print("东墙 x          :", rep["east_faces"])
print("门校验失败      :", sum(1 for d in door_ck if not (d["on_wall"] and d["to_public"])))
for d in door_ck:
    if not (d["on_wall"] and d["to_public"]):
        print("   x", d)
print("轮廓线段数      :", len(runs))
