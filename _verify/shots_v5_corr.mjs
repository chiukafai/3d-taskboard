// 主廊视角补拍：人眼 + 斜俯视两组，挑一张最能体现 4.2m 净宽
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(14000);
await page.evaluate(async () => {
  const THREE = await import('three');
  const THREE2 = THREE;
  const d = window.__boardDebug;
  d.scene.fog = null;
  const w = 31.6, h = 23.6;
  const cam = new THREE2.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.1, 200);
  cam.position.set(14.8, 60, 10.8); cam.up.set(0, 0, -1); cam.lookAt(14.8, 0, 10.8); cam.updateProjectionMatrix();
  d.__ortho = cam;
});
const shots = [
  // [名称, 相机 xyz, 目标 xyz]
  ['q1_corr_eye_e', 8.30, 1.70, 10.30, 29.2, 0.55, 10.30],
  ['q2_corr_eye_w', 28.60, 1.70, 10.30, 7.6, 0.55, 10.30],
  ['q3_corr_iso', 4.00, 9.00, -1.50, 19.0, 0.00, 10.60],
  ['q4_corr_iso2', 20.00, 7.50, 1.00, 16.0, 0.00, 11.00],
  ['q5_lobby_eye', 10.60, 1.62, 15.60, 9.2, 0.55, 10.20],
  ['q6_corr_n_look', 17.00, 3.20, 6.00, 17.0, 0.00, 11.40],
];
for (const [n, px, py, pz, lx, ly, lz] of shots) {
  await page.evaluate(([px, py, pz, lx, ly, lz]) => {
    window.__renderWith = null;
    const d = window.__boardDebug;
    d.camera.position.set(px, py, pz);
    d.controls.target.set(lx, ly, lz);
    d.camera.lookAt(lx, ly, lz);
    d.controls.update();
  }, [px, py, pz, lx, ly, lz]);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: OUT + n + '.png' });
  console.log('  ✓', n);
}
await browser.close();
