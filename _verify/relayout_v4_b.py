# -*- coding: utf-8 -*-
"""v4 落地 B 阶段：8 房家具重排 + CFO 装饰重定位 + 记忆屏 + 中庭 + 相机/灯光"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "office-3d-taskboard.html")
src = open(HTML, encoding="utf-8").read()
orig = len(src)
steps = []


def rep(tag, old, new, count=1):
    global src
    n = src.count(old)
    if n != count:
        print(f"❌ {tag}: 期望 {count} 次，实际 {n} 次")
        sys.exit(1)
    src = src.replace(old, new)
    steps.append(tag)


# ══════════════════════════════════ B1 家具数组（CFO…MEETING 一整段替换）
OLD_SHOW_START = "const CFO_SHOW = ["
i0 = src.index(OLD_SHOW_START)
i1 = src.index("function tintModel(root, hex, strength){")
OLD_SHOW = src[i0:i1]

NEW_SHOW = """/* ══ 家具摆位（2026-09-11 按 v4 非对称布局逐房重排）══
   两条实测朝向约定（_verify/probe_facing2.mjs 实测顶点分布得到）：
     · exec_chair / sofa：r=0 面朝 +Z（靠背在 −Z）
     · office_chair：r=0 面朝 **−Z**（靠背在 +Z，与 exec_chair 相反）
   摆位铁律：椅贴桌子靠门一侧、人面朝桌子（背对门）；桌与主椅同 r；显示器压桌面朝主椅。
   门向 ↔ 人朝向：front(+Z 南墙) → 人面朝 −Z(r=π)；back(−Z 北墙) → 人面朝 +Z(r=0)；
                  right(+X 东墙) → 人面朝 −X(r=−π/2)。 */
