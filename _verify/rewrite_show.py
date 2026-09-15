#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 7 张截图样板 + 「椅背实墙、面朝门」规则，重写 7 间房的 SHOW 布局。
保留 CFO 房（CFO_SHOW 已存在，不动）。

朝向约定：
  +X 右 / +Z 朝相机 / +Y 上
  doorWall:
    front(+Z) → 椅放 -Z 侧、面朝 +Z（r=π）   →  模型 GLB 默认朝 -Z，所以让椅子面朝 +Z 需 r=π
    back (-Z) → 椅放 +Z 侧、面朝 -Z（r=0）
    left (-X) → 椅放 +X 侧、面朝 -X（r=π/2）
    right(+X) → 椅放 -X 侧、面朝 +X（r=-π/2）
"""
import io, re

HTML = io.open(r'C:\Users\Perfect\Desktop\3d-taskboard-main\office-3d-taskboard.html',
               encoding='utf-8').read()

# 全部 7 个新 SHOW（CFO 不动）
NEW_SHOWS = """const CEO_SHOW = [
  /* CEO 6×5  门在前墙(+Z) → 椅背朝后墙(-Z)，面朝门 r=π
     样板：1张L形大桌(已用exec_desk近似) + 1皮椅(坐) + 2访客椅(酒红) + 文件柜 + 2绿植 + 装饰架/相册/地球仪  */
  { key:'exec_desk',      p:[ 0.00,-1.60], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.10], r:Math.PI,   h:1.20, tint:[0x33506B,0.45] },
  { key:'office_chair',   p:[-0.95, 0.10], r:Math.PI,   h:1.00, tint:[0x8A5858,0.40] },
  { key:'office_chair',   p:[ 0.95, 0.10], r:Math.PI,   h:1.00, tint:[0x8A5858,0.40] },
  { key:'filing_cabinet', p:[-2.45, 1.40], r:Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-2.30,-1.85], r:0,         h:0.60 },
  { key:'plant_potted',   p:[ 2.40, 1.80], r:Math.PI/2, h:0.60 },
];
const CRO_SHOW = [
  /* CRO 5×5  门在前墙 → 椅背朝后墙(-Z)、面朝门 r=π
     样板：1桌+1皮椅+2显示器+文件柜(模拟监控墙)+柜面装饰+绿植  */
  { key:'exec_desk',      p:[ 0.00,-1.50], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.00], r:Math.PI,   h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.42,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.42,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-2.00, 0.65], r:Math.PI/2, h:1.10, tint:[0x666060,0.30] },
  { key:'filing_cabinet', p:[-2.00, 1.65], r:Math.PI/2, h:1.10, tint:[0x666060,0.30] },
  { key:'plant_potted',   p:[ 1.95,-1.85], r:0,         h:0.60 },
];
const COO_SHOW = [
  /* COO 7×5  门在前墙 → 椅背朝后墙(-Z)、面朝门 r=π（双工位改单人）
     样板：1桌+1椅+2显示器(数据屏)+文件柜×2(机柜)+茶几(暂用coffee_table)+绿植+相机  */
  { key:'exec_desk',      p:[ 0.00,-1.50], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.00], r:Math.PI,   h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.45,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.45,-1.42], r:Math.PI,   h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-2.95, 1.40], r:Math.PI,   h:1.10, tint:[0x5A5560,0.30] },
  { key:'filing_cabinet', p:[-2.95, 0.30], r:Math.PI,   h:1.10, tint:[0x5A5560,0.30] },
  { key:'coffee_table',   p:[ 1.60, 1.20], r:0,         h:0.45 },
  { key:'office_chair',   p:[ 1.60, 1.85], r:Math.PI,   h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.90,-1.85], r:0,         h:0.60 },
];
const CPO_SHOW = [
  /* CPO 6×8  门在左墙(-X) → 椅背朝右墙(+X)、面朝门 r=π/2
     样板：绘图桌(已用exec_desk近似大桌)+1椅+2显示器+小桌+会客椅+文件柜+绿植+墙上色板(用植物代)  */
  { key:'exec_desk',      p:[ 1.95, 0.00], r:Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[ 1.40, 0.00], r:Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 1.95,-0.45], r:Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 1.95, 0.45], r:Math.PI/2, h:0.50, y:0.76 },
  { key:'coffee_table',   p:[-1.60, 1.80], r:0,         h:0.45 },
  { key:'office_chair',   p:[-1.60, 2.45], r:Math.PI,   h:1.00, tint:[0xB08060,0.45] },
  { key:'filing_cabinet', p:[ 2.55, 2.40], r:-Math.PI/2,h:1.10 },
  { key:'plant_potted',   p:[-2.40, 2.85], r:0,         h:0.60 },
  { key:'plant_potted',   p:[-2.40,-2.70], r:0,         h:0.60 },
];
const CTO_SHOW = [
  /* CTO 8×5  门在后墙(-Z) → 椅背朝前墙(+Z)、面朝门 r=0（双工位改单人）
     样板：1桌+1椅+2显示器(代码屏)+2机柜(用filing_cabinet代)+小桌+绿植+地毯圆环(暂略)  */
  { key:'exec_desk',      p:[ 0.50, 1.30], r:0,         h:0.76 },
  { key:'exec_chair',     p:[ 0.50, 0.80], r:0,         h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 0.10, 1.40], r:0,         h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.90, 1.40], r:0,         h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-3.30, 1.30], r:0,         h:1.10, tint:[0x33383A,0.45] },
  { key:'filing_cabinet', p:[-3.30, 0.30], r:0,         h:1.10, tint:[0x33383A,0.45] },
  { key:'coffee_table',   p:[ 2.40,-1.20], r:0,         h:0.45 },
  { key:'office_chair',   p:[ 2.40,-1.80], r:Math.PI,   h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.50,-1.80], r:0,         h:0.60 },
];
const CMO_SHOW = [
  /* CMO 18×8 横厅 openPlan 无门 → 1张大桌 + 1皮椅(背中央墙)+ 2显示器 + 沙发洽谈角 + 文件柜 + 绿植
     注：CMO 无门、单墙开口，椅子按"背实墙/正面朝主要活动方向"（面向中央桌阵）。 */
  { key:'exec_desk',      p:[ 4.50, 0.00], r:-Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[ 5.05, 0.00], r:-Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 4.50,-0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 4.50, 0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'sofa',           p:[-3.50, 0.00], r:Math.PI/2, h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-2.50, 0.00], r:Math.PI/2, h:0.45 },
  { key:'filing_cabinet', p:[ 7.80,-2.80], r:-Math.PI/2, h:1.10 },
  { key:'filing_cabinet', p:[ 7.80, 2.80], r:-Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-8.20,-3.20], r:0,          h:0.60 },
  { key:'plant_potted',   p:[-8.20, 3.20], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 8.20, 0.00], r:0,          h:0.60 },
];
const MEETING_SHOW = [
  /* MEETING 6×5  门在前墙 → 维持沙发+茶几会谈区，无单领导椅（会议室特征）
     样板：长桌(用沙发×2+茶几近似)+投影屏(记忆屏替代)+白板(记忆屏替代)+绿植×2  */
  { key:'sofa',           p:[-1.25, 0.00], r:Math.PI/2,  h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'sofa',           p:[ 1.25, 0.00], r:-Math.PI/2, h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[ 0.00, 0.00], r:0,          h:0.45 },
  { key:'office_chair',   p:[-1.25,-1.70], r:Math.PI,    h:1.00, tint:[0x8A7070,0.40] },
  { key:'office_chair',   p:[ 1.25,-1.70], r:Math.PI,    h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[ 2.45,-1.85], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.45, 1.80], r:0,          h:0.60 },
];"""

# 替换策略：原文件有 7 个 const XXX_SHOW = [ ... ]; 块（CEO/CRO/COO/CPO/CTO/CMO/MEETING）
# 用正则非贪婪匹配整段，跳过 CFO_SHOW 单独保留。
SHOW_NAMES = ['CEO_SHOW', 'CRO_SHOW', 'COO_SHOW', 'CPO_SHOW', 'CTO_SHOW', 'CMO_SHOW', 'MEETING_SHOW']
pat = re.compile(
    r'/\* ══ 其余 7 间房的高清模型布局 ══.*?const MEETING_SHOW = \[.*?\];',
    re.S,
)
m = pat.search(HTML)
assert m, '未找到 7 间房 SHOW 块'
print(f'找到块长度 {m.end()-m.start()} 字符，从行 {HTML[:m.start()].count(chr(10))+1} 开始')

NEW_HTML = HTML[:m.start()] + NEW_SHOWS + '\n' + HTML[m.end():]
io.open(r'C:\Users\Perfect\Desktop\3d-taskboard-main\office-3d-taskboard.html',
        'w', encoding='utf-8').write(NEW_HTML)

# 校验：grep 一下每个 SHOW 名数量 + 同步验证没有保留旧 SHOW 内容
out = io.open(r'C:\Users\Perfect\Desktop\3d-taskboard-main\office-3d-taskboard.html',
              encoding='utf-8').read()
for n in SHOW_NAMES + ['CFO_SHOW']:
    print(f'  const {n:<14s} 出现 {len(re.findall(rf"const {n} = \[", out))} 次')

# 语法校验
m2 = re.search(r'<script type="module">(.*?)</script>', out, re.S)
io.open(r'C:\Users\Perfect\Desktop\3d-taskboard-main\_verify\_check.mjs',
        'w', encoding='utf-8').write(m2.group(1))
print('\nSHOW 替换完成；脚本继续做 node --check 校验')