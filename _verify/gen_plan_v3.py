# -*- coding: utf-8 -*-
"""错落曲线式办公室平面图（方案 v3）—— 几何计算 + SVG + HTML 生成

设计要点（对齐参考图风格）：
  1. 拱形（曲线）公共走廊贯穿东西，中央膨大为一个圆形接待厅 —— 全程无直线长通道
  2. 南、北外墙均为弧面，两带进深沿 x 连续变化，且变化方向相反（北：中浅端深；南：中深端浅）
  3. 西侧入口内凹成门斗，东端走廊收头
  4. 8 间房全部独立开门向走廊；CMO 营销中心为独立房间（非公共区）
  5. 中央圆厅向南北各鼓出 1.6m，切进相邻四间房的内侧转角，形成弧形凹角

坐标：x 向东 0..28m，z 向南 0..22m（北 = z 小）
运行：python _verify/gen_plan_v3.py
"""
import math
import os

S = 32.0                       # px / m
OX, OY = 42.0, 40.0
CX, HALF = 14.0, 14.0          # 中轴 / 半宽


def T(x):
    return (x - CX) / HALF


# z(x) = Zc + (Ze - Zc) * t^2   t=(x-14)/14 → Zc=中轴处, Ze=两端处
Z_NC, Z_NE = 4.3, 3.2          # 北外墙：中部内凹(south)，两端外凸
Z_CNC, Z_CNE = 9.8, 12.5       # 走廊北界：中部向北拱 2.7m
Z_CSC, Z_CSE = 13.0, 15.7      # 走廊南界
Z_SC, Z_SE = 21.1, 20.2        # 南外墙：中部外凸(south)

HALL_R, HALL_CZ = 3.2, 11.4    # 中央圆形接待厅（圆心落在走廊中线上）
XW = 2.5                       # 走廊西端 / 门斗内沿
STEP = 0.12

NORTH_ROOMS = [("CRO", 0.0, 6.0), ("CTO", 6.0, 13.0),
               ("CPO", 13.0, 20.0), ("CMO", 20.0, 28.0)]
SOUTH_ROOMS = [("CFO", 0.0, 6.0), ("COO", 6.0, 13.0),
               ("CEO", 13.0, 20.5), ("MT", 20.5, 28.0)]

META = {
    "CRO": ("CRO 风控中心", "风控 · 合规 · 授信"),
    "CTO": ("CTO 技术中心", "研发 · 数据 · 运维"),
    "CPO": ("CPO 产品设计室", "产品设计 · 打样"),
    "CMO": ("CMO 营销中心", "市场 · 品牌 · 内容"),
    "CFO": ("CFO 财务中心", "财务 · 资金 · 税务"),
    "COO": ("COO 运营中心", "订单 · 履约 · 客服"),
    "CEO": ("CEO 战略办公室", "战略决策 · 接待"),
    "MT":  ("战略会议室", "高管会 · 评审"),
}
DOOR_X = {"CRO": 3.3, "CTO": 9.6, "CPO": 18.4, "CMO": 24.0,
          "CFO": 3.3, "COO": 9.6, "CEO": 18.0, "MT": 24.0}


def z_north(x):
    return Z_NC + (Z_NE - Z_NC) * T(x) ** 2


def z_south(x):
    return Z_SC + (Z_SE - Z_SC) * T(x) ** 2


def z_corn(x):
    return Z_CNC + (Z_CNE - Z_CNC) * T(x) ** 2


def z_cors(x):
    return Z_CSC + (Z_CSE - Z_CSC) * T(x) ** 2


Z_PN = z_corn(XW)
Z_PS = z_cors(XW)


def z_hall_u(x):
    d = HALL_R * HALL_R - (x - CX) ** 2
    return HALL_CZ - math.sqrt(d) if d > 0 else None


def z_hall_d(x):
    d = HALL_R * HALL_R - (x - CX) ** 2
    return HALL_CZ + math.sqrt(d) if d > 0 else None


def zS_north(x):
    z = Z_PN if x <= XW else z_corn(x)
    zu = z_hall_u(x)
    return zu if (zu is not None and zu < z) else z


def zN_south(x):
    z = Z_PS if x <= XW else z_cors(x)
    zd = z_hall_d(x)
    return zd if (zd is not None and zd > z) else z


def frange(a, b, step):
    out, v = [], a
    while v < b - 1e-9:
        out.append(v)
        v += step
    out.append(b)
    return out


