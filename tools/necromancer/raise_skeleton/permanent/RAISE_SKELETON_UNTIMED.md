# HollowDeep Necromancer — Untimed Raise Skeleton (private playtest revision)

**Status: private development code and focused C tests. Not deployed.** This
revision supersedes the earlier two-minute fixed-HP skeleton at
`tools/necromancer/raise_skeleton/RAISE_SKELETON.md`.

## Confirmed gameplay rule

- Summon with `raise skeleton`, costing **8 MP** on successful creation only.
- Must first kill a real monster in the **same room** as a verified Necromancer.
  The native death hook copies that monster's **maximum HP and MP** into a
  one-use corpse record before the engine frees the killed monster.
- The raised skeleton begins at **full inherited HP and MP**; no static HP
  formula and **no lifetime timer**.
- One skeleton at a time per character. The same kill cannot be raised twice.
- The pet can be wounded and **healed up to its original inherited HP cap** by
  native `vigor` / `mend-wounds` targeted spells, scrolls, healing wands, or
  `drink <healing potion> on skeleton` (also `use <potion> on skeleton`).
  Targeted `restore` wands or potions can refill HP and have the usual chance
  to refill MP. The potion must actually contain Vigor, Mend or Restore.
- The skeleton is removed when its HP reaches zero, without XP/loot/gold,
  and never serves as a source monster for another skeleton.
- It follows the owner, assists the owner's attacks conservatively, and cannot
  independently deliver a killing blow. Existing `raise` social gestures stay.

## Persistence and remaining limit

The pet **does not expire by elapsed time**, and it is retained in room memory
across owner logout and same-process reconnect. Owner death itself does not
kill the pet. **A complete server restart or unloading its room can still
remove it:** the native room/player save format currently has no durable
summon snapshot. Do not claim "until killed" persistence across server
restarts until the pet's ID, owner, inherited HP/MP, current HP/MP, room and
life/death tombstone are committed and reloaded atomically, with duplication
and crash tests. This is a hard production gate, not an intended feature.

## Source-file atlas

| Source | Why changed |
|---|---|
| `hd_necro_skeleton.[ch]` | No-timer pet registry, corpse snapshot, verified owner, stored HP/MP, follower, healing predicate, one-pet policy, safe free/reconnect |
| `creature.c::die` | Intercept skeleton death before loot/XP/chest hooks; record real monster's max HP/MP before freeing it; don't despawn pet when owner dies |
| `command1.c::login` | Rebind a pet retained in memory after a same-process reconnect |
| `magic2.c::vigor`, `magic2.c::mend` | Heal native room monsters safely; avoid writing to monster fd -1; clamp high-HP pet healing before short conversion |
| `magic3.c::restore` | Allow target pet via wand or configured potion, including HP and possible MP restoration |
| `magic1.c::drink` | Authorize only verified owner's pet as a healing-potion target, reuse native spell and charges, reject non-healing potion |
| `run_permanent_private.sh`, `apply_permanent_private.py` | SHA-guarded, all-or-nothing patch on an exact disposable private candidate, actual native C tests, both compiler paths |
| `onepass_linode.sh` | One chained build of the pinned Necromancer identity, original skill, and this revision as ELF32, without service changes |

The existing numeric character class ID remains `MAGE` for Necromancer. Its
private saved marker proves the distinct identity. The creature/object/room
ABI is untouched.

## Evidence and next gate

Local ELF64 tests passed for the actual `hd_necro_skeleton.c` lifecycle,
`magic2.c` Vigor/Mend, `magic3.c` Restore and `magic1.c` potion dispatch,
including HP saturation at 32767. ASan+UBSan passed on the same paths. Both
legacy and private C source branches passed syntax checks. The overlay refuses
source drift or a second application.

**Not yet verified:** ELF32 build on Linode, actual game login, monster kill,
room movement, potion inventory and healing commands, kill attribution,
server restart durability, and full World Builder/save regressions. These
must pass before any production release. Logs and private player fixtures
must remain off the public GitHub repository.

Only a restricted private source build is permitted by this milestone: no
live `hollowdeep.service` restart, player data mutation, public website update,
Discord announcement or game-world replacement.

## SHA mismatch diagnostics

The private SHA guard in `apply_permanent_private.py` expects the original
first-skill `creature.c` SHA-256
`9a1c158811a1c96d4f0190f4c88876afb9dc16d1edba12e08a4dcc18c7f21243`.
The operator reported `Source SHA mismatch or missing: creature.c` during the
one-pass Linode validation. **No live deployment occurred.** This means a
private source differs from the pinned first-skill stage; it does not establish
which edits are present. Do not remove the checksum check, replace the C file
from production, or run `patch --force`.

A read-only diagnostic is at
[`diagnose_creature_sha.sh`](diagnose_creature_sha.sh). It verifies the pinned
source archive, locates the newest private untimed build, reconstructs the
exact expected first-skill `creature.c`, reports the actual SHA-256, and prints
at most 100 diff lines. It refuses a production source path and never writes to
existing source, player files, or game services. The helper was locally tested
against both exact-baseline and pre-modified source copies. The patch now also
prints expected/actual SHA hashes on failure while still refusing drift.

**Current status:** needs the Linode diagnostic output before a safe rebase or
fresh candidate correction; the untimed skill has *not* passed Linode ELF32
validation. Preserve the older private test workspace for comparison.
