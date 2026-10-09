const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const output = process.env.PREVIEW_DIR || '/tmp/infocom-site-preview';
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
    headless: true,
    args: ['--no-sandbox'],
  });
  const url = pathToFileURL(path.resolve(__dirname, '../index.html')).href;
  const errors = [];
  const reports = [];
  try {
    for (const [width, height] of [[1440, 900], [1920, 1080], [1024, 768], [390, 844], [320, 740]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await page.waitForTimeout(200);
      const bounds = await page.evaluate(() => ({
        viewport: innerWidth,
        content: document.documentElement.scrollWidth,
        heroBottom: document.querySelector('.hero').getBoundingClientRect().bottom,
        colored: [...document.querySelector('canvas').getContext('2d').getImageData(0, 0, document.querySelector('canvas').width, document.querySelector('canvas').height).data].filter((x, i) => i % 4 === 3 && x > 0).length,
      }));
      assert(bounds.content <= bounds.viewport, `Page overflow at ${width}: ${JSON.stringify(bounds)}`);
      assert(bounds.heroBottom < height, `No next-section hint at ${width}: ${bounds.heroBottom}`);
      assert(bounds.colored > 500, `Canvas is blank at ${width}`);
      assert.equal(await page.locator('table, #evaluation').count(), 0);
      assert.equal(await page.locator('.hero-links a').count(), 2);
      const sections = await page.locator('main > section[id]').evaluateAll(
        nodes => nodes.map(node => node.id));
      assert.deepEqual(sections, ['overview', 'architecture', 'communication', 'demos', 'resources']);
      for (const link of await page.getByRole('link', { name: 'Code', exact: true }).all()) {
        assert.equal(await link.getAttribute('href'), 'https://github.com/Anonymous-0730/VLA-Fabric/tree/main/code');
      }
      const canvas = page.locator('#fabric-canvas');
      const movingA = await canvas.screenshot();
      await page.waitForTimeout(280);
      const movingB = await canvas.screenshot();
      assert(!movingA.equals(movingB), 'Canvas should animate');
      await page.locator('#motion-toggle').click();
      await page.waitForTimeout(100);
      const pausedA = await canvas.screenshot();
      await page.waitForTimeout(180);
      const pausedB = await canvas.screenshot();
      assert(pausedA.equals(pausedB), 'Pause must freeze the illustration');
      await page.screenshot({ path: path.join(output, `hero-${width}.png`) });

      for (const image of await page.locator('img:not(#dialog-image)').all()) {
        await image.scrollIntoViewIfNeeded();
        await image.evaluate(img => img.decode());
      }
      await page.locator('[data-metric="success_pct"]').click();
      assert.match(await page.locator('.task-chart').last().textContent(), /97\.5/);
      assert.equal(await page.locator('#metric-success').getAttribute('aria-selected'), 'true');
      await page.locator('#metric-success').press('Home');
      assert.equal(await page.locator('#metric-traffic').getAttribute('aria-selected'), 'true');
      await page.locator('#metric-latency').click();
      assert.match(await page.locator('.task-chart').last().textContent(), /126\.2/);
      await page.locator('#communication').screenshot({ path: path.join(output, `communication-${width}.png`) });
      await page.locator('#metric-traffic').click();

      await page.locator('[data-figure]').first().click();
      assert(await page.locator('#figure-dialog').isVisible());
      await page.keyboard.press('Escape');
      assert(!(await page.locator('#figure-dialog').isVisible()));

      for (const id of ['camera', 'stack', 'photo']) {
        await page.locator(`#tab-${id}`).click();
        const video = page.locator(`#demo-${id} video`);
        await video.evaluate(async v => {
          v.muted = true;
          await Promise.race([v.play(), new Promise((_, reject) => setTimeout(() => reject(new Error(`Playback timed out: ${v.currentSrc}, readyState=${v.readyState}`)), 7000))]);
        });
        await page.waitForTimeout(200);
        assert(await video.evaluate(v => v.currentTime > 0 && v.videoWidth > 0), `Video ${id} did not play`);
        await video.evaluate(v => v.pause());
      }
      await page.locator('#tab-camera').click();
      await page.screenshot({ path: path.join(output, `page-${width}.png`), fullPage: true });
      reports.push({ width, height, ...bounds, checks: 'animation, pause, images, tabs, dialog, video' });
      await page.close();
    }
    const reduced = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    await reduced.goto(url);
    await reduced.waitForTimeout(200);
    assert.equal(await reduced.locator('#motion-toggle').getAttribute('aria-pressed'), 'true');
    const a = await reduced.locator('canvas').screenshot();
    await reduced.waitForTimeout(200);
    assert(a.equals(await reduced.locator('canvas').screenshot()));
    await reduced.goto(pathToFileURL(path.resolve(__dirname, '../code/index.html')).href);
    assert.match(await reduced.title(), /^Code/);
    assert.equal(await reduced.locator('a[download]').count(), 5);
    await reduced.screenshot({ path: path.join(output, 'code-mobile.png'), fullPage: true });
    await reduced.close();
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ reports, browserErrors: errors, reducedMotion: 'PASS', codePage: 'PASS', screenshots: output }, null, 2));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
