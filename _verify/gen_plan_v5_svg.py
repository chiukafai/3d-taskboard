# -*- coding: utf-8 -*-
"""平面图 v5 渲染：读 plan_v5.json → 「走廊加宽 + 过道清障」方案图（明/暗双主题）"""
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "plan_v5.json"), encoding="utf-8"))

S = 27.5
PL, PT, PR, PB = 104, 150, 296, 210
EX, EZ = D["envelope"]
VW, VH = PL + EX * S + PR, PT + EZ * S + PB


def px(x):
    return round(PL + x * S, 1)


def py(z):
    return round(PT + z * S, 1)


svg = []
A = svg.append


def rect(x1, z1, x2, z2, cls, rx=0, extra=""):
    A('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"%s%s/>'
      % (cls, px(x1), py(z1), (x2 - x1) * S, (z2 - z1) * S,
         ' rx="%d"' % rx if rx else "", extra))


def txt(x, z, s, cls, anchor="start", dy=0, rot=None):
    if rot is None:
        A('<text class="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
          % (cls, px(x), py(z) + dy, anchor, s))
    else:
        A('<text class="%s" transform="rotate(%.0f %.1f %.1f)" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
          % (cls, rot, px(x), py(z), px(x), py(z) + dy, anchor, s))


# ---------- 场地底：包络 + 室外 ----------
A('<g id="site">')
A('<rect class="env" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
  % (px(0), py(0), EX * S, EZ * S))
