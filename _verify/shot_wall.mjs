// 定点相机：按世界坐标看指定墙面的门 + 门牌
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const views = [
  { n: 'cfoint', pos: [20, 3.6, 6.5], tgt: [20, 1.5, 13] },   // 中庭 → 看 CFO 北墙（门墙）
  { n: 'cpoint', pos: [12.5, 3.6, 9], tgt: [18, 1.5, 9] },    // 中庭 → 看 CPO 左墙（门墙）
  { n: 'ceoint', pos: [21, 3.6, 10.5], tgt: [21, 1.5, 5] },   // 中庭 → 看 CEO 南墙（门墙）
];
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
for (const v of views) {
  const page = await browser.newPage({ viewport: { width: 900, height: 620 }, deviceScaleFactor: 1.4 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await page.evaluate(({ pos, tgt }) => {
    const d = window.__boardDebug;
    d.camera.position.set(...pos);
    d.controls.target.set(...tgt);
    d.controls.update();
    ['toolbar', 'panel', 'legend', 'hint', 'syspanel'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
  }, { pos: v.pos, tgt: v.tgt });
  await page.waitForTimeout(900);
  await page.screenshot({ path: `../_shots/w_${v.n}.png` });
  console.log('saved w_' + v.n + '.png');
  await page.close();
}
await browser.close();
