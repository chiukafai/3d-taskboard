import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'node:fs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1000, height: 720 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(14000);

async function grabAndReport(tag) {
  const r = await page.evaluate(() => {
    const d = window.__boardDebug;
    d.renderer.setClearColor(0xf4f1eb, 1);
    d.renderer.render(d.scene, d.camera);
    const info = d.renderer.info.render;
    const cam = d.camera;
    const dir = new (cam.position.constructor)();
    cam.getWorldDirection(dir);
    return {
      tris: info.triangles, calls: info.calls,
      camPos: cam.position.toArray().map(v => +v.toFixed(2)),
      dir: dir.toArray().map(v => +v.toFixed(2)),
      target: d.controls.target.toArray().map(v => +v.toFixed(2)),
      png: d.renderer.domElement.toDataURL('image/png').slice(0, 30),
      data: d.renderer.domElement.toDataURL('image/png'),
      children: d.scene.children.length,
      visible: d.scene.children.filter(c => c.visible).length,
      gl: !!d.renderer.getContext(),
      showCount: window.__showCount,
    };
  });
  fs.writeFileSync(OUT + tag + '.png', Buffer.from(r.data.split(',')[1], 'base64'));
  delete r.data;
  console.log(tag, JSON.stringify(r));
}
await grabAndReport('t0_default');
await page.evaluate(() => {
  const d = window.__boardDebug;
  d.scene.fog = null;
  d.controls.enableDamping = false;
  d.camera.position.set(12.9, 2.30, 6.10);
  d.controls.target.set(12.5, 0.80, 4.40);
  d.camera.lookAt(12.5, 0.80, 4.40);
  d.controls.update();
});
await page.waitForTimeout(600);
await grabAndReport('t1_cro_desk');
await page.evaluate(() => { const d = window.__boardDebug; d.camera.position.set(14.8, 20.6, 30.4); d.controls.target.set(14.8, 0, 10.8); d.camera.lookAt(14.8, 0, 10.8); d.controls.update(); });
await page.waitForTimeout(600);
await grabAndReport('t2_overview_manual');
await browser.close();
