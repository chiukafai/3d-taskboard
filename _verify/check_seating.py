# -*- coding: utf-8 -*-
"""座位朝向核算：
   exec_chair  实测靠背在 -z ⇒ r=0 时面朝 +z ⇒ 朝向向量 = (sin r, cos r )
   office_chair 实测靠背在 +z ⇒ r=0 时面朝 -z ⇒ 朝向向量 = (-sin r, -cos r)
   检查「椅子 → 桌子」方向与椅子朝向是否一致（点积≈+1 为正确）"""
import io, re, math, sys

h = io.open(sys.argv[1] if len(sys.argv) > 1 else 'office-3d-taskboard.html', encoding='utf-8').read()

# 房间
Z = {}
blk = re.search(r'const ZONES = \{(.*?)\n\};', h, re.S).group(1)
for line in blk.split('\n'):
    m = re.match(r"\s*(\w+):\s*\{", line)
    if not m:
        continue
    g = lambda p: (lambda mm: float(mm.group(1)) if mm else None)(re.search(p, line))
    Z[m.group(1)] = dict(cx=g(r'cx:([\d.]+)'), cz=g(r'cz:([\d.]+)'), w=g(r'w:([\d.]+)'), d=g(r'd:([\d.]+)'),
                         dw=(lambda mm: mm.group(1) if mm else None)(re.search(r"doorWall:'?(\w+|null)'?", line)),
                         dp=g(r'doorPos:([\d.]+)'))

FACING = {'exec_chair': 1, 'office_chair': -1, 'sofa': 1}   # +1: r=0 朝 +z ; -1: r=0 朝 -z

for arr, body in re.findall(r'const (\w+)_SHOW = \[(.*?)\n\];', h, re.S):
    zid = arr.lower()
    z = Z.get(zid)
    if not z:
        continue
    items = []
    for line in body.split('\n'):
        km = re.search(r"key:'(\w+)'", line)
        if not km:
            continue
        pm = re.search(r"p:\[\s*(-?[\d.]+),\s*(-?[\d.]+)", line)
        rm = re.search(r"r:\s*([^,]+),", line)
        if not pm:
            continue
        rv = rm.group(1).strip() if rm else '0'
        try:
            r = eval(rv.replace('Math.PI', str(math.pi)))
        except Exception:
            r = 0.0
        items.append(dict(key=km.group(1), x=float(pm.group(1)), z=float(pm.group(2)), r=r))

    chairs = [i for i in items if i['key'] in FACING]
    desks = [i for i in items if i['key'] in ('exec_desk', 'coffee_table')]
    print(f'\n=== {zid.upper()}  (ctr {z["cx"]},{z["cz"]}  {z["w"]}x{z["d"]}  门={z["dw"]}@{z["dp"]}) ===')
    for c in chairs:
        sgn = FACING[c['key']]
        fx, fz = sgn * math.sin(c['r']), sgn * math.cos(c['r'])
        # 就近的桌/几
        if not desks:
            print(f'   {c["key"]:13s} @({c["x"]:+.2f},{c["z"]:+.2f}) r={c["r"]:.2f}  朝向=({fx:+.2f},{fz:+.2f})  — 无桌可判')
            continue
        d = min(desks, key=lambda t: (t['x'] - c['x']) ** 2 + (t['z'] - c['z']) ** 2)
        vx, vz = d['x'] - c['x'], d['z'] - c['z']
        L = math.hypot(vx, vz) or 1
        dot = (fx * vx + fz * vz) / L
        mark = '✅' if dot > 0.7 else ('⚠️ 侧向' if dot > 0.1 else '❌ 背对')
        print(f'   {c["key"]:13s} @({c["x"]:+.2f},{c["z"]:+.2f}) r={c["r"]:.2f}  朝向=({fx:+.2f},{fz:+.2f})'
              f'  → {d["key"]}@({d["x"]:+.2f},{d["z"]:+.2f}) 夹角点积={dot:+.2f}  {mark}')
