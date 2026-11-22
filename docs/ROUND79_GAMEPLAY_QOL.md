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


## Round 79C — Breath is wilderness travel stamina (confirmed design)

The player has specified that **Breath is spent while moving through the
wilderness**, not an underwater oxygen meter. The status prompt should read
e.g. "HP 14/25 | MP 5/10 | Breath 98/100" and use ANSI warning colors when
PANSIC is enabled. The native PBRWAT water-breathing flag remains unrelated.

Initial gameplay tuning (subject to private native balance testing):
- New characters begin with Breath 100/100.
- Exactly 2 Breath is consumed **only after a successful movement to a
  wilderness room**, including entry from a town. A blocked exit or rejected
  movement must never drain it. A teleport, look, login or map redraw must
  not count as a walking step.
- Movement into ordinary rooms, including leaving wilderness for an indoor
  safe area, costs 0 and must always be permitted even at 0 Breath.
- At 0 or 1 Breath, further ordinary moves into wilderness are denied with
  clear feedback. The player can rest or recover, not get permanently stuck.
- Recovery on the existing *native timed recovery tick* is +5 normally
  and +15 if resting. These are per-tick values; actual tick duration
  and secure resting state must be verified before hooking the engine.
  Repeated "rest" commands must not grant unlimited recovery.
- Breath can never be negative or exceed 100. Breath is not HP and does
  not directly damage, kill, change MP, award XP, or alter monster AI.
- Determine wilderness classification from actual native room metadata /
  verified wilderness-room ranges. Do not guess from a new map drawing
  or silently treat all high room IDs as wilderness.
- A player save/reconnect or server restart must **not** refill the meter
  just to circumvent an exploration limit. Verify an ABI-safe durable
  character-state slot/receipt before enabling native usage.
- Ordinary Mage, Necromancer, Warlock, Conjure, existing wilderness map,
  room exits and native player saves must continue to work.

Source-only preliminary implementation:
- hd_wilderness_breath.h/.c: bounded movement gate, successful-step charge
  and timed recovery, with no direct native game dependencies.
- test_wilderness_breath.c: 50 moves to exhaustion, denial of deeper
  wilderness, free retreat, resting/regeneration, indoor immunity, invalid
  input rejection and integration with the plain/colored status formatter.
- native_wilderness_breath_probe.py: read-only audit of movement,
  regeneration and room-zone classification in the disposable ELF32
  Round 78/79 source.

The *rules library is not a native movement hook*. Mandatory acceptance
before gameplay use: private source audit; clear definition of successful
movement; native regeneration cadence; atomic/ABI-safe persistence;
native ELF32 compile; 100-room wilderness route replay; blocked exits;
safe retreat at exhaustion; timed recovery without command spam;
logout/reconnect; ANSI YES/NO display; existing class/conjure/corpse
regressions; production PID and binary unchanged.

No production deployment or service restart has been authorized.


### Round 79C private rules verification (2026-11-21)

Isolated Linode results reported:
- Wilderness Breath movement and regeneration rules: PASS
- Read-only native movement audit: PASS (262 extracted source lines)
- Native wilderness movement integration: PENDING
- Production deployment: NONE

The source audit contents remain private and must be examined before
choosing native movement hooks, regen cadence or durable character storage.
A passing standalone rules test is not a completed native gameplay test.
The Linux shell reported that `breath` is not a shell command, which
is unrelated to the in-game Breath status display.

Next acceptance gate: inspect the native movement report in a private
workspace; then stage actual movement/recovery hooks only after examining
the native source, compile ELF32 and run successful/blocked movement,
safe-retreat, regeneration, logout/reconnect and class regressions.


## Round 79D - Exact native movement-hook audit

The uploaded Round 79C read-only report contains 262 source lines but does
NOT locate the movement-success path. It shows incidental room references
in command1-6.c and login/logout logic in player.c; neither is sufficient
to debit Breath on a completed step. It also does not establish a durable
Breath field or the correct timed recovery callback.

The revised native_breath_hooks_probe.py searches ALL *.c sources from
the isolated ELF32 Round 78/79 candidate for actual calls to
add_ply_rom/del_ply_rom, character rom_num mutations and move helpers.
Its bounded output also extracts wilderness classification, player
recovery timers, exact HDTR1 receipt-store interfaces and prompt/ANSI
code. The report remains private on Linode, not in GitHub.

Separately, stage_ansi_creation.py had a Python line-continuation syntax
error. Round 79D corrects the syntax before running any Round 79B build.
The private staging tests, real class-creation socket acceptance, Breath
persistence, player prompt, and real wilderness movement remain gates.

Do not treat a read-only source report or 79C pure rules PASS as native
Breath gameplay PASS. The next native implementation must use only exact
audited source anchors, preserve existing player-save ABI and old-world
movement, and never modify or restart the live service.


### Round 79D isolated native acceptance — verified from Linode output

