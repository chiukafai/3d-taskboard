/* ============================================================
   办公室立体物品设计方案 · 3D 交互展示
   12 类 × 3 型号 = 36 个 3D 模型
   Three.js r128 · 圆润暖色风格 · 变体切换
   ============================================================ */

/* ============================================================
   物品数据（每类 3 种型号）
   ============================================================ */
var items = [
    { name: '办公桌', category: '工位区', variants: [
        { id: 'desk', name: '标准款', spec: '140×70×75 cm', material: '板式/实木 · 含键盘托' },
        { id: 'desk_v2', name: '转角款', spec: '160×120×75 cm', material: 'L型板式 · 走线孔' },
        { id: 'desk_v3', name: '升降款', spec: '120×60×110 cm', material: '电动升降 · 钢木结构' }
    ]},
    { name: '办公椅', category: '工位区', variants: [
        { id: 'chair', name: '工学款', spec: '60×60×110 cm', material: '网布/尼龙 · 可升降' },
        { id: 'chair_v2', name: '高管款', spec: '70×70×130 cm', material: '皮质 · 高背头枕' },
        { id: 'chair_v3', name: '访客款', spec: '50×50×85 cm', material: '布艺 · 四脚框架' }
    ]},
    { name: '书柜', category: '储物区', variants: [
        { id: 'bookshelf', name: '高柜款', spec: '80×35×180 cm', material: '板式 · 5层可调' },
        { id: 'bookshelf_v2', name: '梯形款', spec: '90×40×170 cm', material: '实木 · 开放式' },
        { id: 'bookshelf_v3', name: '方格款', spec: '120×35×120 cm', material: '板式 · 6格储物' }
    ]},
    { name: '文件柜', category: '储物区', variants: [
        { id: 'cabinet', name: '竖款', spec: '50×60×140 cm', material: '钢制 · 4层带锁' },
        { id: 'cabinet_v2', name: '横款', spec: '90×45×70 cm', material: '钢制 · 3层横向' },
        { id: 'cabinet_v3', name: '移动款', spec: '40×50×60 cm', material: '钢制 · 带轮' }
    ]},
    { name: '会议桌', category: '会议区', variants: [
        { id: 'conference', name: '长方款', spec: '300×120×75 cm', material: '板式 · 6-8人' },
        { id: 'conference_v2', name: '圆桌款', spec: 'Φ150×75 cm', material: '实木 · 4-6人' },
        { id: 'conference_v3', name: '船型款', spec: '280×130×75 cm', material: '板式 · 8人' }
    ]},
    { name: '白板', category: '会议区', variants: [
        { id: 'whiteboard', name: '支架款', spec: '160×100×5 cm', material: '铝合金+钢化玻璃' },
        { id: 'whiteboard_v2', name: '玻璃款', spec: '120×80×1 cm', material: '钢化玻璃 · 无框' },
        { id: 'whiteboard_v3', name: '翻转款', spec: '70×100×5 cm', material: 'ABS+铝合金 · 三脚' }
    ]},
    { name: '打印机', category: '公共区', variants: [
        { id: 'printer', name: '标准款', spec: '45×40×35 cm', material: 'ABS · 多功能' },
        { id: 'printer_v2', name: '紧凑款', spec: '35×30×20 cm', material: 'ABS · 单功能' },
        { id: 'printer_v3', name: '落地款', spec: '60×60×90 cm', material: '金属 · 复合机' }
    ]},
    { name: '绿植', category: '装饰区', variants: [
        { id: 'plant', name: '中型款', spec: 'Φ30×60 cm', material: '陶瓷盆 · 绿萝' },
        { id: 'plant_v2', name: '大型款', spec: 'Φ40×160 cm', material: '树脂盆 · 龟背竹' },
        { id: 'plant_v3', name: '桌面款', spec: 'Φ10×15 cm', material: '陶瓷盆 · 多肉' }
    ]},
    { name: '饮水机', category: '公共区', variants: [
        { id: 'water', name: '上置款', spec: '35×35×100 cm', material: '不锈钢 · 冷热' },
        { id: 'water_v2', name: '下置款', spec: '30×30×110 cm', material: '金属 · 隐藏式' },
        { id: 'water_v3', name: '桌面款', spec: '25×25×40 cm', material: 'ABS · 过滤型' }
    ]},
    { name: '沙发', category: '休息区', variants: [
        { id: 'sofa', name: '三人款', spec: '180×80×80 cm', material: '布艺 · 可拆洗' },
        { id: 'sofa_v2', name: '双人款', spec: '130×80×80 cm', material: '布艺 · 弧形' },
        { id: 'sofa_v3', name: '转角款', spec: '240×160×80 cm', material: '布艺 · L型' }
    ]},
    { name: '茶几', category: '休息区', variants: [
        { id: 'coffee', name: '长方款', spec: '80×50×40 cm', material: '钢化玻璃+金属' },
        { id: 'coffee_v2', name: '圆桌款', spec: 'Φ45×45 cm', material: '实木 · 三脚' },
        { id: 'coffee_v3', name: '柱型款', spec: 'Φ40×45 cm', material: '混凝土+金属' }
    ]},
    { name: '电脑显示器', category: '工位区', variants: [
        { id: 'monitor', name: '27寸款', spec: '60×40×55 cm', material: 'ABS+金属 · 27寸' },
        { id: 'monitor_v2', name: '超宽款', spec: '80×35×60 cm', material: 'ABS+金属 · 34寸' },
        { id: 'monitor_v3', name: '双屏款', spec: '110×35×55 cm', material: 'ABS+金属 · 双24寸' }
    ]}
];

var tableData = [
    {no:1, name:'办公桌', model:'标准款', zone:'工位区', qty:'按人数', spec:'140×70×75', material:'板式/实木', desc:'含键盘托，可调节高度'},
    {no:2, name:'办公桌', model:'转角款', zone:'工位区', qty:'部分', spec:'160×120×75', material:'L型板式', desc:'走线孔，适合管理岗'},
    {no:3, name:'办公桌', model:'升降款', zone:'工位区', qty:'部分', spec:'120×60×110', material:'钢木结构', desc:'电动升降，健康办公'},
    {no:4, name:'办公椅', model:'工学款', zone:'工位区', qty:'按人数', spec:'60×60×110', material:'网布/尼龙', desc:'人体工学，可升降旋转'},
    {no:5, name:'办公椅', model:'高管款', zone:'工位区', qty:'管理层', spec:'70×70×130', material:'皮质', desc:'高背头枕，宽大舒适'},
    {no:6, name:'办公椅', model:'访客款', zone:'工位区', qty:'备用', spec:'50×50×85', material:'布艺', desc:'四脚框架，轻便易移'},
    {no:7, name:'书柜', model:'高柜款', zone:'储物区', qty:'2-4', spec:'80×35×180', material:'板式', desc:'5层可调，承重≥30kg/层'},
    {no:8, name:'书柜', model:'梯形款', zone:'储物区', qty:'1-2', spec:'90×40×170', material:'实木', desc:'开放式梯形，装饰性强'},
    {no:9, name:'书柜', model:'方格款', zone:'储物区', qty:'1-2', spec:'120×35×120', material:'板式', desc:'6格储物，可配收纳盒'},
    {no:10, name:'文件柜', model:'竖款', zone:'储物区', qty:'2-4', spec:'50×60×140', material:'钢制', desc:'4层带锁，抽屉式'},
    {no:11, name:'文件柜', model:'横款', zone:'储物区', qty:'1-2', spec:'90×45×70', material:'钢制', desc:'3层横向，可兼侧柜'},
    {no:12, name:'文件柜', model:'移动款', zone:'工位区', qty:'按需', spec:'40×50×60', material:'钢制', desc:'带轮，灵活移动'},
    {no:13, name:'会议桌', model:'长方款', zone:'会议区', qty:'1', spec:'300×120×75', material:'板式', desc:'6-8人位，可走线'},
    {no:14, name:'会议桌', model:'圆桌款', zone:'会议区', qty:'1', spec:'Φ150×75', material:'实木', desc:'4-6人位，促讨论'},
    {no:15, name:'会议桌', model:'船型款', zone:'会议区', qty:'1', spec:'280×130×75', material:'板式', desc:'8人位，高端商务'},
    {no:16, name:'白板', model:'支架款', zone:'会议区', qty:'1-2', spec:'160×100×5', material:'铝合金+钢化玻璃', desc:'可移动支架式'},
    {no:17, name:'白板', model:'玻璃款', zone:'会议区', qty:'1', spec:'120×80×1', material:'钢化玻璃', desc:'无框浮贴，现代感'},
    {no:18, name:'白板', model:'翻转款', zone:'会议区', qty:'1', spec:'70×100×5', material:'ABS+铝合金', desc:'三脚架，可翻转'},
    {no:19, name:'打印机', model:'标准款', zone:'公共区', qty:'1-2', spec:'45×40×35', material:'ABS', desc:'打印/扫描/复印一体'},
    {no:20, name:'打印机', model:'紧凑款', zone:'工位区', qty:'按需', spec:'35×30×20', material:'ABS', desc:'单功能，省空间'},
    {no:21, name:'打印机', model:'落地款', zone:'公共区', qty:'1', spec:'60×60×90', material:'金属', desc:'大型复合机，高速'},
    {no:22, name:'绿植', model:'中型款', zone:'装饰区', qty:'4-8', spec:'Φ30×60', material:'陶瓷盆', desc:'净化空气，调节湿度'},
    {no:23, name:'绿植', model:'大型款', zone:'装饰区', qty:'1-2', spec:'Φ40×160', material:'树脂盆', desc:'大型落地，空间分隔'},
    {no:24, name:'绿植', model:'桌面款', zone:'工位区', qty:'按需', spec:'Φ10×15', material:'陶瓷盆', desc:'桌面点缀，缓解视疲劳'},
    {no:25, name:'饮水机', model:'上置款', zone:'公共区', qty:'1-2', spec:'35×35×100', material:'不锈钢', desc:'冷热两用，带消毒'},
    {no:26, name:'饮水机', model:'下置款', zone:'公共区', qty:'1', spec:'30×30×110', material:'金属', desc:'隐藏水桶，更美观'},
    {no:27, name:'饮水机', model:'桌面款', zone:'茶水间', qty:'1', spec:'25×25×40', material:'ABS', desc:'过滤型，适合小空间'},
    {no:28, name:'沙发', model:'三人款', zone:'休息区', qty:'1-2', spec:'180×80×80', material:'布艺', desc:'三人位，可拆洗'},
    {no:29, name:'沙发', model:'双人款', zone:'休息区', qty:'1', spec:'130×80×80', material:'布艺', desc:'弧形双人，温馨'},
    {no:30, name:'沙发', model:'转角款', zone:'休息区', qty:'1', spec:'240×160×80', material:'布艺', desc:'L型带贵妃椅'},
    {no:31, name:'茶几', model:'长方款', zone:'休息区', qty:'1', spec:'80×50×40', material:'钢化玻璃+金属', desc:'钢化玻璃面，圆角'},
    {no:32, name:'茶几', model:'圆桌款', zone:'休息区', qty:'1-2', spec:'Φ45×45', material:'实木', desc:'三脚圆桌，灵活'},
    {no:33, name:'茶几', model:'柱型款', zone:'休息区', qty:'1', spec:'Φ40×45', material:'混凝土+金属', desc:'柱式圆筒，工业风'},
    {no:34, name:'显示器', model:'27寸款', zone:'工位区', qty:'按人数', spec:'60×40×55', material:'ABS+金属', desc:'27寸，可升降旋转'},
    {no:35, name:'显示器', model:'超宽款', zone:'工位区', qty:'部分', spec:'80×35×60', material:'ABS+金属', desc:'34寸带鱼屏，臂挂'},
    {no:36, name:'显示器', model:'双屏款', zone:'工位区', qty:'部分', spec:'110×35×55', material:'ABS+金属', desc:'双24寸，双臂支架'}
];

