#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态校验 7 间房（+CFO 参照）SHOW 布局：
  1. 越界检查：家具是否超出房间墙内边界
  2. 门洞避让：doorWall 那面墙的 doorPos±0.4 通道内 ±0.4m 是否有物品
  3. 记忆屏避让：各房记忆屏位置是否有家具压上
"""
import io, re, math

HTML = io.open(r'C:\Users\Perfect\Desktop\3d-taskboard-main\office-3d-taskboard.html',
               encoding='utf-8').read()

ZONES = {
  'cro':     dict(cx=2.5,  cz=2.5,  w=5,  d=5, doorWall='front', doorPos=2.5),
  'coo':     dict(cx=8.5,  cz=2.5,  w=7,  d=5, doorWall='front', doorPos=8.5),
  'meeting': dict(cx=15,   cz=2.5,  w=6,  d=5, doorWall='front', doorPos=15),
  'ceo':     dict(cx=21,   cz=2.5,  w=6,  d=5, doorWall='front', doorPos=21),
  'cmo':     dict(cx=9,    cz=9,    w=18, d=8, doorWall=None,    doorPos=None, openPlan=True),
  'cpo':     dict(cx=21,   cz=9,    w=6,  d=8, doorWall='left',  doorPos=9),
  'cto':     dict(cx=4,    cz=15.5, w=8,  d=5, doorWall='back',  doorPos=4),
  'cfo':     dict(cx=20,   cz=15.5, w=8,  d=5, doorWall='back',  doorPos=20),
}
# 各类模型的近似占地（宽 × 深，米），用于越界判定
FOOT = {
  'exec_desk':      (1.90, 0.95),
  'exec_chair':     (0.65, 0.65),
  'office_desk':    (1.50, 0.75),
  'office_chair':   (0.58, 0.58),
  'office_monitor': (0.55, 0.22),
  'sofa':           (2.00, 0.85),
  'coffee_table':   (1.10, 0.60),
  'filing_cabinet': (0.45, 0.60),
  'plant_potted':   (0.55, 0.55),
  'laptop':         (0.35, 0.25),
}
# 记忆屏位置（来自 buildMemWall 逻辑）
MEMWALL = {
  'ceo':     dict(style='display',    x=0.00,   z=None),  # 后墙 display
  'cro':     dict(style='display',    x=0.00,   z=None),
  'coo':     dict(style='whiteboard', x=0.00,   z=-2.5 + 0.6),   # cz-hd+0.6
  'meeting': dict(style='whiteboard', x=-1.65,  z=+2.5 - 0.6),   # cz+hd-0.6
  'cpo':     dict(style='display',    x=0.00,   z=None),
  'cto':     dict(style='display',    x=0.00,   z=None),
  'cfo':     dict(style='display',    x=0.00,   z=None),
  'cmo':     dict(style='whiteboard', x=+18/2 - 0.35, z=0.00),   # 右墙
}

# 解析各 SHOW 数组
def parse_show(name):
    m = re.search(rf'const {name} = \[(.*?)\n\];', HTML, re.S)
    if not m: return []
    items = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s.startswith('{'): continue
        km = re.search(r"key:'([^']+)'", s)
        pm = re.search(r"p:\[\s*([-\d.]+),\s*([-\d.]+)\]", s)
        rm = re.search(r"r:(-?[\d./]*Math\.PI[\d./]*)", s)
        if not (km and pm): continue
        r = 0.0
        if rm:
            expr = rm.group(1).replace('Math.PI', str(math.pi))
            try: r = eval(expr)
            except Exception: r = 0.0
        items.append(dict(key=km.group(1), x=float(pm.group(1)), z=float(pm.group(2)), r=r))
    return items

def rot_foot(key, r):
    """按朝向旋转后，家具占地取包围盒"""
    fw, fd = FOOT.get(key, (0.6, 0.6))
    c, s = abs(math.cos(r)), abs(math.sin(r))
    return fw * c + fd * s, fw * s + fd * c

problems = []
for zid, z in ZONES.items():
    name = ('MEETING' if zid == 'meeting' else zid.upper()) + '_SHOW'
    items = parse_show(name)
    hw, hd = z['w'] / 2, z['d'] / 2
    print(f"\n{'='*66}\n{zid.upper():8s} {z['w']}×{z['d']}m  门:{z['doorWall']}  家具 {len(items)} 件\n{'='*66}")

    for it in items:
        bw, bd = rot_foot(it['key'], it['r'])
        # 越界：家具包围盒是否超出墙内边界（留 0.05 余量）
        ox = abs(it['x']) + bw / 2 - hw
        oz = abs(it['z']) + bd / 2 - hd
        flags = []
        if ox > -0.05:
            flags.append(f"❌ 出{'左' if it['x']<0 else '右'}墙 {ox:+.2f}m")
        if oz > -0.05:
            flags.append(f"❌ 出{'后' if it['z']<0 else '前'}墙 {oz:+.2f}m")

        # 门洞避让：门在 doorWall 面，doorPos 相对中心的偏移
        if z['doorWall'] and z['doorPos'] is not None:
            dw = z['doorWall']
            # 门墙侧：front→z=+hd, back→z=-hd, left→x=-hw, right→x=+hw
            if dw == 'front':
                d_off = z['doorPos'] - z['cx']; edge_axis = 'z'; wall_val = +hd
            elif dw == 'back':
                d_off = z['doorPos'] - z['cx']; edge_axis = 'z'; wall_val = -hd
            elif dw == 'left':
                d_off = z['doorPos'] - z['cz']; edge_axis = 'x'; wall_val = -hw
            else:
                d_off = z['doorPos'] - z['cz']; edge_axis = 'x'; wall_val = +hw
            center_axis = it['z'] if edge_axis == 'z' else it['x']
            dist_to_wall = abs(wall_val - center_axis)
            # 仅当家具真的接近"门墙"侧时才判（避免对面墙的误报）
            if dist_to_wall < 1.2:
                along = it['x'] if edge_axis == 'z' else it['z']
                if abs(along - d_off) < (0.4 + (bw if edge_axis == 'z' else bd) / 2 + 0.15):
                    flags.append(f"⚠️  压门洞(距{dw}墙{dist_to_wall:.2f}m, 沿墙偏移{along-d_off:+.2f}m)")

        # 记忆屏避让（用包围盒：屏宽 2.6m × 高 1.5m，中心点 mw.x/mw.z）
        mw = MEMWALL.get(zid)
        if mw and mw['z'] is not None:
            mw_w = 2.6 if mw.get('style') == 'whiteboard' else 2.0
            mw_d = 0.16
            # 屏包围盒 x:[mw.x-1.3, mw.x+1.3], z:[mw.z-0.08, mw.z+0.08] (很薄一面墙)
            # 实际看：家具中心是否进入屏占地区（z 方向上屏只占 0.16m，所以要求 |dz|<mw_d/2+bd/2+0.05）
            dx = abs(it['x'] - mw['x']); dz = abs(it['z'] - mw['z'])
            bd_half = bd / 2
            if dx < (mw_w / 2 + bw / 2 + 0.1) and dz < (mw_d + bd_half + 0.05):
                flags.append(f"⚠️  压记忆屏(x={mw['x']}, z={mw['z']}, dx={dx:.2f} dz={dz:.2f})")

        tag = ' '.join(flags) if flags else '✅'
        print(f"  {it['key']:16s} p=[{it['x']:+.2f},{it['z']:+.2f}] r={it['r']:+.3f}  {tag}")
        if flags: problems.append((zid, it['key'], flags))

print(f"\n{'#'*66}\n合计问题 {len(problems)} 处")
for zid, k, f in problems:
    print(f"  {zid:8s} {k:16s} {' '.join(f)}")
if not problems:
    print("  ✅ 全部通过：无出墙、无压门洞、无压记忆屏")