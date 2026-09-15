# -*- coding: utf-8 -*-
"""v5 落地：走廊加宽（主廊 3.0→4.2m / 西支廊 2.8→4.0、1.6→2.8m）+ 过道清障（拆 9 组家具）

数据源：_verify/gen3d_v5.json（由 gen_plan_v5_geom.py → plan_v5.json 派生）
改动范围（7 处）：
  ① 顶部几何注释 → v5
  ② LOBBY.r 1.9 → 1.5
  ③ PUB_FLOORS / PAD_RECTS / PUB_WALLS 三张表整体替换
  ④ ZONES：cpo doorPos 8.0→9.6；cro/cmo/cto 南界 8.6→8.2（进深各 −0.4）；
            coo 北界 11.6→12.4（进深 −0.8）
  ⑤ createAtrium：圆厅 9 组家具全拆；主廊 2 处缆绳卷拆掉（室外前庭/侧院保留）
  ⑥ 家具微调：房间变小后贴墙的绿植内移（cmo/cto/coo/cpo）
  ⑦ 生成 audit_v5.py（把审计基准切到 plan_v5.json）
用法： python _verify/relayout_v5.py
"""
import io, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "office-3d-taskboard.html")
BAK = os.path.join(ROOT, "office-3d-taskboard.html.bak_pre_v5_20260911")
D = json.load(io.open(os.path.join(HERE, "gen3d_v5.json"), encoding="utf-8"))

if not os.path.exists(BAK):
    shutil.copy2(HTML, BAK)
    print("已备份 →", os.path.basename(BAK))
else:
    print("备份已存在，跳过 →", os.path.basename(BAK))

s = io.open(HTML, encoding="utf-8").read()


def rep(old, new, cnt=1, tag=""):
    global s
    n = s.count(old)
    assert n == cnt, "[%s] 命中 %d 处，期望 %d" % (tag, n, cnt)
    s = s.replace(old, new, cnt)
    print("  OK  %s" % tag)


def num(v):
    """与既有权重写法一致：能被 1 位小数整除就不带 .0 尾巴"""
    r = round(v, 3)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    return ("%.3f" % r).rstrip("0").rstrip(".")


# ══════════════ ① 顶部几何注释
rep("""/* ══ 平面图 v4 · 错落非对称布局（2026-09-11 落地）══
   几何基准：_verify/gen_plan_v4_geom.py → plan_v4.json（栅格 0.1m 校验：0 重叠、8 樘门全部通向公共区）
   包络 29.6 × 21.6 m。房间体量刻意错落：西翼 x = 0 / 1.0 / 2.2 三级退台，
   北墙 z = 5.6 / 3.6 / 1.6 / 0.0 四级退台，无一条贯穿到底的长直廊。
   坐标约定：平面图 x → three.js X，平面图 z(向下=南) → three.js Z。
   门向映射：平面图 S 墙 = front(+Z)；N 墙 = back(−Z)；E 墙 = right(+X)；W 墙 = left(−X)。
   公共区：西北入口前庭 → 蛇形支廊 A1/A2/A3 → 偏心圆厅(接待厅) → 东西主廊 B1/B2 → 东南侧庭。 */""",
"""/* ══ 平面图 v5 · 错落非对称 + 宽走廊（2026-09-11 第二轮落地）══
   几何基准：_verify/gen_plan_v5_geom.py → plan_v5.json（栅格 0.1m 校验：0 重叠、8 樘门全部通向公共区）
   包络 29.6 × 21.6 m 不变；房间体量仍刻意错落：西翼 x = 0 / 1.0 / 2.2 三级退台，
   北墙 z = 5.6 / 3.6 / 1.6 / 0.0 四级退台，无一条贯穿到底的长直廊。

   v4 → v5 只动「室内交通」，外轮廓/退台/房间外墙一律不动（相机、雾、光照、垫层无需重算）：
     · 东西主廊 南北净宽 3.0 → 4.2 m（北排 CRO/CMO/CTO 南界 8.6→8.2；南排 COO 北界 11.6→12.4）
     · 西支廊   东西净宽 上段 2.8 → 4.0 m、下段 1.6 → 2.8 m（东界 10.2→11.4，并入原 7.7㎡ 建筑内死区）
     · 接待圆厅 Ø3.8 → Ø3.0 m（圆心仍在 9.4/10.8，偏心不居中）
     · 走廊内实体家具 清零（原 15 个网格件 / 9 组全部拆除），只留地面铺装与圆形石盘
   坐标约定：平面图 x → three.js X，平面图 z(向下=南) → three.js Z。
   门向映射：平面图 S 墙 = front(+Z)；N 墙 = back(−Z)；E 墙 = right(+X)；W 墙 = left(−X)。
   公共区：西北入口前庭 → 蛇形支廊 A1/A2/A3 → 偏心圆厅(接待厅) → 东西主廊 B1/B2 → 东南侧庭。 */""",
    1, "header-comment")

