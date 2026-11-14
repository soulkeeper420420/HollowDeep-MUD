const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const [url, output] = process.argv.slice(2);
  const browser = await chromium.launch({
    executablePath: process.env.HD_CHROMIUM || "/usr/bin/chromium"
  });
  try {
    let page = await browser.newPage({ viewport: { width: 412, height: 850 } });
    page.setDefaultTimeout(15000);
    const errors = [];
    page.on("pageerror", error => errors.push(error));
    const field = id => page.locator("#" + id);
    const status = text => field("status").filter({ hasText: text }).waitFor();
    const click = id => field(id).click();
    await page.goto(url);
    await page.waitForFunction(() => {
 const picker=document.getElementById("template");
 return picker && picker.options.length>0;
});
    await click("create");
    await status("Area created");
    await field("name").fill("Round 59 Forge");
    await field("shortDescription").fill("The forge bell rings softly.");
    await field("longDescription").fill("A quiet anvil marks the isolated forge.");
    await click("save");
    await status("Room changes validated");
    await click("link");
    await status("Reciprocal connection created");
    assert.match(await field("exits").innerText(), /north → 15/);
    await page.getByRole("button", { name: /^15 · / }).click();
    assert.match(await field("exits").innerText(), /south → 14/);
    await field("name").fill("Round 59 Gallery");
    await click("save");
    await status("Room changes validated");
    await page.getByRole("button", { name: /^14 · / }).click();
    for (const type of ["monsters", "objects"]) {
      await field("type").selectOption(type);
      await field("template").selectOption("1");
      await click("place");
      await status("Placement validated");
      await field(type).filter({ hasText: "ID 1 · count 1 · respawn 60" }).waitFor();
    }
    const legacy = await field("json").inputValue();
    await page.evaluate(plan => localStorage.setItem(
      "hollowdeep.world-builder.draft", JSON.stringify({ plan, selected: 15 })
    ), JSON.parse(legacy));
    await field("draftName").fill("Forge export");
    await click("saveDraft");
    await status("Draft saved in this browser");
    await field("name").fill("Alternate Forge");
    await click("save");
    await status("Room changes validated");
    await page.getByRole("button", { name: /^15 · / }).click();
    await field("draftName").fill("Alternate route");
    await click("saveDraft");
    await status("Draft saved in this browser");
    await field("draftName").fill("Forge export");
    page.once("dialog", dialog => dialog.dismiss());
    await click("saveDraft");
    await page.reload();
    await page.waitForFunction(() => {
 const picker=document.getElementById("template");
 return picker && picker.options.length>0;
});
    await field("savedDraft").selectOption({ label: "Round 60 draft" });
    await click("openDraft");
    await status("Draft reopened");
    assert.equal(await field("selected").innerText(), "Room 15");
    assert.equal(await field("draftName").inputValue(), "");
    assert.equal(await field("json").inputValue(), legacy);
    console.log("PASS: Round 60 draft reopens with its original plan and room");
    await field("savedDraft").selectOption({ label: "Alternate route" });
    await click("openDraft");
    await status("Draft reopened");
    assert.equal(await field("selected").innerText(), "Room 15");
    await page.getByRole("button", { name: /^14 · / }).click();
    assert.equal(await field("name").inputValue(), "Alternate Forge");
    await field("savedDraft").selectOption({ label: "Forge export" });
    await click("openDraft");
    await page.waitForFunction(() => document.getElementById("name").value === "Round 59 Forge");
    assert.equal(await field("selected").innerText(), "Room 14");
    console.log("PASS: Named drafts remain independent after reload");
    assert.equal(await field("name").inputValue(), "Round 59 Forge");
    assert.equal(await field("shortDescription").inputValue(), "The forge bell rings softly.");
    assert.equal(await field("longDescription").inputValue(), "A quiet anvil marks the isolated forge.");
    assert.match(await field("monsters").innerText(), /ID 1/);
    assert.match(await field("objects").innerText(), /ID 1/);
    const beforeTransfer = JSON.parse(await field("json").inputValue());
    const [draftDownload] = await Promise.all([page.waitForEvent("download"), click("exportDraft")]);
    const filename = path.join(output, "transfer.json");
    await draftDownload.saveAs(filename);
    const originalPage = page;
    page = await browser.newPage();
    page.setDefaultTimeout(15000);
    page.on("pageerror", error => errors.push(error));
    await page.goto(url);
    await page.waitForFunction(() => {
 const picker=document.getElementById("template");
 return picker && picker.options.length>0;
});
    assert.equal(await field("savedDraft").locator("option").count(), 1);
    await field("importDraft").setInputFiles(filename);
    await status("Draft imported");
    assert.deepEqual(JSON.parse(await field("json").inputValue()), beforeTransfer);
    assert.equal(await field("draftName").inputValue(), "Forge export");
    assert.equal(await field("selected").innerText(), "Room 14");
    assert.equal(await field("savedDraft").locator("option").count(), 1);
    const invalid = JSON.parse(await fs.readFile(filename, "utf8"));
    invalid.plan.rooms[0].exits[0].destination = 32767;
    await field("importDraft").setInputFiles({
      name: "invalid.json", mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(invalid))
    });
    await status("ERROR:");
    assert.deepEqual(JSON.parse(await field("json").inputValue()), beforeTransfer);
    assert.equal(await field("savedDraft").locator("option").count(), 1);
    assert.equal(await originalPage.locator("#savedDraft option").count(), 4);
    await click("saveDraft");
    await status("Draft saved in this browser");
    console.log("PASS: Draft JSON transfers to a fresh browser; invalid imports preserve the current and saved drafts");