var templateData = [
    { zone: '前台接待区', item: '接待台', qty: 1, price: '3,500', note: '含logo标识' },
    { zone: '前台接待区', item: '等候沙发(双人款)', qty: 1, price: '2,800', note: '弧形双人位' },
    { zone: '前台接待区', item: '绿植(大型款)', qty: 2, price: '500', note: '大型落地盆栽' },
    { zone: '开放工位区', item: '办公桌(标准款)', qty: 20, price: '1,200', note: '工位标配' },
    { zone: '开放工位区', item: '办公椅(工学款)', qty: 20, price: '800', note: '人体工学' },
    { zone: '开放工位区', item: '显示器(27寸款)', qty: 20, price: '1,500', note: '27寸' },
    { zone: '开放工位区', item: '文件柜(移动款)', qty: 4, price: '700', note: '带轮侧柜' },
    { zone: '会议室', item: '会议桌(长方款)', qty: 1, price: '6,000', note: '8人位' },
    { zone: '会议室', item: '会议椅(访客款)', qty: 8, price: '350', note: '—' },
    { zone: '会议室', item: '白板(支架款)', qty: 1, price: '800', note: '可移动' },
    { zone: '休息区', item: '沙发(三人款)', qty: 1, price: '3,200', note: '三人位' },
    { zone: '休息区', item: '茶几(长方款)', qty: 1, price: '600', note: '钢化玻璃' },
    { zone: '储物/打印区', item: '文件柜(竖款)', qty: 2, price: '900', note: '带锁' },
    { zone: '储物/打印区', item: '书柜(高柜款)', qty: 2, price: '1,100', note: '可调层板' },
    { zone: '储物/打印区', item: '打印机(标准款)', qty: 1, price: '2,500', note: '多功能一体' },
    { zone: '茶水间', item: '饮水机(下置款)', qty: 1, price: '1,500', note: '隐藏式' }
];

/* ============================================================
   暖色调色板
   ============================================================ */
var C = {
    wood:0xD4A574, woodLight:0xE8C39E, woodDark:0xB8823C, woodDeep:0x8B6239,
    blue:0x4A90D9, teal:0x2DB8B8, coral:0xE8746C, yellow:0xFFC857,
    pink:0xF4A4B0, lavender:0xB19CD9,
    cream:0xFFF8DC, warmWhite:0xF5F0E6, warmGrey:0xB8AFA6,
    greyBlue:0x7B96A8, metal:0xA8A0A0, darkMetal:0x616161,
    leaf:0x4CAF50, leafDark:0x388E3C, terracotta:0xCC6633,
    water:0x5BB8D9, soil:0x5D4037, screen:0x1A2333
};

/* ============================================================
   材质 & 圆角几何辅助
   ============================================================ */
function mat(color, opts) {
    opts = opts || {};
    return new THREE.MeshPhongMaterial({
        color: color,
        shininess: opts.shininess != null ? opts.shininess : 35,
        specular: opts.specular || 0x444444,
        transparent: opts.transparent || false,
        opacity: opts.opacity != null ? opts.opacity : 1.0
    });
}

function rbox(width, height, depth, radius) {
    radius = Math.min(radius || 0.02, width / 3, height / 3, depth / 3);
    if (radius < 0.005) radius = 0.005;
    var w = width / 2, h = height / 2;
    var shape = new THREE.Shape();
    shape.moveTo(-w + radius, -h);
    shape.lineTo(w - radius, -h);
    shape.quadraticCurveTo(w, -h, w, -h + radius);
    shape.lineTo(w, h - radius);
    shape.quadraticCurveTo(w, h, w - radius, h);
    shape.lineTo(-w + radius, h);
    shape.quadraticCurveTo(-w, h, -w, h - radius);
    shape.lineTo(-w, -h + radius);
    shape.quadraticCurveTo(-w, -h, -w + radius, -h);
    var geo = new THREE.ExtrudeGeometry(shape, {
        depth: Math.max(depth - 2 * radius, 0.001),
        bevelEnabled: true, bevelThickness: radius, bevelSize: radius,
        bevelSegments: 3, curveSegments: 8
    });
    geo.center();
    return geo;
}

function rbMesh(w, h, d, r, material) {
    return new THREE.Mesh(rbox(w, h, d, r), material);
}

/* ============================================================
   3D 模型工厂 — 原始 12 款
   ============================================================ */

// --- 1. 办公桌 标准款 ---
function createDesk() {
    var g = new THREE.Group();
    var wood = mat(C.wood), woodDark = mat(C.woodDark), metal = mat(C.metal, {shininess:60});
    var top = rbMesh(2.0, 0.08, 1.0, 0.04, wood); top.position.y = 0.75; g.add(top);
    var legGeo = rbox(0.08, 0.75, 0.08, 0.03);
    [[-0.9,-0.42],[0.9,-0.42],[-0.9,0.42],[0.9,0.42]].forEach(function(p){
        var l = new THREE.Mesh(legGeo, woodDark); l.position.set(p[0],0.375,p[1]); g.add(l);
    });
    var drawer = rbMesh(0.45,0.32,0.9,0.03,mat(C.woodDeep)); drawer.position.set(0.7,0.55,0); g.add(drawer);
    [0.62,0.48].forEach(function(y){
        var h = new THREE.Mesh(new THREE.SphereGeometry(0.025,12,10),metal); h.position.set(0.95,y,0); h.scale.z=0.4; g.add(h);
    });
    return g;
}

// --- 1b. 办公桌 转角款 (L型) ---
function createDeskV2() {
    var g = new THREE.Group();
    var wood = mat(C.woodLight), metal = mat(C.metal,{shininess:60});
    // 主桌面
    var top1 = rbMesh(1.6,0.08,0.8,0.04,wood); top1.position.set(0,0.75,-0.1); g.add(top1);
    // 侧延桌面
    var top2 = rbMesh(0.8,0.08,0.6,0.04,wood); top2.position.set(0.8,0.75,0.5); g.add(top2);
    // 走线孔
    var hole = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.04,0.02,16),mat(C.darkMetal)); hole.position.set(0.3,0.79,-0.1); g.add(hole);
    // 5条腿 + 金属脚
    [[-0.7,-0.4],[0.7,-0.4],[-0.7,0.4],[1.1,0.4],[1.1,0.7]].forEach(function(p){
        var l = rbMesh(0.06,0.75,0.06,0.02,mat(C.woodDark)); l.position.set(p[0],0.375,p[1]); g.add(l);
        var f = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.05,0.02,12),metal); f.position.set(p[0],0.01,p[1]); g.add(f);
    });
    return g;
}

