// 实测：场景中所有「0.75×1.20×0.73 左右」的网格（= exec_chair）的世界坐标，
// 用以确认 _SHOW 的 p 是「房间局部坐标」还是「世界坐标」。
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);

const out = await page.evaluate(() => {
  const d = window.__boardDebug;
  const hits = [];
  d.scene.traverse(o => {
    if (!o.isMesh || !o.geometry) return;
    o.geometry.computeBoundingBox();
    const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
    const sx = bb.max.x - bb.min.x, sy = bb.max.y - bb.min.y, sz = bb.max.z - bb.min.z;
    // exec_chair 实测 0.64x1.02x0.62，按 h=1.20 缩放 ≈ 0.75x1.20x0.73
    if (sy > 1.05 && sy < 1.35 && sx > 0.55 && sx < 0.95 && sz > 0.55 && sz < 0.95) {
      hits.push({
        x: +((bb.min.x + bb.max.x) / 2).toFixed(2),
        y: +((bb.min.y + bb.max.y) / 2).toFixed(2),
        z: +((bb.min.z + bb.max.z) / 2).toFixed(2),
        s: `${sx.toFixed(2)}x${sy.toFixed(2)}x${sz.toFixed(2)}`,
      });
    }
  });
  return hits.sort((a, b) => a.z - b.z || a.x - b.x);
});
console.log('=== 场景中 exec_chair 类网格（世界坐标）===');
out.forEach(r => console.log(`   (${r.x}, ${r.y}, ${r.z})  ${r.s}`));
console.log('   共', out.length);
console.log('\n期望（若 p 为房间局部坐标 → 世界 = cx+px, cz+pz）:');
console.log('   cro(2.5,2.5) p(0,-1.00) → ( 2.50, 1.50)   coo(8.5,2.5) p(0,-0.65) → ( 8.50, 1.85)');
console.log('   cpo(21,2.5)  p(0,-1.00) → (21.00, 1.50)   cto(4,15.5)  p(0.5,0.80) → ( 4.50,16.30)');
console.log('   ceo(12,15.5) p(0,-1.60) → (12.00,13.90)   cfo(20,15.5) p(0,-1.60) → (20.00,13.90)');
await browser.close();
