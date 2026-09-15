// playwright 验证：8 间房门交互 + 截图
import { chromium } from 'playwright';

const zones = ['ceo','cro','coo','meeting','cpo','cto','cfo','cmo'];
const out = (z) => `C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/v5_${z}.png`;
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();

page.on('console', msg => {
  const t = msg.text();
  if (t.includes('✅') || t.includes('❌') || t.includes('⚠️') || t.includes('Error') || t.includes('zone')) {
    console.log('[browser]', t);
  }
});

const report = {};
for (const z of zones) {
  try {
    await page.goto(`http://127.0.0.1:8934/office-3d-taskboard.html?zone=${z}`, { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => !!window.__boardDebug, { timeout: 15000 });
    await page.waitForTimeout(7000);
    const ok = await page.evaluate((zz) => {
      const dbg = window.__boardDebug;
      const g = dbg.doorGroups[zz];
      const pick = dbg.doorPickables.filter(m => m.userData && m.userData.isDoor && m.userData.zoneId === zz).length;
      return {
        hasGroup: !!g,
        isOpen: g ? g.userData.isOpen : null,
        pickableDoors: pick,
        pivotRotation: g ? g.rotation.y.toFixed(2) : null,
      };
    }, z);
    await page.screenshot({ path: out(z), fullPage: false });
    report[z] = { ...ok, screenshotSize: 0 };
    const stat = await import('fs').then(fs => fs.statSync(out(z)));
    report[z].screenshotSize = stat.size;
  } catch (e) {
    report[z] = { error: e.message };
  }
}

console.log('\n=== 8 间房门状态 ===');
for (const [z, s] of Object.entries(report)) {
  if (s.error) {
    console.log(`  ${z.padEnd(8)} ❌ ${s.error}`);
  } else {
    console.log(`  ${z.padEnd(8)} 门扇=${s.hasGroup ? '✅' : '❌'}  命中数=${s.pickableDoors}  状态=${s.isOpen}  pivot r=${s.pivotRotation}  截图=${(s.screenshotSize/1024).toFixed(0)}KB`);
  }
}

// === 模拟点击 CEO 门 ===
console.log('\n=== 模拟点击 CEO 门（验证 toggleDoor 切换 isOpen） ===');
await page.goto('http://127.0.0.1:8934/office-3d-taskboard.html?zone=ceo', { waitUntil: 'load' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 15000 });
await page.waitForTimeout(7000);

const before = await page.evaluate(() => ({
  isOpen: window.__boardDebug.doorGroups.ceo.userData.isOpen,
  targetOpen: window.__boardDebug.doorGroups.ceo.userData.targetOpen,
}));
await page.evaluate(() => window.__boardDebug.toggleDoor('ceo'));
await page.waitForTimeout(2500);  // 等动画完成
const after = await page.evaluate(() => ({
  isOpen: window.__boardDebug.doorGroups.ceo.userData.isOpen,
  targetOpen: window.__boardDebug.doorGroups.ceo.userData.targetOpen,
  leafRotY: window.__boardDebug.doorGroups.ceo.userData.leaves.map(l => l.rotation.y.toFixed(2)),
}));
console.log('  切换前:', JSON.stringify(before));
console.log('  切换后:', JSON.stringify(after));
await page.screenshot({ path: 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/v5_ceo_open.png', fullPage: false });

// 再次 toggle（关）
await page.evaluate(() => window.__boardDebug.toggleDoor('ceo'));
await page.waitForTimeout(2500);
const closed = await page.evaluate(() => ({
  isOpen: window.__boardDebug.doorGroups.ceo.userData.isOpen,
  leafRotY: window.__boardDebug.doorGroups.ceo.userData.leaves.map(l => l.rotation.y.toFixed(2)),
}));
console.log('  再次切换（关）后:', JSON.stringify(closed));

await browser.close();
console.log('\n截图存到 _shots/v5_*.png');