// --- 1c. 办公桌 升降款 ---
function createDeskV3() {
    var g = new THREE.Group();
    var topMat = mat(C.woodDark), frameMat = mat(C.darkMetal,{shininess:50});
    // 桌面（更高）
    var top = rbMesh(1.2,0.06,0.6,0.03,topMat); top.position.y = 1.0; g.add(top);
    // 控制面板
    var panel = rbMesh(0.15,0.03,0.06,0.01,mat(C.darkMetal,{shininess:60})); panel.position.set(0.4,1.04,0); g.add(panel);
    var btn = new THREE.Mesh(new THREE.SphereGeometry(0.01,8,6),mat(C.coral,{shininess:60})); btn.position.set(0.4,1.06,0); g.add(btn);
    // 4立柱 + 横梁
    [[-0.5,-0.25],[0.5,-0.25],[-0.5,0.25],[0.5,0.25]].forEach(function(p){
        var post = new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.03,1.0,16),frameMat); post.position.set(p[0],0.5,p[1]); g.add(post);
    });
    // 横梁
    var bar = rbMesh(1.0,0.04,0.04,0.02,frameMat); bar.position.set(0,0.2,0); g.add(bar);
    // 脚垫
    [[-0.5,-0.25],[0.5,-0.25],[-0.5,0.25],[0.5,0.25]].forEach(function(p){
        var foot = rbMesh(0.1,0.03,0.15,0.02,frameMat); foot.position.set(p[0],0.015,p[1]); g.add(foot);
    });
    return g;
}

// --- 2. 办公椅 工学款 ---
function createChair() {
    var g = new THREE.Group();
    var s = mat(C.blue,{shininess:25}), f = mat(C.darkMetal,{shininess:60}), w = mat(C.darkMetal,{shininess:80});
    var seat = rbMesh(0.5,0.08,0.5,0.04,s); seat.position.y=0.45; g.add(seat);
    var back = rbMesh(0.48,0.55,0.06,0.04,s); back.position.set(0,0.75,-0.22); g.add(back);
    var armGeo = rbox(0.06,0.04,0.42,0.02);
    [-0.28,0.28].forEach(function(x){
        var a = new THREE.Mesh(armGeo,mat(C.darkMetal)); a.position.set(x,0.55,0); g.add(a);
        var sup = rbMesh(0.06,0.12,0.06,0.02,mat(C.darkMetal)); sup.position.set(x,0.49,0.18); g.add(sup);
    });
    var post = new THREE.Mesh(new THREE.CylinderGeometry(0.035,0.04,0.35,16),f); post.position.y=0.24; g.add(post);
    for(var i=0;i<5;i++){
        var ang=(i/5)*Math.PI*2;
        var arm=rbMesh(0.3,0.03,0.05,0.015,mat(C.darkMetal)); arm.position.set(Math.cos(ang)*0.16,0.05,Math.sin(ang)*0.16); arm.rotation.y=-ang; g.add(arm);
        var wheel=new THREE.Mesh(new THREE.SphereGeometry(0.04,12,10),w); wheel.position.set(Math.cos(ang)*0.29,0.04,Math.sin(ang)*0.29); wheel.scale.y=0.6; g.add(wheel);
    }
    return g;
}

// --- 2b. 办公椅 高管款 ---
function createChairV2() {
    var g = new THREE.Group();
    var leather = mat(C.woodDeep,{shininess:20}), dark = mat(C.darkMetal,{shininess:50}), w = mat(C.darkMetal,{shininess:80});
    // 宽座垫
    var seat = rbMesh(0.6,0.12,0.55,0.05,leather); seat.position.y=0.45; g.add(seat);
    // 高背 + 头枕
    var back = rbMesh(0.58,0.7,0.08,0.05,leather); back.position.set(0,0.85,-0.22); g.add(back);
    var headrest = rbMesh(0.4,0.15,0.08,0.06,leather); headrest.position.set(0,1.25,-0.22); g.add(headrest);
    // 宽扶手
    [-0.33,0.33].forEach(function(x){
        var arm = rbMesh(0.08,0.06,0.45,0.03,leather); arm.position.set(x,0.56,0); g.add(arm);
        var sup = rbMesh(0.06,0.12,0.06,0.02,dark); sup.position.set(x,0.5,0.2); g.add(sup);
    });
    // 4星脚
    var post = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.05,0.35,16),dark); post.position.y=0.24; g.add(post);
    for(var i=0;i<4;i++){
        var ang=(i/4)*Math.PI*2;
        var arm=rbMesh(0.35,0.03,0.06,0.02,dark); arm.position.set(Math.cos(ang)*0.18,0.05,Math.sin(ang)*0.18); arm.rotation.y=-ang; g.add(arm);
        var wheel=new THREE.Mesh(new THREE.SphereGeometry(0.045,12,10),w); wheel.position.set(Math.cos(ang)*0.33,0.045,Math.sin(ang)*0.33); wheel.scale.y=0.6; g.add(wheel);
    }
    return g;
}

// --- 2c. 办公椅 访客款 ---
function createChairV3() {
    var g = new THREE.Group();
    var fabric = mat(C.teal,{shininess:15}), frame = mat(C.metal,{shininess:40});
    // 座垫
    var seat = rbMesh(0.45,0.06,0.42,0.04,fabric); seat.position.y=0.42; g.add(seat);
    // 矮背
    var back = rbMesh(0.45,0.35,0.05,0.04,fabric); back.position.set(0,0.6,-0.18); g.add(back);
    // 4 sled legs (管架)
    [[-0.2,-0.18],[0.2,-0.18]].forEach(function(p){
        var leg = new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.42,12),frame); leg.position.set(p[0],0.21,p[1]); g.add(leg);
        var foot = new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.02,0.02,12),frame); foot.rotation.x=Math.PI/2; foot.position.set(p[0],0.01,p[1]+0.15); foot.scale.x=1.5; g.add(foot);
    });
    // 背后两腿
    [[-0.2,0.18],[0.2,0.18]].forEach(function(p){
        var leg = new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.6,12),frame); leg.position.set(p[0],0.3,p[1]); g.add(leg);
    });
    return g;
}

// --- 3. 书柜 高柜款 ---
function createBookshelf() {
    var g = new THREE.Group();
    var wood = mat(C.wood), woodDark = mat(C.woodDeep);
    var bks = [C.blue,C.coral,C.leaf,C.yellow,C.lavender,C.teal];
    var sideGeo = rbox(0.04,1.8,0.35,0.02);
    [-0.45,0.45].forEach(function(x){var s=new THREE.Mesh(sideGeo,wood);s.position.set(x,0.9,0);g.add(s);});
    var shelfGeo=rbox(0.86,0.04,0.35,0.015);
    [0.15,0.6,1.05,1.5,1.78].forEach(function(y){var s=new THREE.Mesh(shelfGeo,wood);s.position.set(0,y,0);g.add(s);});
    var bp=rbMesh(0.9,1.76,0.02,0.01,woodDark);bp.position.set(0,0.9,-0.17);g.add(bp);
    [0.32,0.78,1.24].forEach(function(y,si){
        for(var i=0;i<6;i++){var bw=0.06+Math.random()*0.04,bh=0.18+Math.random()*0.08;
        var b=rbMesh(bw,bh,0.22,0.02,mat(bks[(i+si)%bks.length]));b.position.set(-0.35+i*0.11,y,0);g.add(b);}
    });
    return g;
}

// --- 3b. 书柜 梯形款 ---
function createBookshelfV2() {
    var g = new THREE.Group();
    var wood = mat(C.woodLight);
    // 4层渐窄隔板
    var shelves = [
        {w:0.9, y:0.1, d:0.35}, {w:0.78, y:0.55, d:0.3},
        {w:0.66, y:1.0, d:0.25}, {w:0.54, y:1.45, d:0.2}
    ];
    shelves.forEach(function(s){
        var shelf = rbMesh(s.w, 0.04, s.d, 0.02, wood);
        shelf.position.set(0, s.y, 0);
        g.add(shelf);
    });
    // 两侧斜杆
    [-1,1].forEach(function(side){
        var pole = new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.025,1.65,12),wood);
        pole.position.set(side*0.42, 0.82, 0);
        pole.rotation.z = side * 0.12;
        g.add(pole);
    });
    // 顶部连接
    var top = rbMesh(0.5,0.04,0.2,0.02,wood); top.position.set(0,1.65,0); g.add(top);
    // 装饰书
    shelves.forEach(function(s,si){
        var cnt = 4 - si;
        for(var i=0;i<cnt;i++){
            var bw=0.05+Math.random()*0.03, bh=0.15+Math.random()*0.05;
            var b = rbMesh(bw,bh,s.d*0.6,0.015,mat([C.coral,C.teal,C.yellow,C.lavender,C.blue][(i+si)%5]));
            b.position.set(-s.w/2+0.08+i*0.1, s.y+0.02, 0);
            g.add(b);
        }
    });
    return g;
}

// --- 3c. 书柜 方格款 ---
function createBookshelfV3() {
    var g = new THREE.Group();
    var wood = mat(C.woodDark);
    // 外框
    var frame = rbMesh(1.2,1.2,0.35,0.03,wood); frame.position.set(0,0.6,0); g.add(frame);
    // 横隔板
    [0.2,0.6,1.0].forEach(function(y){var s=rbMesh(1.15,0.03,0.34,0.015,wood);s.position.set(0,y,0);g.add(s);});
    // 竖隔板
    [-0.3,0.3].forEach(function(x){[0.4,0.8].forEach(function(y){var s=rbMesh(0.03,0.38,0.34,0.015,wood);s.position.set(x,y,0);g.add(s);});});
    // 彩色收纳盒
    var bins = [
        {x:-0.3, y:0.4, c:C.coral}, {x:0.3, y:0.4, c:C.yellow},
        {x:-0.3, y:0.8, c:C.teal}, {x:0.3, y:1.0, c:C.lavender}
    ];
    bins.forEach(function(b){
        var bin = rbMesh(0.38,0.3,0.3,0.04,mat(b.c,{shininess:20}));
        bin.position.set(b.x, b.y, 0.02);
        g.add(bin);
    });
    return g;
}

