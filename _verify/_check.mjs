
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ===== 卡通着色：4 级色阶渐变贴图（cel-shading） =====
const _steps=new Uint8Array([0x55,0x99,0xcc,0xff]);
const _gradientMap=new THREE.DataTexture(_steps,_steps.length,1,THREE.RedFormat);
_gradientMap.minFilter=THREE.NearestFilter;_gradientMap.magFilter=THREE.NearestFilter;
_gradientMap.generateMipmaps=false;_gradientMap.needsUpdate=true;
// 烘焙变换到几何体（用于合并前）
function bake(geo,x,y,z,rx=0,ry=0,rz=0,sx=1,sy=1,sz=1){
  const c=geo.clone();
  c.applyMatrix4(new THREE.Matrix4().compose(
    new THREE.Vector3(x,y,z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx,ry,rz)),
    new THREE.Vector3(sx,sy,sz)));
  return c;
}
// 合并多个几何体为一件完整物件（消除接缝，一体成型）
function merged(parts,mat){
  const idx=parts.filter(g=>g.index!==null).length;
  let geos=parts;
  if(idx>0&&idx<parts.length) geos=parts.map(g=>g.index!==null?g.toNonIndexed():g);
  const g=mergeGeometries(geos);
  const m=new THREE.Mesh(g,typeof mat==='string'?mcolor(mat):mat);m.castShadow=true;m.receiveShadow=true;return m;
}

// 平面图布局：北排服务区 + 中央横厅 + 南角私密房 + 露台
// 建筑尺寸: 24m(宽) × 18m(深)
/* 布局变更 2026-09-11（Kingsley 标注整改）：
   旧布局的致命问题：CPO 占着东侧中段(x18~24,z5~13) → 其南北两邻(CEO 南门 / CFO 北门)的
   门洞后面就是 CPO 的墙，等于被封死在别人房里；CMO 白板又堵在 CPO 门口。
   新布局：中央大厅贯通东西(24×8)，所有办公室的门都开向大厅；
           CEO 迁到南侧正中（正对大厅），CPO 迁到东北角，各自的门都能正常使用。 */
/* ══ 平面图 v4 · 错落非对称布局（2026-09-11 落地）══
   几何基准：_verify/gen_plan_v4_geom.py → plan_v4.json（栅格 0.1m 校验：0 重叠、8 樘门全部通向公共区）
   包络 29.6 × 21.6 m。房间体量刻意错落：西翼 x = 0 / 1.0 / 2.2 三级退台，
   北墙 z = 5.6 / 3.6 / 1.6 / 0.0 四级退台，无一条贯穿到底的长直廊。
   坐标约定：平面图 x → three.js X，平面图 z(向下=南) → three.js Z。
   门向映射：平面图 S 墙 = front(+Z)；N 墙 = back(−Z)；E 墙 = right(+X)；W 墙 = left(−X)。
   公共区：西北入口前庭 → 蛇形支廊 A1/A2/A3 → 偏心圆厅(接待厅) → 东西主廊 B1/B2 → 东南侧庭。 */
const SITE  = { ex:29.6, ez:21.6, cx:14.8, cz:10.8 };   // 包络与几何中心
const LOBBY = { x:9.4,  z:10.8, r:1.9 };                 // 偏心圆厅（接待厅，故意不在中轴上）
const COURT = { x1:0.0, z1:0.0, x2:6.6, z2:5.6 };        // 西北入口前庭（室外）
const YARD  = { x1:26.2, z1:12.6, x2:29.6, z2:19.0 };    // 东南侧庭（室外）
const ENTRY = { x:8.0, z:5.6, w:1.6 };                    // 主入口（A1 北端，双开门）
const EXITX = { x:29.4, z:10.5, w:1.2 };                  // 东侧疏散口

// 公共区地板矩形（栅格贪心分解 → 互不重叠，避免 z-fighting）
const PUB_FLOORS = [
  [7.4, 8.6, 29.400000000000002, 11.600000000000001],
  [8.6, 11.600000000000001, 10.200000000000001, 21.6],
  [6.6000000000000005, 5.6000000000000005, 9.4, 8.6],
  [19.400000000000002, 11.600000000000001, 29.400000000000002, 12.4],
  [10.200000000000001, 16.400000000000002, 11.4, 21.6],
  [7.4, 11.600000000000001, 8.6, 16.400000000000002],
  [6.6000000000000005, 8.6, 7.4, 11.0],
  [10.200000000000001, 11.600000000000001, 11.4, 13.0]
];
// 公共区外墙段（已剔除与房间共墙的段；格式 [朝向, 定位, 起, 止]）
const PAD_RECTS = [
  [11.1, 3.3, 26.3, 19.3],
  [1.9, 5.3, 10.5, 21.6],
  [26.3, 1.3, 29.6, 12.7],
  [15.3, 0.0, 24.1, 3.3],
  [0.7, 5.3, 1.9, 16.7],
  [10.5, 3.3, 11.1, 13.3],
  [24.1, 1.3, 26.3, 3.3],
  [0.0, 5.3, 0.7, 11.3],
  [10.5, 19.3, 19.7, 19.7],
  [9.1, 3.3, 10.5, 5.3],
  [10.5, 19.7, 11.7, 21.6],
  [10.5, 16.1, 11.1, 19.3]
];
const PUB_WALLS = [
  ['h', 56, 66, 94],
  ['v', 294, 86, 124],
  ['h', 124, 260, 294],
  ['h', 130, 102, 114],
  ['v', 102, 130, 164],
  ['v', 114, 194, 216],
  ['h', 164, 102, 114],
  ['h', 216, 86, 114]
];
// 公共区门洞（主入口 / 疏散口）
const PUB_DOORS = [
  { o:'h', k:5.6,  pos:8.0,  w:1.6, kind:'entrance' },
  { o:'v', k:29.4, pos:10.5, w:1.2, kind:'exit' }
];
const ZONES = {
  cpo:      { id:'cpo', name:'CPO 产品设计室', color:'#b08060', cx:3.3, cz:8.3, w:6.6, d:5.4, doorWall:'right', doorPos:8.0, carpetColor:'#885840' },
  meeting:  { id:'meeting', name:'战略会议室', color:'#706898', cx:4.2, cz:13.7, w:6.4, d:5.4, doorWall:'right', doorPos:13.6, carpetColor:'#504870' },
  cfo:      { id:'cfo', name:'CFO 财务中心', color:'#5a8070', cx:5.4, cz:19.0, w:6.4, d:5.2, doorWall:'right', doorPos:19.0, carpetColor:'#406050' },
  cro:      { id:'cro', name:'CRO 风控中心', color:'#8a5858', cx:12.5, cz:6.1, w:6.2, d:5.0, doorWall:'front', doorPos:12.6, carpetColor:'#604040' },
  cmo:      { id:'cmo', name:'CMO 营销中心', color:'#b89850', cx:19.7, cz:4.3, w:8.2, d:8.6, doorWall:'front', doorPos:17.6, carpetColor:'#907038' },
  cto:      { id:'cto', name:'CTO 技术中心', color:'#485c48', cx:26.7, cz:5.1, w:5.8, d:7.0, doorWall:'front', doorPos:26.4, carpetColor:'#304030' },
  coo:      { id:'coo', name:'COO 运营中心', color:'#647080', cx:15.4, cz:15.5, w:8.0, d:7.8, doorWall:'back', doorPos:15.2, carpetColor:'#4a5460' },
  ceo:      { id:'ceo', name:'CEO 战略办公室', color:'#5a6880', cx:22.7, cz:15.7, w:6.6, d:6.6, doorWall:'back', doorPos:22.6, carpetColor:'#445060' }
};

(function loadTasks(){
  const useReal = window.TASK_DATA && Object.keys(window.TASK_DATA).length > 0;
  const src = useReal ? window.TASK_DATA : {}; // 2026-08-11 不再回退示例任务：tasks.js 不可读时显示空，仅合并导入任务
  Object.keys(src).forEach(k => { if (ZONES[k]) ZONES[k].tasks = (ZONES[k].tasks||[]).concat(src[k]); });
  if (window.TASK_INBOX) {
    Object.keys(window.TASK_INBOX).forEach(k => {
      if (ZONES[k] && Array.isArray(window.TASK_INBOX[k])) ZONES[k].tasks = (ZONES[k].tasks||[]).concat(window.TASK_INBOX[k]);
    });
    const n = Object.values(window.TASK_INBOX).reduce((a,b)=>a+(Array.isArray(b)?b.length:0),0);
    console.log('📥 已合并看板导入任务 (' + n + ' 条)');
  }
  console.log('📊 已加载任务数据：' + (useReal ? ((window.TASK_META&&window.TASK_META.totalTasks)||'?')+' 条真实' : '空（未加载到 tasks.js，已禁用示例回退）') + (window.TASK_INBOX?' + 导入':''));
})();

let activeZone=null, activeFilter='all', draggedTaskId=null, activeCollabTask=null, hoveredZone=null;
const connectionLines=[], doorGroups={}, allRoomFloorMeshes=[], doorPickables=[];
let animTime=0;

/* 材质缓存：无 opts 的纯色材质全局复用（同色只建一次，减少 GPU 状态切换与 GC）。
   带 opts（transparent/emissive 等）不缓存，避免共享材质被运行时改写互相污染 */
const _matCache = new Map();
function mcolor(hex, opts){
  const noOpts = !opts || Object.keys(opts).length === 0;
  if (noOpts) { const c = _matCache.get(hex); if (c) return c; }
  const {roughness:_, metalness:__, ...rest} = opts || {};
  const m = new THREE.MeshToonMaterial({color:hex, gradientMap:_gradientMap, ...rest});
  if (noOpts) _matCache.set(hex, m);
  return m;
}
function box(w,h,d,mat){const g=new THREE.Mesh(new RoundedBoxGeometry(w,h,d,5,Math.min(w,h,d)*0.12),typeof mat==='string'?mcolor(mat):mat);g.castShadow=true;g.receiveShadow=true;return g;}
function cyl(rt,rb,h,mat,seg=28){const mesh=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,seg),typeof mat==='string'?mcolor(mat):mat);mesh.castShadow=true;mesh.receiveShadow=true;return mesh;}
function sphere(r,mat,seg=18){const g=new THREE.Mesh(new THREE.SphereGeometry(r,seg,seg),typeof mat==='string'?mcolor(mat):mat);g.castShadow=true;g.receiveShadow=true;return g;}
function torus(r,t,mat,seg=20,arc=7){const g=new THREE.Mesh(new THREE.TorusGeometry(r,t,seg,seg,arc),typeof mat==='string'?mcolor(mat):mat);g.castShadow=true;g.receiveShadow=true;return g;}

function woodTex(base,dark){
  const c=document.createElement('canvas');c.width=512;c.height=256;
  const ctx=c.getContext('2d');ctx.fillStyle=base;ctx.fillRect(0,0,512,256);
  for(let i=0;i<80;i++){const y=Math.random()*256,a=0.03+Math.random()*0.08;ctx.strokeStyle=`rgba(${dark},${a})`;ctx.lineWidth=1+Math.random()*2.5;ctx.beginPath();ctx.moveTo(0,y);for(let x=0;x<512;x+=15)ctx.lineTo(x,y+Math.sin(x*0.015)*4+Math.sin(x*0.04)*2);ctx.stroke();}
  const tex=new THREE.CanvasTexture(c);tex.wrapS=tex.wrapT=THREE.RepeatWrapping;return tex;
}
// 海岸木板纹理（竖向板缝，海岸风标志纹理）
function plankTex(base,dark,gapCol,vertical=true){
  const c=document.createElement('canvas');c.width=512;c.height=512;const x=c.getContext('2d');
  x.fillStyle=base;x.fillRect(0,0,512,512);
  const n=7,pw=512/n;
  for(let i=0;i<n;i++){
    x.fillStyle=`rgba(${dark},${0.06+Math.random()*0.06})`;
    if(vertical)x.fillRect(i*pw,0,pw,512);else x.fillRect(0,i*pw,512,pw);
    x.strokeStyle=gapCol;x.lineWidth=2;
    if(vertical){x.beginPath();x.moveTo(i*pw,0);x.lineTo(i*pw,512);x.stroke();}
    else{x.beginPath();x.moveTo(0,i*pw);x.lineTo(512,i*pw);x.stroke();}
  }
  const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;
}
// 海岸风地毯（波浪/贝壳花纹）
function coastalRugTex(color){
  const c=document.createElement('canvas');c.width=256;c.height=256;const x=c.getContext('2d');
  x.fillStyle=color;x.fillRect(0,0,256,256);
  x.strokeStyle='rgba(255,255,255,0.18)';x.lineWidth=3;
  for(let r=20;r<120;r+=24){x.beginPath();x.arc(128,128,r,0,Math.PI*2);x.stroke();}
  x.fillStyle='rgba(255,255,255,0.12)';
  for(let i=0;i<8;i++){const a=i/8*Math.PI*2;x.beginPath();x.arc(128+Math.cos(a)*90,128+Math.sin(a)*90,8,0,Math.PI*2);x.fill();}
  x.strokeStyle='rgba(255,255,255,0.15)';x.lineWidth=6;x.strokeRect(12,12,232,232);
  return new THREE.CanvasTexture(c);
}
function carpetTex(color){
  return coastalRugTex(color);
}

const MATS={
  woodFloor: new THREE.MeshToonMaterial({map:plankTex('#f0d090','180,130,60','#b8884c'),gradientMap:_gradientMap}),
  woodRoom: new THREE.MeshToonMaterial({map:plankTex('#e0b878','140,85,35','#a86838'),gradientMap:_gradientMap}),
  woodAtrium: new THREE.MeshToonMaterial({map:plankTex('#ecc890','160,100,45','#b07848'),gradientMap:_gradientMap}),
  wallInner: mcolor('#faf2e2'),
  // 海岸木家具（竖向板缝蜜色木）
  coastDesk: new THREE.MeshToonMaterial({map:plankTex('#e8b870','150,95,40','#a86838',true),gradientMap:_gradientMap}),
  coastWood: mcolor('#d8a060'),
  coastWoodDark: mcolor('#b07840'),
  deskLight: mcolor('#eccc88'),
  deskDark: mcolor('#b07840'),
  metal: mcolor('#c8c0b0'),
  metalDark: mcolor('#6a6258'),
  chairCoral: mcolor('#e8786a'),
  chairLeather: mcolor('#c4584a'),
  plantPot: mcolor('#d09868'),
  plantPotBlue: mcolor('#7ab8d8'),
  plantLeaf: mcolor('#5cc888'),
  plantLeafDark: mcolor('#3eb068'),
  rope: mcolor('#e0c890'),
  brass: mcolor('#e8c060'),
  glass: new THREE.MeshPhysicalMaterial({color:'#dff0ff',roughness:0.05,metalness:0,transparent:true,opacity:0.3,transmission:0.6}),
  shellPink: mcolor('#f0a8b0'),
  shellCream: mcolor('#fff0d8'),
};

