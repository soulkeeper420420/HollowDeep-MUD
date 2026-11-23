# HollowDeep MUD — Round79AC3B native lifecycle revocation (private candidate)

Round79AC3A audited the native source: 19 references to `del_crt_rom`,
24 to `free_crt`, 20 to `del_ply_rom`, and no unexpected calls into the
Round79AC2 mount entity-binding registry. Round79AC3B targets those **central
implementations**, rather than patching each scattered gameplay callsite.

## Behavior when the private gate is enabled

`MOUNT_LIFECYCLE_PLAYTEST=1` requires `MOUNT_WORLD_IDENTITY_PLAYTEST=1`.

- Native `add_crt_rom` and `del_crt_rom` revoke the process-local token for
  that exact monster pointer before moving or removing it.
- Native `add_ply_rom` and `del_ply_rom` revoke owner bindings before player
  room entry, room exit, teleport or logout. Until trusted rehydration exists,
  this intentionally may revoke even on ordinary movement.
- Native `free_crt` revokes a creature's monster and owner binding before
  the creature allocation is destroyed. Handles reuse on logout and deletion.
- Native `free_rom` conservatively clears **every** transient binding before
  a room is released. This fails closed if the room is destroyed unexpectedly.
- Hooks never read/write player or world persistence and never award,
  spawn, board, stable, retrieve or move mounts.
- The accepted `hd79_mount_world_identity.h/.c` gain a server-only
  `hd79_world_mount_unbind_all` helper, clearing only memory in this process.

## Validation

The Python patcher must:
- accept a pre-existing accepted private Round79AC2 ELF32 source at
  `/tmp/hd-army-game-round79worldproof-*/src`;
- copy it to a new `/tmp/hd-army-game-round79lifecycle-*/src`;
- locate all six exact native function signatures; refuse drift;
- leave command dispatch, player save, wilderness and original source unchanged;
- add the flag before `frp.new` Makefile prerequisites.

The private runner tests source boundaries, compiles pure native identity
tests as ELF32 including all-token revocation, fully rebuilds the ELF32 MUD
with lifecycle hooks, and replays read-only stablecheck/Breath native socket
regressions in a separate namespace.

**Limits:** This is a *revocation foundation*, not a complete trusted mount
lifecycle: no authoritative spawner, no validated mount NPC ownership in
playable gameplay, no login rehydration, no full combat/death-path replay.
Do not enable boarding, stabling, retrieval or ridden movement from this
candidate. No production deployment.

Acceptance requires Linode runner exit 0 before publishing to
`round79-gameplay-qol`, which will then trigger Discord `#change-log`.
Private logs and synthetic player fixture files must stay off GitHub.

## Round79AC3B R2 signature-format repair

R1's 12 staging tests passed but the native source was rejected before the
ELF32 build: `Native lifecycle function signature drift: add_crt_rom`.
The patcher had required a newline between the closing parameter `)`
and the function body's opening `{`. R2 permits same-line or multiline
C whitespace, while still requiring one exact `void` definition and the
original named, typed parameters; prototypes and ambiguous matches fail closed.
Three regression tests cover native inline braces, multiline parameters,
and rejection of a declaration without a body.

**R2 was not accepted**; R3 superseded its signature handling. No production change.

## Round79AC3B R3 classic K&R function definitions

R2 ran 15 Python regression tests (PASS) but the exact native staging stopped
again because the original HollowDeep source uses old-style C functions,
for example `void add_crt_rom(crt_ptr, rom_ptr, num)`, with separate
`creature *crt_ptr;`, `room *rom_ptr;`, and `int num;` declarations before
its opening brace. R3 matches BOTH strict ANSI and exact K&R function bodies,
checks each named parameter's declared type and pointer status, permits
whitespace and declaration reordering, and rejects prototypes, wrong types,
missing declarations or duplicate definitions. Four regressions cover these.

R3 private Linode validation: **PASS (exit code 0)**. Source staged at `/tmp/hd-army-game-round79lifecycle-hc75BLEp/src` and private results at `/root/hollowdeep-dev/round79ac3b-66QWzPGO` (logs never published). Full native ELF32 game build, identity revocation, all-token clearing, native stablecheck/Breath socket and logout/reconnect regressions passed. Production PID, binary, and accepted private ELF32 baseline remained unchanged.

No production deployment or mount gameplay activation. Trusted mount spawner, native entity registration, and reconnect recovery remain future gates.
