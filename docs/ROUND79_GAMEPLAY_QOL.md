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


## Round 79B — Visible HP / MP / Breath status and creation-time ANSI

**Requested priority change:** implement the on-screen status prompt and ANSI
selection before the planned encounter and sacrifice features.

### Status display

Plain (ANSI off):

    HP 14/25 | MP 5/10 | Breath --

Colored (ANSI on): same words and numbers, with HP green/yellow/red according
to remaining health, MP blue and Breath cyan (red/yellow near exhaustion).
Always reset colors after each component. ANSI color codes are sent only if
the player explicitly selected ANSI. Both modes must be readable on Telnet
clients that do not support colors.

The verified legacy game prompt is approximately "(14 H 5 M):". The original
creature serialization contains hpcur/hpmax and mpcur/mpmax, but **no proven
numeric Breath field yet**. The current pure formatter shows "Breath --"
until native breathing mechanics and their persistence are verified. Never
fabricate "100/100" when no real meter exists. The rendering API accepts
actual breath current/max only when verified game state supplies them.
Breath/air capacity mechanics are a separate native test gate.

### Creation-time color selection

After race selection, before password entry, ask:

    Enable ANSI colors? (yes/no):

Accept y/yes/on, n/no/off, case-insensitively; reprompt on invalid input.
Use the existing native PANSIC character flag (bit 26) for saved preference;
do not add fields to creature or change player-save ABI. The existing PPROMP
flag (bit 18) controls whether a status prompt is shown. Retain the existing
behavior for already-created players; new character creation can enable
the readable prompt after confirmation. Never send ANSI control sequences
to users who selected NO. No color selection or prompt change is deployed
on production without separate approval.

### New source and unit tests

- tools/gameplay/round79/hd_status_hud.{h,c}
- tools/gameplay/round79/test_status_hud.c
- tools/gameplay/round79/hd_ansi_choice.{h,c}
- tools/gameplay/round79/test_ansi_choice.c
- tools/gameplay/round79/native_status_ansi_probe.py (read-only native audit)

Run these as standalone, native-independent checks with cc -std=gnu89.
They are pure tests; the actual native prompt and character-creation handlers
have **not yet been patched**.

Run the read-only audit ONLY on the disposable Round 78E private build.
It prints exact native player.c prompt, command1.c creation choices,
global command table, mtype.h ANSI flag and breath mechanics references.
Inspect that report before writing a strict source patch. Native tests must
verify HP/MP after combat/healing, ANSI YES/NO, failed invalid selection,
save/reconnect preference, plain text no escape bytes, existing Mage,
Necromancer and Warlock creation, and unchanged legacy saves.

The live service, world, character saves and database remain untouched.
