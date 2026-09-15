# -*- coding: utf-8 -*-
"""2026-09-11 座向修正
实测模型朝向（_verify/probe_facing2.mjs）：
  exec_chair  靠背在 -z ⇒ r=0 时面朝 +z
  office_chair 靠背在 +z ⇒ r=0 时面朝 -z   （与 exec_chair 相反！）
  sofa        靠背在 -z ⇒ r=0 时面朝 +z

参照系（用户认可的样板）：CFO / CRO —— 椅子贴桌子靠门一侧、人面朝桌（背对门）。
逐件排查后发现 3 处不合：
  COO  exec_chair 落在桌后(+Z 侧) 且物理嵌进后墙记忆屏(z=0.7 vs 屏 z=0.64)，
       office_chair 背对茶几
  CPO  exec_desk/exec_chair 前后颠倒（本会话重排时引入），filing_cabinet 贴墙却侧转
  CEO  office_chair ×2 背对办公桌（沿用 CFO 访客椅的 r=π 所致）

本脚本按「对齐 CRO 已验证摆法」修正上述三处。
"""
import io, re, sys

P = 'office-3d-taskboard.html'
h = io.open(P, encoding='utf-8').read()
orig = h


def rep(old, new, cnt=1, tag=''):
    global h
    n = h.count(old)
    assert n == cnt, f'[{tag}] 命中 {n} 处，期望 {cnt}\n{old[:120]}'
    h = h.replace(old, new, cnt)
    print(f'  ✔ {tag}')


def block(name):
    m = re.search(r'(const ' + name + r'_SHOW = \[.*?\n\];)', h, re.S)
    assert m, name
    return m.group(1)


def setblock(name, newtext, tag):
    global h
    old = block(name)
    assert h.count(old) == 1
    h = h.replace(old, newtext, 1)
    print(f'  ✔ {tag}')


# ── ① COO：桌子后移贴记忆屏前方，椅子挪到桌子靠门一侧，访客椅转向茶几 ──
setblock('COO', """const COO_SHOW = [
  /* COO 7×5  门在前墙(+Z，开向中央大厅)
     2026-09-11 座向修正：椅贴桌的靠门侧、面朝桌(背对门)，与 CRO/CFO 一致。
     后墙有记忆屏(z≈-1.86)，桌后移留 0.27m 净距，不再与椅互相穿插。 */
  { key:'exec_desk',      p:[ 0.00,-1.15], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-0.65], r:Math.PI,   h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.45,-1.07], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.45,-1.07], r:Math.PI,   h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-2.95, 1.40], r:Math.PI,   h:1.10, tint:[0x5A5560,0.30] },
  { key:'filing_cabinet', p:[-2.95, 0.30], r:Math.PI,   h:1.10, tint:[0x5A5560,0.30] },
  { key:'coffee_table',   p:[ 1.60, 1.20], r:0,         h:0.45 },
  { key:'office_chair',   p:[ 1.60, 1.85], r:0,         h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.90,-1.85], r:0,         h:0.60 },
];""", 'COO 座向')

# ── ② CPO：恢复「桌靠后墙、椅贴桌的靠门侧」──
setblock('CPO', """const CPO_SHOW = [
  /* CPO 6×5  门在前墙(+Z，开向中央大厅)——2026-09-11 由东侧中段迁至东北角。
     北排同门向，摆法对齐 CRO：桌靠后墙留 0.35m 净距(后墙 z≈-2.30 有记忆屏)，
     椅贴桌的靠门侧、面朝桌(背对门)，显示器上桌，柜贴右墙朝内，绿植在门前左角。 */
  { key:'exec_desk',      p:[ 0.00,-1.50], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.00], r:Math.PI,   h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.45,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.45,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_chair',   p:[-1.55, 0.55], r:0,         h:1.00, tint:[0xB08060,0.45] },
  { key:'filing_cabinet', p:[ 2.45,-1.35], r:-Math.PI/2,h:1.10 },
  { key:'plant_potted',   p:[-2.40, 1.70], r:0,         h:0.60 },
];""", 'CPO 座向')

# ── ③ CEO：访客椅转向办公桌（office_chair 与 exec_chair 朝向相反）──
rep("  { key:'office_chair',   p:[-0.90, 0.10], r:Math.PI,    h:1.00, tint:[0x8A5858,0.40] },\n"
    "  { key:'office_chair',   p:[ 0.90, 0.10], r:Math.PI,    h:1.00, tint:[0x8A5858,0.40] },",
    "  /* office_chair 实测 r=0 面朝 -Z（与 exec_chair 相反）→ 面向办公桌 */\n"
    "  { key:'office_chair',   p:[-0.90, 0.10], r:0,          h:1.00, tint:[0x8A5858,0.40] },\n"
    "  { key:'office_chair',   p:[ 0.90, 0.10], r:0,          h:1.00, tint:[0x8A5858,0.40] },",
    1, 'CEO 访客椅')

io.open(P, 'w', encoding='utf-8').write(h)
print(f'\n写入完成：{len(orig)} → {len(h)} 字节（{len(h)-len(orig):+d}）')