const panel=document.getElementById('panel'),panelTitle=document.getElementById('panel-title'),panelDot=document.getElementById('panel-dot');
const panelStats=document.getElementById('panel-stats'),panelFilters=document.getElementById('panel-filters'),taskListEl=document.getElementById('task-list');
const hint=document.getElementById('hint'),collabIndicator=document.getElementById('collab-indicator');

const scene=new THREE.Scene();scene.background=new THREE.Color('#bfe0f5');scene.fog=new THREE.Fog('#cfe8f5',46,96);
const container=document.getElementById('canvas-container');
const camera=new THREE.PerspectiveCamera(38,container.clientWidth/container.clientHeight,0.5,75);
camera.position.set(14.8,20.6,30.4);camera.lookAt(14.8,0,10.8);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setSize(container.clientWidth,container.clientHeight);renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
/* 阴影按需更新：家具/墙体静止，只有门开合与高清模型加载会改变投影 →
   关掉每帧重算，省掉每帧一次 2048² 深度 pass（约 15-30% 帧时间） */
renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
container.appendChild(renderer.domElement);

let animId=0;
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(14.8,0,10.8);
function animateCameraTo(tx,ty,tz,lookX,lookY,lookZ,duration=1.6){
  animId++;const id=animId;
  gsap.killTweensOf(camera.position);
  gsap.killTweensOf(controls.target);
  gsap.to(camera.position,{x:tx,y:ty,z:tz,duration,ease:'power3.out',
    onComplete:()=>{if(id===animId)controls.enableDamping=true;}
  });
  gsap.to(controls.target,{x:lookX,y:lookY,z:lookZ,duration:duration*0.9,ease:'power2.inOut',
    onUpdate:()=>controls.update()
  });
  controls.enableDamping=false;
}
function animateToZone(zone,duration=1.6){
  const{cx,cz,w,d,doorWall,doorPos,openPlan}=zone;
  const hw=w/2,hd=d/2;
  let lookFromX=cx, lookFromZ=cz;
  if(openPlan){
    lookFromX=cx+hw+(d+hw)*0.85;lookFromZ=cz;
  }else if(doorWall==='front'){
    lookFromX=doorPos;lookFromZ=cz+hd+(d+w)*0.55;
  }else if(doorWall==='back'){
    lookFromX=doorPos;lookFromZ=cz-hd-(d+w)*0.55;
  }else if(doorWall==='left'){
    lookFromX=cx-hw-(d+w)*0.55;lookFromZ=doorPos;
  }else if(doorWall==='right'){
    lookFromX=cx+hw+(d+w)*0.55;lookFromZ=doorPos;
  }
  const camY=Math.max(w,d)*0.6;
  animateCameraTo(lookFromX,camY,lookFromZ,cx,0,cz,duration);
}
function animateToOverview(duration=1.8){
  animateCameraTo(14.8,20.6,30.4,14.8,0,10.8,duration);
}
controls.enableDamping=true;controls.dampingFactor=0.08;controls.minDistance=9;controls.maxDistance=48;
controls.maxPolarAngle=Math.PI/2.3;controls.minPolarAngle=0.22;
controls.minAzimuthAngle=-Infinity;controls.maxAzimuthAngle=Infinity;
controls.update();

const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();

scene.add(new THREE.AmbientLight('#fff0e0',1.1));
const sun=new THREE.DirectionalLight('#fff6e8',3.2);
sun.position.set(26.8,34,-8.2);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.near=0.5;sun.shadow.camera.far=95;
sun.shadow.camera.left=-24;sun.shadow.camera.right=24;
sun.shadow.camera.top=22;sun.shadow.camera.bottom=-22;sun.shadow.bias=-0.00006;
sun.target.position.set(SITE.cx,0,SITE.cz);scene.add(sun.target);
scene.add(sun);
const fill=new THREE.DirectionalLight('#cce0ff',1.3);fill.position.set(2,14,38);scene.add(fill);

function addInteriorLight(zone){
  const light=new THREE.PointLight('#ffd870',1.4,zone.w*2.5,1.5);
  light.position.set(zone.cx,2.4,zone.cz);
  if(!zone.openPlan)scene.add(light);
  else{light.position.set(zone.cx+zone.w/2-0.3,2.4,zone.cz);scene.add(light);}
}

function makePlaque(parent, text, color, x, y, z, rotY=0, pw=2.8){
  const group=new THREE.Group();
  const w=pw, h=Math.max(0.55, Math.min(0.7, pw*0.26));
  const bg=new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.06),
    mcolor('#3a3430'));
  group.add(bg);
  const frame=new THREE.Mesh(new THREE.BoxGeometry(w+0.14, h+0.14, 0.03),
    mcolor('#5a5248'));
  frame.position.z=-0.04;group.add(frame);
  const frameR=new THREE.Mesh(new THREE.BoxGeometry(w+0.14, h+0.14, 0.03),
    mcolor('#5a5248'));
  frameR.position.z=0.04;group.add(frameR);

  const cv=document.createElement('canvas');cv.width=640;cv.height=160;
  const ctx=cv.getContext('2d');
  ctx.fillStyle='#3a3430';ctx.fillRect(0,0,640,160);
  ctx.strokeStyle=color;ctx.lineWidth=6;
  ctx.beginPath();ctx.roundRect(18,12,604,136,6);ctx.stroke();
  ctx.fillStyle='#e4ded6';ctx.font='bold 56px -apple-system,"PingFang SC",sans-serif';
  ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,320,80);
  const tex=new THREE.CanvasTexture(cv);tex.minFilter=THREE.LinearFilter;

  const pMat=new THREE.MeshBasicMaterial({map:tex,transparent:true,depthTest:false,depthWrite:false});
  const front=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08), pMat);
  front.position.z=0.03;group.add(front);
  // 背面：贴图水平镜像一次，从背后看文字才是正的（原先背面文字是反的）
  const bMap=tex.clone(); bMap.wrapS=THREE.RepeatWrapping; bMap.center.set(0.5,0.5);
  bMap.repeat.x=-1; bMap.needsUpdate=true;
  const back=new THREE.Mesh(new THREE.PlaneGeometry(w-0.08, h-0.08),
    new THREE.MeshBasicMaterial({map:bMap,transparent:true,depthTest:false,depthWrite:false}));
  back.position.z=-0.03;back.rotation.y=Math.PI;group.add(back);

  group.position.set(x,y,z);group.rotation.y=rotY;
  group.castShadow=true;parent.add(group);
  return group;
}

