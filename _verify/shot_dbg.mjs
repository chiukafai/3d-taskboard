// 最小对照：先基线截图，再改相机截图，定位空白原因
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
page.on('pageerror', e => console.log('  [pageerror]', String(e).slice(0, 200)));
page.on('console', m => { if (m.type() === 'error') console.log('  [console]', m.text().slice(0, 200)); });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(15000);
await page.screenshot({ path: OUT + 'k0_baseline.png' });
console.log('  ✓ k0_baseline');

const info = await page.evaluate(() => {
  const d = window.__boardDebug;
  return {
    bg: d.scene.background ? (d.scene.background.getHexString ? '#' + d.scene.background.getHexString() : String(d.scene.background.type)) : 'null',
    fog: d.scene.fog ? d.scene.fog.type : 'null',
    cam: d.camera.type,
    camPos: d.camera.position.toArray().map(v => +v.toFixed(2)),
    target: d.controls.target.toArray().map(v => +v.toFixed(2)),
    maxDist: d.controls.maxDistance, minDist: d.controls.minDistance,
    maxPolar: +(d.controls.maxPolarAngle * 180 / Math.PI).toFixed(1),
    minPolar: +(d.controls.minPolarAngle * 180 / Math.PI).toFixed(1),
    canvasSize: [d.renderer.domElement.width, d.renderer.domElement.height],
    preserve: d.renderer.getContext().getContextAttributes().preserveDrawingBuffer,
  };
});
console.log(JSON.stringify(info));

await page.evaluate(() => {
  const d = window.__boardDebug;
  d.scene.fog = null;
  d.camera.position.set(12.9, 2.30, 6.10);
  d.controls.target.set(12.5, 0.80, 4.40);
  d.camera.lookAt(12.5, 0.80, 4.40);
  d.controls.update();
});
await page.waitForTimeout(1500);
await page.screenshot({ path: OUT + 'k1_cro_desk.png' });
console.log('  ✓ k1_cro_desk');
const after = await page.evaluate(() => {
  const d = window.__boardDebug;
  return { camPos: d.camera.position.toArray().map(v => +v.toFixed(2)), target: d.controls.target.toArray().map(v => +v.toFixed(2)) };
});
console.log('after', JSON.stringify(after));
await browser.close();
