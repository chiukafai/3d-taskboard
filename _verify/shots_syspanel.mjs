// 截取「系统设置」面板 + 「查看全文」弹窗（修复后留档）
import { chromium } from 'playwright';
const URL = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const page = await (await browser.newContext({ viewport: { width: 1500, height: 940 } })).newPage();
await page.goto(URL, { waitUntil: 'load', timeout: 30000 });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 15000 });
await page.waitForTimeout(6000);

await page.click('#btn-sys');
await page.waitForTimeout(900);
await page.screenshot({ path: '_shots/syspanel_fixed.png' });

// 打开 SOUL.md 全文
const names = await page.locator('#syspanel-body .cfg-card .cfg-name').allInnerTexts();
const idx = names.findIndex(n => n.includes('SOUL.md'));
await page.locator('#syspanel-body .cfg-card').nth(idx < 0 ? 0 : idx).click();
await page.waitForTimeout(700);
await page.screenshot({ path: '_shots/syspanel_modal_ok.png' });

const chk = await page.evaluate(() => {
  const t = document.getElementById('cfg-modal-title').textContent;
  const b = document.getElementById('cfg-modal-body');
  return { title: t, open: document.getElementById('cfg-modal').classList.contains('open'),
           chars: b.innerText.length, first: b.innerText.split('\n').slice(0, 3).join(' / '),
           last: b.innerText.split('\n').slice(-3).join(' / ') };
});
console.log('弹窗:', chk.open ? '✅ 已打开' : '❌ 未打开', '| 标题:', chk.title, '| 正文', chk.chars, '字');
console.log('  开头:', chk.first.slice(0, 90));
console.log('  结尾:', chk.last.slice(0, 90));
await browser.close();
