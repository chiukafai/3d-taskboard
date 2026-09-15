# -*- coding: utf-8 -*-
"""v5.1 修复 A/B：门牌镜像(3处) + CFO 地毯共面闪烁
用法：python _verify/fix_v51_ab.py
可重跑（幂等）：已改过会报"未命中"并中止，不会破坏文件。
"""
import io, sys, shutil, os

HTML = 'office-3d-taskboard.html'
s = io.open(HTML, encoding='utf-8').read()
orig = s
log = []


def rep(old, new, tag, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, '[%s] 命中 %d 处，期望 %d —— 中止' % (tag, n, cnt)
    s = s.replace(old, new, cnt)
    log.append('OK  ' + tag)


# ── A1. makePlaque：撤销背面的多余水平镜像 ────────────────────────────────
rep("""  // 背面：贴图水平镜像一次，从背后看文字才是正的（原先背面文字是反的）
  const bMap=tex.clone(); bMap.wrapS=THREE.RepeatWrapping; bMap.center.set(0.5,0.5);
  bMap.repeat.x=-1; bMap.needsUpdate=true;
  const back=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08),
    new THREE.MeshBasicMaterial({map:bMap,transparent:true,depthTest:false,depthWrite:false}));""",
"""  /* 背面：直接用同一张贴图。
     2026-09-11 修复：Group 已绕 Y 转 π，从背面看文字本来就是正的；
     早前额外做了一次 repeat.x=-1 的水平镜像，反而把背面文字变成了镜像字
     （东/西墙门牌正面朝房内时，走廊侧看到的就是这面镜像字）。 */
  const back=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08),
    new THREE.MeshBasicMaterial({map:tex,transparent:true,depthTest:false,depthWrite:false}));""",
    'A1 makePlaque 撤销背面镜像贴图')

# ── A2. 东/西墙门牌 pr 取反，让"正面"朝走廊 ────────────────────────────────
rep("""    else if(doorWall==='right'){px= hw+off;pz=plqAt;pr=-Math.PI/2;}
    else if(doorWall==='left'){px=-hw-off;pz=plqAt;pr=Math.PI/2;}""",
"""    /* 2026-09-11 修复：right/left 门的 pr 取反。
       原来右墙门牌 pr=-π/2 → 牌面法线指向 −X（房内），走廊侧只能看到背面
       → CPO / 战略会议室 / CFO 三块牌子文字是镜像的。 */
    else if(doorWall==='right'){px= hw+off;pz=plqAt;pr=Math.PI/2;}
    else if(doorWall==='left'){px=-hw-off;pz=plqAt;pr=-Math.PI/2;}""",
    'A2 东墙/西墙门牌朝向取反')

# ── B. CFO 两块地毯共面 Z-fighting ────────────────────────────────────────
rep("""      // 地毯分区：主办公区米白（西侧）+ 会客区鼠尾草绿（北侧，与 CFO_SHOW 一致）
      const rugA=new THREE.Mesh(new THREE.PlaneGeometry(3.0,3.4),new THREE.MeshStandardMaterial({color:0xf0ebe0,roughness:0.92}));
      rugA.rotation.x=-Math.PI/2;rugA.position.set(-1.9,0.095,0.2);rugA.receiveShadow=true;g.add(rugA);
      const rugB=new THREE.Mesh(new THREE.PlaneGeometry(3.2,2.1),new THREE.MeshStandardMaterial({color:0xa8bca4,roughness:0.92}));
      rugB.rotation.x=-Math.PI/2;rugB.position.set(-0.5,0.095,-1.72);rugB.receiveShadow=true;g.add(rugB);""",
"""      /* 地毯分区：主办公区米白（西侧）+ 会客区鼠尾草绿（北侧，与 CFO_SHOW 一致）
         2026-09-11 修复：两块原先 y 同为 0.095 且 x/z 相交 1.70×0.83 → 共面 Z-fighting 不停闪烁。
         现在按 z 切分：rugA z∈[-1.15,1.95]，rugB z∈[-2.55,-1.05]，中间留 0.10m 缝；
         同时把 rugA 从 x=-3.4 收到 -3.15，不再越过西墙（房宽 6.4 → 内边界 ±3.2）。 */
      const rugA=new THREE.Mesh(new THREE.PlaneGeometry(2.9,3.1),new THREE.MeshStandardMaterial({color:0xf0ebe0,roughness:0.92}));
      rugA.rotation.x=-Math.PI/2;rugA.position.set(-1.70,0.095,0.40);rugA.receiveShadow=true;g.add(rugA);
      const rugB=new THREE.Mesh(new THREE.PlaneGeometry(3.2,1.5),new THREE.MeshStandardMaterial({color:0xa8bca4,roughness:0.92}));
      rugB.rotation.x=-Math.PI/2;rugB.position.set(-0.60,0.095,-1.80);rugB.receiveShadow=true;g.add(rugB);""",
    'B CFO 地毯去共面重叠')

# ── 备份 + 写回 ────────────────────────────────────────────────────────────
bak = HTML + '.bak_pre_v51_20260911'
if not os.path.exists(bak):
    shutil.copy2(HTML, bak)
    print('已备份 →', bak)
io.open(HTML, 'w', encoding='utf-8', newline='').write(s)
for l in log:
    print(' ', l)
print('主文件 %d B → %d B' % (len(orig.encode('utf-8')), len(s.encode('utf-8'))))
