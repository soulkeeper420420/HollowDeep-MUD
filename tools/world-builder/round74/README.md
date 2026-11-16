# HollowDeep Round 74A — Character progression core (private candidate)

**Status: development source only. Not installed in any native MUD process and not deployed to a website.**

This is the first combined Round 74 implementation, designed against the actual
Mordor 3.00-era `mstruct.h` and `mtype.h` captured from the owner's disposable
Round 73G native source. It does not overwrite legacy player records.

## Features implemented in pure C

- **Starting stat allocation:** five native stats (STR/DEX/CON/INT/PIETY),
  strict point pool and caps, immutable after finalize. The sample uses
  base 10, maximum 18 and 20 points; these are example playtest values.
- **XP curve & level cap:** `XP(L) = base*(L-1)^2 + growth*(L-1)^3` total
  experience. Integer-only calculations, overflow checks, dynamic levels.
  The sample cap is 60; valid caps are 2–100 while thresholds must fit the
  engine's **signed 32-bit long** XP field. Native `level` is a signed byte.
- **Class-specific skills:** native classes 1–10; current-class skills require
  their minimum level; successful remort retains prior class access. Cannot
  use skills above the configured level cap. Real individual skill IDs and
  command entry points still require mapping to the engine.
- **Timed remort:** only at the configured level cap; unique server-issued
  quest/death event IDs, correct monster template and player, fixed deadline;
  wrong-player/wrong-monster/duplicate/expired/backward-clock events denied.
  On success, reset level/XP, change class, preserve completed class skills
  and stats, and credit capped Legacy Points once.
- **Legacy Points vs Divine Favor:** completely separate fields. Character-
  bound purchases require an exact owner and explicit binding. Purchase
  counts are **bookkeeping only**; no native game object is minted yet.
- **Portable snapshot:** fixed 512-byte, little-endian, versioned, CRC32
  record. Round trip, truncated data and byte corruption tests. This record
  is an **integrity check, not authentication** and is not yet appended to the
  game's compressed player files. It must eventually be committed *inside*
  the same atomic native save, not a detached sidecar.

## Tests

```bash
# Local/host C normal and ASan+UBSan builds:
bash run.sh
HD_SANITIZE=1 bash run.sh

# Linode ONLY, with working gcc -m32 and disposable native source:
HD_TEST_ELF32=1 HD_SANITIZE=0 bash run.sh /root/hollowdeep-dev/round72-build-2DZMdFJd/round72-native-build

# Preview, NEVER active configuration:
python3 preview_xp.py progression.sample.json
```

The optional ELF32 run also compiles `test_native_abi.c` against the actual
Mordor `mstruct.h`/`mtype.h`: 1-byte level/class/stat fields, 4-byte XP `long`,
and actual class IDs. The test uses a private temp build only.

## Remaining native integration and deployment gates

1. Map actual skill/spell/proficiency IDs to class and level requirements;
   add builder/admin configuration safely with stable versioning.
2. Tie starting stat choices and timed verified-kill events to trusted native
   creature/character hooks. Make the rebirth grant and class change atomic.
3. Add the Round 74 snapshot to the same atomic compressed player save as the
   existing inventory, gold and treasure receipt. Verify player reload,
   legacy save compatibility, restart, rollback, and double-remort races.
4. Build, run and replay the full 32-bit isolated MUD; verify old characters,
   combat, skill locks, inventory, equipment, gold, and the existing 59–73J
   regressions. Production deployment/restart only after authorization and
   all blockers are cleared.
5. Character-bound legacy equipment requires actual saved objects with
   explicit no-drop/no-sell/no-trade rules. **Never assume the existing
   `No Save` flag is compatible with permanent personal equipment.**
6. Keep Divine Favor/item sacrifice separate; any offering must delete its
   source item and credit favor in one durable transaction before activation.

## Website status

Do **not** announce this as a live feature on HollowDeepMUD.com. The existing
public website could not be verified reachable through the publisher's tools.
The GitHub Next.js site and the live Linode PHP site are distinct codebases;
no PHP deployment is inferred from publishing this source. Publish a
player-facing guide only after real native command hooks and migration tests
pass. No server process, production player/world record or website changed.

## Operator-reported Linode ELF32 validation — 2026-11-16

The operator executed the private 32-bit test against the disposable Mordor
native source and supplied these final markers:

```text
ROUND 74A: config XP/ELF32 cap/starting stat allocation PASS
ROUND 74A: timed remort/unique kills/class inheritance/bound legacy PASS
ROUND 74A: fixed-size native-safe progression receipt/CRC/reload PASS
ROUND 74A: PRIVATE CORE PASS (NO NATIVE HOOKS/PRODUCTION)
ROUND 74A: native ELF32 Mordor level/XP/stats/class ABI PASS
ROUND 74A ELF32: PASS
PRODUCTION DEPLOYMENT: NONE
WORKSPACE: /root/hollowdeep-dev/round74a-DOMysFit
```

This is user-supplied terminal evidence, not independently retrieved from
Linode. The model validates the source-only progression core and native field
layout; it does **not** validate hooked character creation, player save/load,
legacy skill commands, or production level-cap migration. No production game,
player records, website or service was modified by this test. Round 74B must
integrate incrementally into another disposable candidate and revalidate.

## Learn to edit the native files

The Round 74B branch includes two hands-on guides for the existing source:

- [VS Code Remote SSH + exact native C editing workflow](../../../docs/ROUND74B_EDITING_GUIDE.md)
- [Customize XP, stats, class inheritance, rebirth and Legacy Points](../../../docs/ROUND74B_PROGRESSION_CUSTOMIZATION_GUIDE.md)

Both are **development-only**. Practice against an isolated copy of the
private source archive; do not edit/restart production or advertise the model
as live gameplay. Round 74B native command/save integration is still pending.
