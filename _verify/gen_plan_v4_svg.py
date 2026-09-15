# -*- coding: utf-8 -*-
"""平面图 v4 渲染：读 plan_v4.json → 非对称版 HTML 平面图"""
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "plan_v4.json"), encoding="utf-8"))
D["sym_note"] = [
    "① 西翼三间逐层东退 0 → 1.0 → 2.2m，西立",
    "   面是台阶不是直墙；北带只占东半，北墙",
    "   退台 5.6 / 3.6 / 1.6 / 0.0m；",
    "② 西北让出 52.6㎡ 入口前庭，东南留",
    "   33.1㎡ 侧院 —— 两个空白对角分布；",
    "③ 走廊是蛇形：A1→A2→A3 逐段东移",
    "   0.8~1.2m，无一条贯通到底的长直廊；",
    "④ 圆厅偏心 x=9.4（包络中心 x=14.8），",
    "   不在任何中轴上；房间面宽进深全不等。",
]
S = 27.5
PL, PT, PR, PB = 104, 128, 276, 176
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


def txt(x, z, s, cls, anchor="start", dy=0):
    A('<text class="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
      % (cls, px(x), py(z) + dy, anchor, s))


# ---------- 场地：西北入口前庭 + 东南侧院 ----------
A('<g id="site">')
rect(0.0, 0.0, 9.4, 5.6, "court")
rect(26.0, 12.4, 29.6, 21.6, "garden")
rect(0.0, 11.0, 1.0, 16.4, "slit")
rect(0.0, 16.4, 2.2, 21.6, "slit")
rect(29.4, 8.6, 29.6, 12.4, "slit")
A('</g>')

# ---------- 公共空间（走廊 / 枢纽 / 圆厅） ----------
A('<g id="public">')
for (x1, z1, x2, z2) in D["public"]:
    rect(x1, z1, x2, z2, "pub")
cx, cz, r = D["lobby"]
A('<circle class="pub" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), r * S))
A('<circle class="hallring" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), r * S))
A('</g>')

# ---------- 房间 ----------
A('<g id="rooms">')
for rm in D["rooms"]:
    A('<rect class="room" x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
      'style="fill:%s;stroke:%s"/>'
      % (px(rm["x1"]), py(rm["z1"]), rm["w"] * S, rm["d"] * S,
         rm["color"], rm["color"]))
A('</g>')

# ---------- 家具 ----------
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
    rows = [ (z1 + z2) / 2 ] if deep < 4.2 else [z1 + 1.0 + dd / 2 + 0.55, z2 - 1.0 - dd / 2 - 0.55]
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
          % (px(coord), py(pos - dw / 2), px(coord - dw), py(pos - dw / 2)))
        A('<path class="swing" d="M%.1f,%.1f A%.1f,%.1f 0 0 %d %.1f,%.1f"/>'
          % (px(coord), py(pos + dw / 2), dw * S, dw * S, 1,
             px(coord - dw), py(pos - dw / 2)))
# 主入口（A1 北端）与次出口（B2 东端）
ex, ez = D["entry"]
A('<rect class="gap" x="%.1f" y="%.1f" width="%.1f" height="8"/>' % (px(ex - 0.9), py(ez) - 4, 1.8 * S))
A('<path class="entryarrow" d="M%.1f,%.1f L%.1f,%.1f"/>' % (px(ex), py(ez - 3.6), px(ex), py(ez - 0.9)))
A('<path class="arrowhead" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>'
  % (px(ex), py(ez - 0.2), px(ex - 0.26), py(ez - 1.1), px(ex + 0.26), py(ez - 1.1)))
A('</g>')

# ---------- 接待厅家具 ----------
A('<g id="lobbyfurn">')
A('<circle class="tb" cx="%.1f" cy="%.1f" r="%.1f"/>' % (px(cx), py(cz), 0.82 * S))
for i in range(4):
    ang = math.pi / 4 + i * math.pi / 2
    chx, chz = cx + 1.45 * math.cos(ang), cz + 1.45 * math.sin(ang)
    A('<rect class="ch" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
      % (px(chx - 0.26), py(chz - 0.26), .52 * S, .52 * S))
A('<rect class="tb" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
  % (px(7.55), py(12.25), 1.75 * S, 0.5 * S))
A('<text class="pub1" x="%.1f" y="%.1f" text-anchor="middle">接待台</text>' % (px(8.42), py(12.6)))
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

# ---------- 场地 / 公共空间标注 ----------
A('<g id="notes">')
A('<text class="site" x="%.1f" y="%.1f">入口前庭</text>' % (px(4.7), py(2.6)))
A('<text class="site2" x="%.1f" y="%.1f">9.4×5.6m</text>' % (px(4.7), py(3.5)))
A('<text class="site" transform="rotate(-90 %.1f %.1f)" x="%.1f" y="%.1f">东南侧院 3.6×9.2m</text>'
  % (px(27.8), py(17.0), px(27.8), py(17.0)))
A('<text class="pub1" x="%.1f" y="%.1f">东西主廊</text>' % (px(14.6), py(10.15)))
A('<text class="pub1" x="%.1f" y="%.1f" text-anchor="middle">蛇形支廊</text>' % (px(8.8), py(15.7)))
A('<line class="leader" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(cx), py(cz + 1.9), px(cx), py(cz + 2.4)))
A('<text class="pub1" x="%.1f" y="%.1f" text-anchor="middle">中央接待厅 Ø3.8m</text>'
  % (px(cx), py(cz + 3.0)))
A('<text class="entry" x="%.1f" y="%.1f" text-anchor="middle">主入口</text>' % (px(ex), py(ez - 4.3)))
A('<path class="entryarrow" d="M%.1f,%.1f L%.1f,%.1f"/>'
  % (px(29.4), py(10.5), px(30.5), py(10.5)))
A('<path class="arrowhead" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>'
  % (px(31.3), py(10.5), px(30.3), py(10.18), px(30.3), py(10.82)))
A('<text class="entry" x="%.1f" y="%.1f">次出口·疏散口</text>' % (px(26.6), py(13.1)))
A('</g>')

# ---------- 尺寸线 ----------
A('<g id="dims">')
A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (px(0), PT - 30, px(EX), PT - 30))
A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
  % (PL - 32, py(0), PL - 32, py(EZ)))