function createMainFloor(){
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
createMainFloor();

function createDoor(parentGroup, gapW=0.8, doorH=2, isDouble=false, zoneId=''){
  const pivot=new THREE.Group();
  const leaves=isDouble?2:1, lw=gapW/leaves;
  const dm=new THREE.MeshToonMaterial({map:woodTex('#c8b490','90,72,48'),gradientMap:_gradientMap,side:THREE.DoubleSide});
  for(let i=0;i<leaves;i++){
    const lg=new THREE.Group();
    const door=new THREE.Mesh(new THREE.BoxGeometry(lw,doorH,0.06),dm);
    door.position.set(lw/2,doorH/2,0);
    door.userData={isDoor:true,zoneId,leafIdx:i};   // 命中门扇 → toggleDoor(zoneId)
    doorPickables.push(door);lg.add(door);
    const knob=new THREE.Mesh(new THREE.SphereGeometry(0.04,12,12),mcolor('#c8b088'));
    knob.position.set(lw-0.14,doorH/2+0.08,0.035);
    knob.userData={isDoorKnob:true,zoneId};lg.add(knob);
    lg.position.x=i*lw;pivot.add(lg);
    if(i===0)pivot.userData={...pivot.userData,firstLeaf:lg};
  }
  parentGroup.add(pivot);
  pivot.userData.leaves=pivot.children.filter(c=>c.isGroup||c.type==='Group');
  pivot.userData.openAngle=isDouble?Math.PI/5:Math.PI/2.2;
  pivot.userData.isOpen=false;pivot.userData.isDouble=isDouble;
  pivot.userData.zoneId=zoneId;                       // 便于按 zone 找门
  return pivot;
}

// ===== 海岸风物件创建函数（样板间级别） =====

function createCoastalBench(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const seat=box(2,0.08,0.52,MATS.coastDesk);seat.position.y=0.44;g.add(seat);
  const back=box(2,0.32,0.06,MATS.coastWoodDark);back.position.set(0,0.62,-0.22);g.add(back);
  const legL=box(0.08,0.42,0.08,MATS.coastWoodDark);legL.position.set(-0.85,0.21,0);g.add(legL);
  const legR=box(0.08,0.42,0.08,MATS.coastWoodDark);legR.position.set(0.85,0.21,0);g.add(legR);
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(g);return g;
}


function createShellJar(parent,x,z,rotY=0,s=1){
  const g=new THREE.Group();
  const jar=new THREE.Mesh(new THREE.CylinderGeometry(0.07*s,0.06*s,0.14*s,16),MATS.glass);jar.position.y=0.07*s;g.add(jar);
  const lidColors=[MATS.chairCoral,MATS.plantPotBlue,MATS.brass,MATS.plantLeaf];
  const lidColor=lidColors[Math.floor(Math.random()*lidColors.length)];
  const lid=cyl(0.075*s,0.075*s,0.025*s,lidColor,16);lid.position.y=0.15*s;g.add(lid);
  const shellColors=[MATS.shellCream,MATS.shellPink,'#ffe080','#7ad890'];
  for(let i=0;i<3;i++){
    const sc=shellColors[Math.floor(Math.random()*shellColors.length)];
    const sh=sphere(0.022*s,sc,8);sh.scale.set(1,0.5,1);
    sh.position.set((i-1)*0.025*s,0.04*s,(i%2)*0.02*s);g.add(sh);
  }
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(g);return g;
}


function createCoastalPlant(parent,x,z,s=1){
  const g=new THREE.Group();
  const potColor=Math.random()>0.5?MATS.plantPot:MATS.plantPotBlue;
  const pot=cyl(0.24*s,0.2*s,0.42*s,potColor,20);pot.position.y=0.21*s;g.add(pot);
  const potRim=cyl(0.24*s,0.24*s,0.06*s,potColor,20);potRim.position.y=0.4*s;g.add(potRim);
  for(let i=0;i<7;i++){
    const a=i/7*Math.PI*2;
    const leaf=sphere(0.14*s,i%2?MATS.plantLeaf:MATS.plantLeafDark,14);
    leaf.position.set(Math.cos(a)*0.16*s,0.6*s+Math.random()*0.12*s,Math.sin(a)*0.16*s);
    leaf.scale.set(1,1.1,1);g.add(leaf);
  }
  const top=sphere(0.18*s,MATS.plantLeaf,16);top.scale.set(1,1.2,1);top.position.y=0.7*s;g.add(top);
  for(let i=0;i<4;i++){
    const a=i/4*Math.PI*2;
    const blade=sphere(0.05*s,MATS.plantLeafDark,8);blade.scale.set(0.5,3,0.5);
    blade.position.set(Math.cos(a)*0.1*s,0.85*s,Math.sin(a)*0.1*s);
    blade.rotation.set(0.2,a,Math.cos(a)*0.3);g.add(blade);
  }
  g.position.set(x,0,z);parent.add(g);return g;
}

// 珊瑚色办公椅（椅身一体成型：座垫+靠背弧+头枕+扶手 合并为单件）

// 鹅颈台灯（底盘+鹅颈管合并为单件黄铜，灯罩嵌套在管端）

// 绳索吊灯（绳索吊，对应风格图）


function createRopeCoil(parent,x,y,z,rotY=0,r=0.12){
  const g=new THREE.Group();
  for(let i=0;i<3;i++){
    const loop=torus(r+i*0.025,0.025,MATS.rope,14);loop.rotation.x=Math.PI/2;
    loop.position.y=i*0.04;g.add(loop);
  }
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(g);return g;
}


function createShellFountain(parent,x,z){
  const g=new THREE.Group();
  const basin=cyl(0.35,0.28,0.15,MATS.brass);basin.position.y=0.075;g.add(basin);
  const shellTop=merged([
    bake(new THREE.SphereGeometry(0.2,16,8,0,Math.PI*2,0,Math.PI/2),0,0.15,0),
  ],MATS.shellCream);g.add(shellTop);
  const water=cyl(0.03,0.06,0.12,MATS.glass,12);water.position.y=0.25;g.add(water);
  g.position.set(x,0,z);parent.add(g);return g;
}

// 双显示器（圆角厚实卡通款，带屏幕内容）

// createPlant 统一走办公风版本（见下方移植段，与 CFO 样板房同款球叶植物）；
// 海岸风植物保留 createCoastalPlant，供中庭/走廊装饰单独调用。

// ===== 公共区墙体（走廊/前庭围护）=====
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
function createRoom(zone){
  const{cx,cz,w,d,carpetColor,doorWall,doorPos}=zone;
  const hw=w/2,hd=d/2,wallH=2.8,wallT=0.15;
  const isOpen=zone.openPlan;
  const group=new THREE.Group();

  const platform=new THREE.Mesh(new THREE.BoxGeometry(w,0.08,d),MATS.woodRoom.clone());
  platform.position.y=0.04;platform.receiveShadow=true;group.add(platform);

  const cg=new THREE.PlaneGeometry(w-0.6,d-0.6);
  const carpet=new THREE.Mesh(cg,new THREE.MeshToonMaterial({map:carpetTex(carpetColor),gradientMap:_gradientMap}));
  carpet.rotation.x=-Math.PI/2;carpet.position.y=0.085;carpet.receiveShadow=true;group.add(carpet);

  const fcGeo=new THREE.PlaneGeometry(w-0.2,d-0.2);
  const fc=new THREE.Mesh(fcGeo,mcolor(zone.color,{transparent:true,opacity:0.25,depthWrite:false}));
  fc.rotation.x=-Math.PI/2;fc.position.y=0.09;
  fc.userData={zoneId:zone.id,isFloor:true,color:zone.color};
  group.add(fc);allRoomFloorMeshes.push(fc);

  const wm=MATS.wallInner;
  function wallSeg(x,z,sw,sd){
    const seg=new THREE.Mesh(new THREE.BoxGeometry(sw,wallH,sd),wm);
    seg.position.set(x,wallH/2,z);seg.receiveShadow=true;seg.castShadow=true;group.add(seg);
  }

  if(!isOpen){
    const gapW=zone.doubleDoor?1.4:0.8;
    const wallDefs=[
      {name:'back',segX:0,segZ:-hd,segW:w,segD:wallT,axis:'x'},
      {name:'front',segX:0,segZ:hd,segW:w,segD:wallT,axis:'x'},
      {name:'left',segX:-hw,segZ:0,segW:wallT,segD:d,axis:'z'},
      {name:'right',segX:hw,segZ:0,segW:wallT,segD:d,axis:'z'},
    ];
    wallDefs.forEach(def=>{
      if(def.name===doorWall){
        const isX=def.axis==='x';
        const totalLen=isX?def.segW:def.segD;
        const edgeStart=isX?(-hw):(-hd);
        const relPos=isX?(doorPos-(cx-hw)):(doorPos-(cz-hd));
        const ds=relPos-gapW/2, de=relPos+gapW/2;
        if(ds>0.15){
          const segCx=isX?(edgeStart+ds/2):def.segX;
          const segCz=isX?def.segZ:(edgeStart+ds/2);
          if(isX)wallSeg(segCx,segCz,ds,def.segD);
          else wallSeg(segCx,segCz,def.segW,ds);
        }
        if(totalLen-de>0.15){
          const segLen=totalLen-de;
          const segCx=isX?(edgeStart+de+segLen/2):def.segX;
          const segCz=isX?def.segZ:(edgeStart+de+segLen/2);
          if(isX)wallSeg(segCx,segCz,segLen,def.segD);
          else wallSeg(segCx,segCz,def.segW,segLen);
        }
      }else{wallSeg(def.segX,def.segZ,def.segW,def.segD);}
    });

    const dp=createDoor(group,gapW,2,zone.doubleDoor,zone.id);
    let dpx=0,dpz=0,dpr=0;
    if(doorWall==='front'){dpx=(doorPos-cx)-gapW/2;dpz=hd;dpr=0;}
    else if(doorWall==='back'){dpx=(doorPos-cx)+gapW/2;dpz=-hd;dpr=Math.PI;}
    /* 2026-09-11 修复：侧墙门的铰链侧算反 → 门扇整体偏移 0.8m、门洞只盖住一半 */
    else if(doorWall==='right'){dpx=hw;dpz=(doorPos-cz)-gapW/2;dpr=-Math.PI/2;}
    else if(doorWall==='left'){dpx=-hw;dpz=(doorPos-cz)+gapW/2;dpr=Math.PI/2;}
    dp.position.set(dpx,0.08,dpz);dp.rotation.y=dpr;
    /* 2026-09-11 修正：pivot 局部 +X→−Z 的旋向与墙面朝向组合后，
       东/西墙(right/left)的门恰好外开，但南/北墙(front/back)的门会内开 →
       这里显式标注开合旋向，animateDoors 据此取符号，保证全部外开 */
    dp.userData.openSign=(doorWall==='front'||doorWall==='back')?-1:1;
    group.add(dp);doorGroups[zone.id]=dp;

    /* 门牌位置 2026-09-11 修复：原先固定挂在门墙正中 → 正好压在门洞上（用户标记 Bug）。
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
    makePlaque(group,zone.name,zone.color,px,py,pz,pr,pw);
  }

  group.position.set(cx,0,cz);
  return group;
}

function deskLegs(g,x,z,w,h=0.72){
  [[-w/2+0.1,z-0.22],[w/2-0.1,z-0.22],[-w/2+0.1,z+0.22],[w/2-0.1,z+0.22]].forEach(([lx,lz])=>{
    const leg=box(0.1,h,0.1,MATS.coastWoodDark);
    leg.position.set(lx,h/2+0.04,lz);g.add(leg);
  });
}
function deskTop(g,x,z,w,d=0.7,mat=MATS.coastDesk){
  const top=box(w,0.08,d,mat);top.position.set(x,0.78,z);g.add(top);
}

/* ══ 房间家具：办公风定制套装（移植自 bak_showroom，按当前布局尺寸适配）══
   适配要点：cpo 门在左墙→白板移右墙；meeting 门在前墙→演示屏移后墙；
             cfo 门在后墙、记忆屏在前墙→墙板改左右侧墙，样板房坐标向房间内收；
             cmo 由纵向长廊改横向大厅→工位重排为 2 排 × 4 列 */
function createPrinter(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.7,0.45,0.5),mcolor('#ccc4b8',{roughness:0.3,metalness:0.1}));
  body.position.y=0.43;g.add(body);
  const top=new THREE.Mesh(new THREE.BoxGeometry(0.68,0.03,0.48),mcolor('#b8b0a4',{roughness:0.28}));
  top.position.y=0.67;g.add(top);
  const tray=new THREE.Mesh(new THREE.BoxGeometry(0.45,0.04,0.14),mcolor('#c0b8ac',{roughness:0.3}));
  tray.position.set(0,0.3,-0.25);g.add(tray);
  const paper=new THREE.Mesh(new THREE.BoxGeometry(0.43,0.015,0.12),new THREE.MeshStandardMaterial({color:'#faf8f4',roughness:0.5}));
  paper.position.set(0,0.32,-0.25);g.add(paper);
  g.position.set(x,0,z);g.rotation.y=rotY;g.castShadow=true;g.receiveShadow=true;parent.add(g);return g;
}


function createFilingCabinet(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.5,1.2,0.55),MATS.metal);
  body.position.y=0.6;g.add(body);
  for(let i=0;i<3;i++){
    const drawer=new THREE.Mesh(new THREE.BoxGeometry(0.46,0.3,0.02),MATS.metalDark);
    drawer.position.set(0,0.25+i*0.35,0.27);g.add(drawer);
    const h=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.2,8),MATS.metalDark);
    h.rotation.x=Math.PI/2;h.position.set(0,0.25+i*0.35,0.28);g.add(h);
  }
  g.position.set(x,0,z);g.rotation.y=rotY;g.castShadow=true;g.receiveShadow=true;parent.add(g);return g;
}

function createPlant(parent,x,z,s=1){
  const g=new THREE.Group();
  const pot=new THREE.Mesh(new THREE.CylinderGeometry(0.2*s,0.16*s,0.4*s,16),MATS.plantPot);
  pot.position.y=0.2*s;g.add(pot);
  const leaves=new THREE.Mesh(new THREE.SphereGeometry(0.3*s,10,8),MATS.plantLeaf);
  leaves.position.y=0.55*s;leaves.scale.set(0.85,1.3,0.85);g.add(leaves);
  g.position.set(x,0,z);g.castShadow=true;g.receiveShadow=true;parent.add(g);return g;
}

/* ═══ CFO 样板房家具（移植自 office3d-assets 的 CFO 办公室布局）═══
   朝向约定：rotY=0 时正面朝 +Z（房间内/门口方向）；rotY=Math.PI 朝 -Z（后墙） */
function shadowize(g){g.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});return g;}