def px(x):
    return OX + x * S


def py(z):
    return OY + z * S


def poly_north(xL, xR):
    xs = frange(xL, xR, STEP)
    pts = [(x, z_north(x)) for x in xs]
    pts.append((xR, zS_north(xR)))
    pts += [(x, zS_north(x)) for x in reversed(xs)]
    return pts


def poly_south(xL, xR):
    xs = frange(xL, xR, STEP)
    pts = [(x, zN_south(x)) for x in xs]
    pts.append((xR, z_south(xR)))
    pts += [(x, z_south(x)) for x in reversed(xs)]
    return pts


def area_of(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        a += x1 * z2 - x2 * z1
    return abs(a) / 2.0


def path_of(pts):
    d = "M%.1f,%.1f" % (px(pts[0][0]), py(pts[0][1]))
    for x, z in pts[1:]:
        d += "L%.1f,%.1f" % (px(x), py(z))
    return d + "Z"


def polyline(pts):
    d = "M%.1f,%.1f" % (px(pts[0][0]), py(pts[0][1]))
    for x, z in pts[1:]:
        d += "L%.1f,%.1f" % (px(x), py(z))
    return d


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


rooms = {}
order = []
for name, xL, xR in NORTH_ROOMS:
    pts = poly_north(xL, xR)
    rooms[name] = dict(pts=pts, area=area_of(pts), c=centroid(pts), xL=xL, xR=xR,
                       ztop=z_north, zbot=zS_north)
    order.append(name)
for name, xL, xR in SOUTH_ROOMS:
    pts = poly_south(xL, xR)
    rooms[name] = dict(pts=pts, area=area_of(pts), c=centroid(pts), xL=xL, xR=xR,
                       ztop=zN_south, zbot=z_south)
    order.append(name)

print("=== 房间 ===")
for n in order:
    r = rooms[n]
    ds = [r["zbot"](x) - r["ztop"](x) for x in frange(r["xL"] + 0.05, r["xR"] - 0.05, 0.05)]
    print("%-4s %6.1f m2   宽 %.1f m   进深 %.2f ~ %.2f m" %
          (n, r["area"], r["xR"] - r["xL"], min(ds), max(ds)))


def band_area(zb, zt, x0, x1):
    xs = frange(x0, x1, 0.05)
    return sum(((zt(xs[i]) - zb(xs[i])) + (zt(xs[i + 1]) - zb(xs[i + 1]))) * 0.5
               * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))


cor_band = band_area(z_corn, z_cors, XW, 28.0)
cut = 0.0
for xa in frange(CX - HALL_R, CX + HALL_R, 0.05):
    yu, yd = z_hall_u(xa), z_hall_d(xa)
    if yu is None:
        continue
    if yu < z_corn(xa):
        cut += (z_corn(xa) - yu) * 0.05
    if yd > z_cors(xa):
        cut += (yd - z_cors(xa)) * 0.05

tot = sum(r["area"] for r in rooms.values())
zs = [z_south(x) for x in frange(0, 28, 0.1)] + [z_north(x) for x in frange(0, 28, 0.1)]
env = 28.0 * (max(zs) - min(zs))
print("房间合计   : %.1f m2" % tot)
print("走廊 %0.1f + 圆厅外扩 %.1f = 公共 %.1f m2" % (cor_band, cut, cor_band + cut))
print("室内合计   : %.1f m2" % (tot + cor_band + cut))
print("包络       : 28.0 x %.2f = %.1f m2   占地率 %.1f%%"
      % (max(zs) - min(zs), env, 100 * (tot + cor_band + cut) / env))


def desk_rects(r, w=1.4, d=0.7, gap=1.62, margin=1.0):
    """返回 (x, z, w, d, dir) 工位矩形；进深足够时排两排"""
    mid = (r["xL"] + r["xR"]) / 2
    depth = r["zbot"](mid) - r["ztop"](mid)
    rows = [0.5] if depth < 5.4 else [0.34, 0.66]
    out, x = [], r["xL"] + margin
    while x + w <= r["xR"] - margin + 1e-6:
        xc = x + w / 2
        top, bot = r["ztop"](xc), r["zbot"](xc)
        if bot - top >= d + 1.5:
            for fr in rows:
                zc = top + (bot - top) * fr
                out.append((xc - w / 2, zc - d / 2, w, d, -1 if fr < 0.5 else 1))
        x += gap
    return out


