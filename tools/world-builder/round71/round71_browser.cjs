const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

async function main(){
  const [url,output]=process.argv.slice(2);
  const browser=await chromium.launch({executablePath:process.env.HD_CHROMIUM||'/usr/bin/chromium'});
  try{
    const page=await browser.newPage({viewport:{width:412,height:850},acceptDownloads:true});
    page.setDefaultTimeout(20000);
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    const field=id=>page.locator('#'+id);
    const status=text=>field('status').filter({hasText:text}).waitFor();
    const click=id=>field(id).click();
    await page.goto(url);
    await page.waitForFunction(()=>document.querySelector('#template')?.options.length>0);
    await click('create');await status('Area created');
    await page.locator('details').filter({has:field('round71MakeGrid')}).locator('summary').click();
    await field('round71First').fill('10001');
    await field('round71Rows').fill('4');
    await field('round71Columns').fill('4');
    await field('round71Prefix').fill('HollowDeep Wilds');
    await field('round71Direction').selectOption('up');
    await click('round71MakeGrid');await status('Wilderness region created: 16 rooms');
    let draft=JSON.parse(await field('json').inputValue());
    assert.equal(draft.rooms.length,18);
    const entry=draft.rooms.find(x=>x.room_id===10001);
    assert.equal(entry.name,'HollowDeep Wilds 1,1');
    assert(entry.exits.some(e=>e.direction==='down'&&e.destination===14));
    assert(entry.exits.some(e=>e.direction==='east'&&e.destination===10002));
    assert(entry.exits.some(e=>e.direction==='south'&&e.destination===10005));
    console.log('ROUND 71: browser grid created reciprocal 4x4 region PASS');

    const initial=await field('json').inputValue();
    await field('round71First').fill('10001');
    await click('round71MakeGrid');await status('ERROR:');
    assert.equal(await field('json').inputValue(),initial);
    console.log('ROUND 71: browser duplicate room rejected without draft mutation PASS');

    await field('name').fill('Unapplied wilderness edit');
    page.once('dialog',dialog=>dialog.dismiss());
    await field('round71First').fill('10100');
    await click('round71MakeGrid');await status('Action cancelled');
    assert.equal(await field('name').inputValue(),'Unapplied wilderness edit');
    assert.equal(await field('json').inputValue(),initial);
    console.log('ROUND 71: browser dirty-state protection PASS');

    // Reset, generate again, and download the exported ZIP from the browser.
    await page.reload();
    await page.waitForFunction(()=>document.querySelector('#template')?.options.length>0);
    await click('create');await status('Area created');
    await page.locator('details').filter({has:field('round71MakeGrid')}).locator('summary').click();
    await field('round71First').fill('10001');
    await field('round71Rows').fill('4');
    await field('round71Columns').fill('4');
    await field('round71Prefix').fill('HollowDeep Wilds');
    await field('round71Direction').selectOption('up');
    await click('round71MakeGrid');await status('Wilderness region created: 16 rooms');
    draft=JSON.parse(await field('json').inputValue());
    await click('validatePlan');await status('18 rooms validated');
    await click('export');
    const link=field('download').locator('a');
    await link.waitFor();
    const href=await link.getAttribute('href');
    assert(href.startsWith('/api/download?id='));
    const response=await page.request.get(url+href);
    assert.equal(response.status(),200);
    await fs.writeFile(path.join(output,'round71-browser.zip'),await response.body());
    await fs.writeFile(path.join(output,'round71-browser.json'),JSON.stringify({plan:draft}));
    assert.equal(errors.length,0,errors.join('\n'));
    console.log('ROUND 71: browser native ZIP export and existing validation PASS');
    await click('create'); await status('Area created');
    await field('round71Prefix').fill('Copperreach');
    await field('wildernessSeed').fill('42');
    await click('round71MakeGrid'); await status('Wilderness region created: 16 rooms');
    await field('wildernessPreview').locator('summary').click();
    assert.match(await field('wildernessGrid').innerText(), /Copperreach · column 1, row 1[\s\S]*@/);
    await field('wildernessLandmark').fill('Copper Cairn');
    await field('wildernessTerrain').selectOption('ruins');
    await click('saveWilderness'); await status('Wilderness metadata validated');
    assert.match(await field('wildernessGrid').innerText(), /Landmark: Copper Cairn/);
    await click('export');
    await link.waitFor();
    await page.waitForFunction(previous => {
      const current = document.querySelector('#download a')?.getAttribute('href');
      return current && current !== previous;
    }, href);
    const mapped = await page.request.get(url + await link.getAttribute('href'));
    assert.equal(mapped.status(),200);
    await fs.writeFile(path.join(output,'round72-browser.zip'),await mapped.body());
    assert.equal(errors.length,0,errors.join('\n'));
    console.log('ROUND 72: seeded terrain, map preview, landmark and browser ZIP PASS');
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exit(1)});
