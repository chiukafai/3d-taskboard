# -*- coding: utf-8 -*-
"""把 E 盘 bak_showroom 的办公风家具系统移植到 Desktop 新布局版。保留 Desktop 的 ZONES 布局。"""
import io, re, sys, shutil

E = r"E:/AI/Workbuddy/workbuddy看板/office-3d-taskboard.html"
D = r"C:/Users/Perfect/Desktop/3d-taskboard-main/office-3d-taskboard.html"

e_lines = io.open(E, encoding="utf-8").read().split("\n")   # 0-based
d_html  = io.open(D, encoding="utf-8").read()

# ---------- 1. 提取 E 盘 helper 段：633..955 (1-based) = idx 632..954 ----------
helpers = "\n".join(e_lines[632:955])          # 含 createPrinter ... loadCfoShowcase 结束的 }
assert "function createPrinter" in helpers, "helpers head missing"
assert "function loadCfoShowcase" in helpers, "helpers tail missing"
assert "const CFO_SHOW" in helpers, "CFO_SHOW missing"
assert "const gltfLoader" in helpers, "gltfLoader missing"

# ---------- 2. 新 addFurniture（按 Desktop 新房间尺寸适配）----------
# Desktop ZONES: cro 5x5 | coo 7x5 | meeting 6x5 | ceo 6x5 | cmo 18x8 | cpo 6x8 | cto 8x5 | cfo 8x5
# doorWall: cro/coo/meeting/ceo=front, cmo=null(openPlan), cpo=left, cto/cfo=back
NEW_ADDFURNITURE = r'''/* ══ 房间家具：办公风定制套装（移植自 bak_showroom，按当前布局尺寸适配）══
   适配要点：cpo 门在左墙→白板移右墙；meeting 门在前墙→演示屏移后墙；
             cfo 门在后墙、记忆屏在前墙→墙板改左右侧墙，样板房坐标向房间内收；
             cmo 由纵向长廊改横向大厅→工位重排为 2 排 × 4 列 */
function addFurniture(){
  Object.entries(ZONES).forEach(([id,zone])=>{
    const{cx,cz,w,d}=zone;
    const g=new THREE.Group();
    const hw=w/2,hd=d/2;

    if(id==='ceo'){
      deskTop(g,0,-hd*0.25,2.5,1.1,MATS.deskLight);deskLegs(g,0,-hd*0.25,2.5,1.1);
      const seat=new THREE.Mesh(new THREE.BoxGeometry(0.54,0.06,0.54),MATS.chairLeather);
      seat.position.set(0,0.5,-hd*0.25+0.68);g.add(seat);
      const bk=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.5,0.05),MATS.chairLeather);
      bk.position.set(0,0.78,-hd*0.25+0.38);g.add(bk);
      const base=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.24,0.06,24),MATS.metalDark);
      base.position.set(0,0.44,-hd*0.25+0.68);g.add(base);
      const pole=new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.03,0.35,8),MATS.metalDark);
      pole.position.set(0,0.26,-hd*0.25+0.68);g.add(pole);
      const mon=new THREE.Mesh(new THREE.BoxGeometry(0.6,0.38,0.05),
        new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
      mon.position.set(0,0.99,-hd*0.25+0.12);g.add(mon);
      const stand=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.08,0.2),MATS.metalDark);
      stand.position.set(0,0.8,-hd*0.25+0.12);g.add(stand);
      const shelf=new THREE.Mesh(new THREE.BoxGeometry(0.25,1.6,1),MATS.deskDark);
      shelf.position.set(-hw+0.3,0.8,hd*0.3);shelf.castShadow=true;shelf.receiveShadow=true;g.add(shelf);
      const flag=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.5,0.3),MATS.plantPot);
      flag.position.set(hw-0.4,1.05,-hd+0.4);g.add(flag);
      const flagPole=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,1.2,8),MATS.metalDark);
      flagPole.position.set(hw-0.4,0.6,-hd+0.4);g.add(flagPole);
      createPlant(g,-hw+0.8,hd-0.8);createPlant(g,hw-0.6,hd-0.6);
    }else if(id==='cro'){
      deskTop(g,0,-hd*0.25,1.8,0.85);deskLegs(g,0,-hd*0.25,1.8,0.85);
      [-0.4,0.4].forEach(ox=>{
        const mon=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.34,0.05),
          new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
        mon.position.set(ox,0.99,-hd*0.25+0.1);g.add(mon);
      });
      const alarm=new THREE.Mesh(new THREE.SphereGeometry(0.08,12,12),
        new THREE.MeshStandardMaterial({color:'#cc3333',roughness:0.1,emissive:'#cc3333',emissiveIntensity:0.4}));
      alarm.position.set(hw-0.4,2.2,-hd+0.4);g.add(alarm);
      const cb=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.4,0.04),
        new THREE.MeshStandardMaterial({color:'#f8f4ee',roughness:0.3}));
      cb.position.set(-hw+0.5,0.9,hd-0.2);g.add(cb);
    }else if(id==='cpo'){
      /* cpo 门在左墙(doorWall:'left') → 白板从左侧改挂右墙，避免封门 */
      deskTop(g,0,-hd*0.05,3.2,1.5,MATS.deskLight);deskLegs(g,0,-hd*0.05,3.2,1.5);
      const wbF=new THREE.Mesh(new THREE.BoxGeometry(0.05,1.6,2.4),MATS.metal);
      wbF.position.set(hw-0.15,0.8,0);wbF.castShadow=true;g.add(wbF);
      const wbP=new THREE.Mesh(new THREE.BoxGeometry(0.01,1.5,2.3),
        new THREE.MeshStandardMaterial({color:'#f6f4ee',roughness:0.25}));
      wbP.position.set(hw-0.18,0.8,0);g.add(wbP);
      const sw1=new THREE.Mesh(new THREE.BoxGeometry(0.02,0.2,0.25),
        new THREE.MeshStandardMaterial({color:'#d85a30',roughness:0.3}));
      sw1.position.set(hw-0.2,1.2,-0.6);g.add(sw1);
      const sw2=new THREE.Mesh(new THREE.BoxGeometry(0.02,0.2,0.25),
        new THREE.MeshStandardMaterial({color:'#378add',roughness:0.3}));
      sw2.position.set(hw-0.2,0.9,0.6);g.add(sw2);
      const proto=new THREE.Mesh(new THREE.BoxGeometry(0.25,0.3,0.4),
        new THREE.MeshStandardMaterial({color:'#e8e0d4',roughness:0.3}));
      proto.position.set(-hw+1,0.83,-hd*0.05);g.add(proto);
      createPlant(g,hw-0.6,hd-0.7,0.9);
    }else if(id==='meeting'){
      /* meeting 门在前墙 → 3.8m 长桌保留居中，演示屏移到后墙(-Z) 正对入口 */
      const tbl=new THREE.Mesh(new THREE.BoxGeometry(3.8,0.06,1.7),MATS.deskDark);
      tbl.position.set(0,0.78,0);tbl.castShadow=true;tbl.receiveShadow=true;g.add(tbl);
      for(let i=0;i<4;i++){
        const lx=(i-1.5)*0.9;
        const leg=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.06,0.74,12),MATS.metalDark);
        leg.position.set(lx,0.37,0.4);g.add(leg);
        const leg2=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.06,0.74,12),MATS.metalDark);
        leg2.position.set(lx,0.37,-0.4);g.add(leg2);
      }
      for(let i=0;i<8;i++){
        const a=(i/8)*Math.PI*2,sx=Math.cos(a)*2.2,sz=Math.sin(a)*1.2;
        const seat=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.06,0.5),MATS.chairLeather);
        seat.position.set(sx,0.49,sz);g.add(seat);
        const bk=new THREE.Mesh(new THREE.BoxGeometry(0.48,0.42,0.04),MATS.chairLeather);
        bk.position.set(sx,0.72,sz+0.24*Math.sign(sz||1));g.add(bk);
      }
      const scr=new THREE.Mesh(new THREE.BoxGeometry(2.2,1.3,0.05),
        new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.3}));
      scr.position.set(0,0.95,-hd+0.15);g.add(scr);
      createPlant(g,-hw+0.6,hd-0.6,0.9);createPlant(g,hw-0.6,hd-0.6,0.9);
    }else if(id==='coo'){
      [[2.2,-hd*0.2],[-0.5,-hd*0.2]].forEach(([ox,oz])=>{
        deskTop(g,ox,oz,1.4,0.75);deskLegs(g,ox,oz,1.4,0.75);
        const mon=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.34,0.05),
          new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
        mon.position.set(ox,0.99,oz+0.1);g.add(mon);
      });
      createPrinter(g,-hw+0.7,hd-0.6,Math.PI);
      createFilingCabinet(g,hw-0.5,hd-0.6,Math.PI);
      const dash=new THREE.Mesh(new THREE.BoxGeometry(1.8,0.03,1.2),
        new THREE.MeshStandardMaterial({color:'#f8f4ee',roughness:0.28}));
      dash.position.set(0.8,0.78,hd*0.4);g.add(dash);
      createPlant(g,hw-0.6,-hd+0.6,0.9);
    }else if(id==='cto'){
      for(let i=0;i<3;i++){
        const ox=-hw+1.2+i*2;
        const rack=new THREE.Mesh(new THREE.BoxGeometry(0.55,2,0.8),
          new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.2,metalness:0.6}));
        rack.position.set(ox,1.05,-hd*0.15);rack.castShadow=true;rack.receiveShadow=true;g.add(rack);
        for(let j=0;j<7;j++){
          const lc=j%2===0?'#00ee55':'#00bb33';
          const led=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.04,0.03),
            new THREE.MeshStandardMaterial({color:lc,roughness:0.05,emissive:lc,emissiveIntensity:0.9}));
          led.position.set(ox+0.2,0.25+j*0.26,-hd*0.15+0.4);led.renderOrder=1;g.add(led);
        }
      }
      deskTop(g,hw*0.35,hd*0.4,1.3,0.7,MATS.deskLight);deskLegs(g,hw*0.35,hd*0.4,1.3,0.7);
      const cable1=new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.03,0.8,8),mcolor('#444',{roughness:0.3}));
      cable1.position.set(-hw+1.2,0.4,-hd*0.15);cable1.rotation.z=Math.PI/4;g.add(cable1);
      const cable2=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.6,8),mcolor('#555',{roughness:0.3}));
      cable2.position.set(-hw+3.5,0.35,-hd*0.15);cable2.rotation.z=-Math.PI/3;g.add(cable2);
      createPlant(g,hw-0.6,hd-0.6,0.9);
    }else if(id==='cfo'){
      /* CFO 门在后墙、记忆屏在前墙(cz+hd-0.16) → 橙色墙板改挂左/右两侧墙
         高清 GLB 样板房坐标(CFO_SHOW)整体落在 x∈[-2.95,2.95] z∈[-1.90,0.60]，
         房间 8×5(hd=2.5) 完全容纳，无需缩放 */
      const FLOOR=0.09;
      const wallMat=new THREE.MeshStandardMaterial({color:0xd96a2e,roughness:0.85});
      const leftPanel=new THREE.Mesh(new THREE.PlaneGeometry(d,2.8),wallMat);
      leftPanel.rotation.y=Math.PI/2;leftPanel.position.set(-hw+0.08,1.4,0);g.add(leftPanel);
      const rightPanel=new THREE.Mesh(new THREE.PlaneGeometry(d,2.8),wallMat);
      rightPanel.rotation.y=-Math.PI/2;rightPanel.position.set(hw-0.08,1.4,0);g.add(rightPanel);
      // 地毯分区：主办公区米白 + 会客区鼠尾草绿（会客区在 -X 侧，与 CFO_SHOW 一致）
      const rugA=new THREE.Mesh(new THREE.PlaneGeometry(3.4,2.6),new THREE.MeshStandardMaterial({color:0xf0ebe0,roughness:0.92}));
      rugA.rotation.x=-Math.PI/2;rugA.position.set(-0.4,0.095,-0.6);rugA.receiveShadow=true;g.add(rugA);
      const rugB=new THREE.Mesh(new THREE.PlaneGeometry(2.0,2.4),new THREE.MeshStandardMaterial({color:0xa8bca4,roughness:0.92}));
      rugB.rotation.x=-Math.PI/2;rugB.position.set(-2.2,0.095,0.6);rugB.receiveShadow=true;g.add(rugB);

      // 程序化兜底家具（与 CFO_SHOW 同坐标对齐；高清模型加载成功后整组移除）
      const prog=new THREE.Group();
      createExecDesk(prog, 0.00,-1.10,0);
      createExecChair(prog,0.00,-1.60,0);
      createGuestChair(prog,-0.55,0.10,Math.PI);
      createGuestChair(prog, 0.55,0.10,Math.PI);
      createSofa(prog,-2.45,0.60,Math.PI/2);
      createCoffeeTable(prog,-1.55,0.60,Math.PI/2);
      createLaptop(prog,-0.50,0.81,-1.08,Math.PI);
      createFilingCabinet(prog,-2.95,-1.30,Math.PI/2);
      createPlant(prog, 0.85,-1.75);
      createPlant(prog, 2.95,-1.90);
      g.add(prog);
      // 两种模式共用：保险柜（财务特色）+ 打印机 + 主机箱 + 桌面工作用品
      const safe=new THREE.Mesh(new THREE.BoxGeometry(0.45,0.5,0.42),
        new THREE.MeshStandardMaterial({color:'#5a5248',roughness:0.25,metalness:0.6}));
      safe.position.set(-hw+0.5,0.28,hd-0.4);safe.castShadow=true;g.add(safe);
      const dial=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.03,16),
        new THREE.MeshStandardMaterial({color:'#c8b898',roughness:0.15,metalness:0.7}));
      dial.position.set(-hw+0.5,0.48,hd-0.2);dial.rotation.x=Math.PI/2;g.add(dial);
      createPrinter(g,hw-0.45,0.30,-Math.PI/2);
      createTowerPC(g,-1.35,FLOOR,-1.55,Math.PI/2);
      const deskProps=new THREE.Group();deskProps.position.y=0.85;
      createKeyboard(deskProps, 0.02,0,-0.93,0);
      createMouse(deskProps,    0.30,0,-0.93);
      createDeskPhone(deskProps,0.62,0,-1.22);
      createPenCup(deskProps,   0.74,0,-0.95);
      createMug(deskProps,      0.20,0,-1.20);
      createPaperStack(deskProps,-0.20,0,-1.24,0.2);
      createTray(deskProps,    -0.72,0,-1.22);
      g.add(deskProps);
      if (window.CFO_MODELS) loadCfoShowcase(g, prog, deskProps, FLOOR, 0.90);
    }else if(id==='cmo'){
      /* cmo 由纵向长廊改 18×8 横向大厅 → 工位重排为 2 排 × 4 列沿 X 展开 */
      const rows=2, cols=4;
      for(let r=0;r<rows;r++){
        const oz=-hd*0.42+r*(hd*0.84);
        for(let i=0;i<cols;i++){
          const ox=-hw+1.8+i*(w-3.6)/(cols-1||1);
          deskTop(g,ox,oz,1.5,0.75);deskLegs(g,ox,oz,1.5,0.75);
          const mon=new THREE.Mesh(new THREE.BoxGeometry(0.54,0.36,0.05),
            new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
          mon.position.set(ox+0.35,0.99,oz);g.add(mon);
        }
      }
      const board=new THREE.Mesh(new THREE.BoxGeometry(5,0.06,1.8),MATS.deskDark);
      board.position.set(0,0.78,hd*0.55);board.castShadow=true;board.receiveShadow=true;g.add(board);
      createPrinter(g,-hw+0.8,-hd+0.7,0);
      createFilingCabinet(g,hw-0.6,-hd+0.7,Math.PI);
      createPlant(g,-hw+0.8,hd-0.8,1.1);createPlant(g,hw-0.8,hd-0.8,1.1);
    }

    g.position.set(cx,0,cz);scene.add(g);
  });
}'''