The private run reported the following, without touching production:
- 10/10 Python staging + source-audit tests passed.
- Standalone HP/MP/Breath ANSI formatter test passed.
- Standalone character-creation ANSI choice parser test passed.
- Native ANSI creation was staged and compiled successfully as ELF32.
- Creation socket regressions passed, including a saved ANSI preference for
  Necromancer (YES) and Mage (NO). The Mage probe printed ANSI=0.
- Warlock reconnect/identity regression passed.
- Native help/skills regression passed.
- Production service PID was unchanged and no deployment occurred.

Status HUD rendering in the native player prompt is NOT YET INTEGRATED.
The wilderness Breath resource has NOT YET BEEN CONNECTED to native
movement, recovery ticks, or persisted player state.

The private audit generated two reports that remain solely on Linode:
- A private breath-hooks-report.txt (534 movement/recovery/receipt/prompt source lines).
- A private native-status-report.txt (308 prompt/ANSI/Breath code excerpts).

The source excerpts must be reviewed before patching player.c or committing
any native Breath storage and debit hooks. Do not publish private logs or
fixtures to GitHub.


## Round 79E - Native ANSI status prompt staged privately

The submitted native source audits identify a concrete, safe display hook:
player.c's ply_prompt() (legacy static prompt[40]) contains the existing
HP/MP prompt and is gated by PPROMP, PALIAS, PSPYON and PREADI. The
Round 79E status patch expands that prompt buffer to 256 bytes and uses
the existing standalone hd_status_hud_format() function to render:
- ANSI enabled (saved PANSIC): colorized exact HP/MP current/max values.
- ANSI disabled: exact HP/MP values with no escape sequences.
- Breath until a real durable movement resource exists: "Breath --".
- Preserve absent prompts for private/staff states, alias target HP/MP,
  and the native fallback when PPROMP is off.

The patch is opt-in STATUS_HUD_PLAYTEST=1 and is staged only from the
verified private Round 79 ANSI-creation candidate into a new, disposable
Round 79 HUD source tree. It does not modify player-save ABI, current
player records, running service, production world, or Breath economics.

Files: stage_status_hud.py, test_stage_status_hud.py,
private_status_hud.sh, and native_wilderness_move_exact.py.
Native socket acceptance checks ANSI-on Necromancer, ANSI-off Mage,
saved creation preferences, Warlock persistence, and legacy help.

The source audit reveals native hd_wilderness_move in the command
table and the wilderness.map tile reader, but does NOT give complete
successful-transfer, recovery or atomic save code. The focused
native_wilderness_move_exact.py extracts a bounded code excerpt of
the actual handler to choose a proper Breath pre-move gate and
post-success debit. DO NOT hook Breath directly to a redraw or a
direction command, and do not refill it on logout/reconnect.

Round 79E is **published as unverified private development**, pending
the native build/socket results from Linode. No deployment approved.


### Round 79E — Private HUD socket acceptance and harness fix

The private Linode run confirmed:
- Ten Python staging/audit tests passed.
- ANSI status rendering and native ELF32 compilation passed.
- Native Necromancer and Mage creation, saved ANSI YES/NO choices, and
  ANSI-colored/plain HP/MP/Breath-- status prompts across reconnect passed.
- Production remained unchanged.

Warlock validation was blocked before opening a socket by the test harness
directory allowlist: the new isolated HUD directory has a distinct
round79hud prefix. The regression harness and exact wilderness source
audit now accept that specific additional private build prefix while still
requiring a real ELF32 source in /tmp and isolated networking for sockets.
A separate unit test covers the new private directory and rejects production
and invalid executable paths. The game executable is NOT implicated by the
original Warlock harness refusal.

Only resume Warlock and help regressions and run the focused wilderness
movement source audit against the already built private ELF32 HUD candidate;
do not needlessly recompile the tested native game or replay passing class
creation tests. Actual Breath depletion and persistence are still pending.


### Round 79E final private regression verification

Linode's targeted retest verified, after fixing the strict disposable-source
directory allowlist:
- Private-path security regressions: 5 tests passed.
- Native Warlock creation/reconnect, class isolation: PASS.
- Native Necromancer help and skills regression: PASS.
- Native status HUD and saved ANSI preference had already passed in the
  earlier private ELF32 build and character-creation/reconnect socket test.
- Source-only wilderness movement handler inspection: completed; actual
  Breath debit and durable storage remain pending.
- Production binary and service PID remained unchanged; deployment: NONE.

The generated exact wilderness movement inspection report remains in the
private Linode test directory and must not be committed to GitHub. Review
that report before selecting the movement completion/debit site, resource
checkpoint, failure/rollback handling and timed recovery integration.

The playable Breath meter is NOT complete. Do not conflate the completed
HUD and ANSI functionality with native Breath travel and persistence.


## Round 79F — Verified wilderness move wrappers and Breath receipt wire

The Round 79E focused movement audit supplied the exact existing native
wilderness.c entry points:

- hd_wilderness_move() saves the previous room, calls move(), and then calls
  hd_wilderness_after_move().
- hd_wilderness_go() follows the same pattern but calls go().
- hd_wilderness_after_move() already compares the old and new room numbers
  and suppresses redraw when the room did not change. This is a credible
  POST-success integration point for Breath charging.
