# Levels, experience and the next progression release

Status: source investigation and proposals, November 6, 2026. **No XP curve, training price, level cap, death penalty, class or remort rule is changed by this guide or the help/staff release.** The accompanying [CSV](XP_CURVE_PROPOSALS.csv) is a balancing worksheet, not an installer.

## What the running engine's source does

Mordor stores cumulative experience. Training increases level by one and spends gold; it does **not** spend XP. A character needs the correct class training room, sufficient total XP and gold, and the normal authorization/condition checks. `hclass progress` reports those requirements.

`global.c` defines 25 values in `needed_exp`; `mtype.h` calls its size `MAXALVL=25`. This is an array boundary, **not a level cap**. `train()` in `command7.c` uses entries 0–23 for training from levels 1–24. At current level 25 and above it instead requires `15,000,000 × current_level` total XP. The last entry is used as that coefficient; its 15 million is never the standalone threshold for level 26. `exp_to_lev()` in `misc.c` uses the corresponding extrapolation after reaching level 25, including a literal minimum of 25.

The result is a large discontinuity. Level 25 requires 8,874,375 total XP. Level 26 requires 375,000,000, an additional **366,125,625 XP**. The training fee is half the destination's total threshold: **187,500,000 gold** for 25→26. Every training payment is charged separately. A modest XP event does not correct this curve or the accumulating gold cost.

## Concrete comparison

“Level” below is the destination level. XP columns are cumulative; the final column is additional XP since the previous level. The steady proposal retains every threshold through level 25.

| Level | Current total XP | Current fee to train into level | Proposed steady total XP | Proposed steady step XP |
| --- | ---: | ---: | ---: | ---: |
| 2 | 512 | 256 | 512 | 512 |
| 10 | 100,000 | 50,000 | 100,000 | 34,464 |
| 20 | 2,799,000 | 1,399,500 | 2,799,000 | 595,543 |
| 24 | 7,319,072 | 3,659,536 | 7,319,072 | 1,526,411 |
| 25 | 8,874,375 | 4,437,187 | 8,874,375 | 1,555,303 |
| 26 | 375,000,000 | 187,500,000 | 10,585,375 | 1,711,000 |
| 30 | 435,000,000 | 217,500,000 | 19,328,375 | 2,508,000 |
| 40 | 585,000,000 | 292,500,000 | 63,325,375 | 6,512,000 |
| 50 | 735,000,000 | 367,500,000 | 177,534,375 | 16,900,000 |

The [complete level 1–50 worksheet](XP_CURVE_PROPOSALS.csv) includes three proposals. None is a measured target for hours of play. Real pacing depends on available encounters, contribution shares, downtime, death, grouping and gold income.

## Recommended curve and rollout

Use one explicit cumulative table with a separate, named player-level cap. Preserve levels 1–25 initially and prototype a **level 30 content milestone**. Expand tested content to 40, then 50 after observing class balance. Do not call 30 a newly increased engine cap: the original has no equivalent clean cap. Check existing character levels before introducing one; never downgrade a player above a proposed cap.

Let `T[L]` be total XP to reach level L and `D[L] = T[L] - T[L-1]`. Start with the actual final ordinary step `D[25] = 1,555,303`. For L≥26:

```text
D[L] = round UP to the next 1,000 of D[L-1] × growth
T[L] = T[L-1] + D[L]
```

The worksheet uses growth 1.08 (gentle), 1.10 (steady, recommended prototype), and 1.15 (long). It uses integer rounding at every step, not one floating-point exponent. This is additional-XP growth, not multiplying cumulative XP. All modeled totals through 50 fit signed 32-bit XP, but that alone does not make high-level play safe.

Separate training fees from cumulative XP. The worksheet illustrates `min(250,000, max(100, ceil(D[L] / 10)))` gold for each training step after level 1. This is a hypothesis for playtesting, including lower-level price changes, **not an agreed live price**. Compare fee and repair/consumable spending with normal gold earned per level. Setting a fee from cumulative XP repeatedly charges for earlier progress and can become the dominant grind.

Measure solo and group runs for all ten classes at representative levels. Record net XP/gold per active hour, encounter difficulty, deaths, trainer travel, consumable cost and event uptime. Estimate time as additional XP / measured effective XP per hour, then validate by actual play. Target ranges could begin at 10–30 minutes for early levels, 45–120 minutes for midgame and several sessions for endgame; tune to the host's preferred pace after measurement.

## Engine work required before raising supported levels

