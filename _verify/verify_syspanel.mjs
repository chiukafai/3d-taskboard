// 校验「系统设置（⚙ 系统 · 中控台）」面板是否真实生效
// 用法: node verify_syspanel.mjs [html]
// 需先在 8934 端口起服务: python -m http.server 8934 --bind 127.0.0.1
import { chromium } from 'playwright';

const target = process.argv[2] || 'office-3d-taskboard.html';
const URL = `http://127.0.0.1:8934/${target}`;
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();

const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', e => errs.push('pageerror: ' + e.message));

await page.goto(URL, { waitUntil: 'load', timeout: 30000 });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 15000 });
await page.waitForTimeout(6000);

const R = {};
R.btnExists = await page.locator('#btn-sys').count();
await page.click('#btn-sys');
await page.waitForTimeout(700);

R.panelOpen = await page.evaluate(() => document.getElementById('syspanel').classList.contains('open'));
R.sections = await page.locator('#syspanel-body .sys-section-title').allInnerTexts();
R.cfgCards = await page.locator('#syspanel-body .cfg-card').count();
R.cfgNames = await page.locator('#syspanel-body .cfg-card .cfg-name').allInnerTexts();
R.cfgPaths = await page.locator('#syspanel-body .cfg-card .cfg-path').allInnerTexts();
R.cfgMeta = await page.locator('#syspanel-body .cfg-card .cfg-meta').allInnerTexts();
R.deptBlocks = await page.locator('#syspanel-body .dept-manage').count();
R.doneItems = await page.locator('#syspanel-body .sys-task').count();
R.panelText = (await page.locator('#syspanel-body').innerText()).length;

// 关键：内联 onclick 需要的函数是否挂在全局
R.globals = await page.evaluate(() => ({
  openCfgModal: typeof window.openCfgModal,
  closeCfgModal: typeof window.closeCfgModal,
  deleteTask: typeof window.deleteTask,
  openPanel: typeof window.openPanel,
  inlineOnclicks: Array.from(document.querySelectorAll('#syspanel-body [onclick]'))
    .map(e => (e.getAttribute('onclick') || '').split('(')[0]).slice(0, 8)
}));

// 点第一张卡 → 观察弹窗
const errBefore = errs.length;
await page.locator('#syspanel-body .cfg-card').first().click({ timeout: 5000 });
await page.waitForTimeout(800);
R.modalAfterClick = await page.evaluate(() => ({
  cls: document.getElementById('cfg-modal').className,
  display: getComputedStyle(document.getElementById('cfg-modal')).display,
  visible: document.getElementById('cfg-modal').offsetHeight > 0,
  title: document.getElementById('cfg-modal-title').textContent
}));
R.clickErrors = errs.slice(errBefore);

// 逐张卡片核对源文本（不依赖弹窗是否打开）
R.sources = await page.evaluate(() => {
  return ['SOUL.md', 'IDENTITY.md', 'USER.md', 'MEMORY.md'].map(n => {
    const el = document.getElementById('cfg-' + n);
    return { name: n, exist: !!el, chars: el ? el.textContent.length : -1,
             h1: el ? (el.textContent.match(/^#\s/m) ? 1 : 0) : -1 };
  });
});

// 清掉面板
await page.evaluate(() => { const c = document.getElementById('syspanel-close'); if (c) c.click(); });
await page.waitForTimeout(300);
R.panelClosed = await page.evaluate(() => !document.getElementById('syspanel').classList.contains('open'));
R.consoleErrors = errs.filter(e => !/Shader Error|WebGL|GPU stall|Unable to get browser|tasks\.js|inbox_tasks\.js/i.test(e));

await page.screenshot({ path: '_shots/syspanel_check.png' });
await browser.close();

console.log('===== 系统设置面板 · 生效性校验 =====');
console.log('目标:', URL, '\n');
console.log('① 「⚙ 系统」按钮存在      :', R.btnExists === 1 ? '✅ 1 个' : '❌ ' + R.btnExists);
console.log('② 点击后面板打开          :', R.panelOpen ? '✅ 是' : '❌ 否');
console.log('③ 面板分区标题            :', R.sections.join('  |  '));
console.log('④ 人格配置卡片数          :', R.cfgCards, R.cfgCards === 4 ? '✅' : '⚠️ 期望 4');
console.log('⑤ 部门任务管理区块        :', R.deptBlocks, '  ⑥ 已完成条目:', R.doneItems);
console.log('⑦ 面板正文渲染字符数      :', R.panelText);
console.log('');
console.log('--- 配置卡片清单（卡片上标注的信息） ---');
R.cfgNames.forEach((n, i) => {
  console.log('   ' + n.replace(/\n/g, '  ⁄  '));
  console.log('       路径: ' + R.cfgPaths[i] + '    ' + R.cfgMeta[i]);
});
console.log('');
console.log('--- 内联 onclick 依赖的全局函数 ---');
Object.entries(R.globals).forEach(([k, v]) => {
  if (k === 'inlineOnclicks') return;
  console.log('   window.' + k.padEnd(14) + ' = ' + v + (v === 'undefined' ? '   ❌ 未挂全局' : '   ✅'));
});
console.log('   内联 onclick 调用:', R.globals.inlineOnclicks.join(', '));
console.log('');
console.log('--- 点第 1 张卡片后的弹窗状态 ---');
console.log('   class =', JSON.stringify(R.modalAfterClick.cls),
            '| display =', R.modalAfterClick.display,
            '| 可见 =', R.modalAfterClick.visible ? '是' : '否');
console.log('   新增报错:', R.clickErrors.length ? R.clickErrors.map(e => e.slice(0, 150)).join(' ;; ') : '无');
console.log('');
console.log('--- 内嵌配置源文本（弹窗正文来源）---');
R.sources.forEach(s => console.log(`   ${s.name.padEnd(12)} 存在:${s.exist ? '✅' : '❌'}  ${s.chars} 字`));
console.log('');
console.log('⑧ 关闭面板后状态          :', R.panelClosed ? '✅ 已关闭' : '❌ 未关闭');
console.log('⑨ 控制台错误(已滤GPU噪声) :', R.consoleErrors.length === 0 ? '✅ 0' : R.consoleErrors.length + ' 条');
R.consoleErrors.slice(0, 5).forEach(e => console.log('     ·', e.slice(0, 160)));
console.log('\n截图: _shots/syspanel_check.png');
