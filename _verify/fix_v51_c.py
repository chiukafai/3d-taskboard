# -*- coding: utf-8 -*-
"""v5.1 修复 C：桌面重做
- 撤下所有 office_monitor（实测该模型 = 显示器+键盘+鼠标 摆在 Ø0.88 圆木托底上的一整套工位，
  一个就占满整张桌；原先每桌放两个 = 两套工位叠罗汉，正是用户说的"两台笔记本各自一个圆盘托底"）
- 撤下 GLB laptop（朝向不可控）
- 改为程序化「显示器 + 笔记本 + 桌面小物」，按桌子局部坐标摆放（人坐 −Z，屏一律朝 −Z）
- 每房不同组合 + 办公桌木色 tint，消除"所有桌子一个样"

先跑本文件的 overlap 自检（不碰 HTML），再加 --apply 落盘。
"""
import io, sys, math

# ── 桌子局部坐标：人坐 z=−Z，桌长轴 = X；桌面可用区 x∈[-0.85,0.85] z∈[-0.33,0.33]
# 每个物件的占位footprint（用于重叠自检）
FOOT = {
    'mon':  (0.62, 0.26),   # 显示器（含底座）
    'lap':  (0.36, 0.30),   # 笔记本
    'kb':   (0.46, 0.16),
    'ms':   (0.09, 0.12),
    'mug':  (0.10, 0.10),
    'pen':  (0.10, 0.10),
    'paper':(0.22, 0.31),
    'phone':(0.21, 0.19),
    'tray': (0.26, 0.34),
}
JS = {'mon':'createDeskMonitor','lap':'createLaptop','kb':'createKeyboard','ms':'createMouse',
      'mug':'createMug','pen':'createPenCup','paper':'createPaperStack','phone':'createDeskPhone','tray':'createTray'}

# 每张桌：[房间, 桌局部中心 (dx,dz), 朝向 r, 物件列表]
DESKS = [
    ('cro',  0.00, -1.50, 'PI',  [('mon',-0.26,0.10),('mon',0.40,0.10),('kb',0.00,-0.20),('ms',0.30,-0.22),
                                  ('paper',-0.72,-0.02),('pen',-0.72,-0.26),('mug',0.78,0.10)]),
    ('cto',  0.60, -1.30, 'PI',  [('mon',0.30,0.10),('lap',-0.42,0.00),('kb',0.28,-0.20),('ms',0.56,-0.22),
                                  ('pen',-0.76,-0.24),('mug',-0.72,0.16)]),
    ('ceo', -0.90, -1.15, '0',   [('mon',-0.10,0.10),('lap',0.52,-0.06),('kb',-0.12,-0.20),('ms',0.16,-0.22),
                                  ('phone',0.66,0.22),('paper',-0.74,-0.04),('mug',-0.72,0.20)]),
    ('cfo', -1.90,  0.30, 'NHP', [('mon',0.26,0.10),('lap',-0.40,-0.02),('kb',0.26,-0.20),('ms',0.54,-0.22),
                                  ('pen',-0.72,0.20),('paper',-0.72,-0.10),('phone',0.74,0.20)]),
    ('coo',  0.30, -1.20, '0',   [('mon',0.00,0.10),('kb',-0.10,-0.20),('ms',0.20,-0.22),
                                  ('pen',-0.72,0.16),('mug',0.70,-0.20),('tray',0.70,0.16)]),
    ('cpo', -1.70,  0.00, 'NHP', [('lap',-0.34,-0.04),('mon',0.30,0.12),('kb',0.30,-0.20),('ms',0.58,-0.22),
                                  ('paper',-0.74,0.06),('pen',-0.74,-0.22),('mug',0.72,0.16)]),
    ('cmo1',-1.70, -1.90, 'PI',  [('mon',-0.26,0.10),('mon',0.40,0.10),('kb',0.00,-0.20),('ms',0.30,-0.22),
                                  ('pen',-0.72,-0.04),('mug',0.78,0.10)]),
    ('cmo2', 1.30, -1.90, 'PI',  [('mon',-0.10,0.12),('lap',0.52,-0.02),('kb',-0.12,-0.20),('ms',0.16,-0.22),
                                  ('paper',-0.74,0.02),('mug',0.74,0.20)]),
]
# 桌面板 tint（每房不同木色）
TINT = {'cpo':'0xB08060,0.28','cro':'0x6E5A4A,0.34','cmo':'0xC79A5B,0.30',
        'cto':'0x5A6470,0.30','coo':'0x7A7F86,0.26','ceo':'0x8A6A4A,0.34','cfo':'0x50657A,0.30'}
ROT = {'PI':'Math.PI','0':'0','NHP':'-Math.PI/2'}