// --- 4. 文件柜 竖款 ---
function createCabinet() {
    var g = new THREE.Group();
    var body = mat(C.greyBlue), drw = mat(0x9BB0C0), hd = mat(C.darkMetal,{shininess:60});
    var shell = rbMesh(0.5,1.4,0.6,0.04,body); shell.position.y=0.7; g.add(shell);
    for(var i=0;i<4;i++){
        var y=0.18+i*0.33;
        var front=rbMesh(0.42,0.28,0.02,0.015,drw); front.position.set(0,y,0.31); g.add(front);
        var h=new THREE.Mesh(new THREE.SphereGeometry(0.02,12,10),hd); h.position.set(0.12,y,0.34); h.scale.x=2.5; g.add(h);
    }
    return g;
}

// --- 4b. 文件柜 横款 ---
function createCabinetV2() {
    var g = new THREE.Group();
    var body = mat(C.warmWhite,{shininess:30}), drw = mat(0xE8E0D4), hd = mat(C.darkMetal,{shininess:60});
    var shell = rbMesh(0.9,0.7,0.45,0.04,body); shell.position.y=0.35; g.add(shell);
    // 3横向抽屉
    for(var i=0;i<3;i++){
        var x=-0.28+i*0.28;
        var front=rbMesh(0.24,0.5,0.02,0.015,drw); front.position.set(x,0.35,0.235); g.add(front);
        var knob=new THREE.Mesh(new THREE.SphereGeometry(0.025,12,10),hd); knob.position.set(x,0.35,0.26); g.add(knob);
    }
    // 底座
    var base = rbMesh(0.85,0.04,0.4,0.02,mat(C.warmGrey)); base.position.set(0,0.02,0); g.add(base);
    return g;
}

// --- 4c. 文件柜 移动款 ---
function createCabinetV3() {
    var g = new THREE.Group();
    var body = mat(C.teal,{shininess:25}), drw = mat(0x5BCFCF), hd = mat(C.darkMetal,{shininess:60}), wh = mat(C.darkMetal,{shininess:80});
    var shell = rbMesh(0.4,0.55,0.5,0.04,body); shell.position.y=0.35; g.add(shell);
    // 2抽屉
    [0.42,0.25].forEach(function(y){
        var front=rbMesh(0.32,0.12,0.02,0.015,drw); front.position.set(0,y,0.255); g.add(front);
        var h=new THREE.Mesh(new THREE.SphereGeometry(0.02,12,10),hd); h.position.set(0.08,y,0.28); h.scale.x=2; g.add(h);
    });
    // 4轮
    [[-0.15,-0.18],[0.15,-0.18],[-0.15,0.18],[0.15,0.18]].forEach(function(p){
        var wheel=new THREE.Mesh(new THREE.SphereGeometry(0.035,12,10),wh); wheel.position.set(p[0],0.035,p[1]); wheel.scale.y=0.6; g.add(wheel);
    });
    return g;
}

// --- 5. 会议桌 长方款 ---
function createConference() {
    var g = new THREE.Group();
    var wood = mat(C.wood), woodDark = mat(C.woodDark);
    var top = rbMesh(3.0,0.08,1.2,0.05,wood); top.position.y=0.75; g.add(top);
    var legGeo = rbox(0.12,0.71,0.9,0.04);
    [-1.2,1.2].forEach(function(x){var l=new THREE.Mesh(legGeo,woodDark);l.position.set(x,0.355,0);g.add(l);});
    var modesty=rbMesh(2.6,0.3,0.04,0.02,woodDark); modesty.position.set(0,0.45,0); g.add(modesty);
    return g;
}

// --- 5b. 会议桌 圆桌款 ---
function createConferenceV2() {
    var g = new THREE.Group();
    var wood = mat(C.woodDark), woodDeep = mat(C.woodDeep);
    var top = new THREE.Mesh(new THREE.CylinderGeometry(0.75,0.75,0.06,32),wood); top.position.y=0.75; g.add(top);
    // 边缘圆角效果
    var rim = new THREE.Mesh(new THREE.TorusGeometry(0.75,0.03,8,32),mat(C.woodDeep)); rim.position.y=0.75; rim.rotation.x=Math.PI/2; g.add(rim);
    // 独柱底座
    var post = new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.1,0.65,16),woodDeep); post.position.y=0.4; g.add(post);
    var base = new THREE.Mesh(new THREE.CylinderGeometry(0.35,0.4,0.04,24),woodDeep); base.position.y=0.1; g.add(base);
    var footRing = new THREE.Mesh(new THREE.TorusGeometry(0.37,0.02,8,24),mat(C.darkMetal,{shininess:50})); footRing.position.y=0.08; footRing.rotation.x=Math.PI/2; g.add(footRing);
    return g;
}

// --- 5c. 会议桌 船型款 ---
function createConferenceV3() {
    var g = new THREE.Group();
    var wood = mat(C.woodLight), woodDark = mat(C.woodDark);
    // 船型桌面：中间宽两端窄 — 用缩放的椭圆
    var top = new THREE.Mesh(new THREE.CylinderGeometry(0.65,0.65,0.06,4,1),wood); 
    top.scale.set(2.2,1,1.0); top.rotation.y=Math.PI/4; top.position.y=0.75; g.add(top);
    // 用 ExtrudeGeometry 做船型太复杂，用 4 个 box 拼接近似船型
    // 替换为圆角宽板
    g.remove(top);
    var top2 = rbMesh(2.8,0.07,1.0,0.2,wood); top2.position.y=0.75; g.add(top2);
    // 两端弧形扩展
    var end1 = rbMesh(0.5,0.07,1.3,0.08,wood); end1.position.set(-1.15,0.75,0); g.add(end1);
    var end2 = rbMesh(0.5,0.07,1.3,0.08,wood); end2.position.set(1.15,0.75,0); g.add(end2);
    // A字支架
    [-1.0,1.0].forEach(function(x){
        var legL = rbMesh(0.08,0.7,0.08,0.03,woodDark); legL.position.set(x-0.1,0.36,0); legL.rotation.z=0.15; g.add(legL);
        var legR = rbMesh(0.08,0.7,0.08,0.03,woodDark); legR.position.set(x+0.1,0.36,0); legR.rotation.z=-0.15; g.add(legR);
        var cross = rbMesh(0.25,0.04,0.08,0.02,woodDark); cross.position.set(x,0.15,0); g.add(cross);
    });
    return g;
}

// --- 6. 白板 支架款 ---
function createWhiteboard() {
    var g = new THREE.Group();
    var board = mat(C.cream,{shininess:50}), frame = mat(C.metal,{shininess:60}), stand = mat(C.darkMetal,{shininess:50});
    var panel = rbMesh(1.6,1.0,0.04,0.02,board); panel.position.y=1.1; g.add(panel);
    var edges = [
        {w:1.64,h:0.03,d:0.03,pos:[0,1.6,0]},{w:1.64,h:0.03,d:0.03,pos:[0,0.6,0]},
        {w:0.03,h:1.0,d:0.03,pos:[-0.8,1.1,0]},{w:0.03,h:1.0,d:0.03,pos:[0.8,1.1,0]}
    ];
    edges.forEach(function(e){var m=rbMesh(e.w,e.h,e.d,0.015,frame);m.position.set(e.pos[0],e.pos[1],e.pos[2]);g.add(m);});
    var tray=rbMesh(1.4,0.04,0.06,0.02,frame); tray.position.set(0,0.62,0.04); g.add(tray);
    [-0.5,0.5].forEach(function(x){
        var pole=new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.025,1.1,16),stand); pole.position.set(x,0.55,0.15); g.add(pole);
        var base=rbMesh(0.2,0.04,0.3,0.02,stand); base.position.set(x,0.02,0.15); g.add(base);
    });
    return g;
}

// --- 6b. 白板 玻璃款 ---
function createWhiteboardV2() {
    var g = new THREE.Group();
    var glass = mat(C.teal,{transparent:true,opacity:0.35,shininess:100,specular:0x888888});
    var pole = mat(C.metal,{shininess:60});
    // 无框玻璃板
    var panel = rbMesh(1.2,0.8,0.015,0.008,glass); panel.position.y=1.0; g.add(panel);
    // 细杆支架
    [-0.55,0.55].forEach(function(x){
        var p=new THREE.Mesh(new THREE.CylinderGeometry(0.015,0.015,1.1,16),pole); p.position.set(x,0.55,0.1); g.add(p);
        var b=new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.1,0.02,16),pole); b.position.set(x,0.02,0.1); b.rotation.x=Math.PI/2; g.add(b);
    });
    // 笔托
    var tray=rbMesh(0.8,0.02,0.03,0.01,pole); tray.position.set(0,0.55,0.12); g.add(tray);
    return g;
}

// --- 6c. 白板 翻转款 ---
function createWhiteboardV3() {
    var g = new THREE.Group();
    var board = mat(C.cream,{shininess:40}), frame = mat(C.yellow,{shininess:30}), dark = mat(C.darkMetal,{shininess:50});
    // 倾斜板
    var panel = rbMesh(0.7,1.0,0.03,0.02,board); panel.position.set(0,1.0,-0.1); panel.rotation.x=-0.15; g.add(panel);
    // 黄色边框
    var edges = [
        {w:0.74,h:0.03,d:0.03,pos:[0,1.5,-0.15],rot:-0.15},{w:0.74,h:0.03,d:0.03,pos:[0,0.5,-0.01],rot:-0.15},
        {w:0.03,h:1.0,d:0.03,pos:[-0.35,1.0,-0.07],rot:-0.15},{w:0.03,h:1.0,d:0.03,pos:[0.35,1.0,-0.07],rot:-0.15}
    ];
    edges.forEach(function(e){
        var m=rbMesh(e.w,e.h,e.d,0.015,frame);
        m.position.set(e.pos[0],e.pos[1],e.pos[2]); m.rotation.x=e.rot; g.add(m);
    });
    // 三脚架
    var legs = [
        {x:0, z:0.25, rot:0},
        {x:-0.2, z:-0.15, rot:0.3},
        {x:0.2, z:-0.15, rot:-0.3}
    ];
    legs.forEach(function(l){
        var leg = new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.015,1.1,12),dark);
        leg.position.set(l.x, 0.55, l.z);
        leg.rotation.z = l.rot;
        g.add(leg);
    });
    // 顶部夹子
    var clip = rbMesh(0.15,0.04,0.04,0.02,dark); clip.position.set(0,1.45,-0.13); clip.rotation.x=-0.15; g.add(clip);
    return g;
}

