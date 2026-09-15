# -*- coding: utf-8 -*-
"""v4（现状）<-> v5（走廊加宽+清障提案）对照图 + 走廊断面示意"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, '_shots')
OUT = os.path.join(SH, 'v5_走廊加宽_前后对照.png')
FO = 'C:/Windows/Fonts/msyh.ttc'
FB = 'C:/Windows/Fonts/msyhbd.ttc'


def f(sz, b=False):
    return ImageFont.truetype(FB if b else FO, sz)


def crop_sheet(path, top=0.055, bot=0.94, l=0.006, r=0.994):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    return im.crop((int(w * l), int(h * top), int(w * r), int(h * bot)))


a = crop_sheet(os.path.join(SH, 'plan_v4_light.png'), 0.055, 0.945)
b = crop_sheet(os.path.join(SH, 'plan_v5_light.png'), 0.055, 0.945)

PH = 760


def fith(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


a, b = fith(a, PH), fith(b, PH)

SEC_W = 430          # 右侧走廊断面示意宽度
PAD, HEAD, LBL, FOOT = 30, 78, 42, 230
W = PAD * 3 + a.width + b.width + SEC_W
H = HEAD + LBL + PH + FOOT + PAD
cv = Image.new('RGB', (W, H), (246, 245, 243))
d = ImageDraw.Draw(cv)

d.rectangle([0, 0, W, HEAD], fill=(38, 43, 51))
d.text((PAD, 20), '走廊加宽 · 过道清障 —— 加宽前（v4）  vs  加宽后（v5 提案）', font=f(29, True), fill=(255, 255, 255))
d.text((W - PAD - 330, 28), '包络 29.6 × 21.6 m 不变', font=f(19), fill=(176, 183, 193))

ly = HEAD + 12
d.text((PAD, ly), '① 加宽前（v4 · 现状）', font=f(21, True), fill=(176, 72, 62))
d.text((PAD * 2 + a.width, ly), '② 加宽后（v5 提案）', font=f(21, True), fill=(22, 120, 76))
d.text((PAD * 3 + a.width + b.width, ly), '③ 走廊断面（南北向）', font=f(21, True), fill=(58, 62, 70))

y = HEAD + LBL
cv.paste(a, (PAD, y)); cv.paste(b, (PAD * 2 + a.width, y))
d.rectangle([PAD, y, PAD + a.width, y + PH], outline=(200, 190, 186), width=2)
d.rectangle([PAD * 2 + a.width, y, PAD * 2 + a.width + b.width, y + PH], outline=(186, 202, 190), width=2)

# ---- ③ 断面示意 ----
sx = PAD * 3 + a.width + b.width
sy = y + 30
SC = 26          # px per meter
BAND = 46


def section(oy, corr, title, col):
    d.text((sx, oy - 20), title, font=f(15, True), fill=col)
    # 北侧房间
    d.rectangle([sx, oy, sx + 4.2 * SC, oy + 18], fill=(226, 222, 216), outline=(150, 146, 140))
    d.text((sx + 6, oy + 3), '北排 CRO / CMO / CTO', font=f(12), fill=(96, 92, 88))
    oy += 18
    d.rectangle([sx, oy, sx + 4.2 * SC, oy + corr * SC], fill=(240, 240, 238), outline=(60, 60, 60), width=2)
    d.text((sx + 78, oy + corr * SC / 2 - 11), '走廊  %.1f m' % corr, font=f(17, True), fill=col)
    if corr < 4.2:
        d.rectangle([sx + corr * SC, oy, sx + 4.2 * SC, oy + corr * SC],
                    fill=(250, 224, 220), outline=(176, 72, 62), width=1)
        for k in range(int((4.2 - corr) * SC) // 8 + 1):
            xx = sx + corr * SC + k * 8
            d.line([(xx, oy + corr * SC), (xx + 8, oy)], fill=(232, 190, 184), width=1)
    else:
        d.rectangle([sx + 3.0 * SC, oy, sx + 4.2 * SC, oy + corr * SC],
                    fill=(214, 240, 224), outline=(22, 120, 76), width=1)
    oy += corr * SC
    d.rectangle([sx, oy, sx + 4.2 * SC, oy + 18], fill=(226, 222, 216), outline=(150, 146, 140))
    d.text((sx + 6, oy + 3), '南排 COO / CEO', font=f(12), fill=(96, 92, 88))
    return oy + 18


oy = section(sy, 3.0, 'v4 现状', (176, 72, 62))
d.text((sx, oy + 8), '红斜纹 = 缺的 1.2 m', font=f(13), fill=(176, 72, 62))
oy = section(oy + 52, 4.2, 'v5 提案', (22, 120, 76))
d.text((sx, oy + 8), '绿带 = 补上的 1.2 m', font=f(13), fill=(22, 120, 76))

# ---- 页脚 ----
fy = y + PH + 18
d.text((PAD, fy), '这一版动了什么（外轮廓 / 退台 / 房间外墙一律不动）：', font=f(20, True), fill=(58, 62, 70))
lines = [
    ('① 过道清障', '走廊 + 圆厅内拆除 9 组家具：接待台（含台面屏/杯/笔筒）、访客椅、等候长椅 ×2、中心花坛 + 绿植、贝壳罐/贝壳喷泉 ×2、主廊缆绳卷 ×2 → 走廊内实体家具 0 件，只留地面铺装。室外前庭/侧院景观保留。'),
    ('② 主廊加宽', '东西主廊净宽 3.0 m → 4.2 m（+40%）：北排 CRO/CMO/CTO 南边界 8.6→8.2，南排 COO 北边界 11.6→12.4。'),
    ('③ 支廊加宽', '西支廊上段 2.8 → 4.0 m、下段 1.6 → 2.8 m：把 x10.2~11.4 / z13.0~19.4 这块 7.7㎡ 的"建筑内死区"并入走廊。'),
    ('④ 圆厅收缩', '接待圆厅 Ø3.8 → Ø3.0 m（圆心 9.4,10.8 偏心位置不动），只保留圆形地面铺装作为视觉锚点。'),
    ('⑤ 门位联动', 'CPO 门沿东墙 8.0 → 9.6（居中于加宽后的主廊）；其余 7 樘门位置不变，仍全部朝公共区。'),
    ('⑥ 面积账', '房间 351.6 → 337.1 ㎡（让出 14.5㎡）；公共 114.0 → 132.5 ㎡；室内 465.6 → 469.6 ㎡；公共占比 24.5% → 28.2%。包络 29.6×21.6 与覆盖率 73.4% 不变。'),
]
for i, (tag, txt) in enumerate(lines):
    lyy = fy + 36 + i * 26
    d.text((PAD + 4, lyy), tag, font=f(15, True), fill=(22, 120, 76))
    d.text((PAD + 108, lyy - 1), txt, font=f(14), fill=(88, 92, 100))

cv.save(OUT, quality=95)
print('OK →', OUT, cv.size)
