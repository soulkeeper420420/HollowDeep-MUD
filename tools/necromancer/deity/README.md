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

- `global.c`: register `*deity` as native command ID 151 (private only).
- `hollowdeep_help.c`: allow native command ID 151 only for true `DM` class and authorized staff admin role.
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

## Round 74B integrated-source repair and in-game help

The exact `global.c` and `Makefile` checksums reported by the operator were
independently reconstructed from the known Round 74B progression and
Necromancer patches. Both complete source profiles are accepted; mixed or
unknown inputs are refused before writes. The staff and help source checksums
are unchanged. Command 151 is reserved for `*deity`: 150 already belongs to
`raiseskeleton`. The patch rejects any occupied ID 151. The runner rebuilds
all private objects with `make -B` to prevent stale compile-flag reuse.

Five real native help files are packaged under `help/`, with the actual
`hollowdeep_help.c` dispatcher supporting the following syntax:

| In-game command | Help file |
|---|---|
| `help necromancer` | `help/necromancer` |
| `help raise skeleton`, `help raiseskeleton` | `help/help.150` |
| `help deity` | `help/deity` |
| `help *deity` (authorized DM) | `help/help.151` |
| `help corpse`, `help sacrifice`, `help raise corpse`, `help sacrifice corpse`, `help loot corpse` | `help/corpses-pending` |

The main help menu, `dmcommands`, and `skills` / `skills all` are updated.
The public deity guide does not expose DM powers, and the staff help page
requires both native DM class and staff administrator-level authority.
The corpse page is explicitly marked planned: the physical corpse, sacrifice,
and loot transactions have not been implemented.

`stage_help.py PRIVATE_WORLD` installs the five files into a new isolated
world's `help/` directory (the actual native `DOCPATH`). It refuses live
paths, symlinks, and conflicting existing help pages. The private test runner
installs the pages in its own fixture and tests the actual native dispatcher
with a file-opening test double. It is not an interactive telnet gameplay
replay. For the final approved production deployment, include these exact
files in the live world's help directory, back up any existing pages first,
and verify each page from a real player and authorized DM session. No live
help files are changed by this package.

Local tests passed against both exact source profiles, including native
DM persistence, help routing, skill eligibility, duplicate command ID and
permission safeguards, legacy/private syntax, and refusal of conflicting
help files. ELF32 compilation and interactive gameplay remain pending.

## Operator-reported integrated ELF32 validation — 2026-11-16

At pinned commit `57f4eba8ac518e1166ad4577256bffb4fdcd1ca0`, the maintainer reported PASS for the coupled Round74B source profile, command ID 151, deity assignment/persistence and authorization, real help files and help routing, legacy/private syntax, and the private ELF32 build. The accepted private workspace is `necromancer-playtest-deity-CkReDa0Q`. Production deployment: NONE. These are operator-supplied focused C and compiler results, not independent live access or a socket gameplay/crash/restart test. Keep release private. Next: integrate physical monster corpses, exactly-once loot release, deity-only sacrifice, Necromancer raising and matching native help, then run combined isolated gameplay and persistence tests. Favor and durable pet state remain separate release gates.