// --- 7. 打印机 标准款 ---
function createPrinter() {
    var g = new THREE.Group();
    var body=mat(C.greyBlue,{shininess:30}), tray=mat(0x9BB0C0), scr=mat(C.screen,{shininess:80,specular:0x666666});
    var main=rbMesh(0.5,0.25,0.4,0.06,body); main.position.y=0.2; g.add(main);
    var scanner=rbMesh(0.48,0.04,0.36,0.04,body); scanner.position.set(0,0.345,0); g.add(scanner);
    var output=rbMesh(0.4,0.02,0.12,0.015,tray); output.position.set(0,0.08,0.22); g.add(output);
    var panel=rbMesh(0.12,0.06,0.02,0.01,scr); panel.position.set(0.15,0.28,0.21); g.add(panel);
    var paper=rbMesh(0.25,0.005,0.15,0.01,mat(C.warmWhite)); paper.position.set(0,0.095,0.22); g.add(paper);
    var btn=new THREE.Mesh(new THREE.SphereGeometry(0.012,12,10),mat(C.coral,{shininess:60})); btn.position.set(-0.15,0.28,0.21); g.add(btn);
    return g;
}

// --- 7b. 打印机 紧凑款 ---
function createPrinterV2() {
    var g = new THREE.Group();
    var body = mat(C.coral,{shininess:30}), dark = mat(C.darkMetal,{shininess:50});
    // 小巧圆角机身
    var main = rbMesh(0.35,0.16,0.28,0.06,body); main.position.y=0.1; g.add(main);
    // 顶部出纸
    var top = rbMesh(0.32,0.02,0.2,0.04,body); top.position.set(0,0.19,0); g.add(top);
    // 前面板
    var front = rbMesh(0.3,0.08,0.01,0.01,dark); front.position.set(0,0.08,0.145); g.add(front);
    // 按钮
    var btn = new THREE.Mesh(new THREE.SphereGeometry(0.01,8,6),mat(C.leaf,{shininess:60})); btn.position.set(0.08,0.12,0.15); g.add(btn);
    // 纸槽
    var slot = rbMesh(0.2,0.01,0.08,0.01,dark); slot.position.set(0,0.04,0.12); g.add(slot);
    return g;
}

// --- 7c. 打印机 落地款 ---
function createPrinterV3() {
    var g = new THREE.Group();
    var body = mat(C.darkMetal,{shininess:30}), tray = mat(0x757575), scr = mat(C.screen,{shininess:80,specular:0x666666});
    // 高大机身
    var main = rbMesh(0.6,0.7,0.55,0.06,body); main.position.y=0.5; g.add(main);
    // 顶部供纸塔
    var tower = rbMesh(0.5,0.25,0.4,0.04,body); tower.position.set(0,0.98,0); g.add(tower);
    var paperStack = rbMesh(0.4,0.15,0.3,0.02,mat(C.warmWhite)); paperStack.position.set(0,0.98,0.02); g.add(paperStack);
    // 操作屏
    var screen = rbMesh(0.2,0.12,0.01,0.01,scr); screen.position.set(0,0.65,0.28); g.add(screen);
    // 底部出纸托盘
    var output = rbMesh(0.5,0.03,0.2,0.02,tray); output.position.set(0,0.18,0.25); g.add(output);
    // 底座
    var base = rbMesh(0.65,0.05,0.6,0.03,body); base.position.y=0.05; g.add(base);
    return g;
}

// --- 8. 绿植 中型款 ---
function createPlant() {
    var g = new THREE.Group();
    var potM=mat(C.terracotta,{shininess:20}), soilM=mat(C.soil), leafM=mat(C.leaf,{shininess:15}), leafD=mat(C.leafDark,{shininess:15}), trunkM=mat(C.woodDark);
    var pot=new THREE.Mesh(new THREE.CylinderGeometry(0.17,0.14,0.24,24),potM); pot.position.y=0.12; g.add(pot);
    var rim=new THREE.Mesh(new THREE.CylinderGeometry(0.175,0.175,0.03,24),potM); rim.position.y=0.23; g.add(rim);
    var soil=new THREE.Mesh(new THREE.CylinderGeometry(0.16,0.16,0.015,16),soilM); soil.position.y=0.23; g.add(soil);
    var trunk=new THREE.Mesh(new THREE.CylinderGeometry(0.022,0.028,0.22,8),trunkM); trunk.position.y=0.34; g.add(trunk);
    var ld=[{r:0.12,y:0.48,s:0.09,m:leafM},{r:0.10,y:0.55,s:0.08,m:leafM},{r:0.08,y:0.61,s:0.07,m:leafD},{r:0.14,y:0.45,s:0.08,m:leafD},{r:0.11,y:0.52,s:0.07,m:leafM}];
    ld.forEach(function(p,i){var a=(i/ld.length)*Math.PI*2;var s=new THREE.Mesh(new THREE.SphereGeometry(p.s,12,10),p.m);s.position.set(Math.cos(a)*p.r,p.y,Math.sin(a)*p.r);g.add(s);});
    var top=new THREE.Mesh(new THREE.SphereGeometry(0.085,12,10),leafM); top.position.y=0.65; g.add(top);
    return g;
}

// --- 8b. 绿植 大型款 ---
function createPlantV2() {
    var g = new THREE.Group();
    var potM=mat(C.warmWhite,{shininess:25}), leafM=mat(C.leaf,{shininess:15}), leafD=mat(C.leafDark,{shininess:15}), trunkM=mat(C.woodDark);
    // 大花盆
    var pot=new THREE.Mesh(new THREE.CylinderGeometry(0.22,0.18,0.35,24),potM); pot.position.y=0.175; g.add(pot);
    var rim=new THREE.Mesh(new THREE.CylinderGeometry(0.23,0.23,0.04,24),potM); rim.position.y=0.34; g.add(rim);
    var soil=new THREE.Mesh(new THREE.CylinderGeometry(0.21,0.21,0.02,16),mat(C.soil)); soil.position.y=0.34; g.add(soil);
    // 高树干
    var trunk=new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.045,1.0,12),trunkM); trunk.position.y=0.85; g.add(trunk);
    // 多层叶丛
    var layers=[
        {y:0.9, r:0.18, s:0.12, m:leafD, cnt:5},
        {y:1.1, r:0.22, s:0.14, m:leafM, cnt:6},
        {y:1.3, r:0.18, s:0.11, m:leafD, cnt:5},
        {y:1.45, r:0.12, s:0.09, m:leafM, cnt:4}
    ];
    layers.forEach(function(l){
        for(var i=0;i<l.cnt;i++){
            var a=(i/l.cnt)*Math.PI*2;
            var s=new THREE.Mesh(new THREE.SphereGeometry(l.s,12,10),l.m);
            s.position.set(Math.cos(a)*l.r, l.y, Math.sin(a)*l.r);
            s.scale.set(1,0.7,1);
            g.add(s);
        }
    });
    var top=new THREE.Mesh(new THREE.SphereGeometry(0.1,12,10),leafM); top.position.y=1.5; g.add(top);
    return g;
}

// --- 8c. 绿植 桌面款 ---
function createPlantV3() {
    var g = new THREE.Group();
    var potM=mat(C.lavender,{shininess:30}), leafM=mat(C.leaf,{shininess:20}), leafD=mat(C.leafDark,{shininess:20});
    // 小花盆
    var pot=new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.06,0.07,16),potM); pot.position.y=0.035; g.add(pot);
    var rim=new THREE.Mesh(new THREE.CylinderGeometry(0.082,0.082,0.01,16),potM); rim.position.y=0.07; g.add(rim);
    var soil=new THREE.Mesh(new THREE.CylinderGeometry(0.075,0.075,0.008,12),mat(C.soil)); soil.position.y=0.07; g.add(soil);
    // 多肉莲座
    var leaves=[
        {a:0, r:0.03, s:0.025},
        {a:1.26, r:0.03, s:0.025},
        {a:2.51, r:0.03, s:0.025},
        {a:3.77, r:0.03, s:0.025},
        {a:5.03, r:0.03, s:0.025},
        {a:0.63, r:0.018, s:0.02},
        {a:1.89, r:0.018, s:0.02},
        {a:3.14, r:0.018, s:0.02},
        {a:4.4, r:0.018, s:0.02}
    ];
    leaves.forEach(function(l){
        var leaf = new THREE.Mesh(new THREE.SphereGeometry(l.s,8,6), l.r>0.02?leafM:leafD);
        leaf.position.set(Math.cos(l.a)*l.r, 0.085, Math.sin(l.a)*l.r);
        leaf.scale.set(1,0.5,1);
        g.add(leaf);
    });
    var center=new THREE.Mesh(new THREE.SphereGeometry(0.015,8,6),leafD); center.position.y=0.09; g.add(center);
    return g;
}

