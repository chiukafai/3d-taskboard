# -*- coding: utf-8 -*-
# 深度清理：死代码删除 + 双重家具修复（条件化程序化兜底）+ mcolor 材质缓存
import io, re

PATH = 'office-3d-taskboard.html'
h = io.open(PATH, encoding='utf-8').read()
orig_size = len(h)
report = []

def cut_block(src, start_pat, name):
    """从匹配行起，按行级大括号配对删到闭合"""
    lines = src.split('\n')
    si = next((i for i, ln in enumerate(lines) if re.search(start_pat, ln)), None)
    if si is None:
        raise SystemExit(f'未找到 {name}')
    depth = 0; started = False; ei = si
    for j in range(si, len(lines)):
        for ch in lines[j]:
            if ch == '{': depth += 1; started = True
            elif ch == '}': depth -= 1
        if started and depth == 0:
            ei = j; break
    report.append(f'删除 {name}: {ei-si+1} 行')
    del lines[si:ei+1]
    return '\n'.join(lines)

# ============ 1. 死代码 ============
h = cut_block(h, r'^const FALLBACK_TASKS = \{', 'FALLBACK_TASKS（已废弃示例任务）')
h = cut_block(h, r'^const _MODEL_TINT = \{', '_MODEL_TINT（未使用）')
for fn in ['createWickerBasket', 'createTreasureChest', 'createChair', 'createDeskLamp',
           'createPendantLamp', 'createShipWheel', 'createSurfboard', 'createMonitor',
           'createCoffeeMachine', 'copyToClipboard']:
    h = cut_block(h, r'^function ' + fn + r'\(', fn)

# ============ 2. mcolor 材质缓存 ============
old_mcolor = "function mcolor(hex, opts={}){const {roughness:_,metalness:__,...rest}=opts;return new THREE.MeshToonMaterial({color:hex,gradientMap:_gradientMap,...rest});}"
new_mcolor = """/* 材质缓存：无 opts 的纯色材质全局复用（同色只建一次，减少 GPU 状态切换与 GC）。
   带 opts（transparent/emissive 等）不缓存，避免共享材质被运行时改写互相污染 */
const _matCache = new Map();
function mcolor(hex, opts){
  const noOpts = !opts || Object.keys(opts).length === 0;
  if (noOpts) { const c = _matCache.get(hex); if (c) return c; }
  const {roughness:_, metalness:__, ...rest} = opts || {};
  const m = new THREE.MeshToonMaterial({color:hex, gradientMap:_gradientMap, ...rest});
  if (noOpts) _matCache.set(hex, m);
  return m;
}"""
assert old_mcolor in h, 'mcolor 原文不匹配'
h = h.replace(old_mcolor, new_mcolor)
report.append('mcolor 材质缓存（同色复用）')

# ============ 3. addFurniture 双重家具修复 ============
old_head = "function addFurniture(){\n  Object.entries(ZONES).forEach(([id,zone])=>{"
new_head = """function addFurniture(){
  /* 2026-09-10 深度清理：模型包可用时跳过程序化兜底家具构建。
     此前 7 间房先建程序化家具再叠高清 GLB → 双重家具 + 启动变慢。
     now：OFFICE_MODELS 存在 → 非 CFO 房间直接交给 GLB；
          CFO 保留装饰（墙板/地毯/保险柜/桌面小物，与 GLB 共存）；
          模型包缺失时按原逻辑构建程序化兜底。 */
  const hasModels = !!window.OFFICE_MODELS;
  Object.entries(ZONES).forEach(([id,zone])=>{"""
assert h.count(old_head) == 1
h = h.replace(old_head, new_head)

# 3b. 链头包一层 !hasModels
old_ceo = "    if(id==='ceo'){"
assert h.count(old_ceo) == 1
h = h.replace(old_ceo, "    if(!hasModels){\n    if(id==='ceo'){")

# 3c. cfo 从链中摘出：闭 cto 分支 + 闭 hasModels 壳 + 独立 cfo 块
old_cfo = "    }else if(id==='cfo'){"
assert h.count(old_cfo) == 1
h = h.replace(old_cfo, "    }\n    }\n    if(id==='cfo'){")

# 3d. CFO 分支体内的 prog 家具包进 !hasModels
old_p1 = "      createExecDesk(prog, 0.00,-1.10,0);"
assert h.count(old_p1) == 1
h = h.replace(old_p1, "      if(!hasModels){\n      createExecDesk(prog, 0.00,-1.10,0);")
old_p2 = "      createPlant(prog, 2.95,-1.90);"
assert h.count(old_p2) == 1
h = h.replace(old_p2, "      createPlant(prog, 2.95,-1.90);\n      }")

# 3e. cmo 改为独立块（原链尾）
old_cmo = "    }else if(id==='cmo'){"
assert h.count(old_cmo) == 1
h = h.replace(old_cmo, "    }\n    if(id==='cmo'&&!hasModels){")

io.open(PATH, 'w', encoding='utf-8', newline='\n').write(h)
print(f'大小: {orig_size} → {len(h)} (-{orig_size-len(h)} 字节)')
for r in report: print(' -', r)
print('DONE')
