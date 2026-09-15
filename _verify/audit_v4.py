# -*- coding: utf-8 -*-
"""3D 看板布局审计 v4（非对称平面图版）

六项检查：
  ① 几何自洽：房间互不重叠、公共区不压房间（栅格 0.1m）
  ② 门通向公共区：门外 0.35m 探针格必须是 PUB
  ③ 门牌：不压门洞、不越出房间
  ④ 家具：AABB 不出房间、不压门洞迎面区
  ⑤ 座向：主椅朝向必须指向办公桌（点积）
  ⑥ 家具不与墙面记忆屏（显示屏/白板）相交
用法： python audit_v4.py [html文件]
"""
import json, os, re, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "office-3d-taskboard.html")
html = open(HTML, encoding="utf-8").read()
PLAN = json.load(open(os.path.join(HERE, "plan_v4.json"), encoding="utf-8"))
G = 0.1
EX, EZ = PLAN["envelope"]

# ── 实测模型原始尺寸（_verify/probe_models.mjs）──
NATIVE = {
    'exec_desk':      (1.077, 0.435, 0.472),
    'exec_chair':     (0.644, 1.018, 0.623),
    'office_chair':   (0.677, 0.977, 0.705),
    'office_monitor': (1.044, 0.592, 1.043),
    'sofa':           (1.021, 0.548, 0.583),
    'coffee_table':   (0.931, 0.450, 0.938),
    'filing_cabinet': (0.604, 0.943, 0.636),
    'plant_potted':   (0.783, 1.078, 0.829),
    'laptop':         (0.874, 0.643, 0.643),
}
MEM_STYLE = dict(ceo='projection', cfo='display', cto='display', cro='projection',
                 meeting='whiteboard', cmo='whiteboard', coo='whiteboard', cpo='display')
FLOOR = 0.09
fail = 0


def hdr(t):
    print("\n" + "═" * 66 + f"\n{t}\n" + "═" * 66)


# ══════════════ 解析 ZONES
Z = {}
for m in re.finditer(r"(\w+):\s*\{ id:'(\w+)', name:'([^']+)', color:'[^']+',\s*"
                     r"cx:([\d.-]+), cz:([\d.-]+), w:([\d.-]+), d:([\d.-]+),\s*"
                     r"doorWall:'?(\w+|null)'?, doorPos:([\d.-]+|null)", html):
    Z[m.group(2)] = dict(id=m.group(2), name=m.group(3), cx=float(m.group(4)), cz=float(m.group(5)),
                         w=float(m.group(6)), d=float(m.group(7)),
                         doorWall=(m.group(8) if m.group(8) != 'null' else None),
                         doorPos=(float(m.group(9)) if m.group(9) != 'null' else None),
                         hw=float(m.group(6)) / 2, hd=float(m.group(7)) / 2)
print(f"解析到 {len(Z)} 个房间：{', '.join(Z)}")

# ══════════════ 解析 *_SHOW
SHOW = {}
for m in re.finditer(r"const (\w+)_SHOW = \[(.*?)\n\];", html, re.S):
    rid = m.group(1).lower()
    if rid not in Z:
        continue
    items = []
    for it in re.finditer(r"key:'(\w+)',\s*p:\[\s*(-?[\d.]+),\s*(-?[\d.]+)\],\s*r:\s*([^,]+),\s*h:([\d.]+)"
                          r"(?:,\s*y:([\d.]+))?", m.group(2)):
        items.append(dict(key=it.group(1), x=float(it.group(2)), z=float(it.group(3)),
                          r=it.group(4).strip(), h=float(it.group(5)),
                          y=float(it.group(6)) if it.group(6) else 0.0))
    SHOW[rid] = items
for k, v in SHOW.items():
    print(f"  {k:8s} {len(v)} 件")

# ══════════════ ① 栅格几何
W, H = int(round(EX / G)), int(round(EZ / G))
owner = [[None] * W for _ in range(H)]


def fill(x1, z1, x2, z2, tag, strict=True):
    bad = 0
    for j in range(int(round(z1 / G)), int(round(z2 / G))):
        for i in range(int(round(x1 / G)), int(round(x2 / G))):
            if owner[j][i] is not None:
                if strict and owner[j][i] != 'PUB':
                    bad += 1
                continue
            owner[j][i] = tag
    return bad


hdr("① 几何自洽（栅格 0.1m）")
ov = 0
for r in PLAN["rooms"]:
    ov += fill(r["x1"], r["z1"], r["x2"], r["z2"], r["key"])
print(f"   房间重叠格子        : {ov}   {'✅' if ov == 0 else '❌'}")
pubhit = 0
for (x1, z1, x2, z2) in PLAN["public"]:
    pubhit += fill(x1, z1, x2, z2, "PUB")
lcx, lcz, lr = PLAN["lobby"]
pub_cells = set()
for (x1, z1, x2, z2) in PLAN["public"]:
    for j in range(int(round(z1 / G)), int(round(z2 / G))):
        for i in range(int(round(x1 / G)), int(round(x2 / G))):
            pub_cells.add((i, j))
