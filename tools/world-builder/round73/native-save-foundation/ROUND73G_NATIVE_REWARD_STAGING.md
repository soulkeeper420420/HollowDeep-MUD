# Round 73G — Trusted native reward staging (offline candidate)

**Status: private source-only candidate. NOT deployed; `open chest` still says rewards are disabled.**

Built against the real 73G `mstruct.h` native `object`, `creature`, `otag`,
`files2.c`, `files3.c`, compressed player saves and previous `hd_player_store`
receipt writer. This milestone is the isolated, single-game-thread *native grant
stage* that sits after a trusted ledger has already authorized a claim. It is
not the guardian/map authority and cannot be exposed as a command or RPC.

## Behavior

- Takes only a bounded, fixed C structure authored by a **trusted** engine-side
  caller following `DurableRewardCoordinator._prepare`. Checks exact owner and
  32-hex claim key / 64-hex digest, unique 32-hex item identities, native
  `OMAX` template bounds, total 1,000,000 gold grant limit, and the native
  **80-top-level-item serialization cap**. Negative/overflow gold fails closed.
- Calls the supplied native-only template loader to create owned copies; clears
  all imported object pointers; rejects nonpickupable/scenery/temp/worn
  templates. Requires the game's actual carry/weight rule callback per item.
- Does not support enchanted item grants until an exact native effect mapping
  is audited. Any nonzero enchant power is rejected rather than silently
  misapplying the Python `enchantment` descriptor.
- Constructs a temporary inventory view **without altering live inventory**;
  commits items + gold + matching claim receipt together through
  `hd_store_save_claim`. Ordinary saves preserve receipts.
- If the save is durably committed **and** an independent file reread sees the
  receipt, attaches new items to live inventory and updates gold. If a write
  fails before rename, it frees only new items and leaves live state unchanged.
  If the save returns `HD_STORE_UNCERTAIN` after rename, it returns
  `HD_REWARD_UNCERTAIN`, does not mutate live, and MUST NOT acknowledge or
  allow further saves in that session until explicit recovery. A receipt that
  happens to be visible after a failed directory fsync is **not proof of
  crash durability**.
- If a receipt already exists, the function returns `HD_REWARD_ALREADY`,
  without granting again. A new session must load persisted inventory before
  retry; reconnect/reload is mandatory if runtime state may be stale.

## Tests performed in the standalone container

`HD_SANITIZE=1 bash run_native_reward.sh /mnt/data/round73g_native_integration/stage-test`

- Two actual Mordor native-inventory saves via the patched `files2.c` entry
  points, with nested existing items, 2 reward objects and gold.
- Reopen/restart duplicate claim denial and subsequent gold-only claim.
- Rejected wrong owner, invalid template, enchantment, duplicate instance
  IDs, excess gold, and conflicting digest without inventory mutation.
- Before-rename injected fault: live inventory unchanged and disk old state.
- After-rename injected fault: **uncertain** result, no live mutation, reload
  shows receipt and saved items, and another grant is denied on the reloaded
  session. The model does not claim a simulated power loss after a failed
  directory fsync would preserve the rename.
- Python **real SQLite** `TreasureLedger` verifies early-claim denial, map
  ownership, verified guardian death, stable immutable SHA-256 reward manifest;
  its claim ID, digest and item identifiers are compiled into a second native
  replay. This is offline cross-language protocol verification, not a running
  game engine/Unix-socket interface.

## Required next gates before enabling gameplay

1. Bind native **unique** guardian instances, trusted combat deaths and exact
   carried map *object identity* to the persistent SQLite claim ledger. The
   existing `treasure_guard.c` binds volatile pointers only; its state is not
   persistent, and object names alone are not authoritative map minting.
2. Bind the immutable ledger manifest and digest to a **trusted in-process**
   native caller, not a player argument, external web request or arbitrary
   local CLI. Verify native template allowlist and enchant effects. The test
   loader is a dummy: production needs real native object-bank lookup.
3. Establish single active session/exclusive writer ownership and handle
   ambiguous/uncertain saves by blocking further saves until verified restart
   and replay. Distinct simultaneous claims against stale player snapshots
   are **not yet safe** even though file writes are serialized.
4. Enforce the real MUD character carry weight/slots, serialized equipment
   normalization, item limits and gold capacity in the caller.
5. Build the complete **ELF32 private candidate**, test actual live native
   chest open/kills/reconnect/restart/fault injection, rerun Round 59–73F
   private native/browser regression; confirm production/fixtures unchanged.
6. Only after a durable native receipt is independently verified should the
   SQLite ledger mark the pending claim delivered. Never acknowledge after an
   uncertain save.

**Do not wire `hd_native_reward_apply()` into `hd_treasure_open()` at this
stage.** This is a tested native grant building block, not a complete trust
boundary or approved production deployment.

## Operator-reported ELF32 private validation — 2026-11-16

The owner executed `HD_TEST_ELF32=1 HD_SANITIZE=0` for this branch's
`run_native_reward.sh` against a disposable 32-bit native source tree on
Linode. The operator-provided output reported:

- `ROUND 73G: trusted native reward staging/rollback/receipt/restart PASS`
- `ROUND 73G: trusted ledger guardian/map/immutable manifest fixture PASS`
- `ROUND 73G: Python ledger -> actual native inventory + durable receipt PASS`
- `ROUND 73G NATIVE REWARD ELF32: PASS`
- `Production deployment: NONE`

The test emitted pre-existing warnings in `files2.c` about potential
`sprintf(filebak, "%s~", file)` overflow in `load_rom` and `resave_rom`,
and `files3.c` about unchecked `fgets` in `load_crt_tlk`. Those warnings
remain outstanding, and no fixes or production changes are implied here.

**Scope remains offline/native-component validation only.** This does not
establish persistent authenticated guardian/minted map identities, a trusted
live `open chest` integration, full-game ELF32 build/replay or production
readiness. Previous isolated game regression passed on the *player-store*
candidate, before this native reward staging extension.