// --- 9. 饮水机 上置款 ---
function createWater() {
    var g = new THREE.Group();
    var body=mat(C.warmWhite,{shininess:30}), dark=mat(C.darkMetal,{shininess:50});
    var water=mat(C.water,{transparent:true,opacity:0.55,shininess:60});
    var tap=mat(C.metal,{shininess:60}), bDot=mat(C.blue,{shininess:60}), rDot=mat(C.coral,{shininess:60});
    var main=rbMesh(0.3,0.7,0.3,0.05,body); main.position.y=0.45; g.add(main);
    var top=rbMesh(0.28,0.15,0.28,0.04,body); top.position.y=0.87; g.add(top);
    var jug=new THREE.Mesh(new THREE.CylinderGeometry(0.11,0.09,0.22,24),water); jug.position.y=1.02; jug.rotation.x=Math.PI; g.add(jug);
    var sL=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.07,12),tap); sL.rotation.z=Math.PI/2; sL.position.set(-0.07,0.55,0.16); g.add(sL);
    var sR=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.07,12),tap); sR.rotation.z=Math.PI/2; sR.position.set(0.07,0.55,0.16); g.add(sR);
    var cd=new THREE.Mesh(new THREE.SphereGeometry(0.015,12,10),bDot); cd.position.set(-0.07,0.62,0.17); g.add(cd);
    var hd=new THREE.Mesh(new THREE.SphereGeometry(0.015,12,10),rDot); hd.position.set(0.07,0.62,0.17); g.add(hd);
    var drip=rbMesh(0.14,0.025,0.06,0.015,dark); drip.position.set(0,0.43,0.16); g.add(drip);
    return g;
}

// --- 9b. 饮水机 下置款 ---
function createWaterV2() {
    var g = new THREE.Group();
    var body=mat(C.darkMetal,{shininess:40}), tap=mat(C.metal,{shininess:60});
    var bDot=mat(C.blue,{shininess:60}), rDot=mat(C.coral,{shininess:60});
    // 纤细机身
    var main=rbMesh(0.28,0.95,0.28,0.06,body); main.position.y=0.55; g.add(main);
    // 顶部面板
    var top=rbMesh(0.26,0.08,0.26,0.04,body); top.position.y=1.07; g.add(top);
    // 显示屏
    var screen=rbMesh(0.1,0.04,0.01,0.005,mat(C.screen,{shininess:80,emissive:0x1E3A5F,emissiveIntensity:0.2})); screen.position.set(0,0.95,0.145); g.add(screen);
    // 龙头
    var spout=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.015,0.06,12),tap); spout.rotation.z=Math.PI/2; spout.position.set(0,0.7,0.15); g.add(spout);
    // 冷热水标
    var cd=new THREE.Mesh(new THREE.SphereGeometry(0.012,12,10),bDot); cd.position.set(-0.05,0.78,0.15); g.add(cd);
    var hd=new THREE.Mesh(new THREE.SphereGeometry(0.012,12,10),rDot); hd.position.set(0.05,0.78,0.15); g.add(hd);
    // 接水盘
    var drip=rbMesh(0.18,0.02,0.08,0.01,tap); drip.position.set(0,0.6,0.15); g.add(drip);
    // 底座
    var base=rbMesh(0.3,0.04,0.3,0.02,body); base.position.y=0.06; g.add(base);
    return g;
}

// --- 9c. 饮水机 桌面款 ---
function createWaterV3() {
    var g = new THREE.Group();
    var body=mat(C.blue,{shininess:30}), tap=mat(C.metal,{shininess:60});
    var water=mat(C.water,{transparent:true,opacity:0.5,shininess:60});
    // 矮机身
    var main=rbMesh(0.25,0.2,0.25,0.04,body); main.position.y=0.2; g.add(main);
    // 上方水箱
    var tank=new THREE.Mesh(new THREE.CylinderGeometry(0.1,0.09,0.2,16),water); tank.position.y=0.4; g.add(tank);
    var tankTop=rbMesh(0.2,0.02,0.2,0.01,body); tankTop.position.y=0.51; g.add(tankTop);
    // 龙头
    var spout=new THREE.Mesh(new THREE.CylinderGeometry(0.012,0.01,0.04,8),tap); spout.rotation.z=Math.PI/2; spout.position.set(0.06,0.25,0.13); g.add(spout);
    // 按钮
    var btn=new THREE.Mesh(new THREE.SphereGeometry(0.012,8,6),mat(C.leaf,{shininess:60})); btn.position.set(0,0.15,0.13); g.add(btn);
    // 底座
    var base=rbMesh(0.27,0.03,0.27,0.02,mat(C.darkMetal)); base.position.y=0.04; g.add(base);
    return g;
}

// --- 10. 沙发 三人款 ---
function createSofa() {
    var g = new THREE.Group();
    var fabric=mat(C.teal,{shininess:15}), cushion=mat(0x5BCFCF,{shininess:15}), legM=mat(C.woodDeep,{shininess:30});
    var base=rbMesh(1.8,0.3,0.8,0.08,fabric); base.position.y=0.3; g.add(base);
    var back=rbMesh(1.8,0.45,0.12,0.06,fabric); back.position.set(0,0.65,-0.34); g.add(back);
    [-0.8,0.8].forEach(function(x){var a=rbMesh(0.14,0.4,0.8,0.07,fabric);a.position.set(x,0.4,0);g.add(a);});
    [-0.55,0,0.55].forEach(function(x){var c=rbMesh(0.45,0.1,0.55,0.05,cushion);c.position.set(x,0.5,0.05);g.add(c);});
    [-0.55,0,0.55].forEach(function(x){var c=rbMesh(0.45,0.3,0.1,0.05,cushion);c.position.set(x,0.6,-0.22);g.add(c);});
    var legG=new THREE.CylinderGeometry(0.025,0.02,0.12,12);
    [[-0.8,-0.3],[0.8,-0.3],[-0.8,0.3],[0.8,0.3]].forEach(function(p){var l=new THREE.Mesh(legG,legM);l.position.set(p[0],0.06,p[1]);g.add(l);});
    return g;
}

// --- 10b. 沙发 双人款 ---
function createSofaV2() {
    var g = new THREE.Group();
    var fabric=mat(C.coral,{shininess:15}), cushion=mat(0xF2A09A,{shininess:15}), legM=mat(C.woodDeep,{shininess:30});
    // 弧形底座 — 用宽圆角盒子
    var base=rbMesh(1.3,0.3,0.75,0.12,fabric); base.position.y=0.3; g.add(base);
    // 弧形靠背
    var back=rbMesh(1.3,0.4,0.12,0.1,fabric); back.position.set(0,0.6,-0.3); g.add(back);
    // 圆扶手
    [-0.65,0.65].forEach(function(x){
        var arm=new THREE.Mesh(new THREE.SphereGeometry(0.12,16,12),fabric); arm.position.set(x,0.45,0); arm.scale.set(0.6,1,1.5); g.add(arm);
    });
    // 2座垫
    [-0.3,0.3].forEach(function(x){
        var c=rbMesh(0.5,0.1,0.55,0.05,cushion); c.position.set(x,0.5,0.05); g.add(c);
    });
    // 2靠垫
    [-0.3,0.3].forEach(function(x){
        var c=rbMesh(0.45,0.25,0.1,0.05,cushion); c.position.set(x,0.55,-0.2); g.add(c);
    });
    // 短腿
    var legG=new THREE.CylinderGeometry(0.02,0.015,0.1,10);
    [[-0.5,-0.25],[0.5,-0.25],[-0.5,0.25],[0.5,0.25]].forEach(function(p){var l=new THREE.Mesh(legG,legM);l.position.set(p[0],0.05,p[1]);g.add(l);});
    return g;
}

// --- 10c. 沙发 转角款 ---
function createSofaV3() {
    var g = new THREE.Group();
    var fabric=mat(C.greyBlue,{shininess:15}), cushion=mat(0x9DB5C8,{shininess:15}), legM=mat(C.darkMetal,{shininess:40});
    // 主座
    var main=rbMesh(1.8,0.3,0.8,0.06,fabric); main.position.set(-0.1,0.3,0); g.add(main);
    // 贵妃椅
    var chaise=rbMesh(0.8,0.3,1.2,0.06,fabric); chaise.position.set(0.7,0.3,0.2); g.add(chaise);
    // 主靠背
    var back=rbMesh(1.8,0.4,0.12,0.05,fabric); back.position.set(-0.1,0.6,-0.34); g.add(back);
    // 贵妃端靠背
    var chBack=rbMesh(0.12,0.4,0.8,0.05,fabric); chBack.position.set(1.1,0.6,0.2); g.add(chBack);
    // 座垫
    [-0.55,-0.1,0.35].forEach(function(x){var c=rbMesh(0.42,0.1,0.55,0.04,cushion);c.position.set(x,0.5,0.05);g.add(c);});
    // 贵妃座垫
    var cd=rbMesh(0.65,0.1,0.9,0.04,cushion); cd.position.set(0.72,0.5,0.25); g.add(cd);
    // 金属脚
    var legG=new THREE.CylinderGeometry(0.02,0.015,0.12,10);
    [[-0.8,-0.3],[0.7,-0.3],[-0.8,0.3],[1.1,-0.3],[1.1,0.7]].forEach(function(p){var l=new THREE.Mesh(legG,legM);l.position.set(p[0],0.06,p[1]);g.add(l);});
    return g;
}