// Round 63: validated editing and recovery regression.
{
 const original=JSON.parse(await field("json").inputValue());
 const originalRoom=original.rooms[0];
 const roomButton=page.locator("#rooms button").first();
 await roomButton.click();

 const beforeName=await field("name").inputValue();
 const newName="Round 63 Recovery Test";

 await field("name").fill(newName);
 await click("save");
 await status("Room changes validated");

 await click("round63Undo");
 await status("Undo complete");
 assert.equal(await field("name").inputValue(),beforeName);

 await click("round63Redo");
 await status("Redo complete");
 assert.equal(await field("name").inputValue(),newName);

 // Unsaved text must survive refresh in the correct room.
 await field("shortDescription").fill("Round 63 unsaved recovery");
 await page.reload();
   await page.waitForFunction(() => {
    const room=document.getElementById("selected");
    const description=document.getElementById("shortDescription");
    return room?.textContent==="Room 14" &&
      description?.value==="Round 63 unsaved recovery";
   });
 assert.equal(
  await field("shortDescription").inputValue(),
  "Round 63 unsaved recovery"
 );

  await click("save");
  await status("Room changes validated");
  assert.equal(
    JSON.parse(await field("json").inputValue()).rooms[0].short_description,
    "Round 63 unsaved recovery"
  );
  console.log("ROUND 63: recovered description saved PASS");



 await field("json").evaluate(el=>{
  const details=el.closest("details");
  if(details)details.open=true;
 });


 // Round 63: unsaved text must not leak into another room.
 const room14=JSON.parse(await field("json").inputValue()).rooms[0];
 const room15=JSON.parse(await field("json").inputValue()).rooms[1];

 await page.locator("#rooms button").first().click();
 await field("shortDescription").fill("Round 63 room isolation marker");

 await page.locator("#rooms button").nth(1).click();
 assert.equal(await field("shortDescription").inputValue(),
              room15.short_description??"");

 await page.reload();
 await page.waitForFunction(() => {
  const room=document.getElementById("selected");
  const description=document.getElementById("shortDescription");
  return document.querySelectorAll("#rooms button").length===2 &&
    room?.textContent==="Room 15" &&
    description?.value!=="Round 63 room isolation marker";
 });

 assert.equal(await field("shortDescription").inputValue(),
              room15.short_description??"");

 assert.notEqual(await field("shortDescription").inputValue(),
                 "Round 63 room isolation marker");

 await page.locator("#rooms button").first().click();
 assert.equal(await field("shortDescription").inputValue(),
              room14.short_description??"");

 console.log("ROUND 63: cross-room recovery isolation PASS");

 // Reopen Advanced JSON after the recovery refresh.
 await field("json").evaluate(el=>{
  const details=el.closest("details");
  if(details)details.open=true;
 });
 await field("json").waitFor({state:"visible"});

 // Invalid Advanced JSON must not replace the active plan.
 const beforeInvalid=JSON.parse(await field("json").inputValue());
 const invalid=structuredClone(beforeInvalid);
 invalid.rooms[0].exits[0].destination=32767;
 await field("json").fill(JSON.stringify(invalid));
 await click("applyJson");
 await status("ERROR:");
 await field("json").fill(JSON.stringify(beforeInvalid));

 // Restore the original plan through validated JSON.
 const exportPlan=structuredClone(original);
  exportPlan.rooms[0].short_description="Round 63 unsaved recovery";
  await field("json").fill(JSON.stringify(exportPlan));
  await click("applyJson");
 await status("JSON applied locally");

 const restored=JSON.parse(await field("json").inputValue());
 assert.deepEqual(restored,exportPlan);
  assert.equal(restored.rooms[0].short_description,
               "Round 63 unsaved recovery");
 console.log("ROUND 63: browser reliability checks PASS");
}

await click("validatePlan");
    await status("PASS: 2 rooms validated");
    await click("export");
    const link = page.getByRole("link", { name: "Download validated native ZIP" });
    await link.waitFor();
    const result = JSON.parse(await field("status").innerText());
    const plan = JSON.parse(await field("json").inputValue());
    assert.equal(plan.rooms.length, 2);
    const [download] = await Promise.all([page.waitForEvent("download"), link.click()]);
    await download.saveAs(path.join(output, "browser.zip"));
    await fs.writeFile(path.join(output, "browser.json"), JSON.stringify({ plan, result }));
    assert.deepEqual(errors, []);
    console.log("PASS: Browser created, saved, reopened, validated and downloaded the two-room area");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
