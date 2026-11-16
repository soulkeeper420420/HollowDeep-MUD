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