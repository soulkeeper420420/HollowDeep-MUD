# HollowDeep: Rise of the Necromancer

## Private acceptance release

Round 75F gameplay acceptance passed.

- Necromancer character creation and randomized stats.
- Prime attributes: Intelligence and Piety.
- Raise Corpse and RC alias.
- 120-second cooldown and 5% unique revival chance.
- Capacity of 3-12 raised undead.
- Universal Conjure with six companion species.
- One persistent companion with a 300-second cooldown.
- Persistent companion XP and levels.
- Independent combat-death loot.
- Native help and skill catalog.

Production compatibility and deployment remain pending.
Rebirth skill remains deferred.

## Historical development notes

Earlier descriptions below are superseded.

# HollowDeep Necromancer — Developer and Player Guide

**Private playtest only. Not available in the live game.**

## Class design

The Necromancer is the first new HollowDeep class in development. Its
player-facing identity is stored as a protected identity marker in the existing
compressed player-save receipt. Its native numeric class remains `MAGE` for
now because numeric class IDs also index combat/training arrays and influence
staff permission checks. This is deliberate; never renumber the existing
classes to add a Necromancer.

The prototype identity and its initial ELF32 verification script are at
[`tools/necromancer/build-and-check.sh`](../tools/necromancer/build-and-check.sh).

## First skill — Raise Skeleton

`raise skeleton` costs **8 MP** and requires a monster the Necromancer actually
killed in the current room. The one-use kill record captures that monster's
**maximum HP and MP**, which the raised skeleton receives at full health/mana.
There is **no duration timer**. The skeleton assists the caster's attacks but
cannot independently kill its target, and its own death gives no XP/loot/gold.
It can receive Vigor, Mend, and Restore healing spells and compatible wands,
scrolls, or `drink <healing potion> on skeleton`. The pet remains in memory
through a logout and same-process reconnect; restart durability is not yet built.

The historical `raise` social action is **still available** for other
arguments; `raiseskeleton` is also an exact alias.

**This is a test-only skill:** its implementation requires
`HD_NECROMANCER_PLAYTEST` and a disposable source copy. The first skill uses a trusted monster-death snapshot instead of a physical
corpse object, does not interact with PvP, and does not yet persist pets in
player save files. **A server restart or room unload can still remove a pet;
durable until-killed persistence remains a release blocker.**

## Which C files control which parts?

| Source | System |
|---|---|
| `command1.c` | Necromancer class selection (underlying Mage ID) |
| `hd_player_store.c`, `hd_player_store.h` | Saved identity marker, native character/receipt save and reload |
| `player.c::title_ply` | Displays Necromancer as the character title |
| `global.c::cmdlist` | Maps `raise skeleton` and preserves existing raise social |
| `raise_skeleton/permanent/hd_necro_skeleton.c` | No-timer pet, inherited HP/MP, owner reconnect, pet combat and cleanup |
| `command5.c::attack()` | Safe, nonlethal pet assistance after an owner attack |
| `command2.c::move()` | Following normal player room movement |
| `update.c::update_game()` | Cross-room reconciliation without expiration |
| `creature.c::die()`, `player.c::uninit_ply()` | Capture killed monsters, clean up slain pets, retain pets through owner death/logout in one process |
| `files1.c::free_crt()` | Prevent dangling pet pointers during entity/room destruction |
| `Makefile` | Builds the skill only with `NECROMANCER_PLAYTEST=1` |

Latest design and limitations:
[Untimed Raise Skeleton source guide](../tools/necromancer/raise_skeleton/permanent/RAISE_SKELETON_UNTIMED.md).
The [earlier two-minute prototype](../tools/necromancer/raise_skeleton/RAISE_SKELETON.md) remains available for comparison.

## Roadmap after the first skill

1. Test Necromancer selection and `raise skeleton` inside a real isolated
   ELF32 MUD session on Linode.
2. Verify follow, healing spells/items, pet death, logout/reconnect and restart against
   disposable native rooms/player saves, plus previous game regressions.
3. Tune damage/cooldown, implement durable restart-safe pet persistence, and add a
   controlled `dismiss skeleton` command if desired.
4. Only then consider additional skeleton orders, minion talents, curses and
   Graveburst as a later rebirth-specific skill.

The user's requested 65 starting stat points, half-cost first-life training
and one-level-per-`train` progression remain separate Round 74B systems. This
prototype does not change the live MUD or silently deploy new game mechanics.

No website, Discord or player-facing "live feature" announcement should
claim the class/skill is enabled before the real game is deployed and tested.

## Isolated interactive verification

A new [private socket gameplay replay](../tools/necromancer/raise_skeleton/permanent/gameplay/README.md)
seeds a disposable native Necromancer and monster, performs real commands
and verifies an untimed 8-MP summon inheriting 147 HP / 51 MP and a
same-process reconnect. The script is ready for Linode; actual gameplay
results are still pending. Pet healing handlers have passed private C tests,
but interactive spells/items and restart-safe pet persistence remain separate
NO-GO gates before production.

## Deity allegiance and corpse sacrifice (private development)

