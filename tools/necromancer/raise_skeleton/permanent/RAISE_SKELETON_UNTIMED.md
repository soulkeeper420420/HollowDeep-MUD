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

## Integrated Round 74B SHA repair (2026-11-16)

The earlier untimed patch failed in the user's disposable stage because its
input allowlist expected only the first-skill `creature.c` and `command1.c`.
The actual source also carried the reviewed Round 74B banked XP and
life-dependent death progression. The **complete operator-supplied creature
diff** was reconstructed byte-for-byte against the pinned first-skill baseline:

- First-skill `creature.c`: `9a1c158811a1c96d4f0190f4c88876afb9dc16d1edba12e08a4dcc18c7f21243`
- Round 74B integrated `creature.c`: `6df6f74bce702363c9eae7506d96c962b9b3e3d3e178f07f7ea61015b07c9001`
- Round 74B integrated `command1.c`: `c8525fb2615c49e9c5cebcf321b83b28a3eaa0fea2a8c8bb372904bef20ddd1e` (operator-reported fingerprint)

The patch now accepts **only** the paired first-skill fingerprints or the
paired Round 74B integrated fingerprints. Mixed pairs and arbitrary drift
are rejected before any source writes. The integrated profile additionally
requires its XP helper files and actual life-based functions, and the
Necromancer creation entry. We did not remove or weaken the SHA guard.

Local verification: exact reconstruction of the user's `creature.c` checksum;
paired-profile allow/deny unit tests; an isolated synthetic integration
replay applying the patch to those exact `creature.c` bytes (with a
locally simulated `command1.c` contract); unchanged old XP/death functions;
no-op rejection on repeat invocation; native gnu89 syntax for integrated
`creature.c`, and 64-bit lifecycle/healing tests under normal and ASan/UBSan
builds. **The user's exact `command1.c` bytes are not yet uploaded;** the
real Linode run is still required to confirm all its anchors and complete
the combined 32-bit build. There was no production deployment/restart.

## Operator-reported Linode Round74B-integrated ELF32 validation — 2026-11-16

The maintainer executed the pinned one-pass script against the recognized
**Round74B-integrated** `creature.c` and `command1.c` pair at
`82a3c3c6bea8e216a65370a3fbfc06216df44762`. The operator-supplied
terminal result reports:

```text
NECROMANCER: coupled Round74B creature/creation SHA allowlist; mixed and drifted profiles refused PASS
NECROMANCER: accepted exact private input profile: round74b-integrated
NECROMANCER: no-timer corpse HP/MP and healing patch staged privately
NECROMANCER: verified kill HP/MP, mana charge, unlimited duration, reconnect, death cleanup PASS
NECROMANCER: actual native Vigor/Mend/Restore + targeted healing potions PASS
NECROMANCER: legacy branch syntax PASS
NECROMANCER: private branch syntax PASS
NECROMANCER: corpse-derived no-timer healing ELF32 build PASS
NECROMANCER: PRIVATE CORPSE SKELETON AND HEALING PASS
NECROMANCER: UNTIMED CORPSE HP/MP + NATIVE HEALING ELF32 PASS
PRODUCTION DEPLOYMENT: NONE
PINNED COMMIT: 82a3c3c6bea8e216a65370a3fbfc06216df44762
```

**Evidence scope:** SHA-guarded patch staging, focused native C lifecycle,
healing functions and ELF32 compile. These markers are **operator-provided**,
not independently fetched Linode logs. Do not claim any actual player socket,
monster kill, in-game room follower, save/restart or cross-process pet
persistence test has passed. The pet is process-memory-only and can be lost
on server restart; this **does not yet satisfy** the full rule "stays until it
dies" across outages. Keep the feature **private / NO-GO** until real
isolated gameplay and a crash-safe pet-state restore/rollback pass.

Next focus: a disposable **real MUD player session** that kills a monster,
runs `raise skeleton`, confirms HP/MP, casts Vigor/Mend/Restore and feeds a
healing potion, moves rooms, disconnects/reconnects, kills the pet, and checks
no XP/loot duplication. Then design durable pet saves so an untimed pet does
not silently disappear on a graceful restart or crash, without altering
the native creature ABI or trusting client-supplied state.

## Real-game socket acceptance (new private test)

The focused C tests and operator's private ELF32 build are complete, but the
[disposable native socket gameplay smoke](gameplay/README.md) is the next
gate. It compiles a private fixture (Necromancer + a one-HP victim with
147 maximum HP / 51 maximum MP), starts a loopback-only native game listener
from the verified private binary, kills the victim through the real player
command, raises its skeleton, denies a duplicate summon and checks that the
pet remains visible after logging out and back into the **same** process.
**This gameplay script is published but not yet run on Linode.** It does not
prove healing spells/items via player commands, following into a second room,
monster-vs-pet damage, or restart durability. Its result must not be used
as authorization to deploy. Production remains unchanged.