for j in range(H):
    for i in range(W):
        if ((i + .5) * G - lcx) ** 2 + ((j + .5) * G - lcz) ** 2 <= lr * lr:
            pub_cells.add((i, j))
for (i, j) in pub_cells:
    if owner[j][i] is None:
        owner[j][i] = "PUB"
print(f"   公共区压房间格子    : {pubhit}   {'✅' if pubhit == 0 else '❌'}")
if ov or pubhit:
    fail += 1

# ══════════════ ② 门通向公共区
hdr("② 门通向公共区（门外 0.35m 探针）")
bad = []
for zid, z in Z.items():
    if not z["doorWall"]:
        print(f"   {zid:8s} 无门（开放式）—  跳过")
        continue
    w_, p_ = z["doorWall"], z["doorPos"]
    if w_ == "front":
        pr = (p_, z["cz"] + z["hd"] + 0.35)
    elif w_ == "back":
        pr = (p_, z["cz"] - z["hd"] - 0.35)
    elif w_ == "right":
        pr = (z["cx"] + z["hw"] + 0.35, p_)
    else:
        pr = (z["cx"] - z["hw"] - 0.35, p_)
    i, j = int(pr[0] / G), int(pr[1] / G)
    own = owner[j][i] if (0 <= i < W and 0 <= j < H) else None
    ok = own == "PUB"
    if not ok:
        bad.append(zid)
    print(f"   {zid:8s} {w_:5s} pos={p_:5.1f} → 探针{pr} = {own}   {'✅' if ok else '❌'}")
if bad:
    fail += 1

# ══════════════ ③ 门牌
hdr("③ 门牌不压门洞 / 不越出房间")
bad = []
for zid, z in Z.items():
    if not z["doorWall"]:
        continue
    gapW = 0.8
    dw, cx, cz, w_, d_, hw, hd = z["doorWall"], z["cx"], z["cz"], z["w"], z["d"], z["hw"], z["hd"]
    along = (z["doorPos"] - cx) if dw in ("front", "back") else (z["doorPos"] - cz)
    axisLen = w_ if dw in ("front", "back") else d_
    segA = (along - gapW / 2) + axisLen / 2
    segB = axisLen / 2 - (along + gapW / 2)
    segLen = max(segA, segB)
    segSign = -1 if segA >= segB else 1
    pw = min(2.8, max(1.6, segLen - 0.5))
    plqAt = along + segSign * (gapW / 2 + segLen / 2)
    lo, hi = plqAt - (pw + 0.14) / 2, plqAt + (pw + 0.14) / 2
    door_lo, door_hi = along - gapW / 2, along + gapW / 2
    hitdoor = lo < door_hi + 0.05 and hi > door_lo - 0.05
    outside = lo < -axisLen / 2 - 0.01 or hi > axisLen / 2 + 0.01
    ok = (not hitdoor) and (not outside)
    if not ok:
        bad.append(zid)
    print(f"   {zid:8s} {dw:5s} 牌宽{pw:.2f} 占[{lo:6.2f},{hi:6.2f}] 门洞[{door_lo:5.2f},{door_hi:5.2f}]"
          f" 墙半长{axisLen/2:.2f}   {'✅' if ok else '❌'}")
if bad:
    fail += 1

# ══════════════ ④ 家具边界 + 门洞迎面区
hdr("④ 家具不出房间 / 不压门洞")


def size_of(key, h, rs):
    nx, ny, nz = NATIVE[key]
    s = h / ny
    sx, sz = nx * s, nz * s
    if abs(math.cos(rs)) < 0.5:      # 旋转 ±90° → 交换
        sx, sz = sz, sx
    return sx, sz


bad = []
for zid, items in SHOW.items():
    z = Z[zid]
    x0r, x1r = z["cx"] - z["hw"], z["cx"] + z["hw"]
    z0r, z1r = z["cz"] - z["hd"], z["cz"] + z["hd"]
    # 门洞迎面区（门内 1.1m / 门外 0.3m，宽 = 门洞 + 0.5）
    if z["doorWall"]:
        gapW = 0.8
        if z["doorWall"] in ("front", "back"):
            sgn = 1 if z["doorWall"] == "front" else -1
            wall = z["cz"] + sgn * z["hd"]
            dz = (z["doorPos"] - gapW / 2 - 0.25, z["doorPos"] + gapW / 2 + 0.25)
            dz_ = (min(wall - sgn * 1.1, wall + sgn * 0.3), max(wall - sgn * 1.1, wall + sgn * 0.3))
            doorbox = (dz[0], dz_[0], dz[1], dz_[1])
        else:
            sgn = 1 if z["doorWall"] == "right" else -1
            wall = z["cx"] + sgn * z["hw"]
            dz = (z["doorPos"] - gapW / 2 - 0.25, z["doorPos"] + gapW / 2 + 0.25)
            dz_ = (min(wall - sgn * 1.1, wall + sgn * 0.3), max(wall - sgn * 1.1, wall + sgn * 0.3))
            doorbox = (dz_[0], dz[0], dz_[1], dz[1])
    else:
        doorbox = None
    for it in items:
        sx, sz = size_of(it["key"], it["h"], eval(it["r"].replace("Math.PI", str(math.pi))))
        ax0, ax1 = z["cx"] + it["x"] - sx / 2, z["cx"] + it["x"] + sx / 2
        az0, az1 = z["cz"] + it["z"] - sz / 2, z["cz"] + it["z"] + sz / 2
        probs = []
        if ax0 < x0r - 0.06 or ax1 > x1r + 0.06 or az0 < z0r - 0.06 or az1 > z1r + 0.06:
            probs.append("出房间")
        if doorbox and ax0 < doorbox[2] and ax1 > doorbox[0] and az0 < doorbox[3] and az1 > doorbox[1]:
            probs.append("压门洞")
        if probs:
            bad.append(f"{zid}.{it['key']}@({it['x']},{it['z']}) {'/'.join(probs)}")
    print(f"   {zid:8s} {len(items):2d} 件   {'✅' if not any(b.startswith(zid+'.') for b in bad) else '❌ ' + '; '.join(b for b in bad if b.startswith(zid+'.'))}")
