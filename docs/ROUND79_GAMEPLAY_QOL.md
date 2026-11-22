# Round 79 - Gameplay Quality-of-Life (private development)

Status: **approved direction to improve gameplay; feature specs are proposals, not native implementations**.

Baseline: Round 78E's isolated Warlock creation/save/reconnect and the existing
Necromancer, Conjure, native corpse/loot/deity and mapradius gameplay.
Preserve all working mechanics and player records.

## 79A - Encounter scouting and combat clarity (first implementation target)

Add `consider <monster>`, but **only** if the native command table does not
already supply `consider` (reuse its handler if present; never shadow).
The command:
- Requires an alive, visible monster in the player's current room. Reuse the
  existing native visible-monster lookup; no searching hidden or adjacent rooms.
- Reports a qualitative danger estimate based on relative levels and existing
  visible state; do not reveal exact monster HP, secret flags, loot, or drops.
- Uses neutral risk labels: trivial, manageable, dangerous, deadly. Start with
  level-delta thresholds -5, -1, +3; rebalance after real combat playtesting.
- Never damages, attacks, puts a player in combat, changes hostility, consumes
  mana, awards XP, or modifies a corpse.
- Handles unknown, ambiguous, missing, protected, and malformed targets safely.
- Honors existing staff/invisibility protections, instance boundaries,
  temporary pets and native name-matching semantics.
- Displays a concise command hint via `help consider` and the registered
  command catalog.

Minimum tests: exact C source anchors, no command ID collision, ELF32 build;
visible monster, missing target, hidden monster, protected target, stronger
and weaker encounters; original game combat and save regressions; identical
character/world files before and after using the command.

## 79B - Ground item sacrifice and corpse cleanup (second)

Separate `sacrifice <ground item>` from the already implemented
`sacrifice corpse [id]`. Preserve corpse loot and Raise Corpse behavior.
- Only targets floor objects that the player can actually see and interact
  with; no inventory items, worn equipment, other players' possessions,
  protected/quest/admin items, or objects within containers.
- Reject ambiguity and multiple-object targeting unless the exact native
  selector has been validated. A failed attempt leaves the object unchanged.
- No reward, deity favor, XP, or gold until a safe, non-duplicating ledger
  contract is validated. Initially return an explicit feedback message for
  an eligible offering and remove exactly one object **only** if the native
  deletion/persistence path is proven.
- Combat, floor-drop ownership, offline inventories, corpse loot, NPC shop
  stocks and other rooms must remain unchanged.

Minimum tests: one visible floor object, multiple objects with same name,
protected objects, nested containers, corpse preservation, disconnect/restart
behaviour, atomic failure denial and ordinary object inventory regression.

## 79C - Exploration feedback (third)

Build on existing `showmap` and `mapradius 0-10`, not a second map engine:
- Add optional area/landmark labels on the native map if room metadata can
  support it without world-format migration.
- Make blocked direction and invalid map radius messages actionable.
- Preserve redraw suppression and one-redraw-per-movement behavior.
- Keep the map optional and disabled by default until approved otherwise.

Minimum tests: level 0/off, radius 1 and 10, invalid input, movement redraw,
wilderness 100-room batch, regular interior rooms, no exit/record changes.

## Implementation protocol

1. Inspect *actual* native handler and serializer APIs in a disposable
   /tmp/hd-army-game-* source tree. Fail closed if expected anchors drift.
2. Implement and test **79A first**. Do not ship all three in one native patch.
3. Compile ELF32 privately and run a loopback-only socket game. Retest
   Necromancer (Raise Corpse and RC), universal Conjure, Mage, Warlock,
   corpse loot, saves, and map behavior.
4. Commit only validated source, gameplay tests, and ASCII-compatible help.
   Do not publish private Linode paths, world data, test-account saves,
   credentials or raw logs.
5. **No edits to /srv/hollowdeep/world, no live player-save changes and no
   restart/deployment** without separate explicit user approval.

## Additional ideas for later

Roaming wilderness encounters, day/night effects, better inventory and item
identification, repeatable dungeon objectives, party XP/loot sharing, and
player events. Each needs a separate economy/security and balance review.
