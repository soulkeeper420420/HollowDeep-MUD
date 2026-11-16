# HollowDeep Round 73I — native guardian death → trusted SQLite boundary

**Status: private offline candidate. Chest rewards deliberately DISABLED. Not deployed.**

## What is now working

This milestone extends Round 73H's pointer-verified, durable guardian evidence
with a test-gated native C → Python/SQLite local bridge. In the real native
`treasure_guard.c` integration harness, `open chest` registers an immutable
encounter with native-generated guardian IDs. The exact-bound monster death
hook then sends the corresponding event/guardian ID. The trusted ledger
accepts the event, checks the owner, records it once and creates a *pending*
claim on a later chest opening. The existing reward-delivery module remains
**disconnected**. A pending claim must never be mistaken for player loot.

The native C adapter uses a bounded one-line Unix socket protocol and verifies
the ledger peer's kernel-supplied UID (`SO_PEERCRED`). The ledger service
independently verifies the game's *exact* kernel-supplied PID and UID on each
connection, not merely the shared Unix account. It accepts only a private
server-authored site catalog with names, room IDs and reward contents; player
requests never choose rewards. It rejects unrecognized guardians and modified
replayed combat IDs. The daemon stores claims in the existing
`claim_ledger.py` SQLite schema.

The test-fenced `build_ledger_variant.py` takes only the exact SHA-256 verified
73H generated native guard source and inserts the bridge hooks. It will not
patch production source, and this branch does not modify the shipped MUD
Makefile, existing guardian test feature, or live player saves.

## Tests passed locally

`HD_SANITIZE=1 bash bridge/run.sh /mnt/data/round73i-fixture`

- Actual native guarded `open chest` / wrong owner / same-named decoy monster /
  right pointer and right player death callback → one pending SQLite claim.
- Same Unix UID, **different PID** socket client denied before message parsing.
- Native client validates server UID and bounded request/response, including
  unrecoverable transport rejection.
- Server-selected gold reward stored unchanged and **never delivered**.
- Denied claim when daemon is unavailable; no implicit fallback to CRC sidecar.
- Fresh daemon and a fresh authorized native client reuse the immutable
  encounter and **same pending claim**; valid event replay remains idempotent,
  conflicting kill event or claimant is denied.
- No test mutates the production service, world or player files.

## Trust boundary and remaining blockers

**THIS IS NOT PRODUCTION AUTHENTICATION YET.** In offline tests the server and
native client run as the *same* UID; the protected PID check still rejects
unrelated processes. A real deployment MUST run the SQLite service under a
**different privileged service identity**, use a root-controlled 0700 socket
parent and trusted supervisor-pinned game PID/UID after each native restart,
restrict daemon access to the game, and prevent stale or inherited socket FDs.
The test-only socket is selected by an environment variable and must never be
enabled as a production configuration interface. Do not run this as root to
bypass identity separation.

The Round 73H proof CRC detects accidental corruption, **not same-UID
forgery**. It never authorizes ledger kills independently. Events must arrive
from the actually authenticated native combat callback. If the native proof
commit succeeds but ledger event delivery fails, the attempt is deliberately
**incomplete**; a future recovery/reconciliation transaction or new challenge
is needed. Never trust a proof-file import for automatic kill replay.

`hd_treasure_has_map()` currently relies on a visible native item name: it is
**not** sufficient minted-map identity. Real rewards require a trusted native
item instance ID and map-mint transaction, an authorized immutable manifest
handoff, a restricted inventory-template bank, single-session writer
exclusivity, crash-safe native `hd_native_reward_apply()`, independently
verified receipt and SQLite delivered acknowledgment. Never enable loot based
on the bridge's `PENDING` response.

This milestone tests only the native hook + SQLite ledger interface, not a full
ELF32 native executable or the complete Round 59–73H gameplay regressions.
Run the isolated ELF32 test below first, then later a **single** full game
regression only when the actual chest command can deliver loot in a sandbox.

## Isolated Linode ELF32 test

From a disposable checkout on branch `round73i-native-ledger-bridge`, run:

```bash
HD_TEST_ELF32=1 HD_SANITIZE=0 bash \
  tools/world-builder/round73/bridge/run.sh \
  /root/hollowdeep-dev/round72-build-2DZMdFJd/round72-native-build
```

The referenced source must still contain the exact original Round73D
`treasure_guard.c`, not the later 73H patched variant. `run.sh` never writes
that source directory or starts a game server. The Python test spins up only a
private transient local socket and SQLite file, then removes them.
