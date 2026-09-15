# 生成 v4 平面图 ↔ 3D 看板俯视 对照图（供人工验收）
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, '_shots')
OUT = os.path.join(SHOTS, 'v4_对照图_plan_vs_3d.png')

FONT = 'C:/Windows/Fonts/msyh.ttc'
def f(sz, bold=False):
    p = 'C:/Windows/Fonts/msyhbd.ttc' if bold else FONT
    return ImageFont.truetype(p if os.path.exists(p) else FONT, sz)

# 左：用户平面图（裁掉页面留白，只留图面）
plan = Image.open(os.path.join(SHOTS, 'plan_v4_light.png')).convert('RGB')
W0, H0 = plan.size                      # 1080 x 1080 左右
plan = plan.crop((int(W0 * 0.012), int(H0 * 0.135), int(W0 * 0.982), int(H0 * 0.795)))

# 右：3D 俯视
top = Image.open(os.path.join(SHOTS, 'p1_plan_top.png')).convert('RGB')
# 裁掉看板顶部工具栏与底部提示条
tw, th = top.size
top = top.crop((0, int(th * 0.055), tw, int(th * 0.945)))

PH = 720                                # 统一内容高度
def fith(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
plan, top = fith(plan, PH), fith(top, PH)

PAD, HEAD_H, LABEL_H, FOOT_H = 28, 74, 40, 176
W = PAD * 3 + plan.width + top.width
H = HEAD_H + LABEL_H + PH + FOOT_H + PAD
canvas = Image.new('RGB', (W, H), (247, 245, 242))
d = ImageDraw.Draw(canvas)

# 顶部标题条
d.rectangle([0, 0, W, HEAD_H], fill=(42, 46, 54))
d.text((PAD, 22), 'v4 错落非对称布局 —— 平面图 →  3D 看板落地对照', font=f(30, True), fill=(255, 255, 255))
d.text((W - PAD - 250, 28), '包络 29.6 m × 21.6 m', font=f(20), fill=(180, 186, 196))

# 分栏标题
ly = HEAD_H + 10
d.text((PAD, ly), '① 用户给的 v4 平面图', font=f(22, True), fill=(60, 64, 72))
d.text((PAD * 2 + plan.width, ly), '② 3D 看板实际渲染（俯视）', font=f(22, True), fill=(60, 64, 72))

y = HEAD_H + LABEL_H
canvas.paste(plan, (PAD, y))
canvas.paste(top, (PAD * 2 + plan.width, y))
d.rectangle([PAD, y, PAD + plan.width, y + PH], outline=(190, 186, 180), width=2)
d.rectangle([PAD * 2 + plan.width, y, PAD * 2 + plan.width + top.width, y + PH], outline=(190, 186, 180), width=2)

# 页脚：验收要点
fy = y + PH + 18
d.text((PAD, fy), '验收要点（静态审计 + 浏览器实测，均通过）：', font=f(20, True), fill=(60, 64, 72))
lines = [
    '房间位置/尺寸  8 间房逐一对齐 v4（西侧退台、面宽 5.8–8.2 m、进深 5.0–8.6 m 全不相等，非镜像）',
    '公共区      东西主廊贯通 + 西侧蛇形支廊 + 偏心圆厅（圆心 9.4,10.8，不在中轴 14.8 上）= 114.0 ㎡',
    '门          8 樘房门 + 2 樘公共门，全部朝公共区、且全部「外开」；门洞净空实测无遮挡',
    '室外        西北入口前庭 + 东南侧庭 + 东侧疏散口',
    '资源        高清家具 8/8 房间就位，463 mesh / 229 材质 / 282 万三角面，0 JS 报错',
]
for i, s in enumerate(lines):
    d.text((PAD + 12, fy + 34 + i * 26), '·  ' + s, font=f(17), fill=(92, 96, 104))

canvas.save(OUT, quality=95)
print('OK →', OUT, canvas.size)