def furn_svg():
    out = []
    for n in order:
        r = rooms[n]
        if n == "MT":
            mx = (r["xL"] + r["xR"]) / 2
            zc = (zN_south(mx) + z_south(mx)) / 2
            tw, td = 4.4, 1.3
            out.append('<rect class="furn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/>'
                       % (px(mx - tw / 2), py(zc - td / 2), tw * S, td * S, 0.6 * S))
            for k in range(5):
                cx = mx - tw / 2 + 0.6 + k * (tw - 1.2) / 4
                for s in (-1, 1):
                    out.append('<rect class="furn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
                               % (px(cx - 0.24), py(zc + s * (td / 2 + 0.16)), 0.48 * S, 0.48 * S))
            continue
        for (x, z, w, d, dr) in desk_rects(r):
            out.append('<rect class="furn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2.5"/>'
                       % (px(x), py(z), w * S, d * S))
            cxx = x + w / 2
            czz = z + d / 2 + dr * 0.56
            out.append('<rect class="furn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.5" '
                       'opacity=".75"/>'
                       % (px(cxx - 0.24), py(czz - 0.24), 0.48 * S, 0.48 * S))
    return "".join(out)
    mid = (r["xL"] + r["xR"]) / 2
    depth = r["zbot"](mid) - r["ztop"](mid)
    rows = [0.5] if depth < 5.4 else [0.34, 0.66]
    out, x = [], r["xL"] + margin
    while x + w <= r["xR"] - margin + 1e-6:
        xc = x + w / 2
        top, bot = r["ztop"](xc), r["zbot"](xc)
        if bot - top >= d + 1.5:
            for fr in rows:
                zc = top + (bot - top) * fr
                out.append((xc - w / 2, zc - d / 2, w, d, -1 if fr < 0.5 else 1))
        x += gap
    return out


def d_wall():
    xs = frange(0, 28, 0.15)
    d = polyline([(x, z_north(x)) for x in xs])
    d += "L" + polyline([(x, z_south(x)) for x in reversed(xs)])[1:]
    d += "L%.1f,%.1fL%.1f,%.1fL%.1f,%.1fL%.1f,%.1fZ" % (
        px(0), py(Z_PS), px(XW), py(Z_PS), px(XW), py(Z_PN), px(0), py(Z_PN))
    return d


def d_corridor():
    xs = frange(XW, 28, 0.15)
    d = polyline([(x, z_corn(x)) for x in xs])
    d += "L" + polyline([(x, z_cors(x)) for x in reversed(xs)])[1:]
    return d + "Z"


def doors_svg():
    out = []
    for name, xd in DOOR_X.items():
        north = name in ("CRO", "CTO", "CPO", "CMO")
        zd = zS_north(xd) if north else zN_south(xd)
        zf = zS_north if north else zN_south
        ang = math.degrees(math.atan2(zf(xd + 0.05) - zf(xd - 0.05), 0.1))
        cxp, cyp = px(xd), py(zd)
        sgn = -1 if north else 1
        out.append('<rect class="gap" x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                   'transform="rotate(%.2f %.1f %.1f)"/>'
                   % (cxp - 0.55 * S, cyp - 0.13 * S, 1.1 * S, 0.26 * S, ang, cxp, cyp))
        hx = cxp - 0.55 * S * math.cos(math.radians(ang))
        hy = cyp - 0.55 * S * math.sin(math.radians(ang))
        out.append('<path class="leaf" d="M%.1f,%.1f L%.1f,%.1f"/>'
                   % (hx, hy, hx, hy + sgn * 0.95 * S))
        out.append('<path class="swing" d="M%.1f,%.1f A%.1f,%.1f 0 0 %d %.1f,%.1f"/>'
                   % (hx, hy + sgn * 0.95 * S, 0.95 * S, 0.95 * S, 1 if sgn > 0 else 0,
                      cxp + 0.55 * S * math.cos(math.radians(ang)),
                      cyp + 0.55 * S * math.sin(math.radians(ang))))
    out.append('<path class="leaf" d="M%.1f,%.1f L%.1f,%.1f"/>'
               % (px(XW), py(Z_PN), px(XW), py(Z_PS)))
    return "".join(out)


svg = ['<svg viewBox="0 0 1000 790" width="100%" xmlns="http://www.w3.org/2000/svg" '
       'font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">']