- The route into the destination must be known BEFORE calling move/go to
  enforce an exhaustion gate. The wrapper alone cannot assume a command
  succeeded. Inspect exit selection and hidden/locked door checks before
  patching a pre-move gate.
- Native wilderness.map has explicit tile IDs and terrain; do not assume
  every room with ID above 10000 is walkable wilderness. The current map
  reader enforces a tile schema and a 6000-row limit.
- player.c has LT_HEALS timed HP/MP recovery, but this does not prove that
  it should be the Breath recovery clock or that repeated REST commands
  cannot regenerate on demand. A native timer callback must be reviewed.

New tools/gameplay/round79/hd_breath_record.h/.c supplies a pure 64-hex wire
format suitable for one HDTR1-style receipt value, matching the *width*
of the existing receipt metadata. The record contains:
- Format version, 96-bit character epoch, revision, last recovery timestamp,
  current Breath, fixed maximum 100, and reserved bytes.
- Strict encode/decode, input range and nonzero epoch checks, reject corrupt
  or noncanonical records, no partial output on error.
- Two deterministic state actions: exactly one successfully completed
  wilderness travel debit (-2), or a verified timed recovery (+5 normal /
  +15 resting); no update for ordinary indoor moves.
- Replay/ordering guard via expected revision and same-second recovery denial.
  It does not implement durable locking/CAS by itself.
- Free retreat to an interior remains possible even when Breath is 0,
  the state revision is exhausted, or the wall clock is unavailable.

test_breath_record.c checks the wire roundtrip, fifty wilderness moves to
exhaustion, safe retreat, rest recovery, repeat recovery denial, input
corruption and ANSI HUD rendering with a real numeric Breath reading.

### Still required before activating native Breath

1. Identify a collision-free and server-reserved Breath receipt ID and a
   durable owner/epoch binding contract.
2. Extend the EXISTING native player-store transaction under its lock for
   revision-checked Breath state updates. Both ordinary save and recovery
   replay must preserve the record without dropping other receipts, the
   pet roster, Conjure state or character inventory.
3. Identify a pre-move gate with the resolved destination and a post-success
   charge. A failed persistence write must never allow free repeatable
   wilderness movement. Test injected short writes, crashes and retries.
4. Derive time-based Breath recovery from a verified native timer and test
   both normal and REST rates without command-spam farming.
5. Feed the stored Breath into the existing ANSI/plain HUD. Do not display
   100/100 until the native saved resource actually exists.
6. Run ELF32/private world native movement, repeated travel, exhaustion,
   free retreat, map redraw, old-world movement, save/reconnect and
   Necromancer/Mage/Warlock regressions, plus production safety.

The read-only native_breath_store_audit.py extracts the save, receipt,
legacy timer, location and prompt contracts from the already verified
private ELF32 HUD candidate. Run private_breath_record.sh in a disposable
results directory to execute pure unit tests and collect that report.

**This milestone is source development only. The Breath record has not been
written into the native atomic player store, and the game does not yet debit
or regenerate Breath during travel. Production remains unchanged.**


### Round 79F private Breath record validation

User-reported results from the isolated Linode private candidate:
- Round 79F persistent Breath wire, revision, HUD unit tests: PASS.
- Round 79C wilderness move drain and recovery rule regressions: PASS.
- Read-only native player-store/timer source audit: PASS (561 source excerpt lines).
- Existing private HUD ELF32 candidate unchanged.
- Production service PID, executable, and deployment: UNCHANGED / NONE.

The private audit report was retained on Linode and **was not uploaded** in
the validation output. Its contents must be inspected before integrating a
Breath-specific, collision-free reserved receipt, durable lock/CAS
transaction, regeneration callback, before-move exhaustion check or
post-success charge. None of those native hooks has yet been enabled.

The next implementation gate is to review only the private read-only
breath-storage-report.txt generated by native_breath_store_audit.py.
Do not publish that report, source excerpts, private paths or credentials
to GitHub; commit source patches and public-facing documentation only
after native integration and socket regression tests have passed.


## Round 79G — Mount-focused Breath direction

The player clarified that the reason to introduce wilderness Breath is a
future mount system including ordinary horses and rare dark dragons.
The approved design direction is to preserve **player Breath while walking**
and add a **separate Endurance pool for each owned mount**. Mounted steps
use mount Endurance rather than draining rider Breath. This must not
reset stamina or bypass the travel economy when mounting, dismounting,
stabling, calling or switching mounts. Mounts do not occupy Conjure or
Necromancer pet capacity.

Detailed mount tiers, wilderness terrain symbols, planned controls,
atomic persistence and native movement acceptance gates:
docs/ROUND79G_MOUNTS_AND_BREATH.md

The current implementation is only a **pure, native-independent terrain
and resource selection library** under tools/gameplay/round79.
Actual mounts, owned inventory, stables, flight, movement speed and the
durable player Breath receipt remain unimplemented. No production changes.