# ---------- 3. 替换 Desktop 的 addFurniture（从 'function addFurniture(){' 到其后第一个 '\n}\n'）----------
start = d_html.index("function addFurniture(){")
end   = d_html.index("\n}\n", start) + len("\n}")
old_block = d_html[start:end]
assert len(old_block) < 20000, "old addFurniture too big: %d" % len(old_block)
d_html = d_html[:start] + NEW_ADDFURNITURE + d_html[end:]

# ---------- 4. 在 addFurniture 之前插入 helper 段 ----------
anchor = "function addFurniture(){"
d_html = d_html.replace(anchor, helpers + "\n\n" + anchor, 1)

# ---------- 5. 引入 cfo-models.js + GLTFLoader ----------
mod_tag = '<script type="module">'
assert mod_tag in d_html
d_html = d_html.replace(
    mod_tag,
    '<script src="cfo-models.js" onerror="console.warn(\'cfo-models.js 未找到，CFO 房间使用程序化家具\')"></script>\n'
    + mod_tag, 1)

imp_anchor = "import { OrbitControls } from 'three/addons/controls/OrbitControls.js';"
assert imp_anchor in d_html
d_html = d_html.replace(
    imp_anchor,
    imp_anchor + "\nimport { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';\nimport { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';",
    1)

io.open(D, "w", encoding="utf-8", newline="").write(d_html)
print("OK written. bytes=%d" % len(d_html.encode("utf-8")))