// --- 11. 茶几 长方款 ---
function createCoffee() {
    var g = new THREE.Group();
    var glass=mat(0x3A4A5A,{transparent:true,opacity:0.5,shininess:100,specular:0x888888}), metal=mat(C.metal,{shininess:60});
    var top=rbMesh(0.8,0.04,0.5,0.06,glass); top.position.y=0.4; g.add(top);
    var shelf=rbMesh(0.7,0.02,0.4,0.04,glass); shelf.position.y=0.12; g.add(shelf);
    var legG=new THREE.CylinderGeometry(0.025,0.02,0.4,12);
    [[-0.35,-0.2],[0.35,-0.2],[-0.35,0.2],[0.35,0.2]].forEach(function(p){var l=new THREE.Mesh(legG,metal);l.position.set(p[0],0.2,p[1]);g.add(l);});
    var book=rbMesh(0.2,0.03,0.15,0.01,mat(C.coral)); book.position.set(0.1,0.14,0.05); g.add(book);
    var cup=new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.035,0.07,16),mat(C.warmWhite,{shininess:40})); cup.position.set(-0.15,0.445,0); g.add(cup);
    return g;
}

// --- 11b. 茶几 圆桌款 (套桌) ---
function createCoffeeV2() {
    var g = new THREE.Group();
    var wood=mat(C.woodLight,{shininess:25}), dark=mat(C.woodDark,{shininess:25});
    // 大桌
    var top1=new THREE.Mesh(new THREE.CylinderGeometry(0.28,0.28,0.03,24),wood); top1.position.set(-0.1,0.45,0); g.add(top1);
    // 三脚
    var legs1=[[-0.2,0],[0.1,-0.2],[0.1,0.2]];
    legs1.forEach(function(p){var l=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.015,0.45,12),dark);l.position.set(p[0]+(-0.1),0.22,p[1]);l.rotation.x=Math.atan2(p[1],0.2)*0.1;l.rotation.z=Math.atan2(p[0],0.2)*0.1;g.add(l);});
    // 小桌 (套叠)
    var top2=new THREE.Mesh(new THREE.CylinderGeometry(0.18,0.18,0.025,24),wood); top2.position.set(0.25,0.28,0.1); g.add(top2);
    var sLegs=[[-0.12,0],[0.06,-0.1],[0.06,0.1]];
    sLegs.forEach(function(p){var l=new THREE.Mesh(new THREE.CylinderGeometry(0.015,0.012,0.28,10),dark);l.position.set(p[0]+0.25,0.14,p[1]+0.1);g.add(l);});
    // 装饰
    var vase=new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.02,0.06,12),mat(C.coral,{shininess:40})); vase.position.set(-0.15,0.49,0); g.add(vase);
    return g;
}

// --- 11c. 茶几 柱型款 ---
function createCoffeeV3() {
    var g = new THREE.Group();
    var drum=mat(C.warmGrey,{shininess:20}), metal=mat(C.darkMetal,{shininess:50}), top=mat(C.warmGrey,{shininess:30});
    // 圆筒桌面
    var surface=new THREE.Mesh(new THREE.CylinderGeometry(0.22,0.22,0.04,24),top); surface.position.y=0.45; g.add(surface);
    // 圆筒身
    var body=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.2,0.4,24),drum); body.position.y=0.23; g.add(body);
    // 金属腰线
    var ring1=new THREE.Mesh(new THREE.TorusGeometry(0.2,0.008,8,24),metal); ring1.position.y=0.35; ring1.rotation.x=Math.PI/2; g.add(ring1);
    var ring2=new THREE.Mesh(new THREE.TorusGeometry(0.2,0.008,8,24),metal); ring2.position.y=0.15; ring2.rotation.x=Math.PI/2; g.add(ring2);
    // 中柱
    var post=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.42,12),metal); post.position.y=0.23; g.add(post);
    // 圆底
    var base=new THREE.Mesh(new THREE.CylinderGeometry(0.22,0.22,0.04,24),drum); base.position.y=0.02; g.add(base);
    // 装饰物
    var bowl=new THREE.Mesh(new THREE.SphereGeometry(0.06,16,8),mat(C.coral,{shininess:40})); bowl.position.set(0,0.5,0); bowl.scale.y=0.4; g.add(bowl);
    return g;
}

// --- 12. 显示器 27寸款 ---
function createMonitor() {
    var g = new THREE.Group();
    var bezel=mat(C.darkMetal,{shininess:40}), scr=mat(C.screen,{shininess:80,specular:0x555566,emissive:0x1E3A5F,emissiveIntensity:0.25});
    var stand=mat(C.darkMetal,{shininess:50});
    var frame=rbMesh(0.65,0.4,0.03,0.015,bezel); frame.position.y=0.6; g.add(frame);
    var disp=rbMesh(0.6,0.36,0.01,0.01,scr); disp.position.set(0,0.6,0.018); g.add(disp);
    var neck=rbMesh(0.06,0.2,0.04,0.02,stand); neck.position.set(0,0.3,0); g.add(neck);
    var base=new THREE.Mesh(new THREE.CylinderGeometry(0.14,0.16,0.025,24),stand); base.position.y=0.11; g.add(base);
    var dot=new THREE.Mesh(new THREE.SphereGeometry(0.008,8,6),mat(C.leaf,{shininess:60})); dot.position.set(0.25,0.43,0.018); g.add(dot);
    return g;
}

// --- 12b. 显示器 超宽款 ---
function createMonitorV2() {
    var g = new THREE.Group();
    var bezel=mat(C.darkMetal,{shininess:40}), scr=mat(C.screen,{shininess:80,specular:0x555566,emissive:0x1E3A5F,emissiveIntensity:0.25});
    var arm=mat(C.metal,{shininess:50});
    // 超宽屏幕
    var frame=rbMesh(0.85,0.32,0.03,0.015,bezel); frame.position.set(0,0.85,0); g.add(frame);
    var disp=rbMesh(0.8,0.28,0.01,0.01,scr); disp.position.set(0,0.85,0.018); g.add(disp);
    // 臂挂支架
    var arm1=rbMesh(0.04,0.3,0.04,0.02,arm); arm1.position.set(0,0.6,0); g.add(arm1);
    var joint=new THREE.Mesh(new THREE.SphereGeometry(0.04,12,10),arm); joint.position.set(0,0.7,0); g.add(joint);
    var arm2=rbMesh(0.04,0.2,0.04,0.02,arm); arm2.position.set(0,0.75,0); g.add(arm2);
    // 夹具底座
    var clamp=rbMesh(0.08,0.15,0.06,0.02,arm); clamp.position.set(0,0.3,0); g.add(clamp);
    var clampB=rbMesh(0.1,0.04,0.06,0.02,arm); clampB.position.set(0,0.22,0); g.add(clampB);
    return g;
}

// --- 12c. 显示器 双屏款 ---
function createMonitorV3() {
    var g = new THREE.Group();
    var bezel=mat(C.darkMetal,{shininess:40}), scr=mat(C.screen,{shininess:80,specular:0x555566,emissive:0x1E3A5F,emissiveIntensity:0.2});
    var arm=mat(C.metal,{shininess:50}), blue=mat(C.blue,{shininess:60});
    // 双屏横臂
    var bar=rbMesh(0.6,0.04,0.04,0.02,arm); bar.position.set(0,0.5,0); g.add(bar);
    // 左屏
    var lFrame=rbMesh(0.45,0.28,0.025,0.012,bezel); lFrame.position.set(-0.28,0.78,0); g.add(lFrame);
    var lDisp=rbMesh(0.42,0.25,0.01,0.008,scr); lDisp.position.set(-0.28,0.78,0.015); g.add(lDisp);
    // 右屏
    var rFrame=rbMesh(0.45,0.28,0.025,0.012,bezel); rFrame.position.set(0.28,0.78,0); g.add(rFrame);
    var rDisp=rbMesh(0.42,0.25,0.01,0.008,scr); rDisp.position.set(0.28,0.78,0.015); g.add(rDisp);
    // 立柱
    var post=rbMesh(0.05,0.4,0.05,0.02,arm); post.position.set(0,0.3,0); g.add(post);
    // 底座
    var base=new THREE.Mesh(new THREE.CylinderGeometry(0.12,0.14,0.02,24),arm); base.position.y=0.1; g.add(base);
    // 连接关节
    var j1=new THREE.Mesh(new THREE.SphereGeometry(0.03,10,8),arm); j1.position.set(-0.15,0.6,0); g.add(j1);
    var j2=new THREE.Mesh(new THREE.SphereGeometry(0.03,10,8),arm); j2.position.set(0.15,0.6,0); g.add(j2);
    // 电源指示
    var dot=new THREE.Mesh(new THREE.SphereGeometry(0.006,8,6),blue); dot.position.set(0.4,0.66,0.015); g.add(dot);
    return g;
}

/* ============================================================
   模型工厂注册表 (36 个)
   ============================================================ */
var modelFactories = {
    desk: createDesk, desk_v2: createDeskV2, desk_v3: createDeskV3,
    chair: createChair, chair_v2: createChairV2, chair_v3: createChairV3,
    bookshelf: createBookshelf, bookshelf_v2: createBookshelfV2, bookshelf_v3: createBookshelfV3,
    cabinet: createCabinet, cabinet_v2: createCabinetV2, cabinet_v3: createCabinetV3,
    conference: createConference, conference_v2: createConferenceV2, conference_v3: createConferenceV3,
    whiteboard: createWhiteboard, whiteboard_v2: createWhiteboardV2, whiteboard_v3: createWhiteboardV3,
    printer: createPrinter, printer_v2: createPrinterV2, printer_v3: createPrinterV3,
    plant: createPlant, plant_v2: createPlantV2, plant_v3: createPlantV3,
    water: createWater, water_v2: createWaterV2, water_v3: createWaterV3,
    sofa: createSofa, sofa_v2: createSofaV2, sofa_v3: createSofaV3,
    coffee: createCoffee, coffee_v2: createCoffeeV2, coffee_v3: createCoffeeV3,
    monitor: createMonitor, monitor_v2: createMonitorV2, monitor_v3: createMonitorV3
};