# 建筑外（北侧退台留白）
rect(6.6, 0.0, 9.4, 5.6, "slit")
rect(9.4, 0.0, 15.6, 3.6, "slit")
rect(23.8, 0.0, 29.6, 1.6, "slit")
rect(29.4, 8.2, 29.6, 12.4, "slit")
# 室外场地（保留景观）
rect(0.0, 0.0, 6.6, 5.6, "court")
rect(26.2, 12.6, 29.6, 19.0, "garden")
A('<circle class="tree" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(1.7), py(1.15), 0.9 * S))
A('<circle class="tree" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(1.7), py(3.05), 0.9 * S))
A('<circle class="tree" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(3.7), py(2.10), 0.55 * S))
A('<circle class="tree" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(27.05), py(14.4), 0.8 * S))
A('<circle class="tree" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(27.05), py(17.4), 0.8 * S))
A('</g>')

# ---------- 公共空间（走廊 / 支廊）----------
A('<g id="public">')
for (x1, z1, x2, z2) in D["public"]:
    rect(x1, z1, x2, z2, "pub")
cx, cz, r = D["lobby"]
# 圆厅：仅保留地面铺装（家具已清零）
A('<circle class="hallfloor" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), r * S))
A('<circle class="hallring" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), r * S))
A('<circle class="hallring2" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), r * S * 0.45))
# 已清空标记
for i in range(4):
    ang = math.pi / 4 + i * math.pi / 2
    ax, az = cx + r * 0.68 * math.cos(ang), cz + r * 0.68 * math.sin(ang)
    A('<path class="clearmark" d="M%.1f,%.1f l-5,-5 m5,5 l5,-5 m-5,5 l0,-8"/>'
      % (px(ax), py(az)))
A('</g>')

# ---------- v4 原墙线参考（虚线）----------
A('<g id="v4ref">')
def dash_h(z, x1, x2):
    A('<line class="v4ln" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (px(x1), py(z), px(x2), py(z)))


def dash_v(x, z1, z2):
    A('<line class="v4ln" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (px(x), py(z1), px(x), py(z2)))


dash_h(8.6, 9.4, 29.4)      # v4 主廊北墙
dash_h(11.6, 7.4, 19.4)     # v4 主廊南墙（西段）
dash_v(10.2, 11.6, 21.6)    # v4 西支廊东墙
A('<circle class="v4circ" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), 1.9 * S))
A('<rect class="v4void" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
  % (px(10.2), py(13.0), 1.2 * S, 6.4 * S))
A('</g>')

# ---------- 房间 ----------
A('<g id="rooms">')
for rm in D["rooms"]:
    A('<rect class="room" x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
      'style="fill:%s;stroke:%s"/>'
      % (px(rm["x1"]), py(rm["z1"]), rm["w"] * S, rm["d"] * S, rm["color"], rm["color"]))
A('</g>')

# ---------- 家具（房间内，示意）----------
furn = []
for rm in D["rooms"]:
    x1, z1, x2, z2 = rm["x1"], rm["z1"], rm["x2"], rm["z2"]
    if rm["key"] == "MT":
        tw, td = 3.1, 1.15
        tcx, tcz = (x1 + x2) / 2, (z1 + z2) / 2
        furn.append('<rect class="tb" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3"/>'
                    % (px(tcx - tw / 2), py(tcz - td / 2), tw * S, td * S))
        for i in range(5):
            cxx = tcx - tw / 2 + 0.42 + i * (tw - 0.84) / 4
            for sgn in (-1, 1):
                furn.append('<rect class="ch" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
                            % (px(cxx - 0.24), py(tcz + sgn * (td / 2 + 0.18) - 0.24), .48 * S, .48 * S))
        continue
    dw, dd, gap = 1.5, 0.72, 1.68
    inner = rm["w"] - 2 * 0.85
    n = max(1, int(inner // gap))
    rowspan = n * gap - (gap - dw)
    x0 = (x1 + x2) / 2 - rowspan / 2
    deep = rm["d"] - 2 * 0.95
    rows = [(z1 + z2) / 2] if deep < 4.2 else [z1 + 1.0 + dd / 2 + 0.55, z2 - 1.0 - dd / 2 - 0.55]
    for k, rz in enumerate(rows):
        for i in range(n):
            dx = x0 + i * gap
            furn.append('<rect class="desk" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
                        % (px(dx), py(rz - dd / 2), dw * S, dd * S))
            cs = 0.44
            cy = rz + (dd / 2 + 0.16 if k == 0 else -dd / 2 - 0.16)
            furn.append('<rect class="ch" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
                        % (px(dx + dw / 2 - cs / 2), py(cy - cs / 2), cs * S, cs * S))
A('<g id="furn">' + "".join(furn) + '</g>')

# ---------- 墙 / 外轮廓 ----------
A('<g id="walls">')
for run in D["runs"]:
    k = run["k"] * 0.1
    if run["o"] == "h":
        A('<line class="wall" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
          % (px(run["s"] * .1), py(k), px(run["e"] * .1), py(k)))
    else:
        A('<line class="wall" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
          % (px(k), py(run["s"] * .1), px(k), py(run["e"] * .1)))
A('</g>')

# ---------- 门 ----------
A('<g id="doors">')
for (k, wall, coord, pos) in D["doors"]:
    dw = 1.0
    if wall in ("S", "N"):
        A('<rect class="gap" x="%.1f" y="%.1f" width="%.1f" height="7"/>'
          % (px(pos - dw / 2), py(coord) - 3.5, dw * S))
        sgn = -1 if wall == "S" else 1
        hx, hz = pos - dw / 2, coord
        A('<line class="leaf" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
          % (px(hx), py(hz), px(hx), py(hz + sgn * dw)))
        A('<path class="swing" d="M%.1f,%.1f A%.1f,%.1f 0 0 %d %.1f,%.1f"/>'
          % (px(pos + dw / 2), py(coord), dw * S, dw * S, 1 if sgn < 0 else 0,
             px(hx), py(hz + sgn * dw)))
    else:
        A('<rect class="gap" x="%.1f" y="%.1f" width="7" height="%.1f"/>'
          % (px(coord) - 3.5, py(pos - dw / 2), dw * S))
        A('<line class="leaf" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
          % (px(coord), py(pos - dw / 2), px(coord + dw), py(pos - dw / 2)))
        A('<path class="swing" d="M%.1f,%.1f A%.1f,%.1f 0 0 %d %.1f,%.1f"/>'
          % (px(coord), py(pos + dw / 2), dw * S, dw * S, 0,
             px(coord + dw), py(pos - dw / 2)))
ex, ez = D["entry"]
A('<rect class="gap" x="%.1f" y="%.1f" width="%.1f" height="8"/>' % (px(ex - 0.9), py(ez) - 4, 1.8 * S))
A('<path class="entryarrow" d="M%.1f,%.1f L%.1f,%.1f"/>' % (px(ex), py(ez - 3.6), px(ex), py(ez - 0.9)))
A('<path class="arrowhead" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>'
  % (px(ex), py(ez - 0.2), px(ex - 0.26), py(ez - 1.1), px(ex + 0.26), py(ez - 1.1)))
A('</g>')

# ---------- 过道清障标记（编号 1~9，图例见右侧面板） ----------
CLEARS = [
    (1, 9.40, 11.95, "接待台 + 台面屏 + 杯/笔筒"),
    (2, 9.40, 12.70, "访客椅"),
    (3, 7.88, 10.55, "等候长椅（西弧）"),
    (4, 10.92, 10.55, "等候长椅（东弧）"),
    (5, 9.40, 10.65, "中心花坛 + 绿植"),
    (6, 8.45, 9.55, "贝壳喷泉"),
    (7, 10.35, 9.55, "贝壳罐"),
    (8, 12.60, 10.10, "主廊缆绳卷（西）"),
    (9, 23.40, 10.10, "主廊缆绳卷（东）"),
]
A('<g id="clears">')
for (n, x, z, _lab) in CLEARS:
    A('<circle class="clrC" cx="%.1f" cy="%.1f" r="9"/>' % (px(x), py(z)))
    A('<text class="clrN" x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (px(x), py(z) + 4, n))
A('</g>')

# ---------- 房间标注 ----------
A('<g id="labels">')
for rm in D["rooms"]:
    x1, z1 = rm["x1"], rm["z1"]
    bw = min(rm["w"] - 1.0, 6.4)
    A('<rect class="chip" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>'
      % (px(x1 + 0.5), py(z1 + 0.45), bw * S, 2.5 * S))
    A('<text class="rEN" x="%.1f" y="%.1f">%s</text>' % (px(x1 + 0.85), py(z1 + 1.12), rm["key"]))
    A('<text class="rCN" x="%.1f" y="%.1f">%s</text>' % (px(x1 + 0.85), py(z1 + 1.72), rm["cn"]))
    A('<text class="rSZ" x="%.1f" y="%.1f">%.1f×%.1fm · %.1f㎡</text>'
      % (px(x1 + 0.85), py(z1 + 2.35), rm["w"], rm["d"], rm["area"]))
A('</g>')

# ---------- 走廊净宽尺寸标注 ----------
A('<g id="corrdim">')
wmain = D["widths"]["16.0"]
# 主廊：在 x=14.0 处量 8.2→12.4
A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(14.0), py(8.2), px(14.0), py(12.4)))
for zz in (8.2, 12.4):
    A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
      % (px(13.75), py(zz), px(14.25), py(zz)))
A('<rect class="wtag" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3"/>'
  % (px(11.9) + 6, py(10.3) - 11, 76, 22))
A('<text class="wtagt" x="%.1f" y="%.1f">净宽 %.1f m</text>' % (px(11.9) + 10, py(10.3) + 4, wmain))
# 西支廊：在 z=15.4 处量 7.4→11.4
A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(7.4), py(15.4), px(11.4), py(15.4)))
for xx in (7.4, 11.4):
    A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
      % (px(xx), py(15.15), px(xx), py(15.65)))
A('<text class="dimwt2" x="%.1f" y="%.1f" text-anchor="middle">西支廊 净宽 %.1f m</text>'
  % ((px(7.4) + px(11.4)) / 2, py(16.2), D["west_widths"]["14.0"]))
# 西支廊下段
A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(8.6), py(20.2), px(11.4), py(20.2)))
for xx in (8.6, 11.4):
    A('<line class="dimw" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
      % (px(xx), py(19.95), px(xx), py(20.45)))
A('<text class="dimwt2" x="%.1f" y="%.1f" text-anchor="middle">%.1f m</text>'
  % ((px(8.6) + px(11.4)) / 2, py(20.95), D["west_widths"]["20.0"]))
A('</g>')

# ---------- 公共空间标注 ----------
A('<g id="notes">')
txt(4.7, 2.6, "入口前庭", "site")
txt(4.7, 3.5, "6.6×5.6m（室外）", "site2")
txt(28.5, 15.8, "东南侧院 3.4×6.4m", "site", "middle", 0, -90)
txt(19.5, 10.32, "东西主廊 净宽 4.2m", "pub1b", "middle")
A('<line class="leader" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(cx), py(cz + r + 0.1), px(cx), py(cz + r + 0.5)))
txt(9.4, 13.5, "接待圆厅 Ø3.0m（已清空）", "pub2", "middle")
txt(ex, ez - 4.3, "主入口", "entry", "middle")
A('<path class="entryarrow" d="M%.1f,%.1f L%.1f,%.1f"/>' % (px(29.4), py(10.5), px(30.6), py(10.5)))
A('<path class="arrowhead" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>'
  % (px(31.4), py(10.5), px(30.4), py(10.18), px(30.4), py(10.82)))
txt(29.0, 9.3, "次出口·疏散口", "entry", "end")
A('</g>')

# ---------- 尺寸线 ----------
A('<g id="dims">')
A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (px(0), PT - 34, px(EX), PT - 34))
A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (PL - 34, py(0), PL - 34, py(EZ)))
for xx in (0, EX):
    A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (px(xx), PT - 40, px(xx), PT - 28))
for zz in (0, EZ):
    A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (PL - 40, py(zz), PL - 28, py(zz)))
A('<text class="dimtxt" x="%.1f" y="%.1f" text-anchor="middle">29.6 m（包络不变）</text>' % (px(EX / 2), PT - 40))
A('<text class="dimtxt" transform="rotate(-90 %.1f %.1f)" x="%.1f" y="%.1f" text-anchor="middle">21.6 m（包络不变）</text>'
  % (PL - 42, py(EZ / 2), PL - 42, py(EZ / 2)))
A('<text class="dimnote" x="%.1f" y="%.1f">外轮廓 / 退台 / 房间外墙一律不动 —— 只改室内交通：主廊净宽 3.0→4.2m、西支廊 1.6→2.8~4.0m</text>'
  % (px(0), PT - 58))
A('</g>')

# ---------- 指北针 / 比例尺 ----------
A('<g id="compass">')
nx, nz = PL + EX * S - 34, PT - 70
A('<circle class="cmp" cx="%.1f" cy="%.1f" r="19"/>' % (nx, nz))
A('<path class="cmpn" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>' % (nx, nz - 15, nx - 6, nz + 8, nx + 6, nz + 8))
A('<text class="cmpn2" x="%.1f" y="%.1f" text-anchor="middle">N</text>' % (nx, nz + 22))
bx, bz = PL, VH - 52
A('<g id="scalebar">')
for i in range(5):
    A('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="9"/>'
      % ("sb1" if i % 2 == 0 else "sb2", bx + i * 2 * S, bz, 2 * S))
A('<text class="sb" x="%.1f" y="%.1f">0</text>' % (bx - 4, bz + 24))
A('<text class="sb" x="%.1f" y="%.1f" text-anchor="middle">5</text>' % (bx + 5 * S, bz + 24))
A('<text class="sb" x="%.1f" y="%.1f" text-anchor="end">10 m</text>' % (bx + 10 * S + 6, bz + 24))
A('</g></g>')

# ---------- 图例面板 ----------
lx = PL + EX * S + 66
V4ROOM = {"CPO": 35.6, "MT": 34.6, "CFO": 33.3, "CRO": 31.0, "CMO": 70.5,
          "CTO": 40.6, "COO": 62.4, "CEO": 43.6}
A('<g id="panel">')
A('<rect class="panel" x="%.1f" y="%.1f" width="230" height="%.1f" rx="8"/>'
  % (lx - 12, PT - 70, EZ * S + 118))
A('<text class="pTitle" x="%.1f" y="%.1f">① 走廊加宽（净宽实测）</text>' % (lx, PT - 46))
yy = PT - 22
for lab, v4, v5 in (("东西主廊（南北向）", "3.0 m", "4.2 m"), ("西支廊上段（东西向）", "2.8 m", "4.0 m"),
                    ("西支廊下段（东西向）", "1.6 m", "2.8 m"), ("入口过渡进深", "3.0 m", "2.6 m")):
    A('<text class="pItem" x="%.1f" y="%.1f">%s</text>' % (lx, yy, lab))
    A('<text class="pOld" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (lx + 128, yy, v4))
    A('<text class="pNew" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (lx + 206, yy, v5))
    yy += 21
A('<text class="pNote" x="%.1f" y="%.1f">灰=原值 · 绿=新值</text>' % (lx, yy)); yy += 15
A('<line class="v4ln" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (lx, yy - 4, lx + 26, yy - 4))
A('<text class="pNote" x="%.1f" y="%.1f">红色虚线 = v4 原墙线</text>' % (lx + 32, yy)); yy += 15
A('<text class="pNote" x="%.1f" y="%.1f">虚线与新墙线之间 = 加宽出来的面积</text>' % (lx, yy)); yy += 15
A('<line class="pDiv" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (lx, yy - 6, lx + 206, yy - 6))
yy += 6

A('<text class="pTitle" x="%.1f" y="%.1f">② 过道清障（图中 1~9 号）</text>' % (lx, yy)); yy += 20
for n, s in ((1, "接待台 + 台面屏 + 杯/笔筒"), (2, "访客椅"), (3, "等候长椅（西弧）"),
             (4, "等候长椅（东弧）"), (5, "中心花坛 + 绿植"), (6, "贝壳喷泉"),
             (7, "贝壳罐"), (8, "主廊缆绳卷（西）"), (9, "主廊缆绳卷（东）")):
    A('<circle class="clrC2" cx="%.1f" cy="%.1f" r="7"/>' % (lx + 7, yy - 4))
    A('<text class="clrN2" x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (lx + 7, yy, n))
    A('<text class="pNote" x="%.1f" y="%.1f">%s</text>' % (lx + 19, yy, s)); yy += 17
A('<text class="pNote2" x="%.1f" y="%.1f">走廊内实体家具 → 0 件（实测 15 个网格件）</text>' % (lx, yy)); yy += 15
A('<text class="pNote2" x="%.1f" y="%.1f">只留地面铺装；室外前庭 / 侧院景观保留</text>' % (lx, yy)); yy += 16
A('<line class="pDiv" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (lx, yy - 6, lx + 206, yy - 6))
yy += 6

A('<text class="pTitle" x="%.1f" y="%.1f">③ 面积变化</text>' % (lx, yy)); yy += 20
A('<text class="pItem" x="%.1f" y="%.1f">公共空间合计</text>' % (lx, yy))
A('<text class="pOld" x="%.1f" y="%.1f" text-anchor="end">114.0㎡</text>' % (lx + 128, yy))
A('<text class="pNew" x="%.1f" y="%.1f" text-anchor="end">%.1f㎡</text>' % (lx + 206, yy, D["public_area"]))
yy += 21
for lab, v4, v5 in (("房间合计", 351.6, D["room_area"]), ("室内合计", 465.6, D["indoor"])):
    A('<text class="pItem" x="%.1f" y="%.1f">%s</text>' % (lx, yy, lab))
    A('<text class="pOld" x="%.1f" y="%.1f" text-anchor="end">%.1f㎡</text>' % (lx + 128, yy, v4))
    A('<text class="pNew" x="%.1f" y="%.1f" text-anchor="end">%.1f㎡</text>' % (lx + 206, yy, v5))
    yy += 21
A('<text class="pItem" x="%.1f" y="%.1f">公共占比</text>' % (lx, yy))
A('<text class="pOld" x="%.1f" y="%.1f" text-anchor="end">24.5%%</text>' % (lx + 128, yy))
A('<text class="pNew" x="%.1f" y="%.1f" text-anchor="end">%.1f%%</text>'
  % (lx + 206, yy, 100 * D["public_area"] / D["indoor"])); yy += 21
A('<text class="pItem" x="%.1f" y="%.1f">包络 / 覆盖率</text>' % (lx, yy))
A('<text class="pVal" x="%.1f" y="%.1f" text-anchor="end">29.6×21.6 · %.1f%%</text>'
  % (lx + 206, yy, 100 * D["footprint"] / (EX * EZ))); yy += 18
A('<text class="pNote2" x="%.1f" y="%.1f">房间共让出 %.1f㎡ 给交通</text>'
  % (lx, yy, 351.6 - D["room_area"])); yy += 15
A('<text class="pNote2" x="%.1f" y="%.1f">（公共 = 主廊 + 西支廊 + 圆厅）</text>' % (lx, yy)); yy += 16
A('<line class="pDiv" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (lx, yy - 6, lx + 206, yy - 6))
yy += 4
A('<text class="pNote" x="%.1f" y="%.1f">保留：错落非对称（镜像自洽仅 1/8）</text>' % (lx, yy))
A('</g>')

# ---------- 标题栏 ----------
A('<g id="title">')
A('<text class="ttl" x="%.1f" y="%.1f">走廊加宽 · 过道清障方案 · v5</text>' % (PL, VH - 138))
A('<text class="sub" x="%.1f" y="%.1f">在 v4 错落非对称布局基础上，只动「室内交通」：清空走廊/圆厅内全部家具，并把主廊与西支廊加宽</text>'
  % (PL, VH - 116))
A('<text class="sub" x="%.1f" y="%.1f">包络 29.6×21.6m 不变 · 外轮廓/退台/房间外墙一律不动 · 8 樘房门位置按新墙线联动</text>'
  % (PL, VH - 98))
A('<text class="sub" x="%.1f" y="%.1f">房间 %.1f㎡ · 公共 %.1f㎡ · 室内 %.1f㎡ · 公共占比 %.1f%%（v4 为 24.5%%）'
  % (PL, VH - 80, D["room_area"], D["public_area"], D["indoor"],
     100 * D["public_area"] / D["indoor"]))
A('<text class="sub2" x="%.1f" y="%.1f">几何校验：_verify/gen_plan_v5_geom.py —— 重叠 0 · 公共压房间 0 · 门 8/8 通向公共廊 · 零死区</text>'
  % (PL, VH - 62))
A('</g>')

BODY = "\n".join(svg)
CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 "Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1250px;margin:0 auto;padding:22px 18px 60px}
header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:14px}
h1{font-size:19px;margin:0 0 4px;letter-spacing:.02em}
header p{margin:0;color:var(--ink2);font-size:12.5px}
button{background:var(--btn);color:var(--ink);border:1px solid var(--line);border-radius:6px;
 padding:7px 14px;font-size:12.5px;cursor:pointer}
button:hover{background:var(--btnh)}
.sheet{background:var(--sheet);border:1px solid var(--line);border-radius:10px;padding:6px;overflow:auto}
svg{display:block;width:100%;height:auto}
.env{fill:var(--env)}
.court{fill:var(--court);stroke:var(--courtL);stroke-width:1.2;stroke-dasharray:5 4}
.garden{fill:var(--garden);stroke:var(--gardenL);stroke-width:1.2;stroke-dasharray:5 4}
.slit{fill:var(--slit)}
.tree{fill:var(--tree);stroke:var(--treeL);stroke-width:1}
.pub{fill:var(--pub)}
.hallfloor{fill:var(--hall)}
.hallring{fill:none;stroke:var(--pubL);stroke-width:2.4}
.hallring2{fill:none;stroke:var(--pubL);stroke-width:1.2;stroke-dasharray:4 4}
.clearmark{fill:none;stroke:var(--ok);stroke-width:2.6;stroke-linecap:round}
.v4ln{stroke:var(--v4);stroke-width:2.4;stroke-dasharray:9 6}
.v4circ{fill:none;stroke:var(--v4);stroke-width:2;stroke-dasharray:8 6}
.v4void{fill:var(--v4f);stroke:var(--v4);stroke-width:1;stroke-dasharray:3 3}
.pub3{font:400 10.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.clrC{fill:var(--clrbg);stroke:var(--clr);stroke-width:1.8}
.clrN{font:700 10px/1 "Segoe UI",sans-serif;fill:var(--clrtx)}
.clrC2{fill:var(--clrbg);stroke:var(--clr);stroke-width:1.4}
.clrN2{font:700 9px/1 "Segoe UI",sans-serif;fill:var(--clrtx)}
.room{fill-opacity:.20;stroke-opacity:.85;stroke-width:1.6}
.wall{stroke:var(--wall);stroke-width:5;stroke-linecap:square}
.gap{fill:var(--sheet)}
.leaf{stroke:var(--leaf);stroke-width:2.2}
.swing{fill:none;stroke:var(--leaf);stroke-width:1.1;stroke-dasharray:3 3}
.entryarrow{stroke:var(--acc);stroke-width:2.4;fill:none}
.arrowhead{fill:var(--acc);stroke:none}
.leader{stroke:var(--ink2);stroke-width:1;stroke-dasharray:3 3}
.desk{fill:var(--furn);stroke:var(--furnL);stroke-width:.8}
.tb{fill:var(--furn2);stroke:var(--furnL);stroke-width:.9}
.ch{fill:none;stroke:var(--furnL);stroke-width:.9}
.chip{fill:var(--chip);stroke:var(--line);stroke-width:.8}
.rEN{font:700 15px/1 "Segoe UI",sans-serif;fill:var(--ink)}
.rCN{font:600 11.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.rSZ{font:400 10.5px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.site{font:600 13px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.site2{font:400 10.5px/1 "Segoe UI",sans-serif;fill:var(--ink3)}
.pub1{font:600 12px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.pub1b{font:700 12.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ok)}
.pub2{font:700 10.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ok)}
.entry{font:700 12px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--acc)}
.dim{stroke:var(--ink3);stroke-width:.9}
.dimw{stroke:var(--ok);stroke-width:1.4}
.dimtxt{font:600 11.5px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.dimwt2{font:700 10.5px/1 "Segoe UI",sans-serif;fill:var(--ok)}
.dimnote{font:400 11px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.wtag{fill:var(--okbg);stroke:var(--ok);stroke-width:1}
.wtagt{font:700 11.5px/1 "Segoe UI",sans-serif;fill:var(--oktx)}
.cmp{fill:none;stroke:var(--line);stroke-width:1}
.cmpn{fill:var(--ink2)}
.cmpn2{font:700 10px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.sb1{fill:var(--ink2)}.sb2{fill:var(--sheet);stroke:var(--ink2);stroke-width:.8}
.sb{font:400 10.5px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.panel{fill:var(--panel);stroke:var(--line);stroke-width:1}
.pTitle{font:700 13px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.pItem{font:400 11.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.pVal{font:600 11.5px/1 "Segoe UI",sans-serif;fill:var(--ink)}
.pOld{font:600 11.5px/1 "Segoe UI",sans-serif;fill:var(--ink3)}
.pNew{font:700 11.5px/1 "Segoe UI",sans-serif;fill:var(--ok)}
.pNote{font:400 11px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.pNote2{font:400 10.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.pDiv{stroke:var(--line);stroke-width:1}
.ttl{font:700 20px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.sub{font:400 12px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.sub2{font:400 11px/1 "Segoe UI",sans-serif;fill:var(--ink3)}
body[data-theme="dark"]{--bg:#0f1115;--sheet:#15181d;--panel:#1a1e24;--chip:rgba(22,26,32,.86);
 --line:#2b3138;--wall:#c9ced6;--ink:#eef1f5;--ink2:#a9b2bd;--ink3:#79828d;--leaf:#e8c07d;
 --pub:#222933;--pubL:#4a5563;--hall:#2b3442;--env:#101318;--slit:#101317;
 --court:#1b2318;--courtL:#3e5236;--garden:#152018;--gardenL:#33513a;
 --tree:#24331f;--treeL:#3e5a35;
 --furn:rgba(230,235,242,.20);--furnL:rgba(230,235,242,.34);--furn2:rgba(230,235,242,.28);
 --acc:#f0a95c;--ok:#5fd39a;--okbg:rgba(95,211,154,.12);--oktx:#8ee7ba;--btn:#1e242c;--btnh:#262d36;
 --v4:#e0736a;--v4f:rgba(224,115,106,.10);--clr:#ff8a72;--clrbg:rgba(255,138,114,.16);--clrtx:#ffb9a6}
body[data-theme="light"]{--bg:#f2f3f5;--sheet:#ffffff;--panel:#fafbfc;--chip:rgba(255,255,255,.90);
 --line:#d7dbe0;--wall:#3a3f46;--ink:#1a1d21;--ink2:#5a6068;--ink3:#878d96;--leaf:#8a6a2f;
 --pub:#eef0f2;--pubL:#c3c8cf;--hall:#e6ebef;--env:#f6f7f8;--slit:#f6f7f8;
 --court:#eef3ea;--courtL:#a9bfa0;--garden:#eaf2ea;--gardenL:#9dba9f;
 --tree:#d8ead0;--treeL:#a9c79c;
 --furn:rgba(30,35,42,.14);--furnL:rgba(30,35,42,.30);--furn2:rgba(30,35,42,.22);
 --acc:#c9761f;--ok:#1a8f5a;--okbg:rgba(26,143,90,.10);--oktx:#116b42;--btn:#ffffff;--btnh:#f0f1f3;
 --v4:#c0483c;--v4f:rgba(192,72,60,.10);--clr:#d0442c;--clrbg:rgba(208,68,44,.10);--clrtx:#a8321e}
"""
HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>走廊加宽 · 过道清障方案 v5</title><style>%s</style></head>
<body data-theme="dark"><div class="wrap">
<header><div><h1>走廊加宽 · 过道清障方案 · v5</h1>
<p>在 v4 布局上只改室内交通：清空走廊/圆厅家具 + 主廊净宽 3.0→4.2m + 西支廊加宽并消除死区</p></div>
<button id="tg">切换 浅色 / 深色</button></header>
<div class="sheet"><svg viewBox="0 0 %.1f %.1f" xmlns="http://www.w3.org/2000/svg">%s</svg></div>
</div><script>
var b=document.body,t=document.getElementById('tg');
t.onclick=function(){b.dataset.theme=b.dataset.theme==='dark'?'light':'dark';};
</script></body></html>""" % (CSS, VW, VH, BODY)

path = os.path.join(ROOT, "平面图方案-走廊加宽版.html")
open(path, "w", encoding="utf-8").write(HTML)
print("已生成:", path, "| SVG 元素:", len(svg), "| viewBox %.0fx%.0f" % (VW, VH))