The DM-only `*deity <saved-player> <0-16>` assignment system is in the
[private deity package](../tools/necromancer/deity/README.md).
`*deity <player>` reads the stored assignment, `*deity list` shows ID slots,
and ID **0** clears allegiance. The game has no legacy `deity` field;
`worship` was only a social emote. The guarded new module stores a versioned,
strictly validated record in `hollowdeep-data/deities.db` and demands both
native DM class and audited staff-admin authority. It never changes class IDs
or the player binary serializer.

The corpse/loot stage is **next, not implemented by this patch**. A monster
corpse must own its original inventory and gold until a single server-side
consume operation releases them exactly once. Ordinary players will use
`loot corpse`; deity followers can `sacrifice corpse`; a Necromancer can
`raise corpse`. If allegiance storage is unreadable, sacrifice must be
denied. Death auto-drop, room serialization, crash rollback, summoned-pet
no-loot rules and favor-credit durability are still separate release gates.

### Native in-game help (private deity and Necromancer build)

The corrected private patch accepts the complete, independently reconstructed Round 74B source fingerprint and gives `*deity` command ID 151 (150 remains `raiseskeleton`). Every feature milestone must supply its native in-game help pages, its relevant help index/skill/staff visibility updates, and a regression that opens those pages before release. The new [native help files](../tools/necromancer/deity/help) cover `help necromancer`, `help raise skeleton`, `help raiseskeleton`, `help deity`, authorized `help *deity`, and a clearly labeled development-status `help corpse` / `help sacrifice` page. `skills` lists Raise Skeleton only for verified eligible Necromancers, while `skills all` shows the class requirement. `dmcommands` lists deity administration only for an authorized DM. The private [help installer](../tools/necromancer/deity/stage_help.py) installs these pages into the native `help/` directory of an isolated world; conflicts are refused. For a future approved live deployment, back up existing help files, install the reviewed runtime pages, and test through player and DM sessions. **Nothing has been installed in the production game yet.**

## Corpse consumption and deity sacrifice — newest private milestone

The operator reported ELF32 deity and native help PASS at `57f4eba`.
The new [corpse playtest package and source map](../tools/necromancer/corpse/README.md)
adds room-visible corpse IDs, transfer of actual inventory tags and gold, shared
one-use `loot corpse [id]`, `sacrifice corpse [id]` (valid deity), and
`raise corpse [id]` (Necromancer, 8 MP). `raise skeleton` remains an alias.
The same corpse cannot feed two actions in a single process. Failed actions
leave loot intact. The older last-kill snapshot path is disabled under
`CORPSE_PLAYTEST=1`, and native help routes now open the bundled active
private-feature pages rather than the historical pending page. Seven runtime
help files are staged in the test world. Local C, sanitizer, native healer,
help and reconstructed-source syntax tests passed. The operator has not yet
run this new ELF32 build or a real socket replay. Room-local corpse escrow is
not yet durable; room unload/restart, registry capacity fallback, pet state,
crash-safe exactly-once transactions and rollback are explicit release blockers.

## Same-process room-cache persistence (next private milestone)

The previous combined corpse candidate passed a complete operator-reported native socket replay, including same-process logout/reconnect. The [cache milestone](../tools/necromancer/cache/README.md) now preserves living pets and corpse escrow through native room-cache eviction/reload, excludes registered pets from room saves, removes the fixed corpse registry ceiling, reserves the Necromancer title for the verified class (the old Mage level 7-9 title becomes Conjurer), and provides seven ASCII help pages. Local reconstructed-source tests passed, including native LRU and both room replacement paths; Linode ELF32 and repeat socket tests remain pending. This does not persist corpse escrow or pet state across process restart. Durable ownership, exactly-once crash recovery, capacity and rollback are still required. No live deployment.

## Native saved-pet storage foundation (private, not gameplay-enabled)

The [pet storage API](../tools/necromancer/petstore/README.md) works with the exact verified Linode source handoff. It stores versioned HP/MP, room, character epoch and revision in a reserved existing receipt, uses the native atomic player-file writer, and supports an atomic 8 MP debit plus staged pet record, checkpoint and death tombstone. Local multi-process native64 and sanitizer tests passed; Linode ELF32 pending. The API is not called by any game command or lifecycle path yet. Do not claim skeleton survival across a complete server restart until the corpse/loot transaction journal, runtime recovery, actual socket replay and rollback pass. Three private native help pages retain the restart limitation. Production remains untouched.

## Private saved-pet runtime restart milestone

The [runtime integration](../tools/necromancer/petruntime/README.md) hooks the verified ELF32 pet store into raise, login, follow, eviction, update/command checkpoints and native death. A saved living skeleton is restored when its verified owner logs in, with saved HP/MP, no extra raise charge; a committed death tombstone prevents resurrection. Seven ASCII help pages updated. Exact-source native64 focused replay passed locally; full ELF32 and actual listener restart/death test pending. Corpse inventory and released floor loot remain process-local; the private fail-stop policy is not a production recovery strategy. No deployment.