# ══════════════ ② 圆厅半径
rep("const LOBBY = { x:9.4,  z:10.8, r:1.9 };                 // 偏心圆厅（接待厅，故意不在中轴上）",
    "const LOBBY = { x:9.4,  z:10.8, r:1.5 };                 // 偏心圆厅（接待厅，故意不在中轴上；v5 由 Ø3.8 收到 Ø3.0）",
    1, "LOBBY.r")

# ══════════════ ③ 三张表
pf = "\n".join("  [%s, %s, %s, %s]" % tuple(num(v) for v in r) for r in D["pub_floors"])
pf = re.sub(r"\n(?!$)", ",\n", pf) if False else pf
pf_js = ",\n".join("  [%s, %s, %s, %s]" % tuple(num(v) for v in r) for r in D["pub_floors"])
rep(re.search(r"const PUB_FLOORS = \[.*?\n\];", s, re.S).group(0),
    "const PUB_FLOORS = [\n%s\n];" % pf_js, 1, "PUB_FLOORS")

pad_js = ",\n".join("  [%s, %s, %s, %s]" % tuple(num(v) for v in r) for r in D["pad_rects"])
rep(re.search(r"const PAD_RECTS = \[.*?\n\];", s, re.S).group(0),
    "const PAD_RECTS = [\n%s\n];" % pad_js, 1, "PAD_RECTS")

pw_js = ",\n".join("  ['%s', %d, %d, %d]" % (o, k, a, b) for (o, k, a, b) in D["pub_walls"])
rep(re.search(r"const PUB_WALLS = \[.*?\n\];", s, re.S).group(0),
    "const PUB_WALLS = [\n%s\n];" % pw_js, 1, "PUB_WALLS")

# ══════════════ ④ ZONES
ZN = {z["id"]: z for z in D["zones"]}
for zid in ("cpo", "cro", "cmo", "cto", "coo", "ceo"):
    z = ZN[zid]
    m = re.search(r"^(  %s:\s+\{ id:'%s'.*?\},?)$" % (zid, zid), s, re.M)
    assert m, "找不到 ZONES 行：%s" % zid
    line = m.group(1)
    new = re.sub(r"cx:[\d.]+, cz:[\d.-]+, w:[\d.]+, d:[\d.]+,",
                 "cx:%s, cz:%s, w:%s, d:%s," % (num(z["cx"]), num(z["cz"]), num(z["w"]), num(z["d"])), line)
    new = re.sub(r"doorPos:[\d.]+,", "doorPos:%s," % num(z["doorPos"]), new)
    if new != line:
        s = s.replace(line, new, 1)
        print("  OK  ZONES.%s  %s\n            → %s" % (zid, line.strip(), new.strip()))
    else:
        print("  --  ZONES.%s 无变化" % zid)