// 大班台：1.9m 台面 + 右侧三层抽屉柜
function createExecDesk(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const top=new THREE.Mesh(new THREE.BoxGeometry(1.9,0.06,0.88),MATS.deskLight);
  top.position.y=0.75;g.add(top);
  const mod=new THREE.Mesh(new THREE.BoxGeometry(1.82,0.03,0.80),mcolor('#b8a488',{roughness:0.42}));
  mod.position.y=0.795;g.add(mod);                       // 桌面皮质垫
  const cab=new THREE.Mesh(new THREE.BoxGeometry(0.46,0.60,0.74),mcolor('#e8e2d6',{roughness:0.35}));
  cab.position.set(0.68,0.42,-0.02);g.add(cab);
  for(let i=0;i<3;i++){
    const h=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.02,0.02),MATS.metal);
    h.position.set(0.68,0.24+i*0.19,0.36);g.add(h);
  }
  const leg=new THREE.Mesh(new THREE.BoxGeometry(0.07,0.72,0.82),MATS.metalDark);
  leg.position.set(-0.88,0.36,0);g.add(leg);
  const panel=new THREE.Mesh(new THREE.BoxGeometry(1.8,0.42,0.04),mcolor('#d8d0c0',{roughness:0.5}));
  panel.position.set(-0.1,0.53,-0.40);g.add(panel);       // 前挡板
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
// 高背总经理椅
function createExecChair(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const seat=new THREE.Mesh(new THREE.BoxGeometry(0.58,0.11,0.56),MATS.chairLeather);
  seat.position.y=0.47;g.add(seat);
  const back=new THREE.Mesh(new THREE.BoxGeometry(0.56,0.60,0.10),MATS.chairLeather);
  back.position.set(0,0.82,-0.25);back.rotation.x=-0.08;g.add(back);
  const head=new THREE.Mesh(new THREE.BoxGeometry(0.38,0.17,0.09),MATS.chairLeather);
  head.position.set(0,1.19,-0.28);head.rotation.x=-0.08;g.add(head);
  [-0.31,0.31].forEach(ax=>{
    const arm=new THREE.Mesh(new THREE.BoxGeometry(0.07,0.06,0.44),MATS.chairLeather);
    arm.position.set(ax,0.63,0.02);g.add(arm);
    const ap=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.17,0.05),MATS.metalDark);
    ap.position.set(ax,0.54,0.18);g.add(ap);
  });
  const post=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.05,0.34,12),MATS.metalDark);
  post.position.y=0.25;g.add(post);
  for(let i=0;i<5;i++){
    const a=i/5*Math.PI*2;
    const arm=new THREE.Mesh(new THREE.BoxGeometry(0.06,0.04,0.32),MATS.metalDark);
    arm.position.set(Math.sin(a)*0.16,0.11,Math.cos(a)*0.16);arm.rotation.y=a;g.add(arm);
    const cst=new THREE.Mesh(new THREE.CylinderGeometry(0.035,0.035,0.04,10),MATS.metalDark);
    cst.position.set(Math.sin(a)*0.30,0.04,Math.cos(a)*0.30);g.add(cst);
  }
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
// 访客椅（低靠背）
function createGuestChair(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const seat=new THREE.Mesh(new THREE.BoxGeometry(0.50,0.08,0.48),MATS.chairLeather);
  seat.position.y=0.45;g.add(seat);
  const back=new THREE.Mesh(new THREE.BoxGeometry(0.46,0.40,0.07),MATS.chairLeather);
  back.position.set(0,0.70,-0.21);back.rotation.x=-0.06;g.add(back);
  const post=new THREE.Mesh(new THREE.CylinderGeometry(0.045,0.045,0.36,12),MATS.metalDark);
  post.position.y=0.22;g.add(post);
  for(let i=0;i<5;i++){
    const a=i/5*Math.PI*2;
    const arm=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.035,0.28),MATS.metalDark);
    arm.position.set(Math.sin(a)*0.14,0.09,Math.cos(a)*0.14);arm.rotation.y=a;g.add(arm);
    const cst=new THREE.Mesh(new THREE.CylinderGeometry(0.032,0.032,0.035,10),MATS.metalDark);
    cst.position.set(Math.sin(a)*0.26,0.035,Math.cos(a)*0.26);g.add(cst);
  }
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
// 双人沙发
function createSofa(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(1.58,0.26,0.74),MATS.chairLeather);
  base.position.y=0.24;g.add(base);
  [0,1].forEach(i=>{
    const cu=new THREE.Mesh(new THREE.BoxGeometry(0.72,0.13,0.62),mcolor('#464038',{roughness:0.4}));
    cu.position.set(-0.38+i*0.76,0.44,0.02);g.add(cu);
  });
  const back=new THREE.Mesh(new THREE.BoxGeometry(1.58,0.44,0.16),MATS.chairLeather);
  back.position.set(0,0.62,-0.29);g.add(back);
  [-0.79,0.79].forEach(ax=>{
    const ar=new THREE.Mesh(new THREE.BoxGeometry(0.15,0.20,0.74),MATS.chairLeather);
    ar.position.set(ax,0.50,0);g.add(ar);
  });
  [[-0.7,-0.3],[0.7,-0.3],[-0.7,0.3],[0.7,0.3]].forEach(([lx,lz])=>{
    const lg=new THREE.Mesh(new THREE.BoxGeometry(0.07,0.12,0.07),MATS.deskDark);
    lg.position.set(lx,0.06,lz);g.add(lg);
  });
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
// 茶几
function createCoffeeTable(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const top=new THREE.Mesh(new THREE.BoxGeometry(0.98,0.05,0.56),MATS.deskLight);
  top.position.y=0.43;g.add(top);
  const shelf=new THREE.Mesh(new THREE.BoxGeometry(0.86,0.03,0.44),MATS.deskDark);
  shelf.position.y=0.20;g.add(shelf);
  [[-0.44,-0.23],[0.44,-0.23],[-0.44,0.23],[0.44,0.23]].forEach(([lx,lz])=>{
    const lg=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.41,0.05),MATS.deskDark);
    lg.position.set(lx,0.205,lz);g.add(lg);
  });
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
/* ── 桌面工作用品（台面摆放，y 由调用方给）── */
function createLaptop(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(0.34,0.018,0.24),mcolor('#b0aca4',{roughness:0.3,metalness:0.45}));
  base.position.y=0.009;g.add(base);
  const kb=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.005,0.13),mcolor('#33302c',{roughness:0.5}));
  kb.position.set(0,0.019,-0.02);g.add(kb);
  const tp=new THREE.Mesh(new THREE.BoxGeometry(0.10,0.004,0.07),mcolor('#8e8a82',{roughness:0.35}));
  tp.position.set(0,0.019,0.07);g.add(tp);
  const lidG=new THREE.Group();lidG.position.set(0,0.018,-0.115);lidG.rotation.x=-0.26;
  const lid=new THREE.Mesh(new THREE.BoxGeometry(0.34,0.22,0.012),mcolor('#a8a49c',{roughness:0.3,metalness:0.45}));
  lid.position.set(0,0.11,0);lidG.add(lid);
  const scr=new THREE.Mesh(new THREE.PlaneGeometry(0.30,0.175),
    new THREE.MeshStandardMaterial({color:'#16222c',emissive:'#2a5a72',emissiveIntensity:0.55,roughness:0.2}));
  scr.position.set(0,0.11,-0.008);scr.rotation.y=Math.PI;lidG.add(scr);
  g.add(lidG);
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createKeyboard(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(0.44,0.016,0.14),mcolor('#dcd8d0',{roughness:0.4}));
  base.position.y=0.008;g.add(base);
  const keys=new THREE.Mesh(new THREE.BoxGeometry(0.40,0.006,0.10),mcolor('#44403a',{roughness:0.55}));
  keys.position.set(-0.005,0.018,-0.012);g.add(keys);
  const sp=new THREE.Mesh(new THREE.BoxGeometry(0.12,0.006,0.022),mcolor('#55504a',{roughness:0.55}));
  sp.position.set(0,0.018,0.048);g.add(sp);
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createMouse(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const m=new THREE.Mesh(new THREE.SphereGeometry(0.028,14,10),mcolor('#9a968e',{roughness:0.35}));
  m.scale.set(0.85,0.60,1.25);m.position.y=0.018;g.add(m);
  const wh=new THREE.Mesh(new THREE.BoxGeometry(0.006,0.012,0.015),mcolor('#3a3632',{roughness:0.4}));
  wh.position.set(0,0.032,-0.012);g.add(wh);
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createDeskPhone(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.20,0.045,0.17),mcolor('#3c4048',{roughness:0.35}));
  body.position.y=0.022;g.add(body);
  const pad=new THREE.Mesh(new THREE.BoxGeometry(0.185,0.012,0.075),mcolor('#e8e4dc',{roughness:0.45}));
  pad.position.set(0,0.050,0.035);g.add(pad);
  const scr=new THREE.Mesh(new THREE.BoxGeometry(0.09,0.008,0.022),
    new THREE.MeshStandardMaterial({color:'#7fc8b0',emissive:'#3a8a72',emissiveIntensity:0.5,roughness:0.3}));
  scr.position.set(0,0.050,-0.045);g.add(scr);
  const hs=new THREE.Mesh(new THREE.CapsuleGeometry(0.024,0.10,4,12),mcolor('#3c4048',{roughness:0.35}));
  hs.rotation.z=Math.PI/2;hs.position.set(0,0.080,-0.052);g.add(hs);
  [-0.062,0.062].forEach(ex=>{
    const ep=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.036,0.05),mcolor('#3c4048',{roughness:0.35}));
    ep.position.set(ex,0.080,-0.052);g.add(ep);
  });
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createPenCup(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const cup=new THREE.Mesh(new THREE.CylinderGeometry(0.045,0.041,0.10,16),mcolor('#2f6b5e',{roughness:0.45}));
  cup.position.y=0.05;g.add(cup);
  [['#c9662f',-0.014,-0.008],['#33506b',0.0,0.004],['#e0a93b',0.014,0.0]].forEach(([c,px,pz])=>{
    const p=new THREE.Mesh(new THREE.CylinderGeometry(0.0045,0.0045,0.17,8),mcolor(c,{roughness:0.4}));
    p.position.set(px,0.115,pz);p.rotation.set(0.10,0,-0.08);g.add(p);
  });
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createMug(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const cup=new THREE.Mesh(new THREE.CylinderGeometry(0.038,0.032,0.09,16),mcolor('#f2eee6',{roughness:0.3}));
  cup.position.y=0.045;g.add(cup);
  const liq=new THREE.Mesh(new THREE.CylinderGeometry(0.034,0.034,0.004,16),mcolor('#5a3a22',{roughness:0.25}));
  liq.position.y=0.084;g.add(liq);
  const h=new THREE.Mesh(new THREE.TorusGeometry(0.020,0.0055,8,16),mcolor('#f2eee6',{roughness:0.3}));
  h.rotation.y=Math.PI/2;h.position.set(0.040,0.050,0);g.add(h);
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createPaperStack(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  for(let i=0;i<5;i++){
    const p=new THREE.Mesh(new THREE.BoxGeometry(0.212,0.007,0.298),
      mcolor(i===4?'#f2c14e':'#f5f2ec',{roughness:0.6}));
    p.position.set(0,0.004+i*0.008,0);p.rotation.y=(i-2)*0.02;g.add(p);
  }
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createTray(parent,x,y,z,rotY=0){
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(0.245,0.008,0.325),mcolor('#7e93a6',{roughness:0.4}));
  base.position.y=0.004;g.add(base);
  [[0,-0.158,0.245,0.010],[0,0.158,0.245,0.010],[-0.118,0,0.010,0.325],[0.118,0,0.010,0.325]].forEach(([sx,sz,sw,sd])=>{
    const w=new THREE.Mesh(new THREE.BoxGeometry(sw,0.028,sd),mcolor('#7e93a6',{roughness:0.4}));
    w.position.set(sx,0.022,sz);g.add(w);
  });
  const pa=new THREE.Mesh(new THREE.BoxGeometry(0.20,0.012,0.28),mcolor('#f5f2ec',{roughness:0.6}));
  pa.position.y=0.014;g.add(pa);
  g.position.set(x,y,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}
function createTowerPC(parent,x,z,rotY=0){
  const g=new THREE.Group();
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.17,0.38,0.40),mcolor('#3c4048',{roughness:0.35,metalness:0.3}));
  body.position.y=0.19;g.add(body);
  const fp=new THREE.Mesh(new THREE.BoxGeometry(0.012,0.34,0.09),mcolor('#22262c',{roughness:0.4}));
  fp.position.set(0,0.19,0.201);g.add(fp);
  const led=new THREE.Mesh(new THREE.SphereGeometry(0.008,10,8),
    new THREE.MeshStandardMaterial({color:'#5bc8ff',emissive:'#2fa8e8',emissiveIntensity:1.0}));
  led.position.set(0,0.30,0.212);g.add(led);
  g.position.set(x,0,z);g.rotation.y=rotY;parent.add(shadowize(g));return g;
}

/* ── 房间样板房高清模型加载（all-models.js 提供 base64 GLB；失败自动回退程序化家具）── */
const gltfLoader = new GLTFLoader();
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.157.0/examples/jsm/libs/draco/');
gltfLoader.setDRACOLoader(dracoLoader);

// 布局 = office3d-assets 样板房 CFO_SCENE 原坐标（朝向约定：AI 模型默认正面朝 +Z）
/* ══ 家具摆位（2026-09-11 按 v4 非对称布局逐房重排）══
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
  { key:'office_chair',   p:[ 1.55, 1.10], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
  { key:'office_chair',   p:[ 1.55,-1.10], r:Math.PI/2,  h:1.00, tint:[0x8A7070,0.40] },
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
  { key:'filing_cabinet', p:[ 2.55,-2.20], r:-Math.PI/2, h:1.10, tint:[0x55595F,0.40] },  // 炭灰（避开北墙显示屏）
  { key:'plant_potted',   p:[-2.75, 1.65], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 0.90, 1.95], r:0,          h:0.60 },
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
  { key:'exec_desk',      p:[-0.90,-1.15], r:0,          h:0.76 },
  { key:'exec_chair',     p:[-0.90,-1.75], r:0,          h:1.20, tint:[0x33506B,0.45] },
  { key:'office_monitor', p:[-1.35,-1.07], r:0,          h:0.50, y:0.76 },
  { key:'office_monitor', p:[-0.45,-1.07], r:0,          h:0.50, y:0.76 },
  { key:'filing_cabinet', p:[ 2.95,-2.60], r:-Math.PI/2, h:1.10 },
  { key:'sofa',           p:[ 1.45, 1.55], r:Math.PI,    h:0.80, tint:[0x6F8FA6,0.45] },
  { key:'coffee_table',   p:[ 1.45, 0.55], r:0,          h:0.45 },
  { key:'office_chair',   p:[ 0.35, 0.55], r:-Math.PI/2, h:1.00, tint:[0x8A7070,0.40] },
  { key:'plant_potted',   p:[-2.85,-2.85], r:0,          h:0.60 },
  { key:'plant_potted',   p:[ 2.90, 2.85], r:0,          h:0.60 },
];

function tintModel(root, hex, strength){
  const mixed = new THREE.Color(1,1,1).lerp(new THREE.Color(hex), strength);
  root.traverse(m => {
    if (!(m.isMesh||m.isInstancedMesh)) return;
    if (!m.userData.baseColors){
      const isArr = Array.isArray(m.material);
      const src = isArr ? m.material : [m.material];
      const cloned = src.map(x=>x.clone());
      m.material = isArr ? cloned : cloned[0];
      m.userData.slotMats = cloned;
      m.userData.baseColors = cloned.map(x=>x.color.clone());
    }
    m.userData.slotMats.forEach((mat,i)=>mat.color.copy(m.userData.baseColors[i]).multiply(mixed));
  });
}
function placeShowModel(key, gltf, item, floorY){
  // clone(true)：同一模型在同一房间/多房间重复使用时，直接 add 同一 scene 会被后一次「抢走」
  const root = gltf.scene.clone(true);
  root.traverse(c=>{ if(c.isMesh){c.castShadow=true;c.receiveShadow=true;} });
  const box = new THREE.Box3().setFromObject(root);
  const size = new THREE.Vector3(); box.getSize(size);
  root.scale.setScalar(item.h / (size.y||1));
  root.updateMatrixWorld(true);
  const box2 = new THREE.Box3().setFromObject(root);
  const c2 = new THREE.Vector3(); box2.getCenter(c2);
  root.position.x -= c2.x; root.position.z -= c2.z; root.position.y -= box2.min.y;
  const holder = new THREE.Group();
  holder.add(root);
  // item.y：离地高度（显示器/笔记本放桌面时用，地面家具省略即 0）
  holder.position.set(item.p[0], floorY + (item.y||0), item.p[1]);
  holder.rotation.y = item.r || 0;
  if (item.tint) tintModel(holder, item.tint[0], item.tint[1]);
  return holder;
}
// 解析结果全局缓存：10 类模型只 parse 一次，8 间房共用
const _gltfCache = {};
function getShowModels(keys){
  return Promise.all(keys.map(k => {
    if (_gltfCache[k]) return Promise.resolve([k, _gltfCache[k]]);
    return new Promise((res, rej)=>{
      const bin = Uint8Array.from(atob(window.OFFICE_MODELS[k]), ch=>ch.charCodeAt(0));
      gltfLoader.parse(bin.buffer, '', g=>{ _gltfCache[k]=g; res([k,g]); }, rej);
    });
  })).then(Object.fromEntries);
}
/* 通用房间样板房加载：高清模型就位后移除程序化兜底组；失败则保留兜底并回退桌面小物高度 */
function loadRoomShowcase(roomId, roomGroup, progGroup, items, extraProps, floorY, propFailY){
  if (!window.OFFICE_MODELS) { console.warn('⚠️ 模型包缺失，'+roomId+' 使用程序化家具'); return; }
  getShowModels([...new Set(items.map(i=>i.key))]).then(map => {
    const g = new THREE.Group();
    items.forEach(item => g.add(placeShowModel(item.key, map[item.key], item, floorY)));
    roomGroup.add(g);
    if (progGroup) roomGroup.remove(progGroup);   // 模型就位 → 撤掉程序化兜底家具
    renderer.shadowMap.needsUpdate = true;        // 新增模型 → 重算一次阴影
    window.__showCount = (window.__showCount||0) + 1;   // 调试/性能测量：已就位房间计数
    console.log('✅ '+roomId+' 高清样板房已加载（'+items.length+' 件模型）');
  }).catch(err => {
    if (extraProps) extraProps.position.y = propFailY;  // 回退程序化台面高度
    console.warn('⚠️ '+roomId+' 高清模型加载失败，保留程序化家具', err);
  });
}

function addFurniture(){
  /* 2026-09-10 深度清理：模型包可用时跳过程序化兜底家具构建。
     此前 7 间房先建程序化家具再叠高清 GLB → 双重家具 + 启动变慢。
     now：OFFICE_MODELS 存在 → 非 CFO 房间直接交给 GLB；
          CFO 保留装饰（墙板/地毯/保险柜/桌面小物，与 GLB 共存）；
          模型包缺失时按原逻辑构建程序化兜底。 */
  const hasModels = !!window.OFFICE_MODELS;
  Object.entries(ZONES).forEach(([id,zone])=>{
    const{cx,cz,w,d}=zone;
    const g=new THREE.Group();
    const hw=w/2,hd=d/2;
    // prog = 程序化兜底家具组；高清模型加载成功后整组移除
    const prog=new THREE.Group();
    const FLOOR=0.09;
    let extraProps=null;   // CFO 桌面小物组（模型失败时回退台面高度）

    if(!hasModels){
    if(id==='ceo'){
      deskTop(prog,0,-hd*0.25,2.5,1.1,MATS.deskLight);deskLegs(prog,0,-hd*0.25,2.5,1.1);
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
      createPlant(prog,-hw+0.8,hd-0.8);createPlant(prog,hw-0.6,hd-0.6);
    }else if(id==='cro'){
      deskTop(prog,0,-hd*0.25,1.8,0.85);deskLegs(prog,0,-hd*0.25,1.8,0.85);
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
      deskTop(prog,0,-hd*0.05,3.2,1.5,MATS.deskLight);deskLegs(prog,0,-hd*0.05,3.2,1.5);
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
      createPlant(prog,hw-0.6,hd-0.7,0.9);
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
      // 前墙左侧(x=-2.5)为记忆白板 → 绿植改放右前/右后角避让
      createPlant(prog,hw-0.6,hd-0.6,0.9);createPlant(prog,hw-0.6,-hd+0.6,0.9);
    }else if(id==='coo'){
      [[2.2,-hd*0.2],[-0.5,-hd*0.2]].forEach(([ox,oz])=>{
        deskTop(prog,ox,oz,1.4,0.75);deskLegs(prog,ox,oz,1.4,0.75);
        const mon=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.34,0.05),
          new THREE.MeshStandardMaterial({color:'#2a2824',roughness:0.16,metalness:0.4}));
        mon.position.set(ox,0.99,oz+0.1);g.add(mon);
      });
      createPrinter(prog,-hw+0.7,hd-0.6,Math.PI);
      createFilingCabinet(prog,hw-0.5,hd-0.6,Math.PI);
      const dash=new THREE.Mesh(new THREE.BoxGeometry(1.8,0.03,1.2),
        new THREE.MeshStandardMaterial({color:'#f8f4ee',roughness:0.28}));
      dash.position.set(0.8,0.78,hd*0.4);g.add(dash);
      createPlant(prog,hw-0.6,-hd+0.6,0.9);
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
      deskTop(prog,hw*0.35,hd*0.4,1.3,0.7,MATS.deskLight);deskLegs(prog,hw*0.35,hd*0.4,1.3,0.7);
      const cable1=new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.03,0.8,8),mcolor('#444',{roughness:0.3}));
      cable1.position.set(-hw+1.2,0.4,-hd*0.15);cable1.rotation.z=Math.PI/4;g.add(cable1);
      const cable2=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.6,8),mcolor('#555',{roughness:0.3}));
      cable2.position.set(-hw+3.5,0.35,-hd*0.15);cable2.rotation.z=-Math.PI/3;g.add(cable2);
      createPlant(prog,hw-0.6,hd-0.6,0.9);
    }
    }
    if(id==='cfo'){
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
      createFilingCabinet(prog,2.55,-2.20,-Math.PI/2);
      createPlant(prog,-2.75,1.65);
      createPlant(prog, 0.90, 1.95);
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
    if(id==='cmo'&&!hasModels){
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

    g.add(prog);
    const SHOW={ceo:CEO_SHOW,cro:CRO_SHOW,coo:COO_SHOW,cpo:CPO_SHOW,
                cto:CTO_SHOW,cmo:CMO_SHOW,meeting:MEETING_SHOW,cfo:CFO_SHOW};
    if(SHOW[id]) loadRoomShowcase(id.toUpperCase(), g, prog, SHOW[id], extraProps, FLOOR, 0.90);

    g.position.set(cx,0,cz);scene.add(g);
  });
}