const CPO_SHOW = [
  /* CPO 产品设计室 6.6×5.4（35.6㎡）· 门在东墙(+X) */
  { key:'exec_desk',      p:[-1.70, 0.00], r:-Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[-1.15, 0.00], r:-Math.PI/2, h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-1.62, 0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'office_monitor', p:[-1.62,-0.45], r:-Math.PI/2, h:0.50, y:0.76 },
  { key:'office_chair',   p:[ 0.70, 1.55], r:0,          h:1.00, tint:[0xB08060,0.45] },
  { key:'filing_cabinet', p:[ 2.90,-1.70], r:-Math.PI/2,h:1.10 },
  { key:'plant_potted',   p:[-2.60,-2.10], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.75, 2.05], r:0,          h:0.60 },
];
const MEETING_SHOW = [
  /* 战略会议室 6.4×5.4（34.6㎡）· 门在东墙(+X) · 双沙发对坐 + 茶几，白板居中靠南墙 */
  { key:'sofa',           p:[-0.40, 0.95], r:Math.PI,    h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'sofa',           p:[-0.40,-0.95], r:0,          h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-0.40, 0.00], r:0,          h:0.45 },
  { key:'office_chair',   p:[ 1.75, 1.05], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'office_chair',   p:[ 1.75,-1.05], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[ 2.65, 2.05], r:0,          h:0.60 },
  { key:'plant_potted',   p:[-2.85,-2.05], r:0,          h:0.60 },
];
const CFO_SHOW = [
  /* CFO 财务中心 6.4×5.2（33.3㎡）· 门在东墙(+X) → 人面朝 −X（背对门）；会客区在北侧 */
  { key:'exec_desk',      p:[-1.90, 0.30], r:-Math.PI/2, h:0.76 },
  { key:'exec_chair',     p:[-1.35, 0.30], r:-Math.PI/2, h:1.20, tint:[0x33506B,0.50] },  // 深海军蓝
  { key:'laptop',         p:[-1.88, 0.05], r:Math.PI/2,  h:0.22, y:0.76, tint:[0x55595F,0.30] },
  { key:'office_chair',   p:[-0.05, 1.05], r:Math.PI/2,  h:1.00, tint:[0x7C9A82,0.50] },  // 鼠尾草绿·访客
  { key:'office_chair',   p:[-0.05,-0.45], r:Math.PI/2,  h:1.00, tint:[0x7C9A82,0.50] },
  { key:'sofa',           p:[-1.10,-1.75], r:0,          h:0.80, tint:[0x6F8FA6,0.45] },  // 灰蓝
  { key:'coffee_table',   p:[-0.30,-1.75], r:Math.PI/2,  h:0.45 },
  { key:'filing_cabinet', p:[ 1.30,-2.20], r:-Math.PI/2, h:1.10, tint:[0x55595F,0.40] },  // 炭灰
  { key:'plant_potted',   p:[-2.75, 1.65], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.70,-2.10], r:0,          h:0.60 },
];
const CRO_SHOW = [
  /* CRO 风控中心 6.2×5.0（31.0㎡）· 门在南墙(+Z) → 人面朝 −Z；北墙挂投影屏 */
  { key:'exec_desk',      p:[ 0.00,-1.50], r:Math.PI,    h:0.76 },
  { key:'exec_chair',     p:[ 0.00,-0.95], r:Math.PI,    h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.45,-1.42], r:Math.PI,    h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.45,-1.42], r:Math.PI,    h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-2.60, 0.70], r:Math.PI/2,  h:1.10, tint:[0x666060,0.30] },
  { key:'filing_cabinet', p:[-2.60, 1.70], r:Math.PI/2,  h:1.10, tint:[0x666060,0.30] },
  { key:'office_chair',   p:[ 2.35, 1.30], r:0,          h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[ 2.55,-1.80], r:0,          h:0.60 },
];
const CMO_SHOW = [
  /* CMO 营销中心 8.2×8.6（70.5㎡，全楼最大）· 门在南墙偏西 → 人面朝 −Z；
     两组工位并排 + 西南洽谈角 + 东墙储物，北墙挂白板 */
  { key:'exec_desk',      p:[-1.70,-1.90], r:Math.PI,    h:0.76 },
  { key:'exec_chair',     p:[-1.70,-1.35], r:Math.PI,    h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-2.15,-1.82], r:Math.PI,    h:0.50, y:0.76 },
  { key:'office_monitor', p:[-1.25,-1.82], r:Math.PI,    h:0.50, y:0.76 },
  { key:'exec_desk',      p:[ 1.30,-1.90], r:Math.PI,    h:0.76 },
  { key:'exec_chair',     p:[ 1.30,-1.35], r:Math.PI,    h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 0.85,-1.82], r:Math.PI,    h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 1.75,-1.82], r:Math.PI,    h:0.50, y:0.76 },
  { key:'sofa',           p:[-2.55, 1.90], r:Math.PI/2,  h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-1.55, 1.90], r:Math.PI/2,  h:0.45 },
  { key:'office_chair',   p:[-0.30, 2.30], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'office_chair',   p:[-0.30, 1.50], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'filing_cabinet', p:[ 3.75, 0.40], r:-Math.PI/2, h:1.10 },
  { key:'filing_cabinet', p:[ 3.75,-0.60], r:-Math.PI/2, h:1.10 },
  { key:'plant_potted',   p:[-3.70,-3.60], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 3.70,-3.60], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 3.70, 3.60], r:0,          h:0.60 },
];
const CTO_SHOW = [
  /* CTO 技术中心 5.8×7.0（40.6㎡）· 门在南墙(+Z) → 人面朝 −Z；机柜靠西墙、北墙挂屏 */
  { key:'exec_desk',      p:[ 0.60,-1.30], r:Math.PI,    h:0.76 },
  { key:'exec_chair',     p:[ 0.60,-0.75], r:Math.PI,    h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[ 0.15,-1.22], r:Math.PI,    h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 1.05,-1.22], r:Math.PI,    h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-2.45,-0.60], r:Math.PI/2,  h:1.10, tint:[0x33383A,0.45] },
  { key:'filing_cabinet', p:[-2.45, 0.40], r:Math.PI/2,  h:1.10, tint:[0x33383A,0.45] },
  { key:'coffee_table',   p:[ 1.70, 2.20], r:0,          h:0.45 },
  { key:'office_chair',   p:[ 1.70, 2.85], r:0,          h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.30,-2.90], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.35, 3.10], r:0,          h:0.60 },
];
const COO_SHOW = [
  /* COO 运营中心 8.0×7.8（62.4㎡）· 门在北墙(−Z) → 人面朝 +Z（背对门）；南侧设洽谈角 */
  { key:'exec_desk',      p:[ 0.30,-1.20], r:0,          h:0.76 },
  { key:'exec_chair',     p:[ 0.30,-1.80], r:0,          h:1.20, tint:[0x33506B,0.40] },
  { key:'office_monitor', p:[-0.15,-1.12], r:0,          h:0.50, y:0.76 },
  { key:'office_monitor', p:[ 0.75,-1.12], r:0,          h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[-3.55,-3.35], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },
  { key:'filing_cabinet', p:[-2.55,-3.35], r:Math.PI,    h:1.10, tint:[0x5A5560,0.30] },
  { key:'sofa',           p:[-1.60, 1.80], r:Math.PI/2,  h:0.80, tint:[0x6F8FA6,0.40] },
  { key:'coffee_table',   p:[-0.60, 1.80], r:Math.PI/2,  h:0.45 },
  { key:'office_chair',   p:[ 0.70, 2.25], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'office_chair',   p:[ 0.70, 1.35], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[ 3.55,-3.30], r:0,          h:0.60 },
  { key:'plant_potted',   p:[-3.60, 3.30], r:0,          h:0.60 },
];
const CEO_SHOW = [
  /* CEO 战略办公室 6.6×6.6（43.6㎡）· 门在北墙(−Z) → 人面朝 +Z；东南设会客角 */
  { key:'exec_desk',      p:[-0.90,-1.40], r:0,          h:0.76 },
  { key:'exec_chair',     p:[-0.90,-2.00], r:0,          h:1.20, tint:[0x33506B,0.45] },
  { key:'office_monitor', p:[-1.35,-1.32], r:0,          h:0.50, y:0.76 },
  { key:'office_monitor', p:[-0.45,-1.32], r:0,          h:0.50, y:0.76 },
  { key:'laptop',         p:[-0.90,-1.48], r:0,          h:0.22, y:0.76, tint:[0x55595F,0.30] },
  { key:'filing_cabinet', p:[ 2.95,-2.60], r:-Math.PI/2, h:1.10 },
  { key:'sofa',           p:[ 1.45, 1.55], r:Math.PI,    h:0.80, tint:[0x6F8FA6,0.45] },
  { key:'coffee_table',   p:[ 1.45, 0.55], r:0,          h:0.45 },
  { key:'office_chair',   p:[ 0.35, 0.55], r:-Math.PI/2, h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.85,-2.85], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.90, 2.85], r:0,          h:0.60 },
];

