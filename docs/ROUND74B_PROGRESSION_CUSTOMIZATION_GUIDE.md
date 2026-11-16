# HollowDeep Round 74B — Customize XP, Stats, Classes and Rebirth

**Development guide only.** These instructions change private test configurations, not live character rules.

## Step 1: Open the progression folder

In a separate Git checkout of the Round 74B development branch, open `tools/world-builder/round74/` in VS Code Remote SSH. You will see:

- `progression.sample.json`: development-only test settings
- `preview_xp.py`: XP table printer, with 32-bit overflow checks
- `hd74_progression.h` and `.c`: native C model / API
- `test_progression.c`: stat, XP, remort, class access and Legacy Points tests
- `test_native_abi.c`: ELF32 compatibility with the existing Mordor character layout
- `run.sh`: focused standalone tests

## Step 2: Copy the example, do not modify the live game

```bash
cd tools/world-builder/round74
cp progression.sample.json progression.playtest.json
```

Edit `progression.playtest.json` with VS Code. The starting example has:

```json
{
  "status": "DEVELOPMENT_ONLY_NOT_ACTIVE",
  "level_cap": 60,
  "xp_base": 1000,
  "xp_growth": 50,
  "stat_base": 10,
  "stat_max": 18,
  "starting_points": 20,
  "remort_kills": 3,
  "remort_seconds": 180,
  "points_per_remort": 2,
  "legacy_points_cap": 10
}
```

Do not alter the `status` field: the preview requires this exact development-only value, so it cannot be mistaken for live configuration.

## Step 3: Preview the XP curve

```bash
python3 preview_xp.py progression.playtest.json > xp-preview.tsv
head -n 12 xp-preview.tsv
tail -n 5 xp-preview.tsv
```

Formula used by the Round 74A model:

```text
total_xp(level) = xp_base * (level - 1)^2 + xp_growth * (level - 1)^3
```

`xp_base` increases early-level XP requirements; `xp_growth` increasingly raises higher-level requirements. The preview rejects settings whose totals exceed **2,147,483,647** (the signed 32-bit `long` used by the legacy game). A reported level cap of 60 is a development example, not an active HollowDeep cap.

## Step 4: Customize starting stats safely

`stat_base` defines the initial value for each of STR, DEX, CON, INT and PIETY. `starting_points` is the additional pool distributed before play; `stat_max` is the per-stat limit. A valid pool must fit within `5 * (stat_max - stat_base)`.

The original `command1.c` instead uses five manually typed values totaling no more than **54**, each from **3 to 18**. Replacing that behavior requires a native hook and a legacy migration decision; changing JSON alone does not update character creation.

## Step 5: Rebirth and class inheritance

`remort_kills` sets the required number of distinct verified kill events in the development model; `remort_seconds` is the quest deadline. A valid remort awards `points_per_remort`, limited by `legacy_points_cap`. Class inheritance only takes effect after a validated successful rebirth. Divine Favor is separate from Legacy Points.

Before activating rebirth in the MUD, the native hooks must prove: real authenticated player identity, exact monster instance/template, server-side time/deadline, replay-resistant events, correct class skill mapping and an **atomic progression+inventory+gold save**. A CRC-only progression snapshot is not proof of authority.

**Permanent Legacy equipment:** never implement it using a native `No Save` flag until that flag's actual serializer behavior is verified. Purchased equipment must be character-bound, saved as a real native object and denied on drop, trade and sale.

## Step 6: Run the focused progression tests

```bash
bash run.sh
# On a Linode with the actual disposable native C source and gcc -m32:
HD_TEST_ELF32=1 HD_SANITIZE=0 bash run.sh /absolute/path/to/private-native-src
```

This is a **model/ABI test**, not a substitute for actual 32-bit gameplay, save/reload and rebirth regressions after the code is hooked.

## Step 7: Where the live-game hooks will go

| Gameplay feature | Native source file(s) |
|---|---|
| Initial stat choices and class | `command1.c` |
| XP and training | `command7.c`, `global.c`, `misc.c`, `hollowdeep.c` |
| Level-up effects | `player.c`, `command4.c` |
| Trusted monster-kill event | `creature.c` |
| Commands and permissions | `global.c`, `mextern.h`, new guarded command source |
| Class/spell restrictions | `magic*.c`, relevant `command*.c` |
| Persistent rebirth/Legacy data | `hd_player_store.c`, `files2.c`, receipt/progression codecs |
| Build | `Makefile` |

Only change these after inspecting the exact call sites. On this legacy engine, a command addition needs a tested registry entry, correct dispatch number, function declaration, object-list inclusion and an in-game help entry. A data-only JSON edit does not add a command.

## Step 8: Safe publishing

Keep playtest JSON, generated XP tables, player data, fixtures and any credentials private until reviewed. Publish tested source, public documentation and changelogs to GitHub. Update the public PHP website and Discord guide only when describing the feature's verified state—**development** until it is deployed. Do not restart the live MUD without explicit authorization after all native integration checks.
