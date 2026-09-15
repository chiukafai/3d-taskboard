# -*- coding: utf-8 -*-
"""对比重排前后各房间 _SHOW 配置差异"""
import io, re, sys

def grab(path):
    h = io.open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'const (\w+)_SHOW = \[(.*?)\n\];', h, re.S):
        name, body = m.group(1).upper(), m.group(2)
        items = []
        for line in body.split('\n'):
            mm = re.search(r"key:'(\w+)'", line)
            if not mm:
                continue
            p = re.search(r"p:\[\s*(-?[\d.]+),\s*(-?[\d.]+)", line)
            r = re.search(r"r:\s*([^,]+),", line)
            items.append((mm.group(1), p.group(1) if p else '?', p.group(2) if p else '?',
                          (r.group(1).strip() if r else '?')))
        out[name] = items
    return out

old = grab(sys.argv[1])
new = grab(sys.argv[2])
for k in new:
    o, n = old.get(k, []), new[k]
    same = (o == n)
    print(f'--- {k}: {len(o)} -> {len(n)} 件   {"一致 ✅" if same else "有差异 ⚠️"}')
    if not same:
        for i in range(max(len(o), len(n))):
            a = o[i] if i < len(o) else None
            b = n[i] if i < len(n) else None
            if a != b:
                print(f'      [{i}] 旧={a}')
                print(f'          新={b}')
