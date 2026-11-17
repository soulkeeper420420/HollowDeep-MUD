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

`raise skeleton` summons one skeletal servant for two minutes at a cost of
8 MP. The skeleton follows the caster and assists their attacks against
monsters, but cannot kill a target by itself. It carries no loot, is worth no
XP or gold, and disappears on expiry, owner death, logout or destruction.

The historical `raise` social action is **still available** for other
arguments; `raiseskeleton` is also an exact alias.

**This is a test-only skill:** its implementation requires
`HD_NECROMANCER_PLAYTEST` and a disposable source copy. The first skill does
not depend on actual bones/corpses, does not interact with PvP, and does not
persist pets in player save files.

## Which C files control which parts?

| Source | System |
|---|---|
| `command1.c` | Necromancer class selection (underlying Mage ID) |
| `hd_player_store.c`, `hd_player_store.h` | Saved identity marker, native character/receipt save and reload |
| `player.c::title_ply` | Displays Necromancer as the character title |
| `global.c::cmdlist` | Maps `raise skeleton` and preserves existing raise social |
| `hd_necro_skeleton.c` | Single temporary summon, timer, owner, pet combat and cleanup |
| `command5.c::attack()` | Safe, nonlethal pet assistance after an owner attack |
| `command2.c::move()` | Following normal player room movement |
| `update.c::update_game()` | Expiration and cross-room reconciliation |
| `creature.c::die()`, `player.c::uninit_ply()` | Cleanup when the owner dies or logs out |
| `files1.c::free_crt()` | Prevent dangling pet pointers during entity/room destruction |
| `Makefile` | Builds the skill only with `NECROMANCER_PLAYTEST=1` |

Detailed tests and design limitations:
[Raise Skeleton source guide](../tools/necromancer/raise_skeleton/RAISE_SKELETON.md).

## Roadmap after the first skill

1. Test Necromancer selection and `raise skeleton` inside a real isolated
   ELF32 MUD session on Linode.
2. Verify follow, combat, expiry, death, logout/reconnect and restart against
   disposable native rooms/player saves, plus previous game regressions.
3. Tune MP, duration, damage and cooldown based on gameplay results; add a
   controlled `dismiss skeleton` command if desired.
4. Only then consider additional skeleton orders, minion talents, curses and
   Graveburst as a later rebirth-specific skill.

The user's requested 65 starting stat points, half-cost first-life training
and one-level-per-`train` progression remain separate Round 74B systems. This
prototype does not change the live MUD or silently deploy new game mechanics.

No website, Discord or player-facing "live feature" announcement should
claim the class/skill is enabled before the real game is deployed and tested.