/* ============================================================
   ItemViewer · 单个 3D 查看器
   ============================================================ */
class ItemViewer {
    constructor(canvas, modelFactory) {
        this.canvas = canvas;
        this.isDragging = false;
        this.autoRotate = true;
        this.rotationY = 0;
        this.rotationX = 0.15;
        this.targetRotY = 0;
        this.targetRotX = 0.15;
        this.lastX = 0;
        this.lastY = 0;
        this.init(modelFactory);
    }

    init(modelFactory) {
        var w = this.canvas.parentElement.clientWidth;
        var h = this.canvas.parentElement.clientHeight;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
        this.camera.position.set(2.2, 1.6, 2.2);
        this.camera.lookAt(0, 0.5, 0);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
        this.renderer.setSize(w, h);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // 暖色柔光
        this.scene.add(new THREE.AmbientLight(0xFFF5E6, 0.55));
        var key = new THREE.DirectionalLight(0xFFE4B5, 0.65); key.position.set(3, 4, 3); this.scene.add(key);
        var fill = new THREE.DirectionalLight(0xB0C4DE, 0.3); fill.position.set(-2, 2, 1); this.scene.add(fill);
        var rim = new THREE.DirectionalLight(0xFFD700, 0.2); rim.position.set(-1, 3, -3); this.scene.add(rim);

        // 地面阴影
        var ground = new THREE.Mesh(
            new THREE.CircleGeometry(1.6, 32),
            new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.06 })
        );
        ground.rotation.x = -Math.PI / 2;
        this.scene.add(ground);

        // 模型容器
        this.modelGroup = new THREE.Group();
        this.scene.add(this.modelGroup);
        this.loadModel(modelFactory);

        this.bindEvents();

        this.isVisible = false;
        var self = this;
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) { self.isVisible = entry.isIntersecting; });
        }, { threshold: 0 });
        observer.observe(this.canvas);

        this.animate();
    }

    loadModel(modelFactory) {
        // 清除旧模型
        while (this.modelGroup.children.length > 0) {
            var child = this.modelGroup.children[0];
            this.modelGroup.remove(child);
        }
        if (!modelFactory) return;

        var model = modelFactory();
        var box = new THREE.Box3().setFromObject(model);
        var size = box.getSize(new THREE.Vector3());
        var center = box.getCenter(new THREE.Vector3());
        var maxDim = Math.max(size.x, size.y, size.z, 0.01);
        var scale = 1.4 / maxDim;
        model.scale.setScalar(scale);
        model.position.x = -center.x * scale;
        model.position.y = -box.min.y * scale;
        model.position.z = -center.z * scale;
        this.modelGroup.add(model);
    }

    swapModel(modelFactory) {
        this.loadModel(modelFactory);
        // 重置旋转
        this.targetRotY = 0;
        this.targetRotX = 0.15;
        this.autoRotate = true;
    }

    bindEvents() {
        var self = this;
        var el = this.canvas.parentElement;
        var onStart = function(x, y) { self.isDragging = true; self.autoRotate = false; self.lastX = x; self.lastY = y; };
        var onMove = function(x, y) {
            if (!self.isDragging) return;
            self.targetRotY += (x - self.lastX) * 0.01;
            self.targetRotX += (y - self.lastY) * 0.01;
            self.targetRotX = Math.max(-0.6, Math.min(0.8, self.targetRotX));
            self.lastX = x; self.lastY = y;
        };
        var onEnd = function() {
            self.isDragging = false;
            clearTimeout(self._timer);
            self._timer = setTimeout(function() { self.autoRotate = true; }, 2000);
        };
        el.addEventListener('mousedown', function(e) { onStart(e.clientX, e.clientY); });
        window.addEventListener('mousemove', function(e) { onMove(e.clientX, e.clientY); });
        window.addEventListener('mouseup', onEnd);
        el.addEventListener('touchstart', function(e) { if (e.touches.length > 0) onStart(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
        window.addEventListener('touchmove', function(e) { if (e.touches.length > 0) onMove(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
        window.addEventListener('touchend', onEnd);
    }

    animate() {
        var self = this;
        requestAnimationFrame(function() { self.animate(); });
        if (!this.isVisible) return;
        if (this.autoRotate) this.targetRotY += 0.008;
        this.rotationY += (this.targetRotY - this.rotationY) * 0.1;
        this.rotationX += (this.targetRotX - this.rotationX) * 0.1;
        this.modelGroup.rotation.y = this.rotationY;
        this.modelGroup.rotation.x = this.rotationX;
        this.renderer.render(this.scene, this.camera);
    }

    resize() {
        var w = this.canvas.parentElement.clientWidth;
        var h = this.canvas.parentElement.clientHeight;
        if (w === 0 || h === 0) return;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }
}

/* ============================================================
   DOM 渲染
   ============================================================ */
function renderItems() {
    var grid = document.getElementById('itemGrid');
    grid.innerHTML = items.map(function(item, idx) {
        var tabs = item.variants.map(function(v, vi) {
            return '<button class="variant-tab' + (vi === 0 ? ' active' : '') + '" data-vi="' + vi + '">' + v.name + '</button>';
        }).join('');
        var v0 = item.variants[0];
        return '<div class="item-card" data-idx="' + idx + '">' +
            '<div class="variant-tabs">' + tabs + '</div>' +
            '<div class="item-canvas-wrapper">' +
                '<canvas></canvas>' +
                '<span class="item-canvas-hint">拖拽旋转</span>' +
            '</div>' +
            '<div class="item-info">' +
                '<span class="item-category">' + item.category + '</span>' +
                '<h3 class="item-name">' + item.name + '</h3>' +
                '<p class="item-spec">' + v0.spec + '</p>' +
                '<p class="item-material">' + v0.material + '</p>' +
            '</div>' +
        '</div>';
    }).join('');
}

function renderTable() {
    var tbody = document.getElementById('itemTableBody');
    tbody.innerHTML = tableData.map(function(r) {
        return '<tr>' +
            '<td>' + r.no + '</td>' +
            '<td>' + r.name + '</td>' +
            '<td>' + r.model + '</td>' +
            '<td>' + r.zone + '</td>' +
            '<td>' + r.qty + '</td>' +
            '<td>' + r.spec + '</td>' +
            '<td>' + r.material + '</td>' +
            '<td>' + r.desc + '</td>' +
        '</tr>';
    }).join('');
}

function renderTemplateTable() {
    var tbody = document.getElementById('templateTableBody');
    tbody.innerHTML = templateData.map(function(r) {
        return '<tr>' +
            '<td>' + r.zone + '</td>' +
            '<td>' + r.item + '</td>' +
            '<td>' + r.qty + '</td>' +
            '<td>' + r.price + '</td>' +
            '<td><span class="fill-line" style="display:inline-block;width:60px;"></span></td>' +
            '<td>待定</td>' +
            '<td>' + r.note + '</td>' +
        '</tr>';
    }).join('');
}

function initViewers() {
    if (typeof THREE === 'undefined') {
        document.querySelectorAll('.item-canvas-wrapper').forEach(function(w) {
            w.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#A09384;font-size:0.8rem;">3D 加载失败</div>';
        });
        return;
    }

    var viewers = [];
    document.querySelectorAll('.item-card').forEach(function(card, idx) {
        var canvas = card.querySelector('canvas');
        var itemIdx = parseInt(card.dataset.idx);
        var firstVariant = items[itemIdx].variants[0];
        var factory = modelFactories[firstVariant.id];
        if (factory) {
            viewers[idx] = new ItemViewer(canvas, factory);
        }
    });

    // 变体切换
    document.querySelectorAll('.variant-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            var card = tab.closest('.item-card');
            var itemIdx = parseInt(card.dataset.idx);
            var vi = parseInt(tab.dataset.vi);

            card.querySelectorAll('.variant-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');

            var variant = items[itemIdx].variants[vi];
            var viewer = viewers[itemIdx];
            if (viewer && modelFactories[variant.id]) {
                viewer.swapModel(modelFactories[variant.id]);
            }

            card.querySelector('.item-spec').textContent = variant.spec;
            card.querySelector('.item-material').textContent = variant.material;
        });
    });

    window.addEventListener('resize', function() {
        viewers.forEach(function(v) { if (v) v.resize(); });
    });
}

/* ============================================================
   导航交互
   ============================================================ */
function initNavigation() {
    var toggle = document.getElementById('navToggle');
    var links = document.querySelector('.nav-links');
    var navLinks = document.querySelectorAll('.nav-link');
    if (toggle) {
        toggle.addEventListener('click', function() {
            toggle.classList.toggle('active');
            links.classList.toggle('show');
        });
    }
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (toggle) toggle.classList.remove('active');
            if (links) links.classList.remove('show');
        });
    });
    var sections = document.querySelectorAll('section[id], header[id]');
    var navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function() {
        var current = '';
        sections.forEach(function(sec) {
            if (window.scrollY >= sec.offsetTop - 100) current = sec.id;
        });
        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) link.classList.add('active');
        });
        if (navbar) navbar.style.boxShadow = window.scrollY > 30 ? '0 2px 12px rgba(0,0,0,0.06)' : 'none';
    });
}

/* ============================================================
   初始化
   ============================================================ */
document.addEventListener('DOMContentLoaded', function() {
    renderItems();
    renderTable();
    renderTemplateTable();
    initViewers();
    initNavigation();
});
