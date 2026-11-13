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
    const page = await browser.newPage({ viewport: { width: 412, height: 850 } });
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
    await click("saveDraft");
    await status("Draft saved in this browser");
    await page.reload();
    await status("Catalogs loaded");
    await click("openDraft");
    await status("Draft reopened");
    assert.equal(await field("name").inputValue(), "Round 59 Forge");
    assert.equal(await field("shortDescription").inputValue(), "The forge bell rings softly.");
    assert.equal(await field("longDescription").inputValue(), "A quiet anvil marks the isolated forge.");
    assert.match(await field("monsters").innerText(), /ID 1/);
    assert.match(await field("objects").innerText(), /ID 1/);
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
