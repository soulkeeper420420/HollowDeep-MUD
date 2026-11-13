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
    await status("Catalogs loaded");
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
    await status("Catalogs loaded");
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
    await status("Catalogs loaded");
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
