# Round79AD R2 — unexposed death receipt and verified action gate

**Candidate only. Not a playable release. Never deploy this to production.**

The accepted Round79AD foundation was tested privately on Linode (six harmless species, exact native binding, pure action/travel planner, full ELF32 and socket replay PASS). These new files extend **the same candidate branch** with two conservative contracts.

## 1. Prospective native death receipt #83

`hd79_ad_death_receipt.c/.h` defines a canonical fixed 64-hex value associated with internal record ID `ffffffffffffffffffffffffffffff83`. Binary layout: byte 0 `D`, byte 1 version 1, byte 2 mount count, byte 3 monotonic dead-mask (six bits); bytes 4–7 death serial, bytes 8–19 the twelve canonical owner epoch bytes; bytes 20–27 reserved zero; bytes 28–31 CRC32. This is **not** a token that authenticates itself: CRC only detects corruption. Authentication requires reading it from the protected, atomic native player save alongside owner epoch and existing mount receipts 80, 81, 82.

The policy never creates a death record for an already populated legacy roster: only an entirely empty valid roster may initialize it. A new mount award may extend the record *only with a previously verified before/after award*, preserving old death bits. Death marks are monotonic; a dead mount remains denied for future actions. Even a verified *zero* dead-mask is **insufficient** to prove that a creature survived process exit: `hd79_ad_death_reconnect_allowed()` remains hardcoded to 0.

**Important:** No player-save ID #83 reader/writer is connected yet; no combat death hook persists a death mark. The format and pure transition tests alone are *not* durable death persistence or permission to restore a mount. Before enabling restoration, implement atomic four-receipt save / compare-and-swap, native death hooks, crash/reconnect reconciliation and fail-closed uncertain-rename handling.

## 2. Read-only native owner/mount/stable action preflight

`hd79_ad_verified_action.c/.h` gets the authoritative 80/81/82 player snapshot from the accepted store, verifies the actual live player room list, alive player, exact native pointer/owner/epoch identity via `hd79_world_mount_present`, and uses the **existing root-owned stable registry** for storage/retrieval. The supplied death record must already be native-store authenticated by a future caller, match the durable epoch/count, and have the selected dead bit unset. The existing Round79AD planner calculates the next 80/81/82 state, but **no save is committed and no creature is removed, created, moved or restored**. The routine is not exposed through any MUD command.

The future action writer must re-check proof and live room pointers under one atomic player lock, update receipts 80/81/82/83 together, reconcile uncertain writes, then apply reversible native effects. It must not infer physical presence from a monster name, player input, stable flag or location receipt alone.

## 3. One private ELF32/socket runner

`tools/gameplay/round79/private_mount_ad_death_gate.sh WORK SOURCE` runs eight strict staging tests, real-layout C death-receipt regression, synthetic native command preflight tests, a complete private ELF32 engine build, and the prior isolated socket stablecheck/Breath/logout suite. It compiles against the previously successful private AD fleet source:

`/tmp/hd-army-game-round79adfleet-J8jHd6Io/src`

The runner must be executed only on Linode from a **new** `/root/hollowdeep-dev/round79ad-*` directory. It creates a new `/tmp/hd-army-game-round79adgate-*/src`, copies existing sources and modifies only the private Makefile, adds the four new `.c/.h` files, and refuses symlink/ABI/source drift. It compares the production `hollowdeep.service` PID/binary SHA and the previous private ELF32 SHA before and after. Private source, fixture and player/world logs stay on Linode and do not enter GitHub or Discord.

**Milestone exit code 0 means only this R2 *foundation* passed.** It explicitly reports that player commands, death-persistence, reconnect and mounted travel CAS are still not implemented. The Round79AD branch must **not** be promoted to accepted until the full user-visible native command, survival/death, reconnect and travel socket gates pass.

## Developer file map

| File | Purpose | Safe editing notes |
|---|---|---|
| `hd79_ad_death_receipt.h/.c` | Death bitmask, epoch-bound CRC wire, monotone transition | Keep 64-hex ABI and exact owner epoch; never permit populated auto-upgrade |
| `hd79_ad_verified_action.h/.c` | Exact owner/room/mount/stable read-only precheck | Future caller must authenticate #83 from protected save; no client context |
| `test_hd79_ad_death_receipt.c` | Wire, corruption, double death, legacy denial | Synthetic C source, never copy private player data |
| `test_hd79_ad_verified_action.c` | Invalid pointer/owner/registry and dead rejection | Inert fake player and monster, no save writes |
| `stage_mount_ad_death_gate.py` | Disposable staging, Makefile only | Do not alter native `room.c`, `wilderness.c`, player store or command dispatch |
| `private_mount_ad_death_gate.sh` | One private Linode ELF32/socket runner | Never change production paths into write targets |

No production gameplay mutation is authorized.
