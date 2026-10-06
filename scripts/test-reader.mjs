import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const { chromium } = createRequire(new URL('../../OrgPortal/web/package.json', import.meta.url))('@playwright/test');
const browser = await chromium.launch({executablePath:'/usr/bin/google-chrome', args:['--no-sandbox']});
try {
 const page = await browser.newPage();
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
 for (const width of [1280, 820, 390, 320]) {
  await page.setViewportSize({width,height:900});
  await page.goto('http://127.0.0.1:8878/book_of_doctrine/');
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
  await page.screenshot({path:new URL(`../../OrgPortal/web/.local/deism-clickthrough/reader-${width}.png`, import.meta.url).pathname,fullPage:true});
  console.log(`PASS reader contents, chapter selection, search, images and reflow at ${width}px`);
 }
 assert.deepEqual(errors,[]);
} finally {await browser.close();}
