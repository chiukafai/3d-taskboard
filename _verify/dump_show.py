# -*- coding: utf-8 -*-
import io, re
h = io.open('office-3d-taskboard.html', encoding='utf-8').read()
for m in re.finditer(r'const (\w+)_SHOW = \[(.*?)\n\];', h, re.S):
    name, body = m.group(1).upper(), m.group(2)
    items = re.findall(r"key:'(\w+)',\s*p:\[\s*(-?[\d.]+),\s*(-?[\d.]+)\],\s*r:\s*([^\]]+)", body)
    print(f'--- {name} ({len(items)} 件) ---')
    for k, px, pz, r in items:
        print(f'      {k:16s} p=({px:>7s},{pz:>7s})  r={r.strip()}')
