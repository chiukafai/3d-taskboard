# -*- coding: utf-8 -*-
"""把 v4 非对称平面图落到 3D 看板 office-3d-taskboard.html

改造点：
  Z1  ZONES 全量替换（8 房按 v4 矩形 + 门向映射）
  Z2  新增 SITE/LOBBY/COURT/ENTRY + PUB_FLOORS/PUB_WALLS/PUB_DOORS 常量 + createPublicWalls()
  Z3  createMainFloor 重写（场地地面 + 建筑垫层 + 公共区地板 + 偏心圆厅）
  Z4  createRoom 去掉已失效的 cmo openPlan 分支
  Z5  8 个 *_SHOW 家具数组重写
  Z6  addFurniture 中 CFO 装饰 / cmo 程序化兜底 重定位
  Z7  buildMemWall 中 cmo / coo / meeting 白板定位更新
  Z8  createAtrium 重写（接待厅 + 入口前庭 + 东南侧庭）
  Z9  相机 / 雾 / 灯光 / 阴影包围盒 适配 29.6×21.6 新包络
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "office-3d-taskboard.html")
DATA = json.load(open(os.path.join(HERE, "gen3d_v4.json"), encoding="utf-8"))

src = open(HTML, encoding="utf-8").read()
orig_len = len(src)
steps = []


def rep(tag, old, new, count=1):
    global src
    n = src.count(old)
    if n != count:
        print(f"❌ {tag}: 期望命中 {count} 次，实际 {n} 次")
        sys.exit(1)
    src = src.replace(old, new)
    steps.append(tag)


# ---------------------------------------------------------------- Z1 ZONES
Z = DATA["zones"]
order = ["cpo", "meeting", "cfo", "cro", "cmo", "cto", "coo", "ceo"]
byid = {z["id"]: z for z in Z}
zlines = []
for i, zid in enumerate(order):
    z = byid[zid]
    pad = " " * (9 - len(z["id"]))          # 对齐
    zlines.append(
        f"  {zid}:{pad}{{ id:'{zid}', name:'{z['name']}', color:'{z['color']}', "
        f"cx:{z['cx']}, cz:{z['cz']}, w:{z['w']}, d:{z['d']}, "
        f"doorWall:'{z['doorWall']}', doorPos:{z['doorPos']}, carpetColor:'{z['carpet']}' }}"
    )
NEW_ZONES = "const ZONES = {\n" + ",\n".join(zlines) + "\n};"
OLD_ZONES = """const ZONES = {
  // 北排 (z=0~5)：风控 / 运营 / 会议室 / 产品设计
  cro:  { id:'cro',  name:'CRO 风控中心',   color:'#8a5858', cx:2.5,  cz:2.5,  w:5,  d:5, doorWall:'front', doorPos:2.5,  carpetColor:'#604040' },
  coo:  { id:'coo',  name:'COO 运营中心',   color:'#647080', cx:8.5,  cz:2.5,  w:7,  d:5, doorWall:'front', doorPos:8.5,  carpetColor:'#4a5460' },
  meeting:{id:'meeting',name:'战略会议室',   color:'#706898', cx:15,   cz:2.5,  w:6,  d:5, doorWall:'front', doorPos:15,   carpetColor:'#504870' },
  cpo:  { id:'cpo',  name:'CPO 产品设计室', color:'#b08060', cx:21,   cz:2.5,  w:6,  d:5, doorWall:'front', doorPos:21,   carpetColor:'#885840' },
  // 中央大厅 (z=5~13)：贯通东西的开放区（CMO 营销 + 中庭），全部门都开向它
  cmo:  { id:'cmo',  name:'CMO 营销中心',   color:'#b89850', cx:12,   cz:9,    w:24, d:8, doorWall:null,   doorPos:null,  carpetColor:'#907038', openPlan:true },
  // 南排 (z=13~18)：技术 / 战略(正中) / 财务
  cto:  { id:'cto',  name:'CTO 技术中心',   color:'#485c48', cx:4,    cz:15.5, w:8,  d:5, doorWall:'back',  doorPos:4,    carpetColor:'#304030' },
  ceo:  { id:'ceo',  name:'CEO 战略办公室', color:'#5a6880', cx:12,   cz:15.5, w:8,  d:5, doorWall:'back',  doorPos:12,   carpetColor:'#445060' },
  cfo:  { id:'cfo',  name:'CFO 财务中心',   color:'#5a8070', cx:20,   cz:15.5, w:8,  d:5, doorWall:'back',  doorPos:20,   carpetColor:'#406050' }
};"""
NEW_ZONES_FULL = f"""/* ══ 平面图 v4 · 错落非对称布局（2026-09-11 落地）══
   几何基准：_verify/gen_plan_v4_geom.py → plan_v4.json（栅格 0.1m 校验：0 重叠、8 樘门全部通向公共区）
   包络 29.6 × 21.6 m。房间体量刻意错落：西翼 x = 0 / 1.0 / 2.2 三级退台，
   北墙 z = 5.6 / 3.6 / 1.6 / 0.0 四级退台，无一条贯穿到底的长直廊。
   坐标约定：平面图 x → three.js X，平面图 z(向下=南) → three.js Z。
   门向映射：平面图 S 墙 = front(+Z)；N 墙 = back(−Z)；E 墙 = right(+X)；W 墙 = left(−X)。
   公共区：西北入口前庭 → 蛇形支廊 A1/A2/A3 → 偏心圆厅(接待厅) → 东西主廊 B1/B2 → 东南侧庭。 */
