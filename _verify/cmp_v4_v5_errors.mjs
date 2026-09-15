// 对比 v5 与 v4 备份的错误画像，确认 shader 报错不是本次改动引入
import { chromium } from './node_modules/playwright/index.mjs';

const files = [
  ['v5 现行', 'http://127.0.0.1:8934/office-3d-taskboard.html'],
  ['v4 备份', 'http://127.0.0.1:8934/_cmp_v4.html'],
];
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
for (const [tag, url] of files) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 120)); });
  page.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
  await page.waitForTimeout(12000);
  const st = await page.evaluate(() => {
    const d = window.__boardDebug;
    let mesh = 0; const mats = new Set();
    d.scene.traverse(o => { if (o.isMesh) { mesh++; mats.add(o.material.uuid); } });
    return { zones: Object.keys(d.ZONES).length, show: window.__showCount || 0, mesh, mats: mats.size, children: d.scene.children.length };
  });
  const shader = errs.filter(e => e.includes('WebGLProgram') || e.includes('Shader'));
  console.log(`\n【${tag}】 ${url.split('/').pop()}`);
  console.log('  ', JSON.stringify(st));
  console.log('   报错总数', errs.length, '｜其中 shader 类', shader.length);
  const uniq = [...new Set(errs)];
  uniq.forEach(e => console.log('     ·', e));
  await page.close();
}
await browser.close();