svg.append('<style>'
           '.wall{fill:none;stroke:var(--wall);stroke-width:2.4;stroke-linejoin:round}'
           '.room{stroke-width:1.1;stroke-linejoin:round}'
           '.hall{fill:var(--hall);stroke:var(--hall-line);stroke-width:1}'
           '.core{fill:var(--core);stroke:var(--core-line);stroke-width:1.4}'
           '.furn{fill:var(--furn);stroke:var(--furnL);stroke-width:.6}'
           '.gap{fill:var(--hall)}'
           '.plate{fill:var(--plate);opacity:.86}'
           '.leaf{stroke:var(--leaf);stroke-width:1.2;fill:none;stroke-linecap:round}'
           '.swing{stroke:var(--leaf);stroke-width:.6;fill:none;opacity:.55}'
           '.t1{font-size:13px;font-weight:600;fill:var(--ink)}'
           '.t2{font-size:10.5px;fill:var(--ink2)}'
           '.lb{font-size:11px;fill:var(--ink2)}'
           '</style>')

for n in order:
    svg.append('<path class="room" d="%s" style="fill:var(--%s);stroke:var(--%sL)"/>'
               % (path_of(rooms[n]["pts"]), n.lower(), n.lower()))
svg.append('<path class="hall" d="%s"/>' % d_corridor())
svg.append('<circle class="core" cx="%.1f" cy="%.1f" r="%.1f"/>'
           % (px(CX), py(HALL_CZ), HALL_R * S))

svg.append(furn_svg())

svg.append('<rect class="furn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>'
           % (px(CX - 1.6), py(HALL_CZ - 2.1), 3.2 * S, 0.65 * S))
svg.append('<circle class="furn" cx="%.1f" cy="%.1f" r="%.1f"/>'
           % (px(CX + 0.1), py(HALL_CZ + 1.15), 0.85 * S))
for k in range(6):
    a = math.radians(k * 60 + 15)
    svg.append('<circle class="furn" cx="%.1f" cy="%.1f" r="%.1f"/>'
               % (px(CX + 0.1 + 1.45 * math.cos(a)), py(HALL_CZ + 1.15 + 1.45 * math.sin(a)), 0.3 * S))

svg.append('<path class="wall" d="%s"/>' % d_wall())
svg.append(doors_svg())

for n in order:
    t1, t2 = META[n]
    mid = (rooms[n]["xL"] + rooms[n]["xR"]) / 2
    dep = rooms[n]["zbot"](mid) - rooms[n]["ztop"](mid)
    cxp = px(mid)
    cyp = py((rooms[n]["ztop"](mid) + rooms[n]["zbot"](mid)) / 2)
    svg.append('<rect class="plate" x="%.1f" y="%.1f" width="118" height="46" rx="7"/>'
               % (cxp - 59, cyp - 20))
    svg.append('<text class="t1" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
               % (cxp, cyp - 5, t1))
    svg.append('<text class="t2" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
               % (cxp, cyp + 10, t2))
    svg.append('<text class="t2" x="%.1f" y="%.1f" text-anchor="middle">%.1f×%.1fm · %.1f㎡</text>'
               % (cxp, cyp + 24, rooms[n]["xR"] - rooms[n]["xL"], dep, rooms[n]["area"]))
svg.append('<text class="t1" x="%.1f" y="%.1f" text-anchor="middle" style="fill:var(--coreT)">'
           '中央接待厅</text>' % (px(CX), py(HALL_CZ - 0.62)))
svg.append('<text class="lb" x="%.1f" y="%.1f" text-anchor="middle" style="fill:var(--coreT)">'
           '洽谈 · 茶水 · 动线枢纽</text>' % (px(CX), py(HALL_CZ + 3.15)))
svg.append('<text class="lb" x="%.1f" y="%.1f" text-anchor="middle">入口</text>'
           % (px(1.25), py(11.12)))
