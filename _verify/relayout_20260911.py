# -*- coding: utf-8 -*-
"""2026-09-11 布局整改：修门牌压门洞 / CFO&CEO 门被封死 / CPO 迁移 / 中央大厅贯通
每步替换都断言命中，命中失败立即报错退出（避免静默改坏文件）。"""
import io, sys, re

P = 'office-3d-taskboard.html'
s = io.open(P, encoding='utf-8').read()
orig_len = len(s)
log = []

def rep(old, new, tag, count=1):
    global s
    n = s.count(old)
    if n != count:
        print(f'❌ [{tag}] 期望命中 {count} 次，实际 {n} 次'); sys.exit(1)
    s = s.replace(old, new)
    log.append(tag)
    print(f'✅ {tag}')

# ── E1. ZONES：CPO 迁东北角、CEO 迁南侧正中、CMO 大厅拓宽 24 ──────────────
old_zones = """const ZONES = {
  // 北排 (z=0~5): 服务区+主卧(对应平面图: 电梯/储物/厨房/餐厅/主卧)
  cro:  { id:'cro',  name:'CRO 风控中心',   color:'#8a5858', cx:2.5,  cz:2.5,  w:5,  d:5, doorWall:'front', doorPos:2.5,  carpetColor:'#604040' },
  coo:  { id:'coo',  name:'COO 运营中心',   color:'#647080', cx:8.5,  cz:2.5,  w:7,  d:5, doorWall:'front', doorPos:8.5,  carpetColor:'#4a5460' },
  meeting:{id:'meeting',name:'战略会议室',   color:'#706898', cx:15,   cz:2.5,  w:6,  d:5, doorWall:'front', doorPos:15,   carpetColor:'#504870' },
  ceo:  { id:'ceo',  name:'CEO 战略办公室', color:'#5a6880', cx:21,   cz:2.5,  w:6,  d:5, doorWall:'front', doorPos:21,   carpetColor:'#445060' },
  // 中央 (z=5~13): 横厅(对应平面图: 客厅+书房)
  cmo:  { id:'cmo',  name:'CMO 营销中心',   color:'#b89850', cx:9,    cz:9,    w:18, d:8, doorWall:null,   doorPos:null,  carpetColor:'#907038', openPlan:true },
  cpo:  { id:'cpo',  name:'CPO 产品设计室', color:'#b08060', cx:21,   cz:9,    w:6,  d:8, doorWall:'left',  doorPos:9,    carpetColor:'#885840' },
  // 南排 (z=13~18): 角落私密房(对应平面图: 西南卧室+东南卧室)
  cto:  { id:'cto',  name:'CTO 技术中心',   color:'#485c48', cx:4,    cz:15.5, w:8,  d:5, doorWall:'back',  doorPos:4,    carpetColor:'#304030' },
  cfo:  { id:'cfo',  name:'CFO 财务中心',   color:'#5a8070', cx:20,   cz:15.5, w:8,  d:5, doorWall:'back',  doorPos:20,   carpetColor:'#406050' }
};"""
new_zones = """/* 布局变更 2026-09-11（Kingsley 标注整改）：
   旧布局的致命问题：CPO 占着东侧中段(x18~24,z5~13) → 其南北两邻(CEO 南门 / CFO 北门)的
   门洞后面就是 CPO 的墙，等于被封死在别人房里；CMO 白板又堵在 CPO 门口。
   新布局：中央大厅贯通东西(24×8)，所有办公室的门都开向大厅；
           CEO 迁到南侧正中（正对大厅），CPO 迁到东北角，各自的门都能正常使用。 */
const ZONES = {
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
rep(old_zones, new_zones, 'E1 ZONES 重排')

# ── E2. 门牌避开门口（原先居中 → 正好压门洞） ─────────────────────────
old_plq = """    let px=0,pz=hw?hd:0,pr=0,py=2.4;
    if(doorWall==='front'||doorWall==='back'){px=0;pz=(doorWall==='front'?hd+0.25:-hd-0.25);pr=(doorWall==='front'?0:Math.PI);}
    else if(doorWall==='right'){px=hw+0.25;pz=0;pr=-Math.PI/2;}
    else if(doorWall==='left'){px=-hw-0.25;pz=0;pr=Math.PI/2;}
    makePlaque(group,zone.name,zone.color,px,py,pz,pr);"""
new_plq = """    /* 门牌位置 2026-09-11 修复：原先固定挂在门墙正中 → 正好压在门洞上（用户标记 Bug）。
       新规则：取门洞两侧较长的实墙段，把牌面居中放进该段；段太窄就按 1.6m 缩牌面。 */
    const along=(doorWall==='front'||doorWall==='back'||doorWall==='left'||doorWall==='right')?((doorWall==='front'||doorWall==='back')?(doorPos-cx):(doorPos-cz)):0;
    const axisLen=(doorWall==='front'||doorWall==='back')?w:d;
    const segA=(along-gapW/2)+axisLen/2, segB=axisLen/2-(along+gapW/2);
    const segLen=Math.max(segA,segB), segSign=(segA>=segB)?-1:1;
    const pw=Math.min(2.8,Math.max(1.6,segLen-0.5));
    const plqAt=along+segSign*(gapW/2+segLen/2);      // 门牌沿墙位置（实墙段中心）
    const off=0.14;                                    // 贴墙外侧：墙半厚 0.075 + 牌厚 0.045 + 余量
    let px=0,pz=0,pr=0,py=2.4;
    if(doorWall==='front'){px=plqAt;pz= hd+off;pr=0;}
    else if(doorWall==='back'){px=plqAt;pz=-hd-off;pr=Math.PI;}
    else if(doorWall==='right'){px= hw+off;pz=plqAt;pr=-Math.PI/2;}
    else if(doorWall==='left'){px=-hw-off;pz=plqAt;pr=Math.PI/2;}
    makePlaque(group,zone.name,zone.color,px,py,pz,pr,pw);"""
rep(old_plq, new_plq, 'E2 门牌避开门洞')

# ── E3. makePlaque：支持自定义宽度 + 背面文字不再镜像 ──────────────────
old_mp = """function makePlaque(parent, text, color, x, y, z, rotY=0){
  const group=new THREE.Group();
  const w=2.8, h=0.7;"""
new_mp = """function makePlaque(parent, text, color, x, y, z, rotY=0, pw=2.8){
  const group=new THREE.Group();
  const w=pw, h=Math.max(0.55, Math.min(0.7, pw*0.26));"""
rep(old_mp, new_mp, 'E3a makePlaque 支持宽度')

old_back = """  const back=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08), pMat.clone());
  back.position.z=-0.03;back.rotation.y=Math.PI;group.add(back);"""
new_back = """  // 背面：贴图水平镜像一次，从背后看文字才是正的（原先背面文字是反的）
  const bMap=tex.clone(); bMap.wrapS=THREE.RepeatWrapping; bMap.center.set(0.5,0.5);
  bMap.repeat.x=-1; bMap.needsUpdate=true;
  const back=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08),
    new THREE.MeshBasicMaterial({map:bMap,transparent:true,depthTest:false,depthWrite:false}));
  back.position.z=-0.03;back.rotation.y=Math.PI;group.add(back);"""
rep(old_back, new_back, 'E3b 门牌背面文字镜像修正')

# ── E4. 侧墙门铰链侧修正（原门扇整体偏 0.8m，只盖住半个门洞） ───────────
old_door = """    else if(doorWall==='right'){dpx=hw;dpz=(doorPos-cz)+gapW/2;dpr=-Math.PI/2;}
    else if(doorWall==='left'){dpx=-hw;dpz=(doorPos-cz)-gapW/2;dpr=Math.PI/2;}"""
new_door = """    /* 2026-09-11 修复：侧墙门的铰链侧算反 → 门扇整体偏移 0.8m、门洞只盖住一半 */
    else if(doorWall==='right'){dpx=hw;dpz=(doorPos-cz)-gapW/2;dpr=-Math.PI/2;}
    else if(doorWall==='left'){dpx=-hw;dpz=(doorPos-cz)+gapW/2;dpr=Math.PI/2;}"""
rep(old_door, new_door, 'E4 侧墙门扇对位')

# ── E5. CMO 大厅：补东侧外墙（CPO 迁走后原来靠它挡）+ 门牌朝外 ──────────
old_cmowall = """  if(isOpen && zone.id==='cmo'){
    const bw=new THREE.Mesh(new THREE.BoxGeometry(wallT,wallH,d),wm);
    bw.position.set(-hw,wallH/2,0);bw.castShadow=true;bw.receiveShadow=true;group.add(bw);
    makePlaque(group,zone.name,zone.color,-hw-0.25,2.2,0,Math.PI/2);
  }"""
new_cmowall = """  if(isOpen && zone.id==='cmo'){
    /* 开放大厅补东西两侧外墙：2026-09-11 大厅拓宽到 24 宽后，东侧原本由 CPO 房提供外墙，
       CPO 迁走必须自建，否则建筑东立面出现缺口 */
    const bw=new THREE.Mesh(new THREE.BoxGeometry(wallT,wallH,d),wm);
    bw.position.set(-hw,wallH/2,0);bw.castShadow=true;bw.receiveShadow=true;group.add(bw);
    const be=new THREE.Mesh(new THREE.BoxGeometry(wallT,wallH,d),wm);
    be.position.set(hw,wallH/2,0);be.castShadow=true;be.receiveShadow=true;group.add(be);
    makePlaque(group,zone.name,zone.color,-hw-0.28,2.2,0,-Math.PI/2);
  }"""
rep(old_cmowall, new_cmowall, 'E5 大厅东西外墙 + CMO 门牌朝外')

# ── E6. CMO 白板挪到东墙（原先堵在 CPO 门口） ─────────────────────────
old_wb = """    if(zone.id==='cmo'){
      // CMO：走廊型办公室（沿 Z 纵深、与其他房间垂直）→ 落地白板靠右侧墙、板面朝 +X，正对主视角而非侧面
      x=zone.cx+hw-0.35; z=zone.cz; rotY=Math.PI/2;
    }else if(zone.id==='coo'){"""
new_wb = """    if(zone.id==='cmo'){
      // CMO：2026-09-11 CPO 迁走后大厅贯通 → 落地白板靠东墙，板面朝 -X（朝大厅内）
      // 旧位置 (cx+hw-0.35, cz)= 原东墙内侧，正好堵在 CPO 门口（用户标记 Bug）
      x=zone.cx+hw-0.35; z=zone.cz; rotY=-Math.PI/2;
    }else if(zone.id==='coo'){"""
rep(old_wb, new_wb, 'E6 CMO 白板移至东墙')

# ── E7. 投影仪悬挂高度修正（原 y 高度落在墙顶之上，会飘在屋顶外） ────────
old_pj = """      const pj=new THREE.Mesh(new THREE.BoxGeometry(0.42,0.22,0.5),mcolor('#3a3632',{roughness:0.3,metalness:0.4}));pj.position.set(0,2.45,0.55);g.add(pj);
      const lens=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,0.1,16),mcolor('#101010'));lens.rotation.x=Math.PI/2;lens.position.set(0,2.45,0.18);g.add(lens);"""
new_pj = """      const pj=new THREE.Mesh(new THREE.BoxGeometry(0.42,0.22,0.5),mcolor('#3a3632',{roughness:0.3,metalness:0.4}));pj.position.set(0,1.15,0.55);g.add(pj);
      const lens=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,0.1,16),mcolor('#101010'));lens.rotation.x=Math.PI/2;lens.position.set(0,1.15,0.18);g.add(lens);"""
rep(old_pj, new_pj, 'E7 投影仪吊装高度')

# ── E8. CEO_SHOW：6×5(门前) → 8×5(门后，朝大厅)，沿用 CFO 同门向摆法 ────
old_ceo_show = """const CEO_SHOW = [
  /* CEO 6×5  门在前墙(+Z) → 椅背朝后墙(-Z)，面朝门 r=π
     修正：exec_chair 后挪至 -1.80（更贴背墙）、exec_desk 提到 -1.00（避开记忆屏 z=+0.9 与访客椅区） */
  { key:'exec_desk',      p:[ 0.00,-1.00], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.80], r:Math.PI,   h:1.20, tint:[0x33506B,0.45] },
  { key:'office_chair',   p:[-0.95, 0.10], r:Math.PI,   h:1.00, tint:[0x8A5858,0.40] },
  { key:'office_chair',   p:[ 0.95, 0.10], r:Math.PI,   h:1.00, tint:[0x8A5858,0.40] },
  { key:'filing_cabinet', p:[-2.45, 1.40], r:Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-2.30,-1.85], r:0,         h:0.60 },
  { key:'plant_potted',   p:[ 2.40, 1.80], r:Math.PI/2, h:0.60 },
];"""
new_ceo_show = """const CEO_SHOW = [
  /* CEO 8×5  门在后墙(-Z，开向中央大厅)——2026-09-11 由东北角迁至南侧正中。
     与 CFO 房同门向，直接沿用 CFO 已验证的相对摆法（桌/椅靠门侧、访客椅在对面、柜+绿植在侧） */
  { key:'exec_desk',      p:[ 0.00,-1.10], r:0,          h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.60], r:0,          h:1.20, tint:[0x33506B,0.45] },
  { key:'office_chair',   p:[-0.90, 0.10], r:Math.PI,    h:1.00, tint:[0x8A5858,0.40] },
  { key:'office_chair',   p:[ 0.90, 0.10], r:Math.PI,    h:1.00, tint:[0x8A5858,0.40] },
  { key:'filing_cabinet', p:[-3.45,-1.40], r:Math.PI/2,  h:1.10 },
  { key:'plant_potted',   p:[-3.30, 1.80], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 3.30,-1.85], r:0,          h:0.60 },
];"""
rep(old_ceo_show, new_ceo_show, 'E8 CEO_SHOW 重摆(8×5 门朝大厅)')

# ── E9. CPO_SHOW：6×8(门左墙) → 6×5(门前墙，朝大厅)，沿用北排同门向摆法 ──
old_cpo_show = """const CPO_SHOW = [
  /* CPO 6×8  门在左墙(-X) → 椅背朝右墙(+X)、面朝门 r=π/2
     样板：绘图桌(已用exec_desk近似大桌)+1椅+2显示器+小桌+会客椅+文件柜+绿植+墙上色板(用植物代)  */
  { key:'exec_desk',      p:[ 1.95, 0.00], r:Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[ 1.40, 0.00], r:Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 1.95,-0.45], r:Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 1.95, 0.45], r:Math.PI/2, h:0.50, y:0.76 },
  { key:'coffee_table',   p:[-1.60, 1.80], r:0,         h:0.45 },
  { key:'office_chair',   p:[-1.60, 2.45], r:Math.PI,   h:1.00, tint:[0xB08060,0.45] },
  { key:'filing_cabinet', p:[ 2.55, 2.40], r:-Math.PI/2,h:1.10 },
  { key:'plant_potted',   p:[-2.40, 2.85], r:0,         h:0.60 },
  { key:'plant_potted',   p:[-2.40,-2.70], r:0,         h:0.60 },
];"""
new_cpo_show = """const CPO_SHOW = [
  /* CPO 6×5  门在前墙(+Z，开向中央大厅)——2026-09-11 由东侧中段迁至东北角。
     与北排同门向，沿用已认可的相对摆法（椅贴后墙、面朝门；桌在前；显示器上桌） */
  { key:'exec_desk',      p:[ 0.00,-1.00], r:Math.PI,   h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-1.80], r:Math.PI,   h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.45,-0.92], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.45,-0.92], r:Math.PI,   h:0.50, y:0.76 },
  { key:'office_chair',   p:[-1.55, 0.55], r:Math.PI,   h:1.00, tint:[0xB08060,0.45] },
  { key:'filing_cabinet', p:[ 2.45,-1.35], r:Math.PI,   h:1.10 },
  { key:'plant_potted',   p:[-2.40, 1.70], r:0,         h:0.60 },
];"""
rep(old_cpo_show, new_cpo_show, 'E9 CPO_SHOW 重摆(6×5 门朝大厅)')

# ── E10. CMO_SHOW：18×8 → 24×8，工位簇/洽谈角重新分布，避开各门落客区 ──
old_cmo_show = """const CMO_SHOW = [
  /* CMO 18×8 横厅 openPlan 无门 → 1张大桌 + 1皮椅(背中央墙)+ 2显示器 + 沙发洽谈角 + 文件柜 + 绿植
     注：CMO 无门、单墙开口，椅子按"背实墙/正面朝主要活动方向"（面向中央桌阵）。 */
  { key:'exec_desk',      p:[ 4.50, 0.00], r:-Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[ 5.05, 0.00], r:-Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 4.50,-0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 4.50, 0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'sofa',           p:[-3.50, 0.00], r:Math.PI/2, h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-2.50, 0.00], r:Math.PI/2, h:0.45 },
  { key:'filing_cabinet', p:[ 7.80,-2.80], r:-Math.PI/2, h:1.10 },
  { key:'filing_cabinet', p:[ 7.80, 2.80], r:-Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-8.20,-3.20], r:0,          h:0.60 },
  { key:'plant_potted',   p:[-8.20, 3.20], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 5.20, 3.20], r:Math.PI/2,  h:0.60 },   // 远离右墙大记忆屏
];"""
new_cmo_show = """const CMO_SHOW = [
  /* CMO 24×8 中央大厅 openPlan 无门 —— 2026-09-11 大厅由 18 拓宽到 24（贯通东侧）。
     工位岛居中偏东、洽谈角在西、文件柜靠东墙；3 处绿植填补空区。
     注意：北墙 4 樘门(x=2.5/8.5/15/21)、南墙 3 樘门(x=4/12/20) 前各留 ~1.5m 落客区，家具全部避开。 */
  { key:'exec_desk',      p:[ 5.60, 0.00], r:-Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[ 6.20, 0.00], r:-Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 5.60,-0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 5.60, 0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'sofa',           p:[-4.60, 0.00], r:Math.PI/2, h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-3.60, 0.00], r:Math.PI/2, h:0.45 },
  { key:'filing_cabinet', p:[10.20,-3.10], r:-Math.PI/2, h:1.10 },
  { key:'filing_cabinet', p:[10.20, 3.10], r:-Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-11.20,-3.20], r:0,         h:0.60 },
  { key:'plant_potted',   p:[-11.20, 3.20], r:0,         h:0.60 },
  { key:'plant_potted',   p:[ 9.60, 3.20], r:Math.PI/2,  h:0.60 },
];"""
rep(old_cmo_show, new_cmo_show, 'E10 CMO_SHOW 适配 24×8 大厅')

# ── E11. 中庭装饰：东走廊组删除、南露台组移入大厅西端（原地已是 CEO 房） ──
old_atrium = """  // 入户区（西北角，CRO门外）
  createCoastalPlant(g,1,5,1.2);
  createShellJar(g,2.5,5,0,0.8);

  // 东走廊（CMO与CPO之间，x=18, z=5~13）
  createCoastalBench(g,18.2,6,-Math.PI/2);
  createCoastalBench(g,18.2,12,Math.PI/2);
  createCoastalPlant(g,18.4,7,1);
  createCoastalPlant(g,18.4,11,1);
  createShellJar(g,18.4,9,Math.PI/2,0.9);

  // 南露台（CTO与CFO之间，x=8~16, z=13~18）
  createCoastalBench(g,9,16.5,-Math.PI/2);
  createCoastalBench(g,15,16.5,Math.PI/2);
  createCoastalPlant(g,10,14,1);
  createCoastalPlant(g,12,14,1.2);
  createCoastalPlant(g,14,14,1);
  createShellJar(g,9,17.5,0,1.0);
  createShellJar(g,15,17.5,0,1.0);
  createShellFountain(g,12,16.5);
  createRopeCoil(g,10,0.1,17,0,0.25);
  createRopeCoil(g,14,0.1,17,0,0.25);"""
new_atrium = """  // 入户区（西北角，CRO 门外）——2026-09-11 从门洞正前方挪开，改贴西墙
  createCoastalPlant(g,0.55,5.9,1.2);
  createShellJar(g,0.55,7.2,0,0.8);

  /* 2026-09-11 中庭重整：
     · 原「东走廊」组（x≈18.2）当时服务 CMO 与 CPO 之间的窄走廊；CPO 迁走后该处变成大厅中部，
       家具会挡视线，整组删除（大厅家具由 CMO_SHOW 提供）。
     · 原「南露台」组（x=8~16, z=13~18）所在位置已是新 CEO 战略办公室，整组移入大厅西端做室内花园。 */
  createCoastalBench(g,1.4,6.6,0);
  createCoastalBench(g,1.4,11.4,Math.PI);
  createCoastalPlant(g,2.8,7.8,1);
  createCoastalPlant(g,2.8,10.2,1);
  createShellFountain(g,1.4,9.0);
  createShellJar(g,3.0,9.0,0,0.9);
  createRopeCoil(g,0.5,0.1,8.0,0,0.2);
  createRopeCoil(g,0.5,0.1,10.0,0,0.2);"""
rep(old_atrium, new_atrium, 'E11 中庭装饰重组')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print(f'\n完成 {len(log)} 项修改：{orig_len} → {len(s)} 字节')
