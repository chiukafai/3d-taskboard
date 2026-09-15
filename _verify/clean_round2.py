# -*- coding: utf-8 -*-
# 二轮清理：删除闲置 MATS 条目 + 修正过时注释
import io, re

PATH = 'office-3d-taskboard.html'
h = io.open(PATH, encoding='utf-8').read()
orig = len(h)

# 1. 删除闲置 MATS 条目（已确认 MATS.<key> 全文 0 引用）
unused = ['wallOuter', 'wallBlue', 'wallTrim', 'beam', 'lampShade',
          'mugCoral', 'keyboard', 'lighthouseR', 'lighthouseW']
removed = 0
for k in unused:
    pat = re.compile(r'\n  ' + k + r':[^\n]*')
    m = pat.search(h)
    if m:
        h = h[:m.start()] + h[m.end():]
        removed += 1
    else:
        print('!! 未匹配', k)

# 2. 过时注释修正：cfo-models.js → all-models.js
h = h.replace(
    '/* ── CFO 样板房高清模型加载（cfo-models.js 提供 base64 GLB；失败自动回退程序化家具）── */',
    '/* ── 房间样板房高清模型加载（all-models.js 提供 base64 GLB；失败自动回退程序化家具）── */'
)

io.open(PATH, 'w', encoding='utf-8', newline='\n').write(h)
print(f'删除 MATS 闲置条目 {removed}/{len(unused)} 条；文件 {orig} → {len(h)} (-{orig-len(h)} 字节)')