function createAtrium(){
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

Object.values(ZONES).forEach(zone=>{const room=createRoom(zone);scene.add(room);addInteriorLight(zone);});

/* ===== 记忆派生任务 · 部门墙上显示屏 ===== */
const MEM_STYLE={ceo:'projection',cfo:'display',cto:'display',cro:'projection',meeting:'whiteboard',cmo:'whiteboard',coo:'whiteboard',cpo:'display'};
const memWallMeshes=[], memWalls=[], pulseWalls=[];
function loadMemSeen(){try{return new Set(JSON.parse(localStorage.getItem('wb_mem_seen_v1')||'[]'));}catch(e){return new Set();}}
function saveMemSeen(){try{localStorage.setItem('wb_mem_seen_v1',JSON.stringify([...memSeen]));}catch(e){}}
let memSeen=loadMemSeen();
function wrapText(ctx,text,maxW){const chars=String(text).split('');let line='',lines=[];for(const ch of chars){if(ctx.measureText(line+ch).width>maxW&&line){lines.push(line);line=ch;}else line+=ch;}if(line)lines.push(line);return lines;}
function roundRect(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function drawMemCanvas(ctx,W,H,zone,tasks,style,isNew,unseen){
  ctx.clearRect(0,0,W,H);
  const col=zone.color;
  if(style==='display'){
    let g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#0b0f14');g.addColorStop(1,'#121821');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    ctx.strokeStyle=col;ctx.lineWidth=8;ctx.shadowColor=col;ctx.shadowBlur=isNew?22:10;ctx.strokeRect(6,6,W-12,H-12);ctx.shadowBlur=0;
  }else if(style==='whiteboard'){
    ctx.fillStyle='#f3efe4';ctx.fillRect(0,0,W,H);
    ctx.strokeStyle='#8a7a5e';ctx.lineWidth=8;ctx.strokeRect(6,6,W-12,H-12);
    ctx.strokeStyle='rgba(120,105,80,0.12)';ctx.lineWidth=1;for(let y=48;y<H;y+=26){ctx.beginPath();ctx.moveTo(14,y);ctx.lineTo(W-14,y);ctx.stroke();}
  }else{
    let g=ctx.createRadialGradient(W/2,0,10,W/2,0,H);g.addColorStop(0,'#1a2030');g.addColorStop(1,'#080a10');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    ctx.strokeStyle=col;ctx.lineWidth=8;ctx.shadowColor=col;ctx.shadowBlur=isNew?22:10;ctx.strokeRect(6,6,W-12,H-12);ctx.shadowBlur=0;
    ctx.fillStyle='rgba(255,255,255,0.04)';for(let y=0;y<H;y+=4){ctx.fillRect(0,y,W,1);}
  }
  const titleTxt='看板 · '+zone.name+'  ('+tasks.length+')';
  if(style==='whiteboard'){ctx.fillStyle='#3a342c';}else{ctx.fillStyle='#dff1ff';ctx.shadowColor=col;ctx.shadowBlur=8;}
  ctx.font='bold 30px -apple-system,"PingFang SC",sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';
  ctx.fillText(titleTxt,22,40);ctx.shadowBlur=0;
  ctx.strokeStyle=style==='whiteboard'?'#b9a888':col;ctx.globalAlpha=0.5;ctx.beginPath();ctx.moveTo(22,64);ctx.lineTo(W-22,64);ctx.stroke();ctx.globalAlpha=1;
  const top=82, bottom=H-18, avail=bottom-top, n=tasks.length, rowH=Math.min(avail/(n||1),108), pad=10;
  if(n===0){ctx.fillStyle=style==='whiteboard'?'#8a7d5e':'#7fa8c0';ctx.font='24px -apple-system,"PingFang SC",sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('（暂无任务）',W/2,H/2);return;}
  for(let i=0;i<n;i++){
    const t=tasks[i];const y=top+i*rowH;const x=22,w=W-44,h=rowH-pad;
    if(style==='whiteboard'){
      const rot=((i%2)?1:-1)*0.012;ctx.save();ctx.translate(x+w/2,y+h/2);ctx.rotate(rot);
      ctx.fillStyle=i%2?'#fff7d6':'#e3f0e8';roundRect(ctx,-w/2,-h/2,w,h,8);ctx.fill();ctx.strokeStyle='#cdbf9a';ctx.lineWidth=1.5;ctx.stroke();ctx.restore();
    }else{
      ctx.fillStyle='rgba(255,255,255,0.05)';roundRect(ctx,x,y,w,h,8);ctx.fill();
      ctx.fillStyle=col;ctx.fillRect(x,y+8,5,h-16);
    }
    const txtCol=style==='whiteboard'?'#2e2a22':(style==='display'?'#dbe9f2':'#eef4ff');
    ctx.fillStyle=txtCol;if(style!=='whiteboard'){ctx.shadowColor=col;ctx.shadowBlur=4;}
    ctx.font='bold 19px -apple-system,"PingFang SC",sans-serif';ctx.textAlign='left';ctx.textBaseline='top';
    const lines=wrapText(ctx,t.title,w-30);for(let li=0;li<lines.length&&li<2;li++)ctx.fillText(lines[li],x+16,y+10+li*22);ctx.shadowBlur=0;
    ctx.fillStyle=style==='whiteboard'?'#8a7d5e':'#7fa8c0';ctx.font='13px -apple-system,"PingFang SC",sans-serif';
    ctx.fillText((t.project||'记忆')+(t.id?'  #'+t.id:''),x+16,y+h-18);
  }
  if(isNew){
    const bw=130,bh=42,bx=W-bw-14,by=14;ctx.fillStyle='#c0392b';roundRect(ctx,bx,by,bw,bh,20);ctx.fill();
    ctx.fillStyle='#fff';ctx.font='bold 20px -apple-system,"PingFang SC",sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('新任务 '+unseen,bx+bw/2,by+bh/2);
  }
}
function buildMemWall(zone){
  if(!zone||!ZONES[zone.id])return;
  const style=MEM_STYLE[zone.id]||'display';
  const W=640,H=480;const cv=document.createElement('canvas');cv.width=W;cv.height=H;const ctx=cv.getContext('2d');
  const tex=new THREE.CanvasTexture(cv);tex.minFilter=THREE.LinearFilter;tex.anisotropy=4;
  const hw=zone.w/2,hd=zone.d/2;
  const dispW=style==='whiteboard'?Math.min(2.6,zone.w*0.62):Math.min(3.0,zone.w*0.72);
  const dispH=dispW*(H/W);
  const g=new THREE.Group();
  const frameMat=mcolor('#2a2622',{emissive:new THREE.Color(zone.color),emissiveIntensity:0.12});
  const frame=new THREE.Mesh(new THREE.BoxGeometry(dispW+0.14,dispH+0.14,0.06),frameMat);g.add(frame);
  const pMat=new THREE.MeshBasicMaterial({map:tex,transparent:true});const screen=new THREE.Mesh(new THREE.PlaneGeometry(dispW,dispH),pMat);screen.position.z=0.04;g.add(screen);
  let x=zone.cx,y=1.5,z,rotY;
  if(style==='whiteboard'){
    // 落地白板/黑板：支架 + 托盘 + 脚轮
    const legMat=MATS.metalDark;
    [-dispW/2+0.18,dispW/2-0.18].forEach(lx=>{const leg=new THREE.Mesh(new THREE.BoxGeometry(0.05,1.5,0.05),legMat);leg.position.set(lx,0.75,0);leg.castShadow=true;g.add(leg);});
    const tray=new THREE.Mesh(new THREE.BoxGeometry(dispW-0.1,0.06,0.12),MATS.metal);tray.position.set(0,0.52,0.07);g.add(tray);
    [-1,1].forEach(s=>{const caster=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.06,12),MATS.metalDark);caster.position.set(s*(dispW/2-0.2),0.03,0.12);g.add(caster);});
    if(zone.id==='cmo'){
      // CMO 营销中心 8.2×8.6：门在南墙偏西 → 白板居中靠北墙(−Z)，板面朝南迎门
      x=zone.cx; z=zone.cz-hd+0.6; rotY=0;
    }else if(zone.id==='coo'){
      // COO：v4 起入口改到北墙(−Z) → 白板移到南墙(+Z)实墙，板面仍朝入口
      x=zone.cx; z=zone.cz+hd-0.6; rotY=Math.PI;
    }else if(zone.id==='meeting'){
      // 会议室：v4 起门在东墙(+X)，北/南墙都是实墙 → 白板居中靠南墙(+Z)，板面朝北迎门
      x=zone.cx; z=zone.cz+hd-0.6; rotY=Math.PI;
    }else if(zone.doorWall==='front'){z=zone.cz+hd*0.32;rotY=0;}
    else if(zone.doorWall==='back'){z=zone.cz-hd*0.32;rotY=Math.PI;}
    else {z=zone.cz-hd+0.7;rotY=0;}
  }else{
    // 壁挂式：显示屏（display）/ 投影屏（projection）
    if(zone.doorWall==='front'){z=zone.cz-hd+0.16;rotY=0;}
    else if(zone.doorWall==='back'){z=zone.cz+hd-0.16;rotY=Math.PI;}
    else if(zone.openPlan){z=zone.cz-hd+0.16;rotY=0;}
    else {z=zone.cz-hd+0.16;rotY=0;}
    if(style==='projection'){
      const pj=new THREE.Mesh(new THREE.BoxGeometry(0.42,0.22,0.5),mcolor('#3a3632',{roughness:0.3,metalness:0.4}));pj.position.set(0,1.15,0.55);g.add(pj);
      const lens=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,0.1,16),mcolor('#101010'));lens.rotation.x=Math.PI/2;lens.position.set(0,1.15,0.18);g.add(lens);
    }else{
      const arm=new THREE.Mesh(new THREE.BoxGeometry(0.1,0.1,0.4),MATS.metalDark);arm.position.set(0,-dispH/2-0.05,-0.22);g.add(arm);
      const cap=new THREE.Mesh(new THREE.BoxGeometry(dispW+0.2,0.08,0.05),mcolor('#1a1a1a'));cap.position.set(0,dispH/2+0.06,0);g.add(cap);
    }
  }
  g.position.set(x,y,z);g.rotation.y=rotY;scene.add(g);
  const boardTasks=(zone.tasks||[]).filter(t=>t.session!=='standalone');
  const tasks=boardTasks.length?boardTasks:(zone.tasks||[]).filter(t=>t.session==='standalone');
  const w={zoneId:zone.id,zone,tasks,style,W,H,cv,ctx,tex,frame,screen,isNew:false};
  w.taskIds=tasks.map(t=>t.id);
  w.draw=function(){const unseen=w.taskIds.filter(id=>!memSeen.has(id));w.isNew=unseen.length>0;drawMemCanvas(w.ctx,w.W,w.H,w.zone,w.tasks,w.style,w.isNew,unseen.length);w.tex.needsUpdate=true;if(w.isNew&&pulseWalls.indexOf(w)<0)pulseWalls.push(w);};
  screen.userData={isMemWall:true,zoneId:zone.id};
  memWallMeshes.push(screen);memWalls.push(w);
  w.draw();
}
Object.values(ZONES).forEach(zone=>buildMemWall(zone));
// 种子：示例/真实任务默认已读，仅新导入的 board-export 任务脉冲提示
memWalls.forEach(w=>w.taskIds.forEach(id=>{if(!/^in/.test(id))memSeen.add(id);}));saveMemSeen();
function refreshDeptBoards(){memWalls.forEach(w=>{const zone=ZONES[w.zoneId];if(!zone)return;const bt=(zone.tasks||[]).filter(t=>t.session!=='standalone');const t=bt.length?bt:(zone.tasks||[]).filter(x=>x.session==='standalone');w.tasks=t;w.taskIds=t.map(x=>x.id);w.draw();});}
function ackMemWall(zoneId){
  const w=memWalls.find(x=>x.zoneId===zoneId);if(!w)return;
  w.taskIds.forEach(id=>memSeen.add(id));saveMemSeen();
  const i=pulseWalls.indexOf(w);if(i>=0)pulseWalls.splice(i,1);
  w.frame.material.emissiveIntensity=0.12;w.draw();
}

