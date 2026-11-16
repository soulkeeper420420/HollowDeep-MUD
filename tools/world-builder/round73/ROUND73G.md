# Round 73G — deterministic reward manifest and atomic-save protocol (private foundation)

**Status:** Offline Python acceptance model only. **No native C game reward delivery is enabled.**

Starting from Round 73F commit `d560a0cf4f1f9c54394afe6c6de3668751566931`, the new `durable_delivery.py` defines a strict trust boundary between the existing SQLite treasure claim ledger and a *future* native save adapter:

1. The current claim ledger verifies the owner, exact held treasure map, and all guardian kills before producing one pending claim ID.
2. Round 73G validates the ledger's server-selected rewards against a trusted catalog of native item templates and per-template enchantment caps. It rejects overflow, unsupported templates, and invalid quantities.
3. The immutable manifest is stored in the **same SQLite ledger** as the pending claim, with stable per-item instance IDs and SHA-256 digest. A resumed process must reuse that snapshot, even if the catalog changes.
4. A trusted native player-save adapter must persist **all** new inventory/gold plus the matching claim receipt **atomically**, then independently reread the committed receipt. Only then may the existing ledger mark the claim delivered.
5. If interrupted before the atomic native save, a retry may apply the pending manifest; if interrupted after it, the saved receipt suppresses duplicate grants. This guarantee is **conditional on a genuinely atomic native save adapter**, which has not been implemented in C yet.

## Test

From `tools/world-builder/round73`:

```bash
python3 -m unittest -v test_delivery_protocol
```

The test suite uses real `claim_ledger.py` from that directory and a **simulated** SQLite player-save bridge. It verifies stale-map/owner denial, template and enchantment caps, duplicate chest opens, concurrent calls, and deliberate before/after-commit interruptions. The local standalone fixture used to develop this code is intentionally not published as a native implementation.

## Mandatory next native milestone

**Do not wire `DurableRewardCoordinator.deliver()` into `open chest` yet.** The legacy Mordor engine still stores characters using native binary files, with no atomically persisted claim receipt. Separate sidecar writes are NOT sufficient. Before enabling loot, inspect the exact `savegame` and `read_ply` contracts, add a claim-key-aware native save format or a proven atomic equivalent without breaking existing characters, build a verified 32-bit candidate, replay actual inventory/gear/gold behavior through crash/restart, and rerun the complete Round 59–73F native/browser suite. Keep test assets and runtime secrets private, and leave production untouched.
## 2026-11-16 — operator-reported private Linode regression (Round 73G checkpoint)

The operator supplied the terminal output from the disposable checkout
`/root/hollowdeep-dev/round72-73g-5RBvsQC2/repo`, using the Round 73G
source at commit `ad0b288b883364928233ac71197713e29acbfd86`.

- Combined `test_treasure` and `test_delivery_protocol`: **21 tests passed**.
- The full `tools/world-builder/round72/private.sh` test exited with status **0**.
- The final log includes **`ROUND 73F: native showmap movement, named-go, toggle, radius and suppression PASS`** and **`ROUND 72: private regression suite PASS`**.
- The test's production guard reported **`PASS: Production and prior fixture unchanged`**.
- Tests included existing native/browser regressions; the Round 73G delivery tests use a simulated SQLite native-save bridge, **not** actual in-game reward grants.

This result was reported by the operator, rather than independently fetched
from Linode by the GitHub publisher. No player reward delivery is enabled and
no production deployment or restart was performed by this change.

**Next gate:** inspect and implement the real native save/receipt transaction;
validate actual 32-bit item/gold persistence with interrupted save/reconnect/restart
and then rerun the private regression suite. Do not enable chest rewards earlier.

## Native save-format source-only foundation — after validated private regression

Separate branch `round73g-native-save-foundation` contains only authored C receipt/atomic-save primitives, a 64-bit private serializer compatibility harness and documentation. The code is NOT compiled into the native engine, does not enable treasure rewards, and was never deployed. The supplied `files2.c` still rotates backups before writing and lacks bounded compression and a same-save claim receipt. `files3.c` returns consumed serialized inventory bytes, permitting an *inert* trailing receipt format (verified in a private 64-bit harness with nested inventory and a historical compressor round-trip). The standalone primitive rejects corrupt receipts and uses file+directory fsync/rename with an explicit uncertain-result state after rename. Before enabling native loot, bound the real save and load paths, retain every receipt on ordinary saves, save items/gold/receipt atomically, test actual ELF32 crash recovery and repeat Round 59–73F isolated regressions. Production untouched.

## Round 73G native reward staging — offline extension

The `round73g-native-reward-stage` development branch now has an independent
`hd_native_reward.[ch]` staging API and C replay harness. A real SQLite
`TreasureLedger` authorizes a test encounter, issues an immutable Python
reward manifest, and compiles its stable claim/digest/item IDs into a native
save/reload harness. Local 64-bit ASan/UBSan replay passed for grants, duplicate
reopens, nested inventory, invalid owner/enchantment/template/IDs, failed
writes and explicit uncertain-save recovery. Post-rename visibility is **not**
accepted as crash durability. This component is **not hooked to**
`treasure_guard.c` or the native game and must remain disabled until the
persistent guardian mapping, live-session exclusivity and ELF32 native replay
are validated. Details:
`native-save-foundation/ROUND73G_NATIVE_REWARD_STAGING.md`.

## Round 73H private guardian-evidence candidate

The `round73h-durable-guardian-proof` branch contains a new **test-gated**
C guardian-evidence recorder and native pointer/death/restart test harness.
Local sanitizer checks passed; ELF32 runtime has not yet been verified. This
fixes the volatile *test* challenge-state limitation by persisting encounter
and death-event identities, but the record is not a secure ledger authority:
same-game-UID file writes could forge its CRC. A trusted process-authenticated
native-to-SQLite handoff remains mandatory before rewards may be enabled.
`open chest` still reports disabled rewards. Production unchanged.
