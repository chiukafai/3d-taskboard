"""错落式办公室平面图（v2）几何校验
校验项：房间互不重叠 / 房间不压走廊与凹院 / 面积核算 / 外轮廓错落度
坐标单位：米。x 向东，z 向南（北=z 小）。
"""
import sys

rooms = {
    "CRO":  (0,    2.5,  5.5,  9.0),
    "CTO":  (7.9,  0.0,  13.2, 9.0),
    "CPO":  (13.2, 1.4,  18.4, 9.0),
    "CMO":  (18.4, 3.0,  25.5, 9.0),
    "CFO":  (0,    11.4, 6.5,  18.6),
    "COO":  (6.5,  11.4, 13.5, 19.4),
    "CEO":  (13.5, 11.4, 19.5, 17.4),
    "MEET": (19.5, 11.4, 24.3, 17.8),
}
corridor = [(3.0, 9.0, 24.3, 11.4), (5.5, 4.5, 7.9, 9.0)]
yard = (5.5, 0.0, 7.9, 4.5)


def ov(a, b):
    return (min(a[2], b[2]) - max(a[0], b[0]) > 1e-6
            and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6)


bad = 0
ks = list(rooms)
for i in range(len(ks)):
    for j in range(i + 1, len(ks)):
        if ov(rooms[ks[i]], rooms[ks[j]]):
            print("OVERLAP:", ks[i], ks[j])
            bad += 1
for k, r in rooms.items():
    for c in corridor:
        if ov(r, c):
            print("ROOM-CORRIDOR OVERLAP:", k)
            bad += 1
    if ov(r, yard):
        print("ROOM-YARD OVERLAP:", k)
        bad += 1
print("overlap errors   :", bad)

tot = 0.0
for k, (x1, z1, x2, z2) in rooms.items():
    a = (x2 - x1) * (z2 - z1)
    tot += a
    print(f"{k:5s} {x2 - x1:4.1f} x {z2 - z1:4.1f} = {a:6.1f} m2")

ca = sum((c[2] - c[0]) * (c[3] - c[1]) for c in corridor)
print("rooms total      :", round(tot, 1))
print("corridor total   :", round(ca, 1))
print("indoor total     :", round(tot + ca, 1))
print("yard area        :", round((yard[2] - yard[0]) * (yard[3] - yard[1]), 1))

xmin = min(r[0] for r in rooms.values())
xmax = max(r[2] for r in rooms.values())
zmin = min(r[1] for r in rooms.values())
zmax = max(r[3] for r in rooms.values())
env = (xmax - xmin) * (zmax - zmin)
print(f"envelope         : {xmax - xmin:.1f} x {zmax - zmin:.1f} = {env:.1f} m2")
print("indoor coverage  :", round(100 * (tot + ca) / env, 1), "%")

north = sorted({r[1] for r in rooms.values()})
south = sorted({r[3] for r in rooms.values()})
west = sorted({r[0] for r in rooms.values()})
east = sorted({r[2] for r in rooms.values()})
print("distinct N faces :", north)
print("distinct S faces :", south)
print("distinct W faces :", west)
print("distinct E faces :", east)

sys.exit(1 if bad else 0)