addFurniture();createAtrium();

function openDoor(zoneId,open=true){
  const pvt=doorGroups[zoneId];if(!pvt||pvt.userData.isOpen===open)return;
  pvt.userData.targetOpen=open;
}
function toggleDoor(zoneId){
  const pvt=doorGroups[zoneId];if(!pvt)return;
  openDoor(zoneId, !pvt.userData.isOpen);
}

function getDoorWorldPos(zone){
  const{cx,cz,w,d,doorWall,doorPos}=zone;
  let x=cx,z=cz;
  if(doorWall==='front'){x=doorPos;z=cz+d/2;}else if(doorWall==='back'){x=doorPos;z=cz-d/2;}
  else if(doorWall==='right'){x=cx+w/2;z=doorPos;}else if(doorWall==='left'){x=cx-w/2;z=doorPos;}
  return{x,z};
}
function createConnectionLines(zoneIds){
  clearConnectionLines();if(zoneIds.length<2)return;
  const involved=zoneIds.map(id=>ZONES[id]).filter(Boolean);
  const colors=['#9480d0','#d8a838','#5888c0','#509870','#c87048'];
  function manhattan(a,b){
    const da=getDoorWorldPos(a),db=getDoorWorldPos(b);
    const pts=[new THREE.Vector3(da.x,0.15,da.z)];
    const ax=da.x,az=da.z,bx=db.x,bz=db.z;
    const midX=(ax+bx)/2,midZ=(az+bz)/2;
    if(Math.abs(ax-bx)<2&&Math.abs(az-bz)<2){
      pts.push(new THREE.Vector3(bx,0.15,bz));
    }else if(Math.abs(az-bz)<3||a.cz===b.cz){
      if(Math.abs(ax-bx)>0.5)pts.push(new THREE.Vector3(midX,0.15,az));
      pts.push(new THREE.Vector3(midX,0.15,bz));
      pts.push(new THREE.Vector3(bx,0.15,bz));
    }else{
      pts.push(new THREE.Vector3(ax,0.15,midZ));
      pts.push(new THREE.Vector3(bx,0.15,midZ));
      pts.push(new THREE.Vector3(bx,0.15,bz));
    }
    return pts;
  }
  for(let i=0;i<involved.length;i++){for(let j=i+1;j<involved.length;j++){
    const a=involved[i],b=involved[j],color=colors[(i+j)%colors.length];
    const pts=manhattan(a,b);
    const geo=new THREE.BufferGeometry().setFromPoints(pts);
    const line=new THREE.Line(geo,new THREE.LineBasicMaterial({color,linewidth:1,transparent:true,opacity:0.75,depthTest:true,depthWrite:true}));
    line.renderOrder=1;scene.add(line);
    const glowGeo=new THREE.BufferGeometry().setFromPoints(pts);
    const glow=new THREE.Line(glowGeo,new THREE.LineBasicMaterial({color,linewidth:1,transparent:true,opacity:0.15,depthTest:true,depthWrite:false}));
    glow.renderOrder=0;scene.add(glow);
    const dot=new THREE.Mesh(new THREE.SphereGeometry(0.1,8,8),
      new THREE.MeshBasicMaterial({color,transparent:true,opacity:0.85,depthTest:true,depthWrite:false}));
    dot.renderOrder=2;scene.add(dot);
    connectionLines.push({line,glow,dot,pts,color,mat:line.material,glowMat:glow.material,dotMat:dot.material});
  }}
}
function clearConnectionLines(){
  connectionLines.forEach(l=>{scene.remove(l.line);scene.remove(l.glow);scene.remove(l.dot);
    l.line.geometry.dispose();l.glow.geometry.dispose();l.dot.geometry.dispose();
    l.mat.dispose();l.glowMat.dispose();l.dotMat.dispose();});
  connectionLines.length=0;
}

function activateCollab(task){
  deactivateCollab();
  if(!task?.collaborators||task.collaborators.length<2)return;
  activeCollabTask=task;
  task.collaborators.forEach(zid=>openDoor(zid,true));
  createConnectionLines(task.collaborators);
  const names=task.collaborators.map(id=>ZONES[id]?.name||id).join(' · ');
  collabIndicator.textContent='🔗 跨部门协作: '+names;collabIndicator.style.display='block';
  document.querySelectorAll('.task-card').forEach(card=>{card.classList.toggle('collab-active',card.dataset.taskId===task.id);});
}
function deactivateCollab(){
  if(!activeCollabTask)return;
  const prev=activeCollabTask;activeCollabTask=null;
  if(prev.collaborators)prev.collaborators.forEach(zid=>openDoor(zid,false));
  clearConnectionLines();collabIndicator.style.display='none';
  document.querySelectorAll('.task-card.collab-active').forEach(c=>c.classList.remove('collab-active'));
}

function onMouseMove(e){
  mouse.x=(e.clientX/window.innerWidth)*2-1;mouse.y=-(e.clientY/window.innerHeight)*2+1;
  raycaster.setFromCamera(mouse,camera);
  const hits=raycaster.intersectObjects(allRoomFloorMeshes,false);
  let nh=null;if(hits.length>0&&hits[0].object.userData?.isFloor)nh=hits[0].object.userData.zoneId;
  if(nh!==hoveredZone){
    if(hoveredZone){const prev=allRoomFloorMeshes.find(m=>m.userData?.zoneId===hoveredZone);if(prev){prev.material.opacity=0.25;prev.material.emissive.set(0);prev.material.emissiveIntensity=0;}}
    if(nh){const cur=allRoomFloorMeshes.find(m=>m.userData?.zoneId===nh);if(cur){cur.material.opacity=0.65;cur.material.emissive.set(cur.userData.color);cur.material.emissiveIntensity=0.3;}}
    hoveredZone=nh;
  }
  // 门 hover：手型指针
  const dh=raycaster.intersectObjects(doorPickables,false);
  document.body.style.cursor=dh.length?'pointer':(nh?'pointer':'');
}
function onClick(e){
  if(e.target.closest('#panel')||e.target.closest('#toolbar')||e.target.closest('#legend')||e.target.closest('#syspanel'))return;
  mouse.x=(e.clientX/window.innerWidth)*2-1;mouse.y=-(e.clientY/window.innerHeight)*2+1;
  raycaster.setFromCamera(mouse,camera);
  // 门扇优先命中：点击门 → 切换开/关
  const dh=raycaster.intersectObjects(doorPickables,false);
  if(dh.length>0&&dh[0].object.userData?.isDoor){toggleDoor(dh[0].object.userData.zoneId);return;}
  const mh=raycaster.intersectObjects(memWallMeshes,false);
  if(mh.length>0){const ud=mh[0].object.userData;if(ud&&ud.isMemWall){ackMemWall(ud.zoneId);return;}}
  const hits=raycaster.intersectObjects(allRoomFloorMeshes,false);
  if(hits.length>0&&hits[0].object.userData?.isFloor){openPanel(hits[0].object.userData.zoneId,false);return;}
  closePanel();
}
function onDblClick(e){
  if(e.target.closest('#panel')||e.target.closest('#toolbar')||e.target.closest('#legend')||e.target.closest('#syspanel'))return;
  mouse.x=(e.clientX/window.innerWidth)*2-1;mouse.y=-(e.clientY/window.innerHeight)*2+1;
  raycaster.setFromCamera(mouse,camera);
  const hits=raycaster.intersectObjects(allRoomFloorMeshes,false);
  if(hits.length>0&&hits[0].object.userData?.isFloor){const zone=ZONES[hits[0].object.userData.zoneId];openPanel(zone.id,false);animateToZone(zone);}
}

function openPanel(zoneId, zoom=true){
  closeSysPanel();deactivateCollab();activeZone=zoneId;activeFilter='all';
  const zone=ZONES[zoneId];panelTitle.textContent=zone.name;panelDot.style.background=zone.color;
  panel.classList.add('open');hint.style.opacity='0';
  if(zoom)animateToZone(zone);
  document.querySelectorAll('#toolbar .tool-btn').forEach(b=>{b.classList.toggle('active',b.dataset.view===zoneId);});
  renderPanel();
}
function closePanel(){
  deactivateCollab();activeZone=null;  panel.classList.remove('open');hint.style.opacity='1';
  document.querySelectorAll('#toolbar .tool-btn').forEach(b=>{b.classList.toggle('active',b.dataset.view==='overview');});
}

function renderPanel(){
  if(!activeZone)return;
  const zone=ZONES[activeZone];
  const tasks=(zone.tasks||[]).filter(t=>t.session!=='standalone');
  const filtered=activeFilter==='all'?tasks:tasks.filter(t=>t.status===activeFilter);
  const done=tasks.filter(t=>t.status==='done').length,inProg=tasks.filter(t=>t.status==='in_progress').length;
  const blocked=tasks.filter(t=>t.status==='blocked').length,cross=tasks.filter(t=>t.collaborators?.length>1).length;
  panelStats.innerHTML=`<div class="stat-item">全部 <span class="stat-num">${tasks.length}</span></div><div class="stat-item">进行中 <span class="stat-num">${inProg}</span></div><div class="stat-item">已完成 <span class="stat-num">${done}</span></div>${cross>0?`<div class="stat-item" style="color:#706898">跨部门 <span class="stat-num" style="color:#706898">${cross}</span></div>`:''}${blocked>0?`<div class="stat-item" style="color:#8a5858">阻塞 <span class="stat-num" style="color:#8a5858">${blocked}</span></div>`:''}`;
  const st=[{key:'all',label:'全部'},{key:'todo',label:'待办'},{key:'in_progress',label:'进行中'},{key:'done',label:'已完成'},{key:'blocked',label:'已阻塞'}];
  panelFilters.innerHTML=st.map(s=>`<button class="filter-btn ${activeFilter===s.key?'active':''}" data-filter="${s.key}">${s.label}</button>`).join('');
  if(filtered.length===0){taskListEl.innerHTML='<div class="empty-state">该房间暂无匹配任务</div>';}
  else{
    const labels={todo:'待办',in_progress:'进行中',done:'已完成',blocked:'已阻塞'};
    taskListEl.innerHTML=filtered.map(t=>{
      const cDots=t.collaborators?.length>1?`<div class="task-collab">${t.collaborators.map(cid=>{const cz=ZONES[cid];return cz?`<span class="collab-dot" style="background:${cz.color}" title="${cz.name}"></span>`:'';}).join('')}<span style="font-size:10px;color:#706898;margin-left:2px">跨部门</span></div>`:'';
      return`<div class="task-card" draggable="true" data-task-id="${t.id}" data-zone="${activeZone}" ${t.collaborators?.length>1?'data-has-collab="true"':''}><div class="task-priority ${t.priority}"></div><div class="task-body"><div class="task-title">${t.title}</div>${t.desc?`<div class="task-desc-line">${escapeHtml(t.desc)}</div>`:(t.description?`<div class="task-desc-line">${escapeHtml(t.description)}</div>`:'')}<div class="task-meta"><span class="task-project">${t.project}</span>${t.auto?'<span class="task-auto">🤖 自动化</span>':''}<button class="task-status ${t.status}" data-action="cycle-status" data-task-id="${t.id}">${labels[t.status]}</button></div>${cDots}</div><div class="task-actions"><button class="task-action-btn" data-action="next-status" data-task-id="${t.id}" title="推进">▶</button><button class="task-action-btn" data-action="block" data-task-id="${t.id}" title="阻塞" ${t.status==='blocked'?'style="color:#8a5858"':''}>⏸</button>${t.collaborators?.length>1?`<button class="task-action-btn" data-action="show-collab" data-task-id="${t.id}" title="查看协作关系" style="color:#706898">🔗</button>`:''}<button class="task-action-btn danger" data-action="delete" data-task-id="${t.id}" title="删除任务">🗑</button></div></div>`;
    }).join('');
  }
  bindPanelEvents();
}
function bindPanelEvents(){
  document.querySelectorAll('#panel-filters .filter-btn').forEach(btn=>{btn.addEventListener('click',()=>{activeFilter=btn.dataset.filter;renderPanel();});});
  document.querySelectorAll('.task-status[data-action="cycle-status"]').forEach(btn=>{btn.addEventListener('click',(e)=>{e.stopPropagation();const t=ZONES[activeZone].tasks.find(x=>x.id===btn.dataset.taskId);if(!t)return;t.status={todo:'in_progress',in_progress:'done',done:'todo',blocked:'in_progress'}[t.status];renderPanel();});});
  document.querySelectorAll('.task-action-btn').forEach(btn=>{btn.addEventListener('click',(e)=>{e.stopPropagation();const t=ZONES[activeZone].tasks.find(x=>x.id===btn.dataset.taskId);if(!t)return;if(btn.dataset.action==='next-status'){t.status={todo:'in_progress',in_progress:'done',done:'todo',blocked:'in_progress'}[t.status];renderPanel();}else if(btn.dataset.action==='block'){t.status=t.status==='blocked'?'todo':'blocked';renderPanel();}else if(btn.dataset.action==='show-collab'){activeCollabTask?.id===t.id?deactivateCollab():activateCollab(t);renderPanel();}else if(btn.dataset.action==='delete'){deleteTask(activeZone,btn.dataset.taskId);}});});
  document.querySelectorAll('.task-card').forEach(card=>{
    card.addEventListener('click',(e)=>{
    if(e.target.closest('button'))return;
    const t=ZONES[activeZone].tasks.find(x=>x.id===card.dataset.taskId);
    if(!t)return;
    if(t.collaborators?.length>1 && activeCollabTask?.id!==t.id){
      activateCollab(t);renderPanel();
    }
    openDetail(t, activeZone);
  });
    card.addEventListener('dragstart',(e)=>{draggedTaskId=card.dataset.taskId;card.classList.add('dragging');e.dataTransfer.effectAllowed='move';});
    card.addEventListener('dragend',()=>{card.classList.remove('dragging');document.querySelectorAll('.task-card').forEach(c=>c.classList.remove('drag-over'));draggedTaskId=null;});
    card.addEventListener('dragover',(e)=>{e.preventDefault();e.dataTransfer.dropEffect='move';if(card.dataset.taskId!==draggedTaskId)card.classList.add('drag-over');});
    card.addEventListener('dragleave',()=>{card.classList.remove('drag-over');});
    card.addEventListener('drop',(e)=>{e.preventDefault();card.classList.remove('drag-over');if(!draggedTaskId||draggedTaskId===card.dataset.taskId)return;const tasks=ZONES[activeZone].tasks;const fi=tasks.findIndex(x=>x.id===draggedTaskId);const ti=tasks.findIndex(x=>x.id===card.dataset.taskId);if(fi<0||ti<0)return;const[m]=tasks.splice(fi,1);tasks.splice(ti,0,m);renderPanel();});
  });
}

