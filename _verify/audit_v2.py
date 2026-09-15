# -*- coding: utf-8 -*-
"""布局审计 v3 —— 静态几何全检（不依赖截图，可复现）

① 房间不重叠
② 每樘门朝外 1.2m 为空地（不被别的房间墙封死）
③ 门牌不压门洞
④ 家具在房内、不压门洞（含旋转感知的包围盒）
⑤ 座位朝向：椅/沙发是否面朝最近的桌/几
   ★ 实测模型朝向（_verify/probe_facing2.mjs 顶点分布分析）：
     exec_chair  靠背在 -z ⇒ r=0 面朝 +z   → 朝向向量 ( sin r,  cos r)
     sofa        靠背在 -z ⇒ r=0 面朝 +z   → 同上
     office_chair 靠背在 +z ⇒ r=0 面朝 -z  → 朝向向量 (-sin r, -cos r)   ← 与上两者相反
⑥ 家具是否穿插墙上记忆屏/白板（buildMemWall 实际位置）
"""
import io, re, math, sys

P = sys.argv[1] if len(sys.argv) > 1 else 'office-3d-taskboard.html'
h = io.open(P, encoding='utf-8').read()

# ── 解析 ZONES ──
blk = re.search(r'const ZONES = \{(.*?)\n\};', h, re.S).group(1)
Z = {}
for line in blk.split('\n'):
    m = re.match(r"\s*(\w+):\s*\{", line)
    if not m:
        continue
    g = lambda p: (lambda mm: float(mm.group(1)) if mm else None)(re.search(p, line))
    dwm = re.search(r"doorWall:'?(\w+|null)'?", line)
    Z[m.group(1)] = dict(
        cx=g(r'cx:([\d.]+)'), cz=g(r'cz:([\d.]+)'), w=g(r'w:([\d.]+)'), d=g(r'd:([\d.]+)'),
        doorWall=(None if (not dwm or dwm.group(1) == 'null') else dwm.group(1)),
        doorPos=g(r'doorPos:([\d.]+)'))
print(f'解析到 {len(Z)} 个房间：{list(Z)}')
assert len(Z) == 8, '房间数不对'
MEM_STYLE = dict(re.findall(r"(\w+):'(display|projection|whiteboard)'",
                            re.search(r'const MEM_STYLE=\{(.*?)\};', h).group(1)))
print('记忆屏样式：', MEM_STYLE)

