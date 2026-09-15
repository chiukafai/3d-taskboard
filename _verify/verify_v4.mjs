// v4 落地浏览器侧验证：JS 报错 / 模型加载 / 门开合方向 / 房间归属
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

const errs = [], warns = [], oks = [], r404 = [];
page.on('console', m => {
  const t = m.text();
  if (m.type() === 'error') errs.push(t);
  else if (t.includes('❌') || t.includes('⚠️')) warns.push(t);
  else if (t.includes('✅')) oks.push(t);
});
page.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
page.on('response', r => { if (r.status() >= 400) r404.push(`${r.status()} ${r.url().split('/').pop()}`); });

await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(14000);

const info = await page.evaluate(() => {
  const d = window.__boardDebug;
  const zoneIds = Object.keys(d.ZONES);
  let mesh = 0, tris = 0;
  const mats = new Set();
  d.scene.traverse(o => { if (o.isMesh) { mesh++; mats.add(o.material.uuid); if (o.geometry?.index) tris += o.geometry.index.count / 3; } });
  return {
    zones: zoneIds, showCount: window.__showCount || 0,
    mesh, mats: mats.size, tris: Math.round(tris),
    doors: Object.keys(d.doorGroups),
    children: d.scene.children.length,
    cam: d.camera.position.toArray().map(v => +v.toFixed(1)),
    // 公共区墙体数量（box 且材质为 wallInner）
    plaqueCount: (() => { let n = 0; d.scene.traverse(o => { if (o.isMesh && o.geometry?.type === 'BoxGeometry') { const p = o.geometry.parameters; if (Math.abs(p.depth - 0.06) < 0.01 && p.height > 0.4 && p.height < 0.8) n++; } }); return n; })(),
  };
});

console.log('=== 结构 ===');
console.log('  房间', info.zones.length, JSON.stringify(info.zones));
console.log('  高清样板房就位', info.showCount, '/ 8');
console.log('  门对象', info.doors.length, JSON.stringify(info.doors));
console.log('  场景 mesh', info.mesh, ' 材质', info.mats, ' 三角面', info.tris);
console.log('  相机初始位', info.cam, ' 场景根子节点', info.children);

// ── 门开合方向：叶片尖端相对房间中心是「远离」(外开) 还是「靠近」(内开)
console.log('\n=== 门开合方向（外开=叶片离房间中心更远）===');
const swing = await page.evaluate(async () => {
  const d = window.__boardDebug;
  const THREE = await import('three');
  const tip = zid => {
    const pvt = d.doorGroups[zid];
    const lf = pvt.userData.leaves[0];
    pvt.updateWorldMatrix(true, true);
    const v = new THREE.Vector3(1, 0, 0).multiplyScalar(0.4).applyMatrix4(lf.matrixWorld);
    return v;
  };
  const res = [];
  for (const zid of Object.keys(d.ZONES)) {
    const z = d.ZONES[zid];
    if (!d.doorGroups[zid]) { res.push({ zid, no: true }); continue; }
    const closed = tip(zid);
    d.toggleDoor(zid);
    await new Promise(r => setTimeout(r, 1400));
    const open = tip(zid);
    d.toggleDoor(zid);
    await new Promise(r => setTimeout(r, 1400));
    const dc = Math.hypot(closed.x - z.cx, closed.z - z.cz);
    const doo = Math.hypot(open.x - z.cx, open.z - z.cz);
    res.push({ zid, dc: +dc.toFixed(2), do: +doo.toFixed(2), outward: doo > dc });
  }
  return res;
});
for (const s of swing) {
  if (s.no) { console.log(`  ${s.zid.padEnd(8)} 无门`); continue; }
  console.log(`  ${s.zid.padEnd(8)} 关闭时叶尖距房心 ${String(s.dc).padStart(5)}m → 开启 ${String(s.do).padStart(5)}m   ${s.outward ? '外开 ✅' : '内开 ⚠️'}`);
}

// ── 门洞是否可见（不被家具堵）：从门洞外侧向内打射线看首个命中物
console.log('\n=== 门洞净空（门外 0.6m 沿门轴中心朝房内射线）===');
const ray = await page.evaluate(async () => {
  const d = window.__boardDebug;
  const THREE = await import('three');
  const rc = new THREE.Raycaster();
  const out = [];
  for (const [zid, z] of Object.entries(d.ZONES)) {
    if (!z.doorWall) continue;
    let px = z.cx, pz = z.cz, dx = 0, dz = 0;
    if (z.doorWall === 'front') { px = z.doorPos; pz = z.cz + z.d / 2 + 0.6; dz = -1; }
    else if (z.doorWall === 'back') { px = z.doorPos; pz = z.cz - z.d / 2 - 0.6; dz = 1; }
    else if (z.doorWall === 'right') { px = z.cx + z.w / 2 + 0.6; pz = z.doorPos; dx = -1; }
    else { px = z.cx - z.w / 2 - 0.6; pz = z.doorPos; dx = 1; }
    rc.set(new THREE.Vector3(px, 1.0, pz), new THREE.Vector3(dx, 0, dz));
    const hits = rc.intersectObjects(d.scene.children, true)
      .filter(h => h.object.isMesh && h.distance > 0.1);
    const first = hits[0];
    out.push({ zid, hit: first ? first.object.geometry.type + '@' + first.distance.toFixed(2) : '空' });
  }
  return out;
});
ray.forEach(r => console.log(`  ${r.zid.padEnd(8)} 首个命中：${r.hit}`));

console.log('\n=== 控制台 ===');
console.log(`  ✅ 日志 ${oks.length} 条，⚠️ 警告 ${warns.length} 条，❌ 报错 ${errs.length} 条`);
warns.forEach(w => console.log('   ⚠️', w));
errs.forEach(e => console.log('   ❌', e));
console.log('  404:', r404.length ? r404.join(' | ') : '无');

await browser.close();
