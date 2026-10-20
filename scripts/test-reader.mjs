import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const portalDir = process.env.ORGPORTAL_DIR || fileURLToPath(new URL('../../OrgPortal', import.meta.url));
const base = process.env.DEISM_TEST_BASE || 'http://127.0.0.1:8878';
assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname), 'Use a local test server');
const artifacts = resolve(portalDir, 'web/.local/deism-clickthrough');
mkdirSync(artifacts, { recursive: true });
const { chromium } = createRequire(pathToFileURL(resolve(portalDir, 'web/package.json')))('@playwright/test');
const browser = await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/google-chrome', headless:true, args:['--no-sandbox']});
try {
 const page = await browser.newPage();
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 for (const width of [1280, 820, 390, 320]) {
  await page.setViewportSize({width,height:900});
  await page.goto(base+'/book_of_doctrine/');
  await page.waitForFunction(()=>document.querySelector('#overview-tree a'));
  assert.equal(await page.locator('#overview-panel').isVisible(),width>=1100);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow at ${width}`);
  if(width===820)assert.ok(await page.locator('.reading-column').evaluate(x=>x.clientWidth)>600);
  for(const colorScheme of ['light','dark']) {
   await page.emulateMedia({colorScheme});
   await page.locator('article img').evaluateAll(xs=>Promise.all(xs.map(x=>x.decode())));
  }
  await page.emulateMedia({colorScheme:'light'});
  if(width<1100)await page.locator('#contentsToggle').click();
  await page.locator('#overview-tree a[href="/book_of_doctrine/introduction.html"]').click();
  await page.waitForURL(/introduction/);
  await page.waitForFunction(()=>document.querySelector('#overview-tree a'));
  assert.equal(await page.locator('#overview-panel').isVisible(),width>=1100);
  assert.ok((await page.locator('article').innerText()).includes('Children of Abraham'));
  assert.ok(!(await page.locator('article').innerText()).includes('Cosmological Topology'));
  await page.locator('.reader-more summary').click();
  assert.ok(await page.getByRole('link',{name:'Hadith',exact:true}).isVisible());
  await page.locator('.reader-more summary').click();
  await page.locator('#navSearchInput').fill('annihilation');
  await page.waitForSelector('#navSearchResults button');
  await page.locator('#navSearchInput').press('Enter');
  await page.waitForURL(/annihilation/);
  await page.screenshot({path:resolve(artifacts, `reader-${width}.png`),fullPage:true});
  console.log(`PASS reader contents, chapter selection, search, images and reflow at ${width}px`);
 }
 assert.deepEqual(errors,[]);
} finally {await browser.close();}