rect = lambda z: (z['cx'] - z['w'] / 2, z['cz'] - z['d'] / 2, z['cx'] + z['w'] / 2, z['cz'] + z['d'] / 2)
def ov(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

err = 0
GAP = 0.8

# ═══ ① 房间重叠 ═══
print('\n① 房间重叠')
bad = [(i, j) for k, i in enumerate(Z) for j in list(Z)[k + 1:] if ov(rect(Z[i]), rect(Z[j]))]
print('   ✅ 无重叠' if not bad else f'   ❌ {bad}'); err += len(bad)

# ═══ ② 封门检查 ═══
print('\n② 门洞外侧 1.2m 是否被别的房间占住')
for zid, z in Z.items():
    if not z['doorWall']:
        print(f'   --   {zid:8s} openPlan 无门'); continue
    r = rect(z); dw, dp = z['doorWall'], z['doorPos']
    if dw in ('front', 'back'):
        a = (dp - GAP / 2, r[3] + 0.15, dp + GAP / 2, r[3] + 1.2) if dw == 'front' else (dp - GAP / 2, r[1] - 1.2, dp + GAP / 2, r[1] - 0.15)
    else:
        a = (r[2] + 0.15, dp - GAP / 2, r[2] + 1.2, dp + GAP / 2) if dw == 'right' else (r[0] - 1.2, dp - GAP / 2, r[0] - 0.15, dp + GAP / 2)
    bl = [o for o in Z if o != zid and Z[o]['doorWall'] and ov(a, rect(Z[o]))]   # openPlan 大厅不算阻塞
    print(f'   {"❌" if bl else "✅"} {zid:8s} 门({dw}@{dp:g}) 外侧' + (f' 被 {bl} 占住' if bl else ' 空地'))
    err += len(bl)

# ═══ ③ 门牌 vs 门洞 ═══
print('\n③ 门牌是否压门洞')
for zid, z in Z.items():
    if not z['doorWall']:
        continue
    dw, dp = z['doorWall'], z['doorPos']
    axis = z['w'] if dw in ('front', 'back') else z['d']
    relC = (dp - z['cx']) if dw in ('front', 'back') else (dp - z['cz'])
    sA = (relC - GAP / 2) + axis / 2; sB = axis / 2 - (relC + GAP / 2)
    seg = max(sA, sB); pw = min(2.8, max(1.6, seg - 0.5))
    along = relC + (1 if sB >= sA else -1) * (GAP / 2 + seg / 2)
    lo, hi = along - pw / 2, along + pw / 2
    dlo, dhi = relC - GAP / 2, relC + GAP / 2
    hit = not (hi <= dlo + 0.01 or dhi - 0.01 <= lo)
    print(f'   {"❌" if hit else "✅"} {zid:8s} 牌[{lo:+.2f},{hi:+.2f}] w={pw:.1f}  门洞[{dlo:+.2f},{dhi:+.2f}]' + ('  ← 压门洞' if hit else ''))
    err += hit

# ── 家具实测尺寸（GLB 包围盒 × 高度缩放；x, z 为地面投影）──
FOOT = dict(exec_desk=(1.91, 0.83), exec_chair=(0.75, 0.73), office_chair=(0.69, 0.71),
            office_monitor=(0.60, 0.30), sofa=(1.48, 0.84), coffee_table=(0.93, 0.94),
            filing_cabinet=(0.70, 0.75), plant_potted=(0.62, 0.62), laptop=(0.40, 0.35))
HEIGHT = dict(exec_desk=0.76, exec_chair=1.20, office_chair=1.00, office_monitor=0.50,
              sofa=0.80, coffee_table=0.45, filing_cabinet=1.10, plant_potted=0.60, laptop=0.35)
FACING = {'exec_chair': 1, 'sofa': 1, 'office_chair': -1}   # +1: r=0 朝 +z ; -1: r=0 朝 -z


def parse_show():
    out = {}
    for arr, body in re.findall(r'const (\w+)_SHOW = \[(.*?)\n\];', h, re.S):
        zid = arr.lower()
        if zid not in Z:
            continue
        items = []
        for line in body.split('\n'):
            km = re.search(r"key:'(\w+)'", line)
            pm = re.search(r"p:\[\s*(-?[\d.]+),\s*(-?[\d.]+)", line)
            if not km or not pm:
                continue
            rm = re.search(r"r:\s*([^,]+),", line)
            try:
                r = eval((rm.group(1) if rm else '0').replace('Math.PI', str(math.pi)))
            except Exception:
                r = 0.0
            items.append(dict(key=km.group(1), x=float(pm.group(1)), z=float(pm.group(2)), r=r))
        out[zid] = items
    return out


SHOW = parse_show()


def aabb(it):
    """旋转感知的地面 + 高度包围盒 → (x0,x1,z0,z1,y0,y1)"""
    w, d = FOOT.get(it['key'], (0.7, 0.7))
    if abs(math.sin(it['r'])) > 0.7:      # ±90° → 交换 x/z 跨度
        w, d = d, w
    ymax = HEIGHT.get(it['key'], 0.8) + (it.get('y') or 0)
    return (it['x'] - w / 2, it['x'] + w / 2, it['z'] - d / 2, it['z'] + d / 2,
            (it.get('y') or 0), ymax)


# ═══ ④ 家具在房内 / 不压门洞 ═══
print('\n④ 家具包围盒（越界 / 压门洞）')
for zid, items in SHOW.items():
    z = Z[zid]; hw, hd = z['w'] / 2, z['d'] / 2
    bad = []
    for it in items:
        x0, x1, z0, z1, y0, y1 = aabb(it)
        if not (-hw + 0.03 <= x0 and x1 <= hw - 0.03 and -hd + 0.03 <= z0 and z1 <= hd - 0.03):
            bad.append(f'{it["key"]}@({it["x"]},{it["z"]}) 出界')
        dw = z['doorWall']
        if dw and y1 > 1.2:      # 只有够高的家具才可能挡门
            if dw in ('front', 'back'):
                da = z['doorPos'] - z['cx']
                dist = (hd - it['z']) if dw == 'front' else (it['z'] + hd)
                lateral = abs(it['x'] - da)
                lat_ok = lateral < GAP / 2 + (x1 - x0) / 2
            else:
                da = z['doorPos'] - z['cz']
                dist = (hw - it['x']) if dw == 'right' else (it['x'] + hw)
                lateral = abs(it['z'] - da)
                lat_ok = lateral < GAP / 2 + (z1 - z0) / 2
            if dist < 0.8 and lat_ok:
                bad.append(f'{it["key"]}@({it["x"]},{it["z"]}) 压门洞(d={dist:.2f})')
    print(f'   {"✅" if not bad else "❌"} {zid:8s} {len(items):2d} 件  ' + ('; '.join(bad) if bad else ''))
    err += len(bad)

# ═══ ⑤ 座位朝向 ═══
print('\n⑤ 座位朝向（椅/沙发是否面朝最近桌椅）')
EXEMPT = {('cfo', 'office_chair')}   # 用户明确要求 CFO 房保持原配置不变
for zid, items in SHOW.items():
    ch = [i for i in items if i['key'] in FACING]
    tb = [i for i in items if i['key'] in ('exec_desk', 'coffee_table')]
    msgs = []
    for c in ch:
        sgn = FACING[c['key']]
        fx, fz = sgn * math.sin(c['r']), sgn * math.cos(c['r'])
        if not tb:
            continue
        t = min(tb, key=lambda q: (q['x'] - c['x']) ** 2 + (q['z'] - c['z']) ** 2)
        vx, vz = t['x'] - c['x'], t['z'] - c['z']
        L = math.hypot(vx, vz) or 1
        dot = (fx * vx + fz * vz) / L
        if dot < 0.1:
            tag = '（已知例外，用户要求不改）' if (zid, c['key']) in EXEMPT else ''
            msgs.append(f'{c["key"]}@({c["x"]},{c["z"]}) 背对 {t["key"]} dot={dot:+.2f}{tag}')
            if not tag:
                err += 1
    print(f'   {"✅" if not msgs else "⚠️"} {zid:8s} ' + ('; '.join(msgs) if msgs else '朝向正确'))

# ═══ ⑥ 家具 vs 记忆屏 ═══
print('\n⑥ 家具是否穿插墙上记忆屏/白板')


def mem_box(zid):
    z = Z[zid]; style = MEM_STYLE.get(zid, 'display')
    hw, hd = z['w'] / 2, z['d'] / 2
    dispW = min(2.6, z['w'] * 0.62) if style == 'whiteboard' else min(3.0, z['w'] * 0.72)
    dispH = dispW * 0.75
    x, zz, rotY = z['cx'], None, 0
    if style == 'whiteboard':
        if zid == 'cmo':
            x, zz, rotY = z['cx'] + hw - 0.35, z['cz'], -math.pi / 2
        elif zid == 'coo':
            zz, rotY = z['cz'] - hd + 0.6, 0
        elif zid == 'meeting':
            x, zz, rotY = z['cx'] - 1.65, z['cz'] + hd - 0.6, math.pi
        elif z['doorWall'] == 'front':
            zz, rotY = z['cz'] + hd * 0.32, 0
        elif z['doorWall'] == 'back':
            zz, rotY = z['cz'] - hd * 0.32, math.pi
        else:
            zz, rotY = z['cz'] - hd + 0.7, 0
    else:
        if z['doorWall'] == 'front':
            zz, rotY = z['cz'] - hd + 0.16, 0
        elif z['doorWall'] == 'back':
            zz, rotY = z['cz'] + hd - 0.16, math.pi
        else:
            zz, rotY = z['cz'] - hd + 0.16, 0
    depth = 0.16
    w, d = (depth, dispW) if abs(math.sin(rotY)) > 0.7 else (dispW, depth)
    y0 = 0.0 if style == 'whiteboard' else 1.5 - dispH / 2 - 0.07
    return (x - w / 2, x + w / 2, zz - d / 2, zz + d / 2, y0, 1.5 + dispH / 2 + 0.07)


for zid, items in SHOW.items():
    mb = mem_box(zid)
    z = Z[zid]
    hits = []
    for it in items:
        x0, x1, z0, z1, y0, y1 = aabb(it)
        # _SHOW 的 p 是房间局部坐标 → 转世界坐标（世界 = cx+px, cz+pz）后与记忆屏比较
        fx0, fx1, fz0, fz1 = x0 + z['cx'], x1 + z['cx'], z0 + z['cz'], z1 + z['cz']
        if ov((fx0, fz0, fx1, fz1), (mb[0], mb[2], mb[1], mb[3])) and y0 < mb[5] and y1 > mb[4]:
            hits.append(f'{it["key"]}@({it["x"]},{it["z"]}) 与记忆屏相交')
    print(f'   {"✅" if not hits else "❌"} {zid:8s} 屏(x{mb[0]:.2f}~{mb[1]:.2f}, z{mb[2]:.2f}~{mb[3]:.2f})  ' + ('; '.join(hits) if hits else '无穿插'))
    err += len(hits)

print(f'\n{"✅ 全部通过（0 问题）" if err == 0 else f"⚠️ {err} 项待处理"}')