/* ===== 系统配置面板 (方案B·中控台) ===== */
const SYS_CONFIG_FILES=[
  {name:'SOUL.md',role:'灵魂/行为准则',mtime:'2026-07-05',path:'~/.workbuddy/SOUL.md',desc:'AI 搭档的核心性格与准则：能动手不动嘴、编号要点、第三方评审、记忆机制等。'},
  {name:'IDENTITY.md',role:'身份画像',mtime:'2026-07-05',path:'~/.workbuddy/IDENTITY.md',desc:'定义我是谁：Kingsley 的 AI 搭档 / 财务+营销智囊，含输出风格约定。'},
  {name:'USER.md',role:'用户档案',mtime:'2026-07-05',path:'~/.workbuddy/USER.md',desc:'你的画像：企业财务总监+市场营销、非技术背景、结构化输出与自检偏好。'},
  {name:'MEMORY.md',role:'长期记忆',mtime:'2026-07-15',path:'~/.workbuddy/MEMORY.md',desc:'跨项目长期偏好：输出格式、项目评审机制、任务领域框架、设计风格等。'}
];
const SYS_COMPLETED=[
  {title:'门缝修复',group:'board',desc:'门扇宽度改为 lw=gapW/leaves 填满门洞，消除门扇自由边与对侧墙体的约 0.10m 空隙。'},
  {title:'双击聚焦',group:'board',desc:'交互由"单击 zoom"改为"双击房间才 zoom in"；单击仅开面板、镜头不动。'},
  {title:'投影屏移位',group:'board',desc:'会议室投影屏由后墙（门后）移至前墙 z=hd-0.15，消除"黑方块"。'},
  {title:'GSAP 相机动画',group:'board',desc:'引入 GSAP 平滑过渡（ease-in-out、可中断 killTweensOf），优化镜头切换。'},
  {title:'配置文档产出',group:'doc',desc:'产出 WB看板配置-001.md，梳理布局/门墙/数据管线/相机交互等全部配置基线。'}
];
const syspanel=document.getElementById('syspanel');
const syspanelBody=document.getElementById('syspanel-body');
function openSysPanel(){
  closePanel();
  syspanel.classList.add('open');hint.style.opacity='0';
  document.querySelectorAll('#toolbar .tool-btn').forEach(b=>{b.classList.toggle('active',b.id==='btn-sys');});
  renderSysPanel();
}
function closeSysPanel(){
  syspanel.classList.remove('open');
  if(!document.getElementById('panel').classList.contains('open'))hint.style.opacity='1';
  document.querySelectorAll('#toolbar .tool-btn').forEach(btn=>{btn.classList.toggle('active',btn.dataset.view==='overview');});
}
function toggleSysPanel(){syspanel.classList.contains('open')?closeSysPanel():openSysPanel();}
function renderSysPanel(){
  const memTasks=[];
  if(window.TASK_DATA){Object.entries(window.TASK_DATA).forEach(([dep,arr])=>{(arr||[]).forEach(t=>{if(t.session==='standalone')memTasks.push({dep,title:t.title,desc:t.desc,project:t.project});});});}
  const cfgHtml=SYS_CONFIG_FILES.map(f=>`<div class="cfg-card" data-cfg="${f.name}" onclick="openCfgModal('${f.name}')"><div class="cfg-name">${f.name}<span class="sys-badge">${f.role}</span></div><div class="cfg-path">${f.path}</div><div class="cfg-desc">${f.desc}</div><div class="cfg-meta">更新于 ${f.mtime}</div><div class="cfg-view">👁 点击查看全文</div></div>`).join('');
  const memHtml=memTasks.map(t=>`<div class="sys-task"><div class="sys-task-title">${t.title}</div><div class="sys-task-desc">${t.desc||''}</div><div class="cfg-meta">来源：长期记忆 MEMORY.md · 原属 ${t.dep.toUpperCase()}</div></div>`).join('');
  const boardBatch=SYS_COMPLETED.filter(c=>c.group==='board').map(c=>`<div class="sys-task"><div class="sys-task-title">${c.title}</div><div class="sys-task-desc">${c.desc}</div></div>`).join('');
  const docItem=SYS_COMPLETED.filter(c=>c.group==='doc').map(c=>`<div class="sys-task"><div class="sys-task-title">${c.title}</div><div class="sys-task-desc">${c.desc}</div></div>`).join('');
  const deptManage=Object.values(ZONES).filter(z=>z.id!=='lounge').map(z=>{
    const tasks=(z.tasks||[]);
    const head=`<div class="dept-manage-head"><span class="dept-dot" style="background:${z.color}"></span>${z.name}<span class="count">${tasks.length} 条</span>${tasks.length?`<button class="sys-jump" data-jump="${z.id}">打开</button>`:''}</div>`;
    const rows=tasks.map(t=>`<div class="dept-task-row"><span class="dept-task-title" title="${escapeHtml(t.title)}">${escapeHtml(t.title)}</span><button class="sys-del-btn" data-del-zone="${z.id}" data-del-task="${t.id}" title="删除">🗑</button></div>`).join('');
    return `<div class="dept-manage">${head}${rows}</div>`;
  }).join('');
  const totalTasks=Object.values(ZONES).reduce((a,z)=>a+(z.tasks?z.tasks.length:0),0);
  syspanelBody.innerHTML=`
    <div class="sys-section">
      <div class="sys-section-title">🧩 人格配置文件 <span class="count">${SYS_CONFIG_FILES.length} 份</span></div>
      ${cfgHtml}
    </div>
    <div class="sys-section">
      <div class="sys-section-title">📄 记忆派生任务 <span class="count">${memTasks.length} 条 · 非部门</span></div>
      <div class="sys-note" style="margin-bottom:10px">以下任务来自你的长期记忆（MEMORY.md），不归属任何部门房间，统一在此中控台展示。</div>
      ${memHtml}
    </div>
    <div class="sys-section">
      <div class="sys-section-title">🗑 部门任务管理 <span class="count">${totalTasks} 条</span></div>
      <div class="sys-note" style="margin-bottom:10px">各部门房间内的任务。点「打开」跳转该部门面板，或点 🗑 直接删除（不可撤销）。</div>
      ${deptManage}
    </div>
    <div class="sys-section">
      <div class="sys-section-title">✅ 本会话已完成 <span class="count">${SYS_COMPLETED.length} 项</span></div>
      <div class="sys-group-label">看板过程处理批次（前 4 项）</div>
      ${boardBatch}
      <div class="sys-group-label" style="margin-top:14px">配置文档产出</div>
      ${docItem}
    </div>`;
  syspanelBody.querySelectorAll('.sys-del-btn').forEach(b=>b.addEventListener('click',()=>deleteTask(b.dataset.delZone,b.dataset.delTask)));
  syspanelBody.querySelectorAll('.sys-jump').forEach(b=>b.addEventListener('click',()=>openPanel(b.dataset.jump)));
}