svg.append('</svg>')
SVG = "".join(svg)

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>错落曲线式办公室平面图 · 8 部门</title>
<style>
:root{
--bg:#F7F6F2;--ink:#1E1E1C;--ink2:#6E6E68;--wall:#3C3C39;--line:#DCD9D0;
--hall:#EDE7D8;--hall-line:#C6BBA1;--core:#E1D6BE;--core-line:#B9A97F;--coreT:#5A4A28;
--furn:rgba(255,255,255,.72);--furnL:rgba(0,0,0,.16);--leaf:#4A4A46;--plate:#FDFCFA;
--cro:#F5C6C6;--croL:#A32D2D;--coo:#D6D4CB;--cooL:#5F5E5A;
--mt:#D2CFF7;--mtL:#534AB7;--cpo:#F8CDBD;--cpoL:#993C1D;
--cmo:#FBD08A;--cmoL:#854F0B;--cto:#C9E3A5;--ctoL:#3B6D11;
--ceo:#C0DAF6;--ceoL:#185FA5;--cfo:#ADDFCE;--cfoL:#0F6E56;
}
body.dark{
--bg:#191A1C;--ink:#EDEDEA;--ink2:#9C9C96;--wall:#DADAD4;--line:#3A3B3E;
--hall:#33302A;--hall-line:#5C5648;--core:#3E392D;--core-line:#6E6450;--coreT:#D8CBAB;
--furn:rgba(255,255,255,.16);--furnL:rgba(255,255,255,.22);--leaf:#C9C9C3;--plate:#232427;
--cro:#5B2222;--croL:#F09595;--coo:#3A3A37;--cooL:#B4B2A9;
--mt:#2E2A6B;--mtL:#AFA9EC;--cpo:#5A2410;--cpoL:#F0997B;
--cmo:#5C3B0E;--cmoL:#EF9F27;--cto:#223F0B;--ctoL:#97C459;
--ceo:#0E3B69;--ceoL:#85B7EB;--cfo:#0A4A38;--cfoL:#5DCAA5;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;padding:28px 32px 40px;transition:background .2s}
h1{font-size:19px;font-weight:600;margin:0 0 6px}
.sub{font-size:13px;color:var(--ink2);margin:0 0 20px;line-height:1.7}
.card{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:18px}
.legend{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:12.5px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:7px;
vertical-align:-1px;border:1px solid rgba(0,0,0,.18)}
.notes{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px 26px;
font-size:12.5px;line-height:1.8;color:var(--ink2)}
.notes b{color:var(--ink);font-weight:600}
button{font-size:12px;padding:6px 12px;border-radius:8px;border:1px solid var(--line);
background:var(--bg);color:var(--ink2);cursor:pointer;font-family:inherit;float:right}
</style></head><body>
<button onclick="document.body.classList.toggle('dark')">明 / 暗</button>
<h1>错落曲线式办公室平面图 · 8 部门</h1>
<p class="sub">拱形走廊贯通东西 + 中央圆形接待厅 · 南北外墙均为弧面 · 8 间房全部独立开门 · 无直线长通道 ·
包络 28.0 × 17.9m</p>
<div class="card">%s</div>
<div class="card legend">
<span><i style="background:var(--cro)"></i>CRO 风控中心</span>
<span><i style="background:var(--coo)"></i>COO 运营中心</span>
<span><i style="background:var(--mt)"></i>战略会议室</span>
<span><i style="background:var(--cpo)"></i>CPO 产品设计室</span>
<span><i style="background:var(--cmo)"></i>CMO 营销中心</span>
<span><i style="background:var(--cto)"></i>CTO 技术中心</span>
<span><i style="background:var(--ceo)"></i>CEO 战略办公室</span>
<span><i style="background:var(--cfo)"></i>CFO 财务中心</span>
<span><i style="background:var(--hall)"></i>公共走廊 / 中央接待厅</span>
</div>
<div class="card notes">
<div><b>错落在哪里</b><br>
① 南北外墙都是弧面：北墙中部内凹、南墙中部外凸，于是<b>北带进深「中间浅两端深」(5.5→9.3m)，南带正好相反 (8.1→4.5m)</b>；<br>
② 中央圆厅向南北各鼓出 1.6m，切进 CTO / CPO / COO / CEO 四间房的内侧转角，形成弧形凹角；<br>
③ 北侧分界 x=6 / 13 / 20 与南侧 x=6 / 13 / 20.5 错开，8 间房面积 36.0 ~ 60.3㎡ 不等；<br>
④ 西侧入口内退 2.5m 成门斗，东端走廊收头。</div>
<div><b>有序在哪里</b><br>
① 房间主体仍是直边矩形（只有内侧带弧角），工位、家具照常排布；<br>
② 一条走廊串起全部 8 间房，无穿套、无暗房；<br>
③ 中央接待厅是全楼唯一枢纽，访客不穿越任何办公区；<br>
④ CEO 与会议室相邻，决策动线最短；CTO / COO 上下对位，技术与运营呼应。</div>
</div>
</body></html>
""" % SVG

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "平面图方案-错落曲线版.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("已生成:", out)