const SITE  = {{ ex:29.6, ez:21.6, cx:14.8, cz:10.8 }};   // 包络与几何中心
const LOBBY = {{ x:9.4,  z:10.8, r:1.9 }};                 // 偏心圆厅（接待厅，故意不在中轴上）
const COURT = {{ x1:0.0, z1:0.0, x2:6.6, z2:5.6 }};        // 西北入口前庭（室外）
const YARD  = {{ x1:26.2, z1:12.6, x2:29.6, z2:19.0 }};    // 东南侧庭（室外）
const ENTRY = {{ x:8.0, z:5.6, w:1.6 }};                    // 主入口（A1 北端，双开门）
const EXITX = {{ x:29.4, z:10.5, w:1.2 }};                  // 东侧疏散口

// 公共区地板矩形（栅格贪心分解 → 互不重叠，避免 z-fighting）
const PUB_FLOORS = [
{chr(10).join("  [%s, %s, %s, %s]," % tuple(f) for f in DATA["pub_floors"]).rstrip(',')}
];
// 公共区外墙段（已剔除与房间共墙的段；格式 [朝向, 定位, 起, 止]）
const PAD_RECTS = [
{chr(10).join("  [%s, %s, %s, %s]," % tuple(f) for f in DATA["pad_rects"]).rstrip(',')}
];
const PUB_WALLS = [
{chr(10).join("  ['%s', %s, %s, %s]," % tuple(w) for w in DATA["pub_walls"]).rstrip(',')}
];
// 公共区门洞（主入口 / 疏散口）
const PUB_DOORS = [
  {{ o:'h', k:5.6,  pos:8.0,  w:1.6, kind:'entrance' }},
  {{ o:'v', k:29.4, pos:10.5, w:1.2, kind:'exit' }}
];
{NEW_ZONES}"""
rep("Z1 ZONES 全量替换", OLD_ZONES, NEW_ZONES_FULL)

# ---------------------------------------------------------------- Z2 createPublicWalls
ANCHOR = "function createRoom(zone){"
PUB_WALL_FN = """// ===== 公共区墙体（走廊/前庭围护）=====
function pubWallBox(o, k, a, b, cy, h){
  const wm = MATS.wallInner;
  const m = o === 'h'
    ? new THREE.Mesh(new THREE.BoxGeometry(b - a, h, 0.15), wm)
    : new THREE.Mesh(new THREE.BoxGeometry(0.15, h, b - a), wm);
  m.position.set(o === 'h' ? (a + b) / 2 : k, cy, o === 'h' ? k : (a + b) / 2);
  m.castShadow = true; m.receiveShadow = true; scene.add(m);
  return m;
}
function createPubDoor(o, k, pos, w){
  const dm = new THREE.MeshToonMaterial({map:woodTex('#c8b490','90,72,48'), gradientMap:_gradientMap, side:THREE.DoubleSide});
  const dmGlass = new THREE.MeshToonMaterial({map:woodTex('#c8b490','90,72,48'), gradientMap:_gradientMap, side:THREE.DoubleSide});
  const leaves = w > 1.4 ? 2 : 1, lw = w / leaves;
  for (let i = 0; i < leaves; i++){
    const g = new THREE.Group();
    const panel = new THREE.Mesh(new THREE.BoxGeometry(lw - 0.02, 2.0, 0.06), dm);
    panel.position.set(lw / 2, 1.0, 0); panel.castShadow = true; panel.receiveShadow = true;
    g.add(panel);
    // 玻璃亮窗（主入口观感）
    const gl = new THREE.Mesh(new THREE.BoxGeometry(lw * 0.5, 0.9, 0.02),
      mcolor('#cfe8f5', {transparent:true, opacity:0.55}));
    gl.position.set(lw / 2, 1.45, 0.04); g.add(gl);
    const kn = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 12), mcolor('#c8b088'));
    kn.position.set(lw - 0.16, 1.02, 0.05); g.add(kn);
    if (o === 'h'){
      g.position.set(i === 0 ? pos - w / 2 : pos + w / 2, 0.08, k);
      g.rotation.y = i === 0 ? 0 : Math.PI;
    } else {
      g.position.set(k, 0.08, i === 0 ? pos - w / 2 : pos + w / 2);
      g.rotation.y = i === 0 ? -Math.PI / 2 : Math.PI / 2;
    }
    scene.add(g);
  }
}
function createPublicWalls(){
  const WALL_H = 2.8, DOOR_H = 2.05;
  PUB_WALLS.forEach(seg => {
    const [o, k, s, e] = seg;
    const cuts = PUB_DOORS.filter(d => d.o === o && Math.abs(d.k - k) < 1e-6 && d.pos > s && d.pos < e);
    let pieces = [[s, e]];
    cuts.forEach(d => {
      const out = [];
      pieces.forEach(([a, b]) => {
        if (d.pos - d.w / 2 > a + 0.02) out.push([a, d.pos - d.w / 2]);
        if (d.pos + d.w / 2 < b - 0.02) out.push([d.pos + d.w / 2, b]);
      });
      pieces = out;
    });
    pieces.forEach(([a, b]) => pubWallBox(o, k, a, b, WALL_H / 2, WALL_H));
    cuts.forEach(d => {
      pubWallBox(o, k, d.pos - d.w / 2, d.pos + d.w / 2, (DOOR_H + WALL_H) / 2, WALL_H - DOOR_H); // 门楣
      createPubDoor(o, k, d.pos, d.w);
      if (d.kind === 'entrance'){
        // 入口雨棚 + 立柱 + 踏面（朝北前庭）
        const canopy = new THREE.Mesh(new THREE.BoxGeometry(d.w + 1.6, 0.12, 2.2), MATS.coastWoodDark);
        canopy.position.set(d.pos, 2.55, k - 1.1); canopy.castShadow = true; scene.add(canopy);
        [-1, 1].forEach(sgn => {
          const post = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 2.5, 12), MATS.coastWoodDark);
          post.position.set(d.pos + sgn * (d.w / 2 + 0.6), 1.25, k - 2.0); post.castShadow = true; scene.add(post);
        });
        const step = new THREE.Mesh(new THREE.BoxGeometry(d.w + 1.0, 0.08, 1.0), mcolor('#cfc4b2'));
        step.position.set(d.pos, -0.02, k - 0.55); step.receiveShadow = true; scene.add(step);
      } else {
        const step = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.08, d.w + 0.6), mcolor('#cfc4b2'));
        step.position.set(k + 0.55, -0.02, d.pos); step.receiveShadow = true; scene.add(step);
      }
    });
  });
}
"""
rep("Z2 新增 createPublicWalls", ANCHOR, PUB_WALL_FN + ANCHOR)

# ---------------------------------------------------------------- Z4 createRoom cmo 分支删除
OLD_CMO_BLOCK = """  if(isOpen && zone.id==='cmo'){
    /* 开放大厅补东西两侧外墙：2026-09-11 大厅拓宽到 24 宽后，东侧原本由 CPO 房提供外墙，
       CPO 迁走必须自建，否则建筑东立面出现缺口 */
    const bw=new THREE.Mesh(new THREE.BoxGeometry(wallT,wallH,d),wm);
    bw.position.set(-hw,wallH/2,0);bw.castShadow=true;bw.receiveShadow=true;group.add(bw);
    const be=new THREE.Mesh(new THREE.BoxGeometry(wallT,wallH,d),wm);
    be.position.set(hw,wallH/2,0);be.castShadow=true;be.receiveShadow=true;group.add(be);
    makePlaque(group,zone.name,zone.color,-hw-0.28,2.2,0,-Math.PI/2);
  }