function inlineMd(s){return s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>');}
function renderMarkdown(md){
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const lines=md.split('\n');let html='';let inCode=false;let listOpen=false;
  const closeList=()=>{if(listOpen){html+='</ul>';listOpen=false;}};
  for(let raw of lines){
    if(raw.trim().startsWith('```')){if(inCode){html+='</code></pre>';inCode=false;}else{closeList();html+='<pre class="cfg-code"><code>';inCode=true;}continue;}
    if(inCode){html+=esc(raw)+'\n';continue;}
    let m=raw.match(/^(#{1,6})\s+(.*)$/);
    if(m){closeList();const lvl=m[1].length;html+='<h'+lvl+' class="cfg-h'+lvl+'">'+inlineMd(esc(m[2]))+'</h'+lvl+'>';continue;}
    if(/^>\s?/.test(raw)){closeList();html+='<blockquote>'+inlineMd(esc(raw.replace(/^>\s?/,'')))+'</blockquote>';continue;}
    if(/^[-*]\s+/.test(raw)){if(!listOpen){html+='<ul>';listOpen=true;}html+='<li>'+inlineMd(esc(raw.replace(/^[-*]\s+/,'')))+'</li>';continue;}
    if(/^\|.*\|\s*$/.test(raw)){closeList();html+='<div class="cfg-table-row">'+inlineMd(esc(raw))+'</div>';continue;}
    if(raw.trim()===''){closeList();continue;}
    closeList();html+='<p>'+inlineMd(esc(raw))+'</p>';
  }
  closeList();if(inCode)html+='</code></pre>';return html;
}
function openCfgModal(name){
  const el=document.getElementById('cfg-'+name);
  if(!el)return;
  document.getElementById('cfg-modal-title').textContent=name;
  document.getElementById('cfg-modal-body').innerHTML=renderMarkdown(el.textContent);
  document.getElementById('cfg-modal').classList.add('open');
}
function closeCfgModal(){document.getElementById('cfg-modal').classList.remove('open');}
document.getElementById('cfg-modal-close').addEventListener('click',closeCfgModal);
document.getElementById('cfg-modal').addEventListener('click',function(e){if(e.target.id==='cfg-modal')closeCfgModal();});

document.getElementById('btn-sys').addEventListener('click',(e)=>{e.stopPropagation();toggleSysPanel();});
document.getElementById('syspanel-close').addEventListener('click',closeSysPanel);

document.getElementById('panel-close').addEventListener('click',closePanel);
window.addEventListener('mousemove',onMouseMove);window.addEventListener('click',onClick);window.addEventListener('dblclick',onDblClick);
document.querySelectorAll('#toolbar .tool-btn').forEach(btn=>{btn.addEventListener('click',(e)=>{e.stopPropagation(); if(btn.id==='btn-sys')return; const v=btn.dataset.view; closeSysPanel(); if(v==='overview'){animateToOverview();}else if(ZONES[v])openPanel(v);});});
const legend=document.getElementById('legend');
legend.innerHTML=Object.values(ZONES).filter(z=>z.id!=='lounge').map(z=>`<div class="legend-item" data-zone="${z.id}"><div class="legend-dot" style="background:${z.color}"></div><span>${z.name}</span></div>`).join('');
document.querySelectorAll('.legend-item').forEach(item=>{item.addEventListener('click',(e)=>{e.stopPropagation();const zid=item.dataset.zone;if(ZONES[zid])openPanel(zid);});});

function animateDoors(){
  let shadowDirty=false;   // 门在动 → 本帧需重算阴影贴图
  Object.entries(doorGroups).forEach(([zid,pvt])=>{
    if(pvt.userData.targetOpen===undefined)return;
    shadowDirty=true;
    const target=pvt.userData.targetOpen?pvt.userData.openAngle:0;
    if(pvt.userData.leaves){pvt.userData.leaves.forEach((lf,i)=>{
      /* 开门方向：所有门一律向"门外"侧开。
         叶片尖端在 pivot 局部系里从 +X 转向 −Z；该旋向是否等于"朝外"
         取决于 pivot.rotation.y（见 createRoom）→ 由 openSign 统一折算：
           · 东/西墙(right/left)：局部旋向 = 朝外 → openSign = +1
           · 南/北墙(front/back)：局部旋向 = 朝内 → openSign = −1
         单开门 sign = openSign；双开门首片 +openSign、次片 −openSign（对称外开） */
      const sign=(pvt.userData.isDouble?(i===0?+1:-1):+1)*(pvt.userData.openSign||1);
      const goal=target*sign,cur=lf.rotation.y,diff=goal-cur;
      if(Math.abs(diff)<0.004){lf.rotation.y=goal;if(i===pvt.userData.leaves.length-1){pvt.userData.isOpen=pvt.userData.targetOpen;delete pvt.userData.targetOpen;}}
      else lf.rotation.y+=diff*0.1;
    });}
  });
  if(shadowDirty) renderer.shadowMap.needsUpdate=true;   // 门动画期间按需刷新阴影
}
function animateLines(){
  animTime+=0.007;
  connectionLines.forEach(l=>{const t=(Math.sin(animTime*2.2)+1)/2;l.mat.opacity=0.5+t*0.35;l.glowMat.opacity=0.08+t*0.12;
    if(l.pts&&l.pts.length>1){const n=Math.floor((animTime*3)%(l.pts.length-1));const f=(animTime*3)%1;const p0=l.pts[n];const p1=l.pts[n+1]||l.pts[0];
      l.dot.position.lerpVectors(p0,p1,f);}
    l.dot.material.opacity=0.55+t*0.45;});
}
let currentDetailTask=null,currentDetailZone=null;

function openDetail(task, zoneId){
  currentDetailTask=task;currentDetailZone=zoneId;
  const overlay=document.getElementById('detail-overlay');
  document.getElementById('detail-priority').className='task-priority '+task.priority;
  document.getElementById('detail-title').textContent=task.title;

  const pj=document.getElementById('detail-project');
  pj.textContent=task.project;
  pj.className='task-project';

  const st=document.getElementById('detail-status');
  const labels={todo:'待办',in_progress:'进行中',done:'已完成',blocked:'已阻塞'};
  st.textContent=labels[task.status]||task.status;
  st.className='task-status '+task.status;

  const autoEl=document.getElementById('detail-auto');
  autoEl.style.display=task.auto?'inline':'none';
  if(task.auto){autoEl.textContent='🤖 自动化';autoEl.className='task-auto';}

  const desc=document.getElementById('detail-desc');
  desc.textContent=task.desc||task.description||'暂无详细描述。';

  const bar=document.getElementById('detail-progress-bar');
  const fill=document.getElementById('detail-progress-fill');
  const stats=document.getElementById('detail-stats');
  const stepsTitle=document.getElementById('detail-steps-title');
  const stepsEl=document.getElementById('detail-steps');

  if(task.progress&&task.progress.steps){
    const total=task.progress.steps.length;
    const done=task.progress.steps.filter(s=>s.d).length;
    const pct=Math.round(done/total*100);
    bar.style.display='block';fill.style.width=pct+'%';
    stats.style.display='flex';
    stats.innerHTML=`<span>进度 ${done}/${total}</span><span style="font-weight:600;color:#485c48">${pct}%</span>`;
    stepsTitle.style.display='block';
    stepsEl.innerHTML=task.progress.steps.map((s,i)=>`
      <div class="progress-step" data-step-idx="${i}">
        <div class="step-check ${s.d?'checked':''}">${s.d?'✓':''}</div>
        <span class="step-label ${s.d?'done':''}">${s.n}</span>
      </div>
    `).join('');
    stepsEl.querySelectorAll('.progress-step').forEach(step=>{
      step.addEventListener('click',()=>{
        const idx=parseInt(step.dataset.stepIdx);
        task.progress.steps[idx].d=!task.progress.steps[idx].d;
        renderPanel();openDetail(task,zoneId);
      });
    });
  }else{
    bar.style.display='none';stats.style.display='none';stepsTitle.style.display='none';stepsEl.innerHTML='';
  }

  const collabTitle=document.getElementById('detail-collab-title');
  const collabEl=document.getElementById('detail-collab');
  const collabBtn=document.getElementById('detail-btn-collab');
  if(task.collaborators&&task.collaborators.length>1){
    collabTitle.style.display='block';collabBtn.style.display='block';
    collabEl.innerHTML=task.collaborators.map(cid=>{
      const cz=ZONES[cid];if(!cz)return'';
      return`<span class="detail-collab-tag" style="background:${cz.color}22;color:${cz.color};border:1px solid ${cz.color}44">● ${cz.name}</span>`;
    }).join('');
  }else{
    collabTitle.style.display='none';collabEl.innerHTML='';collabBtn.style.display='none';
  }

  const btnBlock=document.getElementById('detail-btn-block');
  if(task.status==='blocked'){btnBlock.textContent='⏸ 取消阻塞';btnBlock.classList.add('danger');}
  else{btnBlock.textContent='⏸ 标记阻塞';btnBlock.classList.remove('danger');}

  overlay.classList.add('show');
}

function closeDetail(){
  document.getElementById('detail-overlay').classList.remove('show');
  currentDetailTask=null;currentDetailZone=null;
}

function detailNextStatus(){
  if(!currentDetailTask||!currentDetailZone)return;
  const cycle={todo:'in_progress',in_progress:'done',done:'todo',blocked:'in_progress'};
  currentDetailTask.status=cycle[currentDetailTask.status];
  renderPanel();openDetail(currentDetailTask,currentDetailZone);
}
function detailToggleBlock(){
  if(!currentDetailTask||!currentDetailZone)return;
  currentDetailTask.status=currentDetailTask.status==='blocked'?'todo':'blocked';
  renderPanel();openDetail(currentDetailTask,currentDetailZone);
}
function deleteTask(zoneId, taskId){
  const zone=ZONES[zoneId]; if(!zone||!zone.tasks)return;
  const t=zone.tasks.find(x=>x.id===taskId); if(!t)return;
  if(!confirm('确认删除任务「'+t.title+'」？此操作不可撤销。'))return;
  zone.tasks=zone.tasks.filter(x=>x.id!==taskId);
  if(currentDetailTask&&currentDetailTask.id===taskId)closeDetail();
  if(activeZone===zoneId)renderPanel();
  if(syspanel.classList.contains('open'))renderSysPanel();
  if(typeof refreshDeptBoards==='function')refreshDeptBoards();
}
function detailShowCollab(){
  if(!currentDetailTask)return;
  if(activeCollabTask?.id===currentDetailTask.id)deactivateCollab();
  else activateCollab(currentDetailTask);
  closeDetail();
}

document.getElementById('detail-close').addEventListener('click',closeDetail);
document.getElementById('detail-overlay').addEventListener('click',(e)=>{
  if(e.target===document.getElementById('detail-overlay'))closeDetail();
});
document.getElementById('detail-btn-next').addEventListener('click',detailNextStatus);
document.getElementById('detail-btn-block').addEventListener('click',detailToggleBlock);
document.getElementById('detail-btn-collab').addEventListener('click',detailShowCollab);
document.addEventListener('keydown',(e)=>{if(e.key==='Escape')closeDetail();});

function animate(){requestAnimationFrame(animate);animTime+=0.016;controls.update();animateDoors();if(connectionLines.length>0)animateLines();pulseWalls.forEach(w=>{if(w.frame)w.frame.material.emissiveIntensity=0.45+0.4*Math.sin(animTime*3.5);});renderer.render(scene,camera);}

// === board-export 浏览器内导入（无需终端/服务器） ===
const IMPORT_DEPTS = new Set(['ceo','cfo','cto','cpo','cmo','coo','cro','meeting']);

function parseImportMd(text){
  let project='board-export';
  const m = text.match(/触发会话[:：]\s*(.+)/);
  if (m) project = m[1].trim();
  const tasks = [];
  const blockRe = /```board\s*([\s\S]*?)```/g;
  let bm;
  while ((bm = blockRe.exec(text)) !== null) {
    for (const line of bm[1].split('\n')) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const lm = trimmed.match(/^\[(\w+)\]\s+(.*)$/);
      if (!lm) continue;
      const dept = lm[1].toLowerCase();
      if (!IMPORT_DEPTS.has(dept)) { console.warn('skip unknown dept:', dept); continue; }
      const rest = lm[2].trim();
      const parts = rest.split(' | ').map(p => p.trim());
      const title = parts[0];
      if (!title) continue;
      const entry = { title: title.slice(0, 50), status: 'todo', priority: 'medium', project: project.slice(0, 20), source: 'board-export' };
      for (const seg of parts.slice(1)) {
        const idx = seg.indexOf(':');
        if (idx < 0) continue;
        const k = seg.slice(0, idx).trim().toLowerCase();
        const v = seg.slice(idx + 1).trim();
        if (k === 'p' || k === 'priority') entry.priority = v;
        else if (k === 'd' || k === 'due') entry.due = v;
        else if (k === 's' || k === 'status') entry.status = v;
        else if (k === 'dep' || k === 'collaborators') entry.collaborators = v.split(',').map(x => x.trim()).filter(Boolean);
        else if (k === 'desc' || k === 'description') { entry.desc = v.slice(0, 200); entry.description = v.slice(0, 200); }
      }
      tasks.push({ dept, entry });
    }
  }
  return { project, tasks };
}

function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }


function downloadFile(filename, content) {
  const blob = new Blob([content], { type: 'application/javascript;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}

function showImportModal(opts) {
  const modal = document.getElementById('import-modal');
  const title = document.getElementById('import-modal-title');
  const body = document.getElementById('import-modal-body');
  title.textContent = opts.title;
  let html = '';
  if (opts.body) {
    html = '<div style="line-height:1.7;font-size:14px;">' + escapeHtml(opts.body) + '</div>';
  } else {
    html += '<div class="summary">';
    html += '<span>处理文件<b>' + (opts.files ? opts.files.length : 0) + '</b></span>';
    html += '<span>新增任务<b>' + (opts.total || 0) + '</b></span>';
    if (opts.depCounts) {
      const parts = Object.entries(opts.depCounts);
      if (parts.length > 0) {
        html += '<span style="flex-basis:100%;margin-top:6px;font-size:12px;color:#666;">按部门：';
        for (const [d, c] of parts) {
          html += '<span class="dept-b">' + d.toUpperCase() + '·' + c + '</span>';
        }
        html += '</span>';
      }
    }
    html += '</div>';
    if (opts.files && opts.files.length > 0) {
      html += '<div class="file-list">';
      for (const f of opts.files) {
        if (f.error) {
          html += '<div class="file-row error">⚠ ' + escapeHtml(f.name) + ' — ' + escapeHtml(f.error) + '</div>';
        } else {
          html += '<div class="file-row">✅ <b>' + escapeHtml(f.name) + '</b> &nbsp;·&nbsp; ' + f.count + ' 条 &nbsp;·&nbsp; <span style="color:#888;">' + escapeHtml(f.project || '') + '</span></div>';
        }
      }
      html += '</div>';
    }
    html += '<div class="tip">点下方按钮把 inbox_tasks.js 保存到看板 tasks-data/ 目录即可持久化</div>';
    html += '<div class="actions">';
    html += '<button class="secondary" id="import-modal-close-btn">关闭</button>';
    html += '</div>';
  }
  body.innerHTML = html;
  modal.style.display = 'flex';
  const closeBtn = document.getElementById('import-modal-close-btn');
  if (closeBtn) closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });
}

async function handleImportFolder(files) {
  const mdFiles = files.filter(f => f.name.endsWith('.md') && !f.name.startsWith('.'));
  const allTasks = [];
  const fileResults = [];
  for (const f of mdFiles) {
    try {
      const text = await f.text();
      const r = parseImportMd(text);
      fileResults.push({ name: f.name, project: r.project, count: r.tasks.length, error: null });
      for (const t of r.tasks) allTasks.push(t);
    } catch (e) {
      fileResults.push({ name: f.name, project: null, count: 0, error: e.message });
    }
  }
  const seen = new Set();
  const unique = [];
  const counters = {};
  for (const { dept, entry } of allTasks) {
    const key = dept + ':' + (entry.title || '').toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    counters[dept] = (counters[dept] || 0) + 1;
    entry.id = 'in' + dept + counters[dept];
    unique.push({ dept, entry });
  }
  const newInbox = {};
  for (const d of IMPORT_DEPTS) newInbox[d] = [];
  for (const { dept, entry } of unique) newInbox[dept].push(entry);
  window.TASK_INBOX = newInbox;
  for (const { dept, entry } of unique) {
    if (ZONES[dept]) {
      if (!ZONES[dept].tasks) ZONES[dept].tasks = [];
      if (!ZONES[dept].tasks.some(t => t.id === entry.id)) ZONES[dept].tasks.push(entry);
    }
  }
  if (typeof refreshDeptBoards === 'function') refreshDeptBoards();
  if (activeZone && ZONES[activeZone]) renderPanel();
  const inboxJs = 'window.TASK_INBOX = ' + JSON.stringify(window.TASK_INBOX, null, 2) + ';\n' +
    'window.TASK_INBOX_META = {"generated":"' + new Date().toISOString() + '","total":' + unique.length + ',"source":"board-export"};\n';
  downloadFile('inbox_tasks.js', inboxJs);
  showImportModal({ title: '📥 导入完成', files: fileResults, total: unique.length, depCounts: counters });
}

// 绑定导入入口：工具栏📥按钮 + 选目录 + 整窗拖拽 .md（无需终端/服务器）
function setupImportFeature(){
  const picker = document.getElementById('import-picker');
  const btn = document.getElementById('btn-import');
  const overlay = document.getElementById('drop-overlay');
  const hasFiles = (e) => {
    const t = e.dataTransfer && e.dataTransfer.types;
    if (!t) return false;
    if (typeof t.includes === 'function') return t.includes('Files');
    for (let i = 0; i < t.length; i++) if (t[i] === 'Files') return true;
    return false;
  };
  if (btn && picker) btn.addEventListener('click', () => picker.click());
  if (picker) picker.addEventListener('change', (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length) handleImportFolder(files);
    e.target.value = '';
  });
  let depth = 0;
  window.addEventListener('dragenter', (e) => { if (!hasFiles(e)) return; e.preventDefault(); depth++; overlay.classList.add('active'); });
  window.addEventListener('dragover', (e) => { if (!hasFiles(e)) return; e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'; });
  window.addEventListener('dragleave', (e) => { if (!hasFiles(e)) return; depth = Math.max(0, depth - 1); if (depth === 0) overlay.classList.remove('active'); });
  window.addEventListener('drop', (e) => {
    if (!hasFiles(e)) return;
    e.preventDefault(); depth = 0; overlay.classList.remove('active');
    const files = Array.from(e.dataTransfer.files || []).filter(f => (f.name || '').toLowerCase().endsWith('.md'));
    if (files.length) handleImportFolder(files);
    else showImportModal({ title: '📥 未找到 .md', body: '拖入的内容里没有 .md 任务清单文件。请拖入 board-export 生成的 .md。' });
  });
}
setupImportFeature();

animate();
window.addEventListener('resize',()=>{camera.aspect=container.clientWidth/container.clientHeight;camera.updateProjectionMatrix();renderer.setSize(container.clientWidth,container.clientHeight);});
console.log('WorkBuddy 3D Office v4 — Perimeter layout with central atrium, deep wall tones, wall plaques');

/* URL 深链：?zone=ceo 直达某房（只缩放、不开面板）；?overview 全景 */
(function(){
  try{
    const p=new URLSearchParams(location.search);
    const z=p.get('zone');
    if(z && ZONES[z]){
      activeZone=z;
      animateToZone(ZONES[z], 0.01);
    }else if(z==='overview'){
      animateToOverview(0.01);
    }
  }catch(e){console.warn('URL zone 解析失败', e);}
})();

/* 调试挂载：将内部关键状态暴露到 window，便于 Playwright/控制台验证 */
window.__boardDebug = {
  ZONES, doorGroups, doorPickables, scene, camera, controls, renderer,
  toggleDoor, openDoor, animateToZone, animateToOverview,
};
