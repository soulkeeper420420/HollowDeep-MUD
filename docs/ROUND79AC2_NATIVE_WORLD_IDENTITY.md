# Round 79AC2 — Private trusted mount entity identity foundation

Goal: prevent client text, copied creature names, room-id receipts and ordinary
monster templates from being mistaken for **owned live mounts**.

## Native structs audited

Mordor 3.00 native room stores `ctag *first_mon`, `ctag *first_ply`.
A creature stores `parent_rom`, `rom_num`, `type`, HP and a native pointer.
`room.c` adds/deletes creatures from `first_mon` via `add_crt_rom` and
`del_crt_rom`; teardown can call `free_crt`. These are NOT automatically
trusted lifecycle hooks for mount identity. Native ELF32 build must verify
actual HollowDeep layout independently.

## Candidate design

`hd79_world_mount_bind` is a **trusted internal function** for a future
spawn service, never a user verb. It checks owner alive, player membership in
native room, mount alive and listed exactly once among native monsters,
matching pointers/room IDs and matching durable 80/81/82 location+epoch.
The process-local binding stores owner pointer+name, character epoch, mount
pointer/id/species and native room. `hd79_world_mount_present` then refuses
same-name fake monsters, unbound entities, other owners, wrong room, wrong
species, dead/detached monsters, stale character epochs or mismatch with the
native room lists. Duplicate registration is denied.

`hd79_world_mount_unbind_creature` and `hd79_world_mount_unbind_owner` are
future mandatory teardown hooks. This stage does NOT register a creature
from gameplay, does NOT spawn mounts, and does NOT hook native destruction.
The registry is volatile across restart, so it cannot prove a durable mount
without a later verified runtime rehydration and explicit lifecycle gates.

## Security boundaries

- No changes to the 32-bit player/creature/room save ABI.
- No world/room/player files edited, and no live service restart.
- No new public commands, awards, spawning, boarding or stabling.
- No use of a creature name as an identity token. No command-supplied owner.
- The registry is **not** safe for gameplay until every free/delete/logout
  path is verified to revoke bindings and the trusted spawner is implemented.
- The new Makefile object is gated and registered before the target rule.

Linode full ELF32 private build and socket replay are pending. Do not promote
until the tester reports exit code 0; keep fixture logs private.

## Round79AC2 R2 native ELF32 include repair

R1 completed the policy tests but failed full-game compilation because its
identity C translation unit included `mextern.h` without first importing
`hd_player_store.h`, the established native type provider used by the accepted
mount command and `stablecheck` objects. Compiler errors were unknown
`creature` and `room` structure members. R2 adds this header in the same order
as those working objects and moves the mock creature definitions to a dedicated
mock `hd_player_store.h` so pure ELF32 tests will catch this regression.

R2 requires a fresh complete private ELF32 game and socket replay on Linode.
No live gameplay hooks or mount awards are enabled, and no production change
is authorized by this source-only candidate.