for xx in (0, EX):
    A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
      % (px(xx), PT - 36, px(xx), PT - 24))
for zz in (0, EZ):
    A('<line class="dim" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
      % (PL - 38, py(zz), PL - 26, py(zz)))
A('<text class="dimtxt" x="%.1f" y="%.1f" text-anchor="middle">29.6 m</text>' % (px(EX / 2), PT - 36))
A('<text class="dimtxt" transform="rotate(-90 %.1f %.1f)" x="%.1f" y="%.1f" text-anchor="middle">21.6 m</text>'
  % (PL - 40, py(EZ / 2), PL - 40, py(EZ / 2)))
A('<text class="dimnote" x="%.1f" y="%.1f">北墙四道退台（自西向东）：CPO 5.6 · CRO 3.6 · CTO 1.6 · CMO 0.0 m</text>'
  % (px(0), PT - 52))
A('</g>')

# ---------- 指北针 / 比例尺 ----------
A('<g id="compass">')
nx, nz = PL + EX * S - 34, PT - 62
A('<circle class="cmp" cx="%.1f" cy="%.1f" r="19"/>' % (nx, nz))
A('<path class="cmpn" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>'
  % (nx, nz - 15, nx - 6, nz + 8, nx + 6, nz + 8))
A('<text class="cmpn2" x="%.1f" y="%.1f" text-anchor="middle">N</text>' % (nx, nz + 22))
bx, bz = PL, VH - 46
A('<g id="scalebar">')
for i in range(5):
    cls = "sb1" if i % 2 == 0 else "sb2"
    A('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="9"/>' % (cls, bx + i * 2 * S, bz, 2 * S))
A('<text class="sb" x="%.1f" y="%.1f">0</text>' % (bx - 4, bz + 24))
A('<text class="sb" x="%.1f" y="%.1f" text-anchor="middle">5</text>' % (bx + 5 * S, bz + 24))
A('<text class="sb" x="%.1f" y="%.1f" text-anchor="end">10 m</text>' % (bx + 10 * S + 6, bz + 24))
A('</g></g>')