| Finding in prepared original source | Required work |
| --- | --- |
| `mstruct.h`: level, class, primary stats and room level gates are `char`; HP/mana are `short`; XP/gold/proficiencies are `long`. On the supported x86 ELF32 build these have narrow ranges. | Validate levels/stats before indexing or arithmetic. Do not widen the serialized fields casually: player, monster and room files contain raw structures. Signed char level 127 is a representation boundary, not a supported design target. |
| `global.c`: `bonus[35]` is indexed directly by stats throughout combat/magic. `up_level()` repeatedly adds stats without a general bound. | Centralize bounded stat lookup and define a stat cap/soft cap. A stat of 35 is already outside this array. Include equipment, blessings and temporary effects; the level at which a stat reaches that boundary varies by character. |
| `player.c`: `compute_thaco()` reuses level-20 entries above 20; titles have eight tiers ending at levels 22+. | Decide whether later progression changes accuracy, unlocks mechanics or primarily adds content. Extend titles intentionally. More level numbers do not automatically provide new combat mechanics. |
| `player.c`: monk `up_level()` cases 21–25 fall through to the default 1d3 damage. The downgrade table differs from the upgrade table. | Replace duplicated monk switches with one tested lookup; test up/down round trips and existing characters. Fix this before marketing higher levels. |
| Training, `info`, `hclass progress`, `exp_to_lev`, death recovery and drain effects each use progression assumptions. | Route every caller through shared threshold/level/fee helpers. Changing only `needed_exp` or `MAXALVL` leaves inconsistent behavior. |
| Native XP comes from kills, quests, exchanges/kingdom actions and PvP; some additions bypass the new monster-event helper. | Audit every reward and subtraction with 64-bit intermediates, clamp before storing, and validate saves. New event protections do not establish safety for every legacy award path. |
| Healing, spell damage, saves, daily uses and level-difference chances scale separately; monk armor reaches a clamped floor. | Test all class matchups and probabilities at 25, 30, 40 and 50. Document which values cap and which keep growing. |
| `files1.c` and `files3.c` serialize/memcpy native character and world structures. | Preserve the original structure layout for this first progression release. A later wider-data engine needs a separately versioned converter and rollback procedure. |

A good API would expose `xp_threshold(level)`, `level_for_xp(total)`, `training_fee(level)` and one bounded reward function. These names are proposals. Use explicit lengths and validate all indices. Training at the approved cap should return a clear message without charging gold. Decide separately whether XP can accumulate at that cap.

## Death, events and saved characters

Native monster/self-inflicted death normally removes 10% XP below level 4 and 25% afterward, with a higher-level adjustment intended to limit level loss. PvP has separate rules. Rework the adjustment using the same threshold helpers and specify the desired loss policy before deployment. A curve edit must not accidentally turn one death into many level losses.

The current event source allows Moderator/Implementor 1–5× for 1–60 minutes, Admin 1–10× for 1–1,440 minutes and Owner 1–20× for 1–1,440 minutes. It affects monster reward XP and newly generated monster gold, not training prices, quest claims, trade or existing coins. Evaluate at 1× first and stress-test all permitted multipliers. Do not multiply event × remort × rested × party bonuses without a single documented composition and cap policy. A long 20× event will substantially accelerate a curve tuned at 1×.

Before migration, inventory the actual level, XP and gold distribution privately. The live data was not available for this investigation. Recommended first policy: preserve earned level and inventories, and explicitly map progress within that level's old interval into the new interval. Store the old values and curve version in a recoverable migration record. Handle XP banked above the next threshold and characters above the proposed cap as separate reviewed cases; do not silently discard that progress. Alternative raw-XP preservation grants large windfalls when thresholds shrink, and must be a conscious choice. Do not change the default on login without a migration record.

Do not enable remort in the same release as a curve migration. A remort needs a preview, explicit confirmation and a recoverable transaction across character and progression records. Preserve names, login credentials, staff roles and builder ranges independently of combat progress; remort must never grant staff authority. See [remort/class options](PROGRESSION_OPTIONS.md).

## Acceptance checks for a future implementation

- Thresholds are monotonic and below storage limits; each threshold−1, threshold and threshold+1 agrees between displays, training and reverse XP lookup.
- Levels 24→25, 25→26 and the chosen cap work; cap+1, level 0, corrupt negative stats and near-overflow balances cannot read outside tables or charge incorrectly.
- Every class gains and loses the intended stats; monk damage up/down agrees; temporary stat effects stay within lookup bounds.
- A failed training step never spends gold. A successful step increments once, consumes the published fee once and survives save/reload.
- Death, drain and flee losses obey the selected level-loss policy and use the new curve consistently.
- 1×, 5×, 10× and 20× monster rewards, group contribution splits and integer limits cannot wrap or duplicate rewards.
- Migration can resume after interruption and is idempotent. A full private backup restores the exact prior characters and rules.

Use disposable characters and copied worlds for these checks. Current release validation does not certify this proposed progression system.