"""
rep("Z4 移除 cmo openPlan 专用分支", OLD_CMO_BLOCK, "")

# ---------------------------------------------------------------- Z3 createMainFloor
OLD_FLOOR = """function createMainFloor(){
  // 建筑主体地板 24×18
  const mt=MATS.woodFloor.clone();mt.map.repeat.set(8,6);
  const f=new THREE.Mesh(new THREE.PlaneGeometry(24,18),mt);
  f.rotation.x=-Math.PI/2;f.position.set(12,-0.04,9);f.receiveShadow=true;scene.add(f);
  const pad=new THREE.Mesh(new THREE.PlaneGeometry(24.2,18.2),mcolor('#b0a490',{roughness:0.88}));
  pad.rotation.x=-Math.PI/2;pad.position.set(12,-0.1,9);pad.receiveShadow=true;scene.add(pad);

  const am=MATS.woodAtrium.clone();am.map.repeat.set(4,3);
  // 东走廊（CMO开放区东缘与CPO/CEO/CFO之间）
  const corrE=new THREE.Mesh(new THREE.PlaneGeometry(2,18),am);
  corrE.rotation.x=-Math.PI/2;corrE.position.set(18,-0.015,9);corrE.receiveShadow=true;scene.add(corrE);
  // 南露台（CTO与CFO之间，对应平面图南侧露台）
  const terraceS=new THREE.Mesh(new THREE.PlaneGeometry(8,5),am.clone());
  terraceS.rotation.x=-Math.PI/2;terraceS.position.set(12,-0.015,15.5);terraceS.receiveShadow=true;scene.add(terraceS);
  // 西露台（建筑外侧西侧，对应平面图西侧大露台）
  const terraceW=new THREE.Mesh(new THREE.PlaneGeometry(4,8),am.clone());
  terraceW.rotation.x=-Math.PI/2;terraceW.position.set(-2,-0.015,9);terraceW.receiveShadow=true;scene.add(terraceW);
}
createMainFloor();"""
NEW_FLOOR = """function createMainFloor(){
  // ── 场地大地面（室外草地） ──
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(96,96),mcolor('#a9c18c',{roughness:0.95}));
  ground.rotation.x=-Math.PI/2;ground.position.set(SITE.cx,-0.17,SITE.cz);ground.receiveShadow=true;scene.add(ground);

  // ── 建筑垫层：随错落外轮廓外扩 0.3m（栅格膨胀后分解，不会在凹口处凸出） ──
  PAD_RECTS.forEach(r=>{
    const m=new THREE.Mesh(new THREE.BoxGeometry(r[2]-r[0],0.10,r[3]-r[1]),mcolor('#b0a490',{roughness:0.88}));
    m.position.set((r[0]+r[2])/2,-0.11,(r[1]+r[3])/2);m.receiveShadow=true;scene.add(m);
  });

  // ── 公共区地板（蛇形支廊 A1/A2/A3 + 东西主廊 B1/B2 + 中央枢纽） ──
  PUB_FLOORS.forEach(r=>{
    const w=r[2]-r[0],d=r[3]-r[1];
    const mt=MATS.woodAtrium.clone();mt.map=mt.map.clone();mt.map.needsUpdate=true;
    mt.map.repeat.set(Math.max(1,Math.round(w/2)),Math.max(1,Math.round(d/2)));
    const m=new THREE.Mesh(new THREE.BoxGeometry(w,0.08,d),mt);
    m.position.set((r[0]+r[2])/2,0.04,(r[1]+r[3])/2);m.receiveShadow=true;scene.add(m);
  });

  // ── 偏心圆厅（接待厅）：浅色石纹圆盘 + 外圈环带 ──
  const disc=new THREE.Mesh(new THREE.CylinderGeometry(LOBBY.r,LOBBY.r,0.06,56),
    new THREE.MeshToonMaterial({map:carpetTex('#e8e0cc'),gradientMap:_gradientMap}));
  disc.position.set(LOBBY.x,0.075,LOBBY.z);disc.receiveShadow=true;scene.add(disc);
  const ring=new THREE.Mesh(new THREE.TorusGeometry(LOBBY.r-0.08,0.05,10,64),
    mcolor('#b8a888',{roughness:0.6}));
  ring.rotation.x=Math.PI/2;ring.position.set(LOBBY.x,0.105,LOBBY.z);ring.receiveShadow=true;scene.add(ring);

  // ── 西北入口前庭（室外）：石板铺装 + 通往主入口的步道 ──
  const pave=new THREE.Mesh(new THREE.PlaneGeometry(COURT.x2-COURT.x1,COURT.z2-COURT.z1),
    new THREE.MeshToonMaterial({map:plankTex('#d8cdb8','150,135,110','#b8a890',false),gradientMap:_gradientMap}));
  pave.rotation.x=-Math.PI/2;pave.position.set((COURT.x1+COURT.x2)/2,-0.05,(COURT.z1+COURT.z2)/2);
  pave.receiveShadow=true;scene.add(pave);
  const walk=new THREE.Mesh(new THREE.PlaneGeometry(3.0,COURT.z2-1.4),
    new THREE.MeshToonMaterial({map:plankTex('#e0d6c2','150,135,110','#b8a890',false),gradientMap:_gradientMap}));
  walk.rotation.x=-Math.PI/2;walk.position.set(ENTRY.x,-0.045,(COURT.z2+1.4)/2);walk.receiveShadow=true;scene.add(walk);

  // ── 东南侧庭（室外）：铺装 ──
  const yard=new THREE.Mesh(new THREE.PlaneGeometry(YARD.x2-YARD.x1,YARD.z2-YARD.z1),
    new THREE.MeshToonMaterial({map:plankTex('#d5cab4','150,135,110','#b5a58c',false),gradientMap:_gradientMap}));
  yard.rotation.x=-Math.PI/2;yard.position.set((YARD.x1+YARD.x2)/2,-0.05,(YARD.z1+YARD.z2)/2);
  yard.receiveShadow=true;scene.add(yard);
}
createMainFloor();"""
rep("Z3 createMainFloor 重写", OLD_FLOOR, NEW_FLOOR)

print("✅ 结构块改造完成")
open(HTML, "w", encoding="utf-8").write(src)
print(f"→ {orig_len} → {len(src)} 字节；步骤：{', '.join(steps)}")