"""
rep("B1 家具数组重排", OLD_SHOW, NEW_SHOW)

# ══════════════════════════════════ B2 CFO 装饰重定位
OLD_CFO = src[src.index("    if(id==='cfo'){"):src.index("    if(id==='cmo'&&!hasModels){")]
NEW_CFO = """    if(id==='cfo'){
      /* CFO 财务中心 6.4×5.2（门在东墙）→ 橙墙板改挂北/南两端墙；地毯按新分区重铺 */
      const wallMat=new THREE.MeshStandardMaterial({color:0xd96a2e,roughness:0.85});
      const northPanel=new THREE.Mesh(new THREE.PlaneGeometry(w-0.3,2.8),wallMat);
      northPanel.position.set(0,1.4,-hd+0.08);g.add(northPanel);
      const southPanel=new THREE.Mesh(new THREE.PlaneGeometry(w*0.5,2.8),wallMat);
      southPanel.rotation.y=Math.PI;southPanel.position.set(1.35,1.4,hd-0.08);g.add(southPanel);
      // 地毯分区：主办公区米白（西侧）+ 会客区鼠尾草绿（北侧，与 CFO_SHOW 一致）
      const rugA=new THREE.Mesh(new THREE.PlaneGeometry(3.0,3.4),new THREE.MeshStandardMaterial({color:0xf0ebe0,roughness:0.92}));
      rugA.rotation.x=-Math.PI/2;rugA.position.set(-1.9,0.095,0.2);rugA.receiveShadow=true;g.add(rugA);
      const rugB=new THREE.Mesh(new THREE.PlaneGeometry(3.2,2.1),new THREE.MeshStandardMaterial({color:0xa8bca4,roughness:0.92}));
      rugB.rotation.x=-Math.PI/2;rugB.position.set(-0.5,0.095,-1.72);rugB.receiveShadow=true;g.add(rugB);

      // 程序化兜底家具（与 CFO_SHOW 同坐标对齐；高清模型加载成功后整组移除）
      if(!hasModels){
      createExecDesk(prog, -1.90, 0.30,-Math.PI/2);
      createExecChair(prog,-1.35, 0.30,-Math.PI/2);
      createGuestChair(prog,-0.05, 1.05,Math.PI/2);
      createGuestChair(prog,-0.05,-0.45,Math.PI/2);
      createSofa(prog,-1.10,-1.75,0);
      createCoffeeTable(prog,-0.30,-1.75,Math.PI/2);
      createLaptop(prog,-1.88,0.81,0.05,Math.PI/2);
      createFilingCabinet(prog,1.30,-2.20,-Math.PI/2);
      createPlant(prog,-2.75,1.65);
      createPlant(prog, 2.70,-2.10);
      }
      // 两种模式共用：保险柜（财务特色）+ 打印机 + 主机箱 + 桌面工作用品
      const safe=new THREE.Mesh(new THREE.BoxGeometry(0.45,0.5,0.42),
        new THREE.MeshStandardMaterial({color:'#5a5248',roughness:0.25,metalness:0.6}));
      safe.position.set(-2.75,0.28,-2.10);safe.castShadow=true;g.add(safe);
      const dial=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.03,16),
        new THREE.MeshStandardMaterial({color:'#c8b898',roughness:0.15,metalness:0.7}));
      dial.position.set(-2.75,0.48,-1.90);dial.rotation.x=Math.PI/2;g.add(dial);
      createPrinter(g,2.65,-1.55,-Math.PI/2);
      createTowerPC(g,-1.95,FLOOR,1.20,Math.PI/2);
      const deskProps=new THREE.Group();deskProps.position.y=0.85;
      createKeyboard(deskProps, -1.72,0, 0.30,-Math.PI/2);
      createMouse(deskProps,    -1.72,0, 0.72);
      createDeskPhone(deskProps, -2.02,0, 0.88,-Math.PI/2);
      createPenCup(deskProps,   -2.08,0, 0.10);
      createMug(deskProps,      -1.98,0, 0.55);
      createPaperStack(deskProps,-2.05,0,-0.25,-Math.PI/2);
      createTray(deskProps,     -2.10,0, 0.52);
      g.add(deskProps);
      extraProps = deskProps;
    }
