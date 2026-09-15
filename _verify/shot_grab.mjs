// 可靠的取图方式：在同一个 JS 任务里 render() + toDataURL()
// 原因：renderer 用 {alpha:true} 未开 preserveDrawingBuffer，page.screenshot() 常抓到空画布
import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'node:fs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';

export async function openBoard(waitMs = 16000) {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
  await page.waitForTimeout(waitMs);
  return { browser, page };
}
export async function grab(page, name) {
  const data = await page.evaluate(() => {
    const d = window.__boardDebug;
    d.renderer.setClearColor(0xf4f1eb, 1);
    d.renderer.render(d.scene, d.camera);
    return d.renderer.domElement.toDataURL('image/png');
  });
  fs.writeFileSync(OUT + name + '.png', Buffer.from(data.split(',')[1], 'base64'));
  console.log('  ✓', name);
}
export async function look(page, px, py, pz, lx, ly, lz) {
  await page.evaluate(([px, py, pz, lx, ly, lz]) => {
    const d = window.__boardDebug;
    d.scene.fog = null;
    d.controls.enableDamping = false;
    d.camera.position.set(px, py, pz);
    d.controls.target.set(lx, ly, lz);
    d.camera.lookAt(lx, ly, lz);
    d.controls.update();
    d.camera.updateMatrixWorld(true);
  }, [px, py, pz, lx, ly, lz]);
  await page.waitForTimeout(300);
}

if (import.meta.url === 'file:///' + process.argv[1].replace(/\\/g, '/')) {
  const VIEWS = [
    ['z1_cfo_plaque', [11.6, 1.75, 18.4], [8.74, 2.35, 17.9]],
    ['z2_cpo_plaque', [9.8, 1.75, 7.6], [6.74, 2.35, 7.4]],
    ['z3_cfo_rugs_top', [5.4, 9.5, 19.6], [5.4, 0.0, 18.9]],
    ['z4_cro_desk', [12.9, 2.30, 6.10], [12.5, 0.80, 4.40]],
    ['z5_ceo_desk', [22.9, 2.20, 16.40], [21.8, 0.80, 14.60]],
    ['z6_cmo_desks', [20.2, 2.60, 3.10], [19.6, 0.80, 2.10]],
  ];
  const { browser, page } = await openBoard();
  for (const [n, cam, tgt] of VIEWS) { await look(page, ...cam, ...tgt); await grab(page, n); }
  await browser.close();
  console.log('done');
}
