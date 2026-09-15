# -*- coding: utf-8 -*-
"""v5 落地验收对照图（两张）
  A. v5_落地对照_plan_vs_3d.png  —— 左：确认过的 v5 平面图 / 右：3D 看板俯视实际渲染 / 下：验收要点
  B. v5_走廊净宽与清障.png        —— 主廊人眼视角 + 圆厅俯视 + 逐断面净宽实测数据
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, '_shots')
FONT = 'C:/Windows/Fonts/msyh.ttc'


def f(sz, bold=False):
    p = 'C:/Windows/Fonts/msyhbd.ttc' if bold else FONT
    return ImageFont.truetype(p if os.path.exists(p) else FONT, sz)


def fitw(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def fith(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


# ══════════════ A ══════════════
plan = Image.open(os.path.join(S, 'plan_v5_light.png')).convert('RGB').crop((13, 100, 1787, 1603))
top = Image.open(os.path.join(S, 'p1_plan_top.png')).convert('RGB')
tw, th = top.size
top = top.crop((0, int(th * 0.052), tw, int(th * 0.945)))

PH = 700
plan, top = fith(plan, PH), fith(top, PH)

PAD, HEAD, LBL, FOOT = 28, 76, 40, 190
W = PAD * 3 + plan.width + top.width
H = HEAD + LBL + PH + FOOT + PAD
c = Image.new('RGB', (W, H), (247, 245, 242))
d = ImageDraw.Draw(c)

d.rectangle([0, 0, W, HEAD], fill=(38, 42, 50))
d.text((PAD, 20), 'v5 走廊加宽 + 过道清障 —— 平面图 →  3D 看板落地对照', font=f(31, True), fill=(255, 255, 255))
d.text((W - PAD - 300, 29), '包络 29.6 × 21.6 m（未变）', font=f(20), fill=(178, 184, 194))

ly = HEAD + 10
d.text((PAD, ly), '① 已确认的 v5 平面图', font=f(22, True), fill=(58, 62, 70))
d.text((PAD * 2 + plan.width, ly), '② 3D 看板实际渲染（正交俯视）', font=f(22, True), fill=(58, 62, 70))

y = HEAD + LBL
c.paste(plan, (PAD, y))
c.paste(top, (PAD * 2 + plan.width, y))
d.rectangle([PAD, y, PAD + plan.width, y + PH], outline=(188, 184, 178), width=2)
d.rectangle([PAD * 2 + plan.width, y, PAD * 2 + plan.width + top.width, y + PH], outline=(188, 184, 178), width=2)

fy = y + PH + 16
d.text((PAD, fy), '验收要点（静态审计 6/6 + 浏览器射线实测，全部通过）', font=f(20, True), fill=(58, 62, 70))
lines = [
    ('净宽实测',   '东西主廊 沿 x 逐 0.2m 取 110 个断面，全部 = 4.2 m（v4 为 3.0 m）；西支廊上段 4.0 m、下段 2.8 m'),
    ('过道清障',   '公共区步行高度带（0.20~1.60 m）内实体家具 0 件；原 9 组 15 件（接待台/访客椅/长椅×2/花坛/喷泉/贝壳罐/缆绳卷×2）全拆'),
    ('房间联动',   '北排 CRO/CMO/CTO 南界 8.6→8.2、南排 COO 北界 11.6→12.4；CPO 门随墙线移到 z=9.6；其余 7 樘门不动'),
    ('几何校验',   '0.1 m 栅格：房间重叠 0 / 公共压房间 0 / 8 樘门全部通向公共区 / 门牌不压门洞 / 家具不出房 / 座位朝向全对'),
    ('资源与门',   '高清家具 8/8 房间就位；396 mesh / 212 材质 / 281 万三角面；10 樘门全部外开且门洞净空'),
]
for i, (t, s) in enumerate(lines):
    yy = fy + 34 + i * 27
    d.text((PAD + 10, yy), t, font=f(17, True), fill=(22, 116, 76))
    d.text((PAD + 108, yy), s, font=f(17), fill=(90, 94, 102))

c.save(os.path.join(S, 'v5_落地对照_plan_vs_3d.png'), quality=95)
print('A OK →', c.size)

# ══════════════ B ══════════════
corr = Image.open(os.path.join(S, 'q1_corr_eye_e.png')).convert('RGB')
cw, ch = corr.size
corr = corr.crop((0, int(ch * 0.24), int(cw * 0.90), int(ch * 0.95)))
lob = Image.open(os.path.join(S, 'p11_lobby_top.png')).convert('RGB')
lw, lh = lob.size
lob = lob.crop((int(lw * 0.06), 0, int(lw * 0.86), int(lh * 0.95)))

IH = 470
corr, lob = fith(corr, IH), fith(lob, IH)
PAD2, HEAD2, LBL2, FOOT2 = 26, 66, 36, 300
lw_ = PAD2 * 3 + corr.width + lob.width
W2 = max(lw_, 1400)
H2 = HEAD2 + LBL2 + IH + FOOT2 + PAD2
c2 = Image.new('RGB', (W2, H2), (247, 245, 242))
d2 = ImageDraw.Draw(c2)
d2.rectangle([0, 0, W2, HEAD2], fill=(38, 42, 50))
d2.text((PAD2, 17), 'v5 走廊加宽 · 过道清障 —— 3D 实景复核', font=f(29, True), fill=(255, 255, 255))
d2.text((W2 - PAD2 - 320, 26), '射线实测（非目测）', font=f(19), fill=(178, 184, 194))

bx = (W2 - (corr.width + lob.width + PAD2)) // 2
ly2 = HEAD2 + 8
d2.text((bx, ly2), '③ 主廊人眼视角：4.2 m 净宽、两侧只剩门牌，无任何落地陈设', font=f(21, True), fill=(58, 62, 70))
d2.text((bx + corr.width + PAD2, ly2), '④ 接待圆厅俯视：只剩圆形石盘 + 外环带', font=f(21, True), fill=(58, 62, 70))
y2 = HEAD2 + LBL2
c2.paste(corr, (bx, y2))
c2.paste(lob, (bx + corr.width + PAD2, y2))
d2.rectangle([bx, y2, bx + corr.width, y2 + IH], outline=(188, 184, 178), width=2)
d2.rectangle([bx + corr.width + PAD2, y2, bx + corr.width + PAD2 + lob.width, y2 + IH], outline=(188, 184, 178), width=2)

fy2 = y2 + IH + 18
d2.text((PAD2 + 4, fy2), '逐断面净宽实测（对 y=1.6 m 高处垂直下打射线，步行高度带内有实体即判「不通」）',
        font=f(19, True), fill=(58, 62, 70))
rows = [
    ('断面位置', '采样数', 'v4 净宽', 'v5 净宽', '结论'),
    ('东西主廊（z 8.2~12.4）沿 x 每 0.2 m', '110', '3.0 m', '4.2 m', '全程无收窄 √'),
    ('西支廊上段（z 12.6~16.2）沿 z 每 0.2 m', '19', '2.8 m', '4.0 m', '无收窄 √'),
    ('西支廊下段（z 16.6~21.6）沿 z 每 0.2 m', '25', '1.6 m', '2.8 m', '并入原死区 √'),
]
colx = [PAD2 + 14, PAD2 + 430, PAD2 + 540, PAD2 + 640, PAD2 + 740]
for i, r in enumerate(rows):
    ry = fy2 + 34 + i * 30
    if i == 0:
        d2.line([(PAD2 + 4, ry + 24), (PAD2 + 880, ry + 24)], fill=(206, 202, 196), width=2)
    for cx_, cell in zip(colx, r):
        d2.text((cx_, ry), cell, font=f(17, i == 0), fill=(58, 62, 70) if i == 0 else (92, 96, 104))
d2.text((PAD2 + 4, fy2 + 34 + 4 * 30 + 8),
        '公共区步行带障碍物聚类：0 件（v4 为 9 组）。室外入口前庭与东南侧庭的景观陈设按约定保留，不计入「过道」。',
        font=f(17), fill=(22, 116, 76))
c2.save(os.path.join(S, 'v5_走廊净宽与清障.png'), quality=95)
print('B OK →', c2.size)
