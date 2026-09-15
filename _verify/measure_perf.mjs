// 性能测量：首屏/模型就位耗时 + 网格材质统计 + 网络请求明细
import { chromium } from './node_modules/playwright/index.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage();
const reqs = new Map();
page.on('response', r => {
  const u = r.url();
  if (!/^https?:/.test(u)) return;
  reqs.set(u, (reqs.get(u) || 0) + 1);
});
const t0 = Date.now();
await page.goto(URL, { waitUntil: 'domcontentloaded' });
const domTime = Date.now() - t0;
await page.waitForFunction(() => window.__showCount >= 8, null, { timeout: 60000 }).catch(() => {});
const modelTime = Date.now() - t0;
const paint = await page.evaluate(() => {
  const fcp = performance.getEntriesByName('first-contentful-paint')[0];
  return fcp ? Math.round(fcp.startTime) : -1;
});
const stats = await page.evaluate(() => {
  let meshes = 0; const mats = new Set(); const geos = new Set();
  window.__boardDebug.scene.traverse(o => {
    if (o.isMesh) { meshes++; if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => mats.add(m.uuid)); if (o.geometry) geos.add(o.geometry.uuid); }
  });
  return { meshes, materials: mats.size, geometries: geos.size };
});
const dupes = [...reqs.entries()].filter(([, n]) => n > 1);
console.log('=== 性能测量 ===');
console.log('首屏内容绘制(FCP):', paint, 'ms');
console.log('DOMContentLoaded:', domTime, 'ms');
console.log('8 房模型就位:', modelTime, 'ms');
console.log('网格:', stats.meshes, '| 材质:', stats.materials, '| 几何体:', stats.geometries);
console.log('网络请求数:', reqs.size, '| 重复请求:', dupes.length);
dupes.slice(0, 6).forEach(([u, n]) => console.log('   重复 x' + n, u.slice(0, 90)));
await browser.close();