if bad:
    fail += 1

# ══════════════ ⑤ 座向
hdr("⑤ 座向：主椅必须面朝办公桌")
print("   约定：exec_chair r=0 面朝 +Z；office_chair r=0 面朝 −Z")
bad = []
for zid, items in SHOW.items():
    desk = next((i for i in items if i["key"] == "exec_desk"), None)
    chair = next((i for i in items if i["key"] == "exec_chair"), None)
    if not (desk and chair):
        print(f"   {zid:8s} 无「主桌+主椅」组合 —  跳过")
        continue
    rs = eval(chair["r"].replace("Math.PI", str(math.pi)))
    fx, fz = math.sin(rs), math.cos(rs)               # exec_chair 朝向
    vx, vz = desk["x"] - chair["x"], desk["z"] - chair["z"]
    n = math.hypot(vx, vz) or 1
    dot = (fx * vx + fz * vz) / n
    ok = dot > 0.6
    if not ok:
        bad.append(zid)
    print(f"   {zid:8s} 椅({chair['x']:5.2f},{chair['z']:5.2f})→桌({desk['x']:5.2f},{desk['z']:5.2f})"
          f"  朝向({fx:.2f},{fz:.2f})  点积 {dot:+.2f}   {'✅' if ok else '❌ 背对桌子'}")
if bad:
    fail += 1

# ══════════════ ⑥ 记忆屏
hdr("⑥ 家具不与墙面记忆屏相交")


def mem_box(zid):
    z = Z[zid]
    st = MEM_STYLE[zid]
    if st == "whiteboard":
        dispW = min(2.6, z["w"] * 0.62)
        if zid == "cmo":
            cx_, cz_, zz = z["cx"], z["cz"] - z["hd"] + 0.6, None
        else:
            cx_, cz_ = z["cx"], z["cz"] + z["hd"] - 0.6
        y0, y1 = 0.0, 1.5 + dispW * 0.75 / 2 + 0.07
    else:
        dispW = min(3.0, z["w"] * 0.72)
        cz_ = z["cz"] - z["hd"] + 0.16 if z["doorWall"] != "back" else z["cz"] + z["hd"] - 0.16
        cx_ = z["cx"]
        y0, y1 = 1.5 - dispW * 0.75 / 2 - 0.07, 1.5 + dispW * 0.75 / 2 + 0.07
    return (cx_ - dispW / 2 - 0.07, cz_ - 0.16, cx_ + dispW / 2 + 0.07, cz_ + 0.16, y0, y1, st, dispW)


bad = []
for zid, items in SHOW.items():
    mx0, mz0, mx1, mz1, my0, my1, st, dispW = mem_box(zid)
    hits = []
    for it in items:
        sx, sz = size_of(it["key"], it["h"], eval(it["r"].replace("Math.PI", str(math.pi))))
        ax0, ax1 = Z[zid]["cx"] + it["x"] - sx / 2, Z[zid]["cx"] + it["x"] + sx / 2
        az0, az1 = Z[zid]["cz"] + it["z"] - sz / 2, Z[zid]["cz"] + it["z"] + sz / 2
        ay0, ay1 = FLOOR + it["y"], FLOOR + it["y"] + it["h"]
        if ax0 < mx1 and ax1 > mx0 and az0 < mz1 and az1 > mz0 and ay0 < my1 and ay1 > my0:
            hits.append(f"{it['key']}@({it['x']},{it['z']})")
    if hits:
        bad.append(zid)
    print(f"   {zid:8s} {st:10s} 板宽{dispW:.2f} @z={mz0+0.16:.2f} y[{my0:.2f},{my1:.2f}]   "
          f"{'✅' if not hits else '❌ ' + ', '.join(hits)}")
if bad:
    fail += 1

hdr("审计结论")
print(f"   {'✅ 六项全部通过' if fail == 0 else f'❌ 有 {fail} 项未通过'}")
sys.exit(1 if fail else 0)