# ── 重叠 + 越界自检 ──────────────────────────────────────────────────────
bad = 0
for room, dx, dz, r, items in DESKS:
    problems = []
    for i in range(len(items)):
        k, x, z = items[i]; w, d = FOOT[k]
        if x - w/2 < -0.86 or x + w/2 > 0.86: problems.append('%s@%.2f 超出桌宽 x' % (k, x))
        if z - d/2 < -0.34 or z + d/2 > 0.34: problems.append('%s@%.2f 超出桌深 z' % (z if False else k, z))
        for j in range(i+1, len(items)):
            k2, x2, z2 = items[j]; w2, d2 = FOOT[k2]
            ox = min(x+w/2, x2+w2/2) - max(x-w/2, x2-w2/2)
            oz = min(z+d/2, z2+d2/2) - max(z-d/2, z2-d2/2)
            if ox > 0.005 and oz > 0.005: problems.append('%s@(%.2f,%.2f) ↔ %s@(%.2f,%.2f) 叠 %.2f×%.2f' % (k,x,z,k2,x2,z2,ox,oz))
    print('%-5s %d 件  %s' % (room, len(items), ('✅ 无冲突' if not problems else '⚠️ ' + '; '.join(problems))))
    bad += len(problems)
print('\n合计问题：%d' % bad)
if bad:
    sys.exit(1)

if '--apply' not in sys.argv:
    print('\n（自检通过，加 --apply 才写文件）')
    sys.exit(0)

# ── 生成 JS 代码块 ───────────────────────────────────────────────────────
lines = []
for room, dx, dz, r, items in DESKS:
    lines.append("    if(id==='%s'){ const d=deskGrp(g,%s,%s,%s,DTOP);" % (room.rstrip('12') if room.startswith('cmo') else room,
                 '%0.2f' % dx, '%0.2f' % dz, ROT[r]))
    call = []
    for k, x, z in items:
        rot = ',Math.PI' if k == 'lap' else ''
        call.append('%s(d,%0.2f,0,%0.2f%s);' % (JS[k], x, z, rot))
    for i in range(0, len(call), 3):
        lines.append('      ' + ' '.join(call[i:i+3]))
    lines.append('    }')
block = '\n'.join(lines)

HTML = 'office-3d-taskboard.html'
s = io.open(HTML, encoding='utf-8').read()
assert 'if(id===\'cmo1\')' not in s

# ① 插入 deskGrp 帮助函数 + deskGrp 调用块（放在 g.add(prog) 之前）
anchor = '    g.add(prog);\n    const SHOW={'
assert s.count(anchor) == 1
s = s.replace(anchor, block + '\n' + anchor, 1)

# ② 定义 deskGrp + DTOP（放在 addFurniture 之前）
helper = """/* 桌面布置（2026-09-11 重做 v5.1）
   ⚠️ office_monitor 模型实测是「显示器 + 键盘 + 鼠标 摆在一块 Ø0.88 圆木托底上」的一整套工位，
      一个就占满整张 1.88×0.70 的办公桌；原先每桌放两个 = 两套工位叠罗汉，
      正是用户看到的"两台笔记本 + 各自一个圆盘托底" → 已全部撤下桌面。
   现改用程序化「显示器 / 笔记本 + 桌面小物」，一律按「桌子局部坐标」摆放：
      人坐 局部 −Z，桌长轴 = X，所有屏幕朝 −Z（正对使用者）。
   每间房的组合与办公桌木色 tint 都不同，避免"所有办公桌长一个样"。 */
const DTOP_HI = 0.85, DTOP_PROG = 0.90;   // 高清 GLB 桌面 / 程序化兜底桌面
function deskGrp(parent, dx, dz, r, y){
  const g=new THREE.Group(); g.position.set(dx,y,dz); g.rotation.y=r; parent.add(g); return g;
}
function createDeskMonitor(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(0.30,0.018,0.18),mcolor('#4a4f55',{roughness:0.42,metalness:0.45}));
  base.position.set(0,0.009,-0.03);g.add(base);
  const neck=new THREE.Mesh(new THREE.BoxGeometry(0.07,0.17,0.05),mcolor('#4a4f55',{roughness:0.42,metalness:0.45}));
  neck.position.set(0,0.10,-0.01);g.add(neck);
  const shell=new THREE.Mesh(new THREE.BoxGeometry(0.60,0.36,0.035),mcolor('#3b3f45',{roughness:0.34,metalness:0.35}));
  shell.position.set(0,0.36,0.02);g.add(shell);
  const scr=new THREE.Mesh(new THREE.PlaneGeometry(0.56,0.32),
    new THREE.MeshStandardMaterial({color:'#1b2b33',emissive:'#2c6076',emissiveIntensity:0.45,roughness:0.22}));
  scr.position.set(0,0.36,0.001);scr.rotation.y=Math.PI;g.add(scr);   // 朝 −Z = 正对使用者
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}

"""
assert s.count('function addFurniture(){') == 1
s = s.replace('function addFurniture(){', helper + 'function addFurniture(){', 1)

# ③ DTOP 变量：在 addFurniture 内、hasModels 之后插入
old = "  const hasModels = !!window.OFFICE_MODELS;"
assert s.count(old) == 1
s = s.replace(old, old + "\n  const DTOP = hasModels ? DTOP_HI : DTOP_PROG;", 1)

io.open(HTML, 'w', encoding='utf-8', newline='').write(s)
print('\n已写入 %s' % HTML)
print(block[:400] + ('\n...' if len(block) > 400 else ''))
