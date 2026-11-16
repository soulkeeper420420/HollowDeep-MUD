# HollowDeep Round 74B — First-life training prices and five-level XP bank

**Status: isolated private native candidate; no live player/save/website changes.**

## Player rules (requested)

- **Character creation:** the private test build permits up to **65 total** STR/DEX/CON/INT/PIETY points, each stat **3–18**. Live game remains at the legacy 54-point rule.
- **First life (zero verified remorts):** next-level **cumulative XP threshold = floor(normal threshold / 2)**. Training **gold fee = floor(normal gold fee / 2)**. Standard gold fee already is `floor(normal threshold / 2)` in the legacy engine. An example 1 → 2 uses **525 XP** and **262 gold** on the first life; after rebirth it requires **1,050 XP** and **525 gold**.
- **After first rebirth:** all XP and gold requirements revert to 100%. Later rebirths do not receive the discount.
- **Unknown life count:** **normal 100% prices**, never free/discounted. The current standalone private implementation has a test-only verified remort bridge, **NOT a real player-save integration**, so the full game build cannot yet recognize first lives. Do not guess life status from class/level/name; actual life count must be securely persisted in the same atomic player save and loaded before any cost check.
- **Banked XP:** a character may accumulate enough cumulative XP to qualify for **at most five levels ahead** of their current level. Award sites are capped at the fifth future level's total threshold; XP is **not consumed** on training. After each successful train, the five-level horizon advances by one level, so new XP can again be earned. Existing legacy XP over the bank limit is preserved rather than silently deleted.
- **One level per `train` command:** even with five eligible levels banked, the player must use `train` **five separate times**; each call checks the current level's threshold, checks gold, charges one gold fee, and calls `up_level()` once. The sixth command fails unless the player has earned additional XP. No cap bypass beyond level 60.

## Which files control the behavior?

| Source | Role in this private build |
|---|---|
| `command1.c` | Starting 65-point validation and character creation prompt |
| `command7.c::train()` | One-level-per-command, first-life XP/gold thresholds, no charge at level cap |
| `hd74_xp.c`, `hd74_xp.h` | Shared life-price functions, five-level bank limits, saturating XP grants, level cap |
| `creature.c::die()` | Bounded monster/PvP XP awards and death penalties |
| `command2.c`, `command8.c`, `command10.c` | Bound quest/pledge XP grants to five bankable future levels |
| `command4.c::info()` | Player-visible XP-to-next-level for the life-based price |
| `hollowdeep.c::training_progress()` | Training room readiness and XP/gold requirements |
| `hd74_native.c::hd74_progress()` | Read-only private `hprogress` explanation |
| `files2.c`, `hd_player_store.c`, `treasure_receipt.c` | **Future** trusted remort count/save/reload bridge (NOT implemented here) |
| `misc.c::exp_to_lev()` | Existing full-cost XP conversion; life-specific death penalty migration **pending** |
| `Makefile` | Private ELF32 `hd74_xp.o` build |

## Test evidence and limits

Local 64-bit native helpers and the **actual `command7.c::train()` function** passed both normal and AddressSanitizer/UndefinedBehaviorSanitizer runs. Tests include first life, reborn, unknown life (denied discounts), level cap, 5 earned levels, **five separate train calls**, sixth denied, XP saturation, and legacy/private syntax checks. Local test-only function `hd74_test_verified_remorts()` simulates a trusted saved count; it is never compiled into production. No Linode ELF32 execution, isolated native gameplay replay, character migration, PvP/death XP reconciliation or full regressions are claimed yet.

The private scripts are layered **in order** over the verified uploaded Round 74B source in a brand-new disposable `round74b-*/src`: `native-hook/apply_private.py`, `xp60/apply_xp_private.py`, `first-life/apply_first_life_private.py`, and `bank5/apply_bank5_private.py`. Each stage refuses an unsafe path/source drift, and the final stage checks that actual `train()` still contains only one `up_level()` call. `native-hook/combined/run_combined_private.sh` runs all four stages then the focused tests in one pass, without opening network sockets or starting any game server.

## Live deployment gates

1. Implement trusted remort count persisted and loaded **atomically with the character**; avoid using CRC-only sidecars as authorization. Reconcile first-life training with death level/XP loss and all XP writers.
2. Verify native ELF32 build and run isolated creation, login, repeated training, XP accumulation, save/reload, remort, death and older-character replay. Evaluate reward amounts and any PvP/social economy impact.
3. Keep the level-60 proposal separate from actual production balance approval. Run a full isolated Round 59–74B regression before scheduling a reviewed deployment and restart.
4. Update website/Discord/player help only after production activation; keep private credentials/logs/player data out of GitHub.

## Operator-reported Linode ELF32 combined validation — 2026-11-16

The maintainer executed the all-in-one Round 74B disposable candidate on Linode and
reported these results, verbatim (these are operator-supplied terminal markers,
not independently retrieved server logs):

```text
ROUND 74B: checksum-guarded private native stats/progress hooks installed
ROUND 74B: guarded level-60 training/score/death/XP cap hooks staged privately
ROUND 74B: first-life 50%% XP/50%% gold private training policy staged
ROUND 74B: unknown remort status defaults to standard costs (safe)
ROUND 74B: XP bank capped at five future level thresholds (private)
ROUND 74B: actual train remains one level per command
ROUND 74B: first-life 50% XP / 50% normal gold cost policy and cap checks PASS
ROUND 74B: actual native train() firstlife/reborn/unknown price and cap PASS
ROUND 74B: firstlife private native compiler branches PASS
ROUND 74B: trusted remort save bridge PENDING; live MUD unchanged
ROUND 74B: five-level cumulative XP bank, life-based thresholds, cap, legacy XP preservation PASS
ROUND 74B: first-life 5 banked levels -> 5 separate train uses, no sixth PASS
ROUND 74B: reborn 5 banked levels -> 5 separate train uses, no sixth PASS
ROUND 74B: native train remains exactly one level per invocation PASS
ROUND 74B: 5-level banked XP award paths and private/legacy syntax PASS
ROUND 74B COMBINED ELF32 BUILD: PASS
PRODUCTION DEPLOYMENT: NONE
WORKSPACE: /root/hollowdeep-dev/round74b-SVnpPdcJ
```

**Scope:** checksum-verified private stage application, targeted real native
`train()` tests, 32-bit compilation and binary creation. This is **not** a
full isolated multiplayer/login/combat/save/restart gameplay regression and
not a production deployment. The native remort count is still unavailable;
unknown count defaults to normal fees. Before live enablement, the first-life
counter must be saved/recovered durably and authenticated; combined progression
and save migration plus isolated real-game replay must pass. No live world,
player file, PHP site or service was modified by this validation.
