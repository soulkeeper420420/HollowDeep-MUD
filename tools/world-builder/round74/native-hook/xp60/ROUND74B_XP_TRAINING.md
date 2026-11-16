# HollowDeep Round 74B — Private XP, training and level-cap integration

**Status: isolated development candidate only. NOT deployed. No player-save migration.**

The source is based on the verified owner-supplied `round74b-native-source.tar.gz`. It layers **on top of** the existing Round 74B 65-point character creation and `hprogress` patch, without modifying the original production source. The PHP website and live `hollowdeep.service` remain untouched.

## What changes in an explicitly patched, disposable native test build

- Character creation retains **up to 65 total** STR/DEX/CON/INT/PIETY points, **3–18 each** (the prior private patch). Production still has the legacy **up to 54** rule.
- Training uses a **development proposal** of **level cap 60** and the monotonic total-XP curve `XP(level) = 1000*(level-1)^2 + 50*(level-1)^3`, with a 32-bit signed XP bound.
- Example: level 2 costs 1,050 total XP; level 3 costs 4,400; the **training gold cost is half the XP threshold**, matching the existing source's training economics.
- Actual native `command7.c::train()` refuses any training at or above 60 **without deducting gold**, and `player.c::up_level()` has a defensive cap while retaining level-0 initial character creation.
- `command4.c::info()`, `hollowdeep.c::hclass progress` and `misc.c::exp_to_lev()` use the same private XP helper. Death-related minimum-level XP recovery in `creature.c` uses the same new curve, not the old 25-entry table.
- Native monster/PvP/quest/pledge XP reward sites are guarded against crossing the signed 32-bit XP ceiling using saturating arithmetic. The quest grant sites live in `command2.c`, `command8.c`, `command10.c`; combat grants live in `creature.c`.
- `global.c`'s original 25-entry table, `mtype.h`'s `MAXALVL` and `mextern.h` declarations remain untouched, so the **non-private compilation path** still uses legacy mechanics. The private path never increases the array bound.
- The private `hprogress` command calls its state **PRIVATE TRAINING**, not a preview of inactive training. Legacy XP and remort state are not silently migrated.

## Actual source-file map

| File | Private hook | Teaching note |
|---|---|---|
| `command1.c` | 65-point allocation | Only new-character prompts and parsing; old saves unchanged |
| `command7.c` | `train()` | Threshold, training room/class check, gold charge, hard cap |
| `misc.c` | `exp_to_lev()` | XP-to-level calculation used by death penalties |
| `player.c` | `up_level()` | Native HP, MP, stat changes; hard cap guard |
| `command4.c` | `info()` | Player-visible XP remaining / cap status |
| `hollowdeep.c` | `hclass progress` | Class training-room and gold/XP readiness |
| `creature.c` | `die()` | Monster XP gains, death penalties, PvP rewards |
| `command2.c`, `command8.c`, `command10.c` | Quests and pledges | Bounded XP rewards from other game events |
| `hd74_xp.[ch]` | New private shared helper | Consistent XP curve and overflow-safe additions |
| `hd74_progression.[ch]` | Previous Round 74A model | XP rule validation, future remort/Legacy implementation |
| `Makefile` | `hd74_xp.o` | Build private helper only in the disposable candidate |

## How the patch is applied (assistant-maintained)

First run the existing `native-hook/apply_private.py` on a *fresh* `/root/hollowdeep-dev/round74b-*/src` copy, then run `xp60/apply_xp_private.py` against that resulting source. The second script checks exact SHA-256 checksums for all 16 input files, refuses drift, symlinks, wrong paths and a second application **before any changes**. Use only with the verified source archive, never `/srv/hollowdeep`.

The package's `run_xp_private.sh` executes unit tests for threshold inversion, 32-bit XP saturation, all 60 levels, the real `command7.c::train()` function (including gold, level 59->60 and cap refusal), and syntax checks of both legacy/private code branches for 11 native files. Local normal and ASan/UBSan 64-bit checks passed. An ELF32 compile and isolated gameplay replay are **not claimed** until the owner runs the combined private command on Linode.

## Not yet included

- No automatic rebirth, class-skill inheritance, timed boss quest, Legacy Points awards, native character-bound items or sacrifice/divine-favor commands.
- No changes to native binary character structures or durable progression receipts in actual player saves. Saved legacy characters are **not migrated** to the new curve.
- No complete ELF32 executable build or real native login/combat/reload regression for this candidate yet.
- Core XP award multiplication in some legacy combat paths predates this change and still needs careful overflow validation before production; the bounded add only protects the final accumulation.
- No PHP website, Discord announcement, service restart, live world, production players or deploy action has been performed.

**Next release gate:** ELF32 private build, test new-character 65-point creation and XP training in an isolated native gameplay session, test existing saved characters and death/quest XP, then rerun the complete isolated Round 59–74B regression once. Production requires a separate reviewed deployment plan, player-save migration policy and explicit restart authorization.
