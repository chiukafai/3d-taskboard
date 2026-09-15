# -*- coding: utf-8 -*-
"""v5.1 修复前后对照图（门牌 / 桌面）"""
from PIL import Image, ImageDraw, ImageFont

SH = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/'
OUT = SH + 'v51_修复对照.png'
FONT = 'C:/Windows/Fonts/msyh.ttc'
def f(sz, b=False): return ImageFont.truetype(FONT, sz, index=0)

PAD, HEAD, LBL, FOOT = 26, 74, 34, 150
CW, CH = 560, 400          # 单个画格
GAP = 18
W = PAD * 2 + CW * 2 + GAP
H = HEAD + LBL + CH + LBL + CH + FOOT + PAD

cv = Image.new('RGB', (W, H), (247, 245, 242))
d = ImageDraw.Draw(cv)

d.rectangle([0, 0, W, HEAD], fill=(42, 46, 54))
d.text((PAD, 18), 'v5.1 三处修复 · 前后对照', font=f(30, True), fill=(255, 255, 255))
d.text((PAD, 52 * 0 + 0, ), '', font=f(10))
d.text((W - PAD - 330, 26), '门牌字反 / 地毯闪烁 / 桌面千篇一律', font=f(18), fill=(184, 190, 200))

def slot(x, y, path, title, sub, ok):
    im = Image.open(path).convert('RGB')
    r = min(CW / im.width, CH / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    d.rectangle([x, y, x + CW, y + CH], fill=(255, 255, 255), outline=(214, 210, 204), width=2)
    cv.paste(im, (x + (CW - im.width) // 2, y + (CH - im.height) // 2))
    col = (22, 120, 76) if ok else (176, 72, 62)
    d.rectangle([x, y - LBL + 4, x + 8, y - 6], fill=col)
    d.text((x + 16, y - LBL + 2), title, font=f(19, True), fill=col)
    d.text((x + 16 + d.textlength(title, font=f(19, True)) + 10, y - LBL + 4), sub, font=f(15), fill=(120, 124, 132))

y1 = HEAD + LBL
slot(PAD, y1, SH + 'r1_cfo_plaque.png', '修复前', 'CFO 门牌：走廊侧看到的是背面镜像字（文字反了）', False)
slot(PAD + CW + GAP, y1, SH + 'v5_cfo_plaque.png', '修复后', '正面朝走廊，CFO 财务中心 正常可读', True)

y2 = y1 + CH + LBL
slot(PAD, y2, SH + 'r4_cro_desk.png', '修复前', '每桌 2 个 office_monitor：其实是「显示器+键盘+鼠标+Ø0.88 圆木托底」整套工位', False)
slot(PAD + CW + GAP, y2, SH + 'v1_cro_desk.png', '修复后', '程序化显示器/笔记本，屏幕正对使用者；木色与桌面小物逐房不同', True)

fy = y2 + CH + 16
d.text((PAD, fy), '本轮改了什么（全部已通过静态审计 6/6）', font=f(20, True), fill=(50, 54, 62))
lines = [
    ('① 门牌字反', '东/西墙(right/left)门的门牌 pr 取反：原来牌面法线朝房内，走廊侧只能看到镜像背面 → CPO / 战略会议室 / CFO 三块牌子字是反的。同时撤销背面贴图多余的 repeat.x=-1 镜像。现 8/8 门牌正视点积 0.82~0.97（全部正面朝外）。'),
    ('② 地毯闪烁', 'CFO 两块地毯 y 同为 0.095、x/z 相交 1.70×0.83 → 共面 Z-fighting。改为按 z 切分：米白 z∈[-1.15,1.95]、鼠尾草绿 z∈[-2.50,-1.20]，留 0.05m 缝；顺带把米白毯从 x=-3.4 收到 -3.15，不再越过西墙。现同 y 重叠 = 0 处。'),
    ('③ 桌面全一样', 'office_monitor 实测是「显示器+键盘+鼠标 摆在一块 Ø0.88 圆木托底上」的一整套工位，一个就占满整张 1.88×0.70 的桌子，每桌放两个 = 两套工位叠罗汉（就是"两台笔记本各自一个圆盘托底"）。已从 8 张桌全部撤下，改用程序化显示器/笔记本 + 桌面小物，按桌子局部坐标摆放、屏幕一律朝使用者；办公桌按房间加不同木色 tint，8 张桌组合各不相同。'),
]
for i, (tag, txt) in enumerate(lines):
    ly = fy + 34 + i * 40
    d.text((PAD + 4, ly), tag, font=f(16, True), fill=(22, 120, 76))
    # 手写折行
    x0 = PAD + 132
    cur, yy = '', ly
    for ch in txt:
        if d.textlength(cur + ch, font=f(14)) > W - PAD - x0:
            d.text((x0, yy), cur, font=f(14), fill=(88, 92, 100)); cur, yy = ch, yy + 19
        else:
            cur += ch
    d.text((x0, yy), cur, font=f(14), fill=(88, 92, 100))

cv.save(OUT, quality=95)
print('OK ->', OUT, cv.size)
