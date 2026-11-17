# HollowDeep — Necromancer: Raise Skeleton (first skill)

**Private playtest only. Not deployed to the production MUD.** Built on the
Codex Necromancer identity prototype at commit
`3324e24c7ab2fa8fb60dae9965385fa4a41f9533`.

The base class remains **Mage for the engine's numeric class ID**. Changing
`MAGE` to an unused class number is unsafe: in this engine `class` participates
in staff permissions, combat arrays, and the binary saved-creature ABI.
Instead, the prototype records Necromancer identity in a reserved receipt
inside the existing atomic compressed character save; the summon checks that
verified marker via `hd_store_is_necromancer`.

## Skill rules (first private tune)

| Setting | Prototype behavior |
|---|---|
| Player command | `raise skeleton` (also `raiseskeleton`); other `raise` social commands work normally |
| Eligibility | Logged-in player with verified Necromancer identity and underlying `MAGE` numeric class |
| Minimum level | 1 (temporary development setting) |
| MP cost | 8; charged only on successful summon |
| Lifetime | 120 seconds of server time |
| Limit | One summoned skeleton per connected character |
| Follower | Appears in owner's room and follows normal movement; timer reconciles teleport paths |
| Combat | Helps only while the player attacks a real monster; light damage, 3-second cooldown |
| Kill/loot | The skeleton cannot deliver killing blows; has 0 XP, 0 gold, and no carried objects |
| End of life | Dismissed on logout, owner death, skeleton death, expiry, or source-room destruction |
| Persistence | **None.** The minion is session-only, not appended to creature or player files |

This is deliberately a *starter pet*. It has no independent AI, no orders,
no PvP targeting, and no personal loot. **Graveburst** remains a proposed
rebirth skill and is not implemented here. Do not advertise the pet or rebirth
features on the live website until final native gameplay validation and an
approved release.

## Files that control this skill

| File | Purpose |
|---|---|
| `tools/necromancer/raise_skeleton/hd_necro_skeleton.c` | Owner registry, summon, follow, capped combat assist, expiry and cleanup |
| `hd_necro_skeleton.h` | Forward-declared callbacks (avoids duplicate `mstruct.h` inclusion) |
| `apply_private.py` | Exact, all-or-nothing anchor checks before changing a **disposable** native source copy |
| `global.c` | Routes `raise skeleton` through a wrapper; retains ordinary `raise` social action; registers `raiseskeleton` alias |
| `command5.c::attack()` | Assists only if the native player attack did not kill the monster |
| `command2.c::move()` | Follows ordinary room movement |
| `update.c::update_game()` | Expires pets and follows other room transfers on a server tick |
| `player.c::uninit_ply()` and `creature.c::die()` | Removes pet on logout/player death |
| `files1.c::free_crt()` | Clears any pointer tracking when a monster/owner is freed |
| `Makefile` | Compiles new object only under `NECROMANCER_PLAYTEST=1` |
| `hd_player_store.c` (from prior prototype) | Persists and verifies Necromancer identity; **not edited by this patch** |

The skill does **not** modify `mstruct.h`, saved character format, class IDs,
monster template banks, world rooms, equipment, or the production executable.

## Testing

Local 64-bit C tests include: verified Necromancer identity; non-Necromancer
denial; invalid command; MP debit; duplicate summon rejection; actual monster
record flags; moving owner to a new room; bounded damage credited to the
owner; no killing blow; no XP/gold; cleanup via logout, free callbacks and
expiry; preservation of ordinary `raise` social actions. Normal and
ASan/UBSan builds have passed. Both the legacy and private C syntax checks
against the uploaded native source also passed.

The combined **ELF32 native build and actual game session** require Linode.
Run the published Necromancer `build-and-check.sh` first, which checks its
pinned source archives and creates a fresh private `necromancer-playtest-*/src`
folder. Then run `run_private.sh` with that directory and `HD_TEST_ELF32=1`.
Run a disposable native socket/world replay to verify summon, movement, combat,
reconnect, death and time expiry before considering any release. A standalone
C test and ELF32 compilation alone do **not** certify gameplay.

## Known limitations and hard gates

- **No native gameplay test yet.** Room broadcast messages, movement, attack
  assist and cleanup need the actual game loop and player session test.
- The existing engine's follower and monster-vs-monster systems are incomplete.
  This skill avoids `following` and `first_fol` pointer chains by keeping a
  separate, explicitly cleaned up **process-only** registry.
- The pet cannot deliver a killing blow or trigger autonomous experience or
  quest credit. Do not add pet-driven kill credit until attribution and
  exploit/dupe controls have been tested.
- Its owner is pinned by native creature pointer and the Necromancer saved
  identity is checked at summon. Session rollback/reload never persists a pet.
- Rebirth and first-life progression use separate save metadata; this patch
  does not attempt a new numeric class or character migration.
- No service restart, production world, website, or player files are touched.

## Suggested follow-up after private ELF32 gameplay replay

Tune mana cost, skill unlock level, duration, damage and cooldown using actual
player-vs-monster recordings. Add one safe `dismiss skeleton` command and
potential target restrictions, **then** consider additional minions, spell
advancement, curses, or a later Graveburst rebirth quest. The maintainer does
not need to edit C files manually; this guide explains exactly where they live.
