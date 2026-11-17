# HollowDeep private deity assignment (Necromancer + corpse-sacrifice groundwork)

**Status:** private C prototype; **not deployed to the live game**. This
release adds the DM deity assignment and durable (atomic-rename) ID lookup,
**not** the corpse-loot consumption or sacrifice command yet. Deity names,
rewards and favor are not defined; the initial 1–16 numeric IDs are reserved
and need approval before any live use.

## Commands

- `*deity list`: show valid numeric IDs (1–16, names pending).
- `*deity <saved player>`: show assignment for a saved character.
- `*deity <saved player> <1-16>`: assign or replace the deity.
- `*deity <saved player> 0`: clear the assignment.

Examples: `*deity Hdnecro 3`, `*deity Hdnecro`, `*deity Hdnecro 0`.

Only **native DM class 12** **and** an authorized staff admin/owner role
may use it; the handler checks both even if invoked without the native
command dispatcher. Assignments require an existing saved character, work
for offline accounts, and record a staff audit action before the database is
written. Invalid names, missing staff privileges/audit, malformed IDs,
corrupted deity data or symlinked/unsafe data files fail closed.

Data lives in the existing private `hollowdeep-data/deities.db` protective
sidecar, NOT inside the Mordor native `creature` struct. A versioned strict
header + fixed saved-character name/number records is used. Updates use the
existing `hd_staff_write_data` fsync+rename writer, and reads use its guarded
`hd_staff_open_data` path policy; the patch extends that allowlist under a
private compile flag. Staff role file, player inventory, class number,
Necromancer identity marker and save layout are unchanged. This file must be
included in backup/restore/rollback plans and should receive a parent-directory
fsync and interprocess concurrency audit before a production deployment.

## Corpse / Sacrifice integration contract (next feature)

The existing `worship` command is a **social emote**, not faith metadata.
`hd_deity_get(player->name)` returns `-1` for unsafe or corrupt storage,
`0` for unassigned and `1..16` for a confirmed assignment.

- Every monster death should create a non-lootable corpse in the room with
  its exact inventory and gold moved to one corpse record, **not copied**.
- Anyone may `loot corpse` to release inventory and gold once and consume the
  corpse. Necromancer may `raise corpse` and a deity-assigned player may
  `sacrifice corpse`; both also release carried contents exactly once and
  consume the corpse atomically before rewards or summons.
- Only a valid deity ID (>0) authorizes sacrifice; `-1` must be denied, never
  interpreted as unassigned-but-allowed. Favor points are NOT implemented;
  they require a durable two-sided transaction (item removal plus reward).
- The corpse must be identified by a server-issued identity and must not be
  replayable across a restart. Death loot and auto-drop must be mutually
  exclusive. Pet skeletons never generate corpses/loot/favor/XP.

These corpse commands and their safe release/consume transaction are
**not yet implemented** in this package. Do not tell players they are live.

## Source file map

- `global.c`: register `*deity` as native command ID 150 (private only).
- `hollowdeep_help.c`: allow native command ID 150 only for true `DM` class.
- `hd_deity.c` + `hd_deity.h`: strict command parser, ID registry, persistent
  assignment storage, audited admin authorization, fail-closed reader.
- `hollowdeep_staff.c`: add `deities.db` to protected sidecar allowlist only
  when `HD_DEITY_PLAYTEST` is enabled.
- `Makefile`: compile the new module only with `DEITY_PLAYTEST=1`.

## Testing

1. Copy the previously verified `necromancer-playtest-*/src` into a new
   disposable directory. Never use `/srv/hollowdeep`.
2. Run `run_private.sh PATH_TO_DISPOSABLE_SRC`, which refuses any source profile
   outside its pinned SHA allowlist, patches once, and executes a real C
   persistence/authorization test plus legacy/private compile syntax tests.
3. On Linode, set `HD_TEST_ELF32=1` to include a full 32-bit game build using
   `NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1`.
4. Real multiuser and crash/restart tests, and corpse/sacrifice atomicity,
   remain blockers. **Production unchanged, no service restart.**

**Local evidence:** C command/persistence unit PASS; sanitizer PASS;
private and legacy native syntax PASS; SHA drift rejected; duplicate patch
rejected. A full Linode ELF32 build is pending.