# ---------- 图例面板 ----------
lx = PL + EX * S + 58
A('<g id="panel">')
A('<rect class="panel" x="%.1f" y="%.1f" width="210" height="%.1f" rx="8"/>'
  % (lx - 12, PT - 62, EZ * S + 60))
A('<text class="pTitle" x="%.1f" y="%.1f">部门面积</text>' % (lx, PT - 38))
yy = PT - 14
for rm in D["rooms"]:
    A('<rect x="%.1f" y="%.1f" width="11" height="11" rx="2" style="fill:%s"/>'
      % (lx, yy - 9, rm["color"]))
    A('<text class="pItem" x="%.1f" y="%.1f">%s %s</text>' % (lx + 18, yy, rm["key"], rm["cn"]))
    A('<text class="pVal" x="%.1f" y="%.1f" text-anchor="end">%.1f㎡</text>'
      % (lx + 186, yy, rm["area"]))
    yy += 24
yy += 8
A('<line class="pDiv" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (lx, yy - 12, lx + 186, yy - 12))
for lab, val in (("公共空间（走廊+枢纽+圆厅）", "%.1f㎡" % D["public_area"]),
                 ("室内合计", "%.1f㎡" % D["indoor"]),
                 ("外轮廓占地（包络 639.4㎡）", "%.1f㎡" % D["footprint"]),
                 ("公共占比 / 覆盖率", "%.1f%% / %.1f%%"
                  % (100 * D["public_area"] / D["indoor"], 100 * D["footprint"] / 639.4))):
    A('<text class="pItem" x="%.1f" y="%.1f">%s</text>' % (lx, yy, lab))
    A('<text class="pVal" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (lx + 186, yy, val))
    yy += 22
yy += 10
A('<text class="pTitle" x="%.1f" y="%.1f">为什么不对称</text>' % (lx, yy))
yy += 20
for line in D["sym_note"]:
    A('<text class="pNote" x="%.1f" y="%.1f">%s</text>' % (lx, yy, line))
    yy += 18
yy += 8
A('<text class="pTitle" x="%.1f" y="%.1f">退台数据（脚本实测）</text>' % (lx, yy))
yy += 20
for line in ("北墙（西→东）：5.6 / 3.6 / 1.6 / 0.0 m",
             "南墙（西→东）：21.6 / 19.4 / 19.0 m",
             "西墙（北→南）：0.0 / 1.0 / 2.2 m",
             "房间面宽 5.8~8.2m · 进深 5.0~8.6m 全不相等"):
    A('<text class="pNote" x="%.1f" y="%.1f">%s</text>' % (lx, yy, line))
    yy += 18
A('</g>')

# ---------- 标题栏 ----------
A('<g id="title">')
A('<text class="ttl" x="%.1f" y="%.1f">错落非对称办公室平面图 · v4</text>' % (PL, VH - 122))
A('<text class="sub" x="%.1f" y="%.1f">8 部门 · 单体均为矩形房间 · 体量组合刻意不设左右/上下镜像轴</text>' % (PL, VH - 100))
A('<text class="sub" x="%.1f" y="%.1f">包络 29.6×21.6m · 房间 %.1f㎡ · 公共 %.1f㎡ · 室内 %.1f㎡ · 8 樘门全部朝公共廊</text>'
  % (PL, VH - 82, D["room_area"], D["public_area"], D["indoor"]))
A('<text class="sub2" x="%.1f" y="%.1f">几何校验：_verify/gen_plan_v4_geom.py（重叠 0 · 门 8/8 通向公共廊 · 房间级镜像自洽 1/8）</text>' % (PL, VH - 64))
A('</g>')

BODY = "\n".join(svg)
CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 "Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:22px 18px 60px}
header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:14px}
h1{font-size:19px;margin:0 0 4px;letter-spacing:.02em}
header p{margin:0;color:var(--ink2);font-size:12.5px}
button{background:var(--btn);color:var(--ink);border:1px solid var(--line);border-radius:6px;
 padding:7px 14px;font-size:12.5px;cursor:pointer}
button:hover{background:var(--btnh)}
.sheet{background:var(--sheet);border:1px solid var(--line);border-radius:10px;padding:6px;overflow:auto}
svg{display:block;width:100%;height:auto}
.court{fill:var(--court);stroke:var(--courtL);stroke-width:1.2;stroke-dasharray:5 4}
.garden{fill:var(--garden);stroke:var(--gardenL);stroke-width:1.2;stroke-dasharray:5 4}
.slit{fill:var(--slit)}
.pub{fill:var(--pub)}
.hallring{fill:none;stroke:var(--pubL);stroke-width:2}
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
.entry{font:700 12px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--acc)}
.dim{stroke:var(--ink3);stroke-width:.9}
.dimtxt{font:600 11.5px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.dimnote{font:400 11px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.cmp{fill:none;stroke:var(--line);stroke-width:1}
.cmpn{fill:var(--ink2)}
.cmpn2{font:700 10px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.sb1{fill:var(--ink2)}.sb2{fill:var(--sheet);stroke:var(--ink2);stroke-width:.8}
.sb{font:400 10.5px/1 "Segoe UI",sans-serif;fill:var(--ink2)}
.panel{fill:var(--panel);stroke:var(--line);stroke-width:1}
.pTitle{font:700 13px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.pItem{font:400 11.5px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.pVal{font:600 11.5px/1 "Segoe UI",sans-serif;fill:var(--ink)}
.pNote{font:400 11px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink3)}
.pDiv{stroke:var(--line);stroke-width:1}
.ttl{font:700 20px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.sub{font:400 12px/1 "PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink2)}
.sub2{font:400 11px/1 "Segoe UI",sans-serif;fill:var(--ink3)}
body[data-theme="dark"]{--bg:#0f1115;--sheet:#15181d;--panel:#1a1e24;--chip:rgba(22,26,32,.86);
 --line:#2b3138;--wall:#c9ced6;--ink:#eef1f5;--ink2:#a9b2bd;--ink3:#79828d;--leaf:#e8c07d;
 --pub:#222933;--pubL:#4a5563;--court:#1b2318;--courtL:#3e5236;--garden:#152018;--gardenL:#33513a;
 --slit:#101317;--furn:rgba(230,235,242,.20);--furnL:rgba(230,235,242,.34);--furn2:rgba(230,235,242,.28);
 --acc:#f0a95c;--btn:#1e242c;--btnh:#262d36}
body[data-theme="light"]{--bg:#f2f3f5;--sheet:#ffffff;--panel:#fafbfc;--chip:rgba(255,255,255,.90);
 --line:#d7dbe0;--wall:#3a3f46;--ink:#1a1d21;--ink2:#5a6068;--ink3:#878d96;--leaf:#8a6a2f;
 --pub:#f0f1f3;--pubL:#c3c8cf;--court:#eef3ea;--courtL:#a9bfa0;--garden:#eaf2ea;--gardenL:#9dba9f;
 --slit:#f6f7f8;--furn:rgba(30,35,42,.14);--furnL:rgba(30,35,42,.30);--furn2:rgba(30,35,42,.22);
 --acc:#c9761f;--btn:#ffffff;--btnh:#f0f1f3}
"""
HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>错落非对称办公室平面图 v4</title><style>%s</style></head>
<body data-theme="dark"><div class="wrap">
<header><div><h1>错落非对称办公室平面图 · v4</h1>
<p>8 部门 · 蛇形走廊 · 偏心圆厅 · 西北入口前庭 + 东南侧院 · 房间本身仍是矩形，只让体量错落</p></div>
<button id="tg">切换 浅色 / 深色</button></header>
<div class="sheet"><svg viewBox="0 0 %.1f %.1f" xmlns="http://www.w3.org/2000/svg">%s</svg></div>
</div><script>
var b=document.body,t=document.getElementById('tg');
t.onclick=function(){b.dataset.theme=b.dataset.theme==='dark'?'light':'dark';};
</script></body></html>""" % (CSS, VW, VH, BODY)

path = os.path.join(ROOT, "平面图方案-非对称版.html")
open(path, "w", encoding="utf-8").write(HTML)
print("已生成:", path, "| SVG 元素:", len(svg), "| viewBox %.0fx%.0f" % (VW, VH))

