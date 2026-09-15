// 渲染建筑剪影：隐藏室外草地、背景置黑 → 正交俯视拍下建筑外轮廓（供 vision_v4.py 比对）
import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'fs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(13000);

const info = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const hidden = [];
  d.scene.traverse(o => {
    if (!o.isMesh || !o.geometry) return;
    const p = o.geometry.parameters || {};
    if (o.geometry.type === 'PlaneGeometry' && p.width >= 50) { o.visible = false; hidden.push('ground96'); }
  });
  d.scene.background = new THREE.Color('#000000');
  d.scene.fog = null;
  const w = 31.6, h = 23.6;                       // 正交取景：x 14.8±15.8 ; z 10.8±11.8
  const cam = new THREE.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.1, 300);
  cam.position.set(14.8, 80, 10.8);
  cam.up.set(0, 0, -1);
  cam.lookAt(14.8, 0, 10.8);
  cam.updateProjectionMatrix();
  if (!window.__origRender) {
    window.__origRender = d.renderer.render.bind(d.renderer);
    d.renderer.render = (sc, c) => window.__origRender(sc, cam);
  }
  const cv = document.querySelector('#canvas-container canvas');
  const r = cv.getBoundingClientRect();
  return { hidden, frustum: { cx: 14.8, cz: 10.8, hw: w / 2, hh: h / 2 },
           rect: { x: r.x, y: r.y, w: r.width, h: r.height },
           buf: { w: cv.width, h: cv.height }, dpr: window.devicePixelRatio };
});
console.log('隐藏对象:', JSON.stringify(info.hidden));
console.log('正交取景:', JSON.stringify(info.frustum));
console.log('画布 CSS 矩形:', JSON.stringify(info.rect), ' 缓冲:', JSON.stringify(info.buf), ' dpr:', info.dpr);
fs.writeFileSync('_canvas_rect.json', JSON.stringify(info, null, 1));
await page.waitForTimeout(1500);
await page.screenshot({ path: OUT + 'p0_silhouette.png' });
console.log('→ _shots/p0_silhouette.png');
await browser.close();
