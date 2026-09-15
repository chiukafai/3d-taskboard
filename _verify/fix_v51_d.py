# -*- coding: utf-8 -*-
"""v5.1 修复 D：撤下 office_monitor / GLB laptop + 办公桌木色 tint + 修正 createLaptop 屏幕朝向"""
import io, re, sys

HTML = 'office-3d-taskboard.html'
s = io.open(HTML, encoding='utf-8').read()
orig = s

TINT = {'cpo': '[0xB08060,0.28]', 'cro': '[0x6E5A4A,0.34]', 'cmo': '[0xC79A5B,0.30]',
        'cto': '[0x5A6470,0.30]', 'coo': '[0x7A7F86,0.26]', 'ceo': '[0x8A6A4A,0.34]',
        'cfo': '[0x50657A,0.30]'}
KEYS = ['CPO', 'MEETING', 'CFO', 'CRO', 'CMO', 'CTO', 'COO', 'CEO']
report = []

for k in KEYS:
    m = re.search(r'(const %s_SHOW = \[)(.*?)(\n\];)' % k, s, re.S)
    assert m, k
    body = m.group(2)
    low = k.lower()
    # ① 删掉 office_monitor / laptop 两行
    lines = body.split('\n')
    kept, removed = [], 0
    for ln in lines:
        if re.search(r"key:'(office_monitor|laptop)'", ln):
            removed += 1
            continue
        kept.append(ln)
    body2 = '\n'.join(kept)
    # ② exec_desk 加木色 tint
    if low in TINT:
        body2 = re.sub(r"(\{ key:'exec_desk',\s*p:\[[^\]]*\],\s*r:[^,]+,\s*h:[\d.]+)(\s*\})",
                       lambda mm: mm.group(1) + ", tint:%s" % TINT[low] + mm.group(2), body2)
    s = s[:m.start()] + m.group(1) + body2 + m.group(3) + s[m.end():]
    report.append('%s_SHOW 撤下 %d 件；exec_desk tint %s' % (k, removed, TINT.get(low, '—')))

# ③ 修正 createLaptop：屏幕原本朝 −Z（背对使用者/键盘面），改回朝 +Z
old = "  scr.position.set(0,0.11,-0.008);scr.rotation.y=Math.PI;lidG.add(scr);"
assert s.count(old) == 1, 'createLaptop 屏幕行未命中'
s = s.replace(old,
  "  /* 2026-09-11 修复：屏幕原来是 rotation.y=π + z=−0.008 → 贴在盖子背面、朝向键盘的反侧，\n"
  "     使用者看到的是灰盖子。改为贴在盖子正面、朝 +Z（触控板那一侧 = 使用者侧）。 */\n"
  "  scr.position.set(0,0.11,0.008);scr.rotation.y=0;lidG.add(scr);", 1)

io.open(HTML, 'w', encoding='utf-8', newline='').write(s)
for r in report:
    print('  OK', r)
print('主文件 %d B → %d B' % (len(orig.encode('utf-8')), len(s.encode('utf-8'))))
