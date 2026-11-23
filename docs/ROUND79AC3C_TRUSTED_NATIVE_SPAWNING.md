# Round79AC3C — server-only native template spawn and rollback

## Scope and threat model

A physical native creature is not an owned mount merely because it has a
horse-like name or happens to stand in the same room. The existing AC2
identity proof requires a trusted pointer binding, and AC3B revokes that
binding on native movement/free/unload. This stage implements **only** the
internal spawn-to-bind transaction. It never accepts template selection
from player text, and it is not wired to command dispatch or login.

The caller supplies a server-maintained six-species catalog of native template
IDs, where zero disables that species. Catalog IDs must be unique and within
the native template limit. The catalog is **not yet configured**; the native
world templates have not been audited. Therefore no game spawn is activated.

The backend re-reads exact authoritative native player-save three-receipt
state, validates a live native PLAYER pointer in the room's actual player list,
checks the owner and target room, mount capacity/stabled/ridden status and
species mapping, and refuses a second in-process binding. It calls native
`load_crt` and `add_crt_rom` only after those checks. A malformed or dead
loaded creature is immediately freed. If the real room pointer binding fails,
`del_crt_rom` and `free_crt` roll back the new creature. The existing AC3B
native hooks clear transient identity on removal. No player save is mutated.

## Security limits still enforced

- No public award, board, stable, retrieve or movement hookup.
- No native creature/room binary ABI changes.
- No monster-template assignment until validated by a separate operator
  authority and gameplay regression.
- The native loader may modify its in-memory template cache; this is not
  a persistent award or world change. Loader failure never acknowledges a spawn.
- Actual logout cleanup/reconnect rehydration and combat/room-transition
  ownership are future gates; they must pass before enabling the gameplay path.
- No live player save, service restart, live-world edit, or credentials in GitHub.

## Private validation

Use `tools/gameplay/round79/private_mount_trusted_spawn_round79ac3c.sh` with a
fresh `/root/hollowdeep-dev/round79ac3c-*` directory and accepted R3 private
ELF32 source `/tmp/hd-army-game-round79lifecycle-hc75BLEp/src`.

Accepted on Linode (private exit code 0, 2026-11-22): 10 staging tests, trusted native template and rollback policy, real ELF32 full game compilation, stablecheck/Breath/logout/reconnect isolated socket regression PASS. Production PID/binary and accepted private ELF32 unchanged. Private results: `/root/hollowdeep-dev/round79ac3c-R3JagCC3`; staged private source: `/tmp/hd-army-game-round79trustedspawn-3W2RXVIA/src` (do not publish raw logs/fixtures). Production deployment: NONE.
