# HollowDeep Round 79AD R6C — Private native creature reconciliation

**Stage:** Unaccepted, private ELF32 candidate. R6B native action-CAS and R6A authenticated proof required. Production is not deployed or restarted.

## Contract

R6C adds an internal-only native action adapter. Before any write, it consults R6A to prove the live owner and, for board/stable, the exact registered living creature pointer in the same native room. The new world-identity helper scans the existing private registry and refuses duplicate registered identities, stale owner epochs, mismatched species/rooms, or absent native list membership. No name-based creature selection or client-supplied context is accepted.

The R6B action-CAS writes saved mount roster/location/death receipts #80/#81/#82/#83. R6C then verifies **all four canonical wires** against the intended post-state, including the unchanged permanent death serial and bitmap. Neither a before-rename failure nor an unresolved uncertain rename can change a native creature or report success.

For a confirmed board or stable, R6C removes and frees the exact previously attested creature, using the native remove hooks that invalidate ephemeral ownership tokens. For a confirmed dismount or retrieval, it calls the existing R5 four-receipt-aware private creature constructor to instantiate exactly one owned mount in the confirmed room. When a physical reconciliation fails, R6C returns `PENDING`, never `COMPLETE`. No regular player command calls this module.

## Reproduction

Run `tools/gameplay/round79/private_mount_ad_creature_action.sh` using the trusted prior R6B staged ELF32 source `/tmp/hd-army-game-round79adcas-6qHWwK2O/src` into a new private `/root/hollowdeep-dev/round79ad-*` results root. It performs Python staging-generator tests, 32-bit C mock lifecycle tests, normal ELF32 linking without fixture symbols, and a **separate disposable test-only** native ELF32 socket replay. The socket replay tests before/after rename, physical board/dismount, duplicate denial, and all six R5 native combat deaths and restart tombstones. The actual native result must pass on Linode before acceptance.

## Open safety gates / not a release

- The mock tests cover stable/retrieve; their **real native socket verification remains pending**.
- A disk-committed dismount/retrieve can still leave `PENDING` if native allocation or binding fails; there is not yet a durable restart-safe reconciliation token. This is **not** permission to auto-spawn from a zero #83 death bit.
- All native commands, login/restart restoration, mounted-state creature combat handling, and Endurance/native movement checkpoint remain disabled.
- Do not publish any test-only `adfixture` command into the normal game. Never push private room/player worlds, test artifacts, logs, or secrets.

## Files

- `hd79_ad_creature_action.c/.h` — unexposed four-wire confirmed native creature reconciliation.
- `hd79_ad_bound_creature.inc` — exact pointer lookup inside the existing private native identity registry.
- `stage_mount_ad_creature_action.py` — guarded disposable native source copy; prohibits production and command changes.
- `build_ad_r6c_socket_fixture.py` / `build_ad_r6c_socket_replay.py` — test-build-only socket harness.
- `test_hd79_ad_creature_action.c` — deterministic fault/physical-state mock tests.
- `test_stage_mount_ad_creature_action.py`, `test_build_ad_r6c_socket.py` — source-isolation and generator regressions.
- `private_mount_ad_creature_action.sh` — all-in-one Linode private native validation runner.