"""
rep("B2 CFO 装饰重定位", OLD_CFO, NEW_CFO)

# ══════════════════════════════════ B3 cmo 程序化兜底
OLD_CMO_FB = src[src.index("    if(id==='cmo'&&!hasModels){"):src.index("    g.add(prog);")]
NEW_CMO_FB = """    if(id==='cmo'&&!hasModels){
      /* cmo 8.2×8.6 独立办公室（v4 起不再是开放大厅）→ 两组工位沿 X 并排 + 储物 + 绿植 */
      [[-1.70,-1.90],[1.30,-1.90]].forEach(([ox,oz])=>{
        deskTop(g,ox,oz,2.5,0.7);deskLegs(g,ox,oz,2.5,0.7);
        [[-0.45,-0.08],[0.45,-0.08]].forEach(([dx,dz])=>{
          const mon=new THREE.Mesh(new THREE.BoxGeometry(0.54,0.36,0.05),
            new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
          mon.position.set(ox+dx,0.99,oz+dz);g.add(mon);
        });
      });
      createPrinter(g,-3.60,-3.40,0);
      createFilingCabinet(g,3.70,0.40,-Math.PI/2);
      createPlant(g,-3.70,3.60,1.1);createPlant(g,3.70,3.60,1.1);
    }

"""
rep("B3 cmo 程序化兜底", OLD_CMO_FB, NEW_CMO_FB)

# ══════════════════════════════════ B4 记忆屏定位
OLD_MEM = """    if(zone.id==='cmo'){
      // CMO：2026-09-11 CPO 迁走后大厅贯通 → 落地白板靠东墙，板面朝 -X（朝大厅内）
      // 旧位置 (cx+hw-0.35, cz)= 原东墙内侧，正好堵在 CPO 门口（用户标记 Bug）
      x=zone.cx+hw-0.35; z=zone.cz; rotY=-Math.PI/2;
    }else if(zone.id==='coo'){
      // COO：入口在前(+Z) → 白板推到后墙(-Z)倚靠，板面朝入口，不再悬在房间中央
      z=zone.cz-hd+0.6; rotY=0;
    }else if(zone.id==='meeting'){
      // 会议室：入口在后(-Z)、前墙已有演示屏 → 白板靠前墙、置于演示屏左侧，板面朝入口
      // 房间仅 6m 宽，白板宽 2.6 → 中心 x 取 -1.65 才不穿左墙（原 -2.5 会出墙 0.8m）
      x=zone.cx-1.65; z=zone.cz+hd-0.6; rotY=Math.PI;
    }else if(zone.doorWall==='front'){z=zone.cz+hd*0.32;rotY=0;}"""
NEW_MEM = """    if(zone.id==='cmo'){
      // CMO 营销中心 8.2×8.6：门在南墙偏西 → 白板居中靠北墙(−Z)，板面朝南迎门
      x=zone.cx; z=zone.cz-hd+0.6; rotY=0;
    }else if(zone.id==='coo'){
      // COO：v4 起入口改到北墙(−Z) → 白板移到南墙(+Z)实墙，板面仍朝入口
      x=zone.cx; z=zone.cz+hd-0.6; rotY=Math.PI;
    }else if(zone.id==='meeting'){
      // 会议室：v4 起门在东墙(+X)，北/南墙都是实墙 → 白板居中靠南墙(+Z)，板面朝北迎门
      x=zone.cx; z=zone.cz+hd-0.6; rotY=Math.PI;
    }else if(zone.doorWall==='front'){z=zone.cz+hd*0.32;rotY=0;}"""
rep("B4 记忆屏定位", OLD_MEM, NEW_MEM)

# ══════════════════════════════════ B5 中庭重写
OLD_ATRIUM = src[src.index("function createAtrium(){"):src.index("Object.values(ZONES).forEach(zone=>{const room=createRoom(zone);")]
NEW_ATRIUM = """function createAtrium(){
  const g=new THREE.Group();

  /* ── 偏心圆厅（接待厅 9.4/10.8 r1.9，故意不在中轴上）──
       接待台面朝北迎主入口，东西两弧放等候长椅，中心花坛 */
  const top=box(3.0,0.06,0.72,MATS.coastDesk);top.position.set(LOBBY.x,0.76,LOBBY.z+1.15);g.add(top);
  const body=box(2.9,0.70,0.62,MATS.coastWood);body.position.set(LOBBY.x,0.40,LOBBY.z+1.15);g.add(body);
  const kick=box(3.0,0.10,0.14,MATS.coastWoodDark);kick.position.set(LOBBY.x,0.14,LOBBY.z+1.44);g.add(kick);
  const scr=new THREE.Mesh(new THREE.BoxGeometry(0.62,0.38,0.05),
    new THREE.MeshToonMaterial({color:'#2a2824',gradientMap:_gradientMap}));
  scr.position.set(LOBBY.x-0.55,1.02,LOBBY.z+1.10);scr.rotation.y=Math.PI;g.add(scr);
  createMug(g,LOBBY.x+0.66,0.79,LOBBY.z+1.08);
  createPenCup(g,LOBBY.x+0.34,0.79,LOBBY.z+1.12);
  createGuestChair(g,LOBBY.x,LOBBY.z+1.92,Math.PI);
  createCoastalBench(g,LOBBY.x-1.52,LOBBY.z-0.25,Math.PI/2);
  createCoastalBench(g,LOBBY.x+1.52,LOBBY.z-0.25,-Math.PI/2);
  const pot=cyl(0.44,0.36,0.5,MATS.plantPot);pot.position.set(LOBBY.x,0.25,LOBBY.z-0.15);g.add(pot);
  createCoastalPlant(g,LOBBY.x,LOBBY.z-0.15,1.35);
  createShellJar(g,LOBBY.x+0.95,LOBBY.z-1.25,0,0.9);
  createShellFountain(g,LOBBY.x-0.95,LOBBY.z-1.25);

  /* ── 西北入口前庭（室外 0,0~6.6,5.6）：长椅 + 绿植 + 贝壳喷泉，正对西翼退台 ── */
  createCoastalBench(g,1.7,1.15,0);
  createCoastalBench(g,1.7,3.05,Math.PI);
  createCoastalPlant(g,0.85,0.85,1.2);
  createCoastalPlant(g,5.65,0.85,1.2);
  createShellFountain(g,3.7,2.10);
  createShellJar(g,5.65,3.40,0,0.9);
  createRopeCoil(g,5.30,0.10,4.40,0,0.2);

  /* ── 东南侧庭（室外 26.2,12.6~29.6,19.0）：CEO 东侧小院 ── */
  createCoastalBench(g,27.05,14.40,-Math.PI/2);
  createCoastalBench(g,27.05,17.40,Math.PI/2);
  createCoastalPlant(g,28.85,13.55,1.1);
  createCoastalPlant(g,28.85,18.20,1.1);
  createShellJar(g,28.85,15.90,0,0.9);
  createRopeCoil(g,27.05,0.10,15.90,0,0.2);

  /* ── 东西主廊点缀（B1/B2 两处）── */
  createRopeCoil(g,12.6,0.10,10.10,0,0.2);
  createRopeCoil(g,23.4,0.10,10.10,0,0.2);

  g.position.set(0,0,0);scene.add(g);
}

"""
rep("B5 中庭重写", OLD_ATRIUM, NEW_ATRIUM)

# ══════════════════════════════════ B6 相机 / 雾 / 灯光 / 地形
rep("B6a 雾", "scene.fog=new THREE.Fog('#cfe8f5',34,66);",
    "scene.fog=new THREE.Fog('#cfe8f5',46,96);")
rep("B6b 相机初始位", """camera.position.set(12,16,24);camera.lookAt(12,0,9);""",
    """camera.position.set(14.8,20.6,30.4);camera.lookAt(14.8,0,10.8);""")
rep("B6c 轨道中心", "const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(12,0,9);",
    "const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(14.8,0,10.8);")
rep("B6d 总览视角", """function animateToOverview(duration=1.8){
  animateCameraTo(12,16,24,12,0,9,duration);
}""", """function animateToOverview(duration=1.8){
  animateCameraTo(14.8,20.6,30.4,14.8,0,10.8,duration);
}""")
rep("B6e 缩放范围", "controls.minDistance=8;controls.maxDistance=32;",
    "controls.minDistance=9;controls.maxDistance=48;")
rep("B6f 阳光与阴影", """sun.position.set(20,32,-12);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.near=0.5;sun.shadow.camera.far=75;
sun.shadow.camera.left=-20;sun.shadow.camera.right=20;
sun.shadow.camera.top=18;sun.shadow.camera.bottom=-12;sun.shadow.bias=-0.00006;
scene.add(sun);
const fill=new THREE.DirectionalLight('#cce0ff',1.3);fill.position.set(-14,12,26);scene.add(fill);""",
"""sun.position.set(26.8,34,-8.2);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.near=0.5;sun.shadow.camera.far=95;
sun.shadow.camera.left=-24;sun.shadow.camera.right=24;
sun.shadow.camera.top=22;sun.shadow.camera.bottom=-22;sun.shadow.bias=-0.00006;
sun.target.position.set(SITE.cx,0,SITE.cz);scene.add(sun.target);
scene.add(sun);
const fill=new THREE.DirectionalLight('#cce0ff',1.3);fill.position.set(2,14,38);scene.add(fill);""")

open(HTML, "w", encoding="utf-8").write(src)
print(f"✅ B 阶段完成 {orig} → {len(src)} 字节")
for s in steps:
    print("   ·", s)