# ══════════════ ⑤ createAtrium 清障
new_atrium = """function createAtrium(){
  const g=new THREE.Group();

  /* ── 偏心圆厅（接待厅 9.4/10.8 r1.5，故意不在中轴上）──
     v5：走廊内实体家具全部拆除（原接待台/台面屏/杯笔筒/访客椅/两张等候长椅/
         中心花坛/贝壳喷泉/贝壳罐 共 9 组 15 件）→ 只留地面圆形石盘 + 外圈环带作视觉锚点，
         走廊彻底回归「通行」职能。 */
  // （圆厅家具已在 v5 移除，勿再加回；如需陈设请贴墙且不侵占 4.2m 净通行带）

  /* ── 西北入口前庭（室外 0,0~6.6,5.6）：长椅 + 绿植 + 贝壳喷泉，正对西翼退台 ──
     注：室外场地景观不属于「过道」，v5 保留 */
  createCoastalBench(g,1.7,1.15,0);
  createCoastalBench(g,1.7,3.05,Math.PI);
  createCoastalPlant(g,0.85,0.85,1.2);
  createCoastalPlant(g,5.65,0.85,1.2);
  createShellFountain(g,3.7,2.10);
  createShellJar(g,5.65,3.40,0,0.9);
  createRopeCoil(g,5.30,0.10,4.40,0,0.2);

  /* ── 东南侧庭（室外 26.2,12.6~29.6,19.0）：CEO 东侧小院 ── */
  createCoastalBench(g,27.05,14.40,-Math.PI/2);
  createCoastalBench(g,27.05,17.40,Math.PI/2);
  createCoastalPlant(g,28.85,13.55,1.1);
  createCoastalPlant(g,28.85,18.20,1.1);
  createShellJar(g,28.85,15.90,0,0.9);
  createRopeCoil(g,27.05,0.10,15.90,0,0.2);

  /* ── 东西主廊：v5 起不放任何落地陈设（原 2 处缆绳卷已拆），保证 4.2m 净宽无阻 ── */

  g.position.set(0,0,0);scene.add(g);
}"""
m = re.search(r"function createAtrium\(\)\{.*?\n\}", s, re.S)
assert m, "找不到 createAtrium"
s = s.replace(m.group(0), new_atrium, 1)
print("  OK  createAtrium 清障（原 %d 行 → %d 行）" % (m.group(0).count("\n") + 1, new_atrium.count("\n") + 1))

# ══════════════ ⑥ 家具微调（房间进深变小后贴墙的绿植内移）
FIX = [
    # (tag, old, new)
    ("CPO.plant 让开新门位(z=9.6)",
     "  { key:'plant_potted',   p:[ 2.75, 2.05], r:0,          h:0.60 },\n];\nconst MEETING_SHOW",
     "  { key:'plant_potted',   p:[ 2.80,-0.20], r:0,          h:0.60 },\n];\nconst MEETING_SHOW"),
    ("CMO.plant 南侧内移 0.15",
     "  { key:'plant_potted',   p:[ 3.70, 3.60], r:0,          h:0.60 },",
     "  { key:'plant_potted',   p:[ 3.70, 3.45], r:0,          h:0.60 },"),
    ("CTO.plant 北侧内移 0.10",
     "  { key:'plant_potted',   p:[-2.30,-2.90], r:0,          h:0.60 },",
     "  { key:'plant_potted',   p:[-2.30,-2.78], r:0,          h:0.60 },"),
    ("CTO.plant 南侧内移 0.35",
     "  { key:'plant_potted',   p:[ 2.35, 3.10], r:0,          h:0.60 },",
     "  { key:'plant_potted',   p:[ 2.35, 2.75], r:0,          h:0.60 },"),
    ("COO.plant 西南内移（原越出南墙）",
     "  { key:'plant_potted',   p:[-3.60, 3.30], r:0,          h:0.60 },",
     "  { key:'plant_potted',   p:[-3.50, 2.90], r:0,          h:0.60 },"),
    ("COO.filing ×2 南移 0.30（原越出北墙）",
     """  { key:'filing_cabinet', p:[-3.55,-3.35], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },
  { key:'filing_cabinet', p:[-2.55,-3.35], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },""",
     """  { key:'filing_cabinet', p:[-3.55,-3.05], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },
  { key:'filing_cabinet', p:[-2.55,-3.05], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },"""),
]
for tag, old, new in FIX:
    rep(old, new, 1, tag)

# ══════════════ ⑦ 写回 + 生成 audit_v5.py
io.open(HTML, "w", encoding="utf-8", newline="").write(s)
print("\n→ 已写出 %s（%d B）" % (os.path.basename(HTML), len(s.encode("utf-8"))))

av4 = io.open(os.path.join(HERE, "audit_v4.py"), encoding="utf-8").read()
av5 = av4.replace("plan_v4.json", "plan_v5.json").replace("布局审计 v4", "布局审计 v5").replace("audit_v4.py", "audit_v5.py")
io.open(os.path.join(HERE, "audit_v5.py"), "w", encoding="utf-8", newline="").write(av5)
print("→ 已生成 _verify/audit_v5.py（基准 plan_v5.json）")
