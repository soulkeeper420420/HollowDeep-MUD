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
