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


## Round 79H — Native atomic Breath receipt staging

The newly uploaded Round 79F audit establishes the native store's
private extension points:
- The existing reserved HDTR1 receipt IDs use suffixes 74 through 78.
- Native store_internal holds a directory flock(LOCK_EX) while it reads
  and writes checksum-protected player/receipt data.
- Ordinary player saves preserve the HDTR1 receipt trailer.
- Pet and Conjure storage already use locked CAS updates and the
  hd_atomic_player_snapshot writer, including uncertain rename handling.
- The original ELF32 creature ABI has no new Breath member.

Round 79G foot-versus-mount travel rules and the read-only mount command
audit both passed on the isolated Linode ELF32 test. Native mounts are
not yet implemented.

### Round 79H private, source-gated storage patch

stage_breath_store.py verifies the previous private Round 79E HUD
candidate and copies it to a NEW /tmp/hd-army-game-round79store-*
candidate. It does not edit the source baseline or production.

The new private feature gate HD79_BREATH_STORE_PLAYTEST:
- Reserves a separate HDTR1 receipt suffix 79 for Breath, including
  refusal to use it for public loot claims, without touching IDs 74-78.
- Installs hd_breath_store.inc in the existing native atomic store.
- Adds fail-closed read; one-time init with random 96-bit character epoch;
  and revisioned, expected-state CAS debit/recovery operations.
- Reuses player-file directory locking, HDTR1 encoding, compression
  and snapshot write mechanics. A before_rename fault denies mutation;
  an after_rename uncertain commit requires re-read reconciliation.
- Preserves the native character ABI, the existing pet/Conjure receipts,
  inventory and other player save data.
- Does not refill Breath on ordinary save or reconnect.
- Does not edit player.c, wilderness.c or the live service.

test_native_breath_store.c exercises reservation, init, 50 sequential
native receipt debits, exhausted travel denial, timed recovery, ordinary
save, stale CAS, before/after rename faults, Necromancer pet coexistence
and rejection of old character epochs after name reuse.

private_breath_store.sh compiles the ELF32 native receipt regression
and private full MUD executable, and checks the production PID/hash.

This patch is NOT YET TESTED ON LINODE. It contains the storage
operations but deliberately does not connect them to wilderness travel
or native timed recovery. A later integration must atomically checkpoint
both successful movement position and Breath. Charging one without the
other risks overcharging or allowing free travel across crashes or
write failures.

The six proposed mounts remain a separate milestone after the player
Breath store and native movement are validated. No deployment or
production restart has been authorized.


### Round 79H private native persistence acceptance — verified

The private Round79H Linode run reported:
- Seven private staging/security unit tests passed.
- Breath receipt successfully staged in a separate ELF32 source tree.
- Native atomic storage fixture passed one-time initialization, reservation,
  fifty movement debits, exhaustion, timed recovery, ordinary player-save
  preservation, stale revision rejection, pre/post-rename fault replay,
  Necromancer pet record preservation, and recreation epoch isolation.
- Private full ELF32 game compiled with Breath store enabled but gameplay
  movement and recovery hooks **disabled**.
- The live service PID and binary were unchanged; deployment: NONE.

The persistence functions have been verified with synthetic private players,
NOT through native player wilderness movement. The next milestone must audit
actual move/go destination selection and room transitions, and identify a
crash-consistent update strategy for *both* new room and Breath. A free
non-wilderness retreat must remain possible when exhausted. Source reports,
private fixture paths, logs, credentials and real player data remain off GitHub.


## Round 79I — Crash-consistent wilderness movement integration audit

The Round 79H native atomic Breath storage test has **PASSED on Linode**
for the private ELF32 synthetic native player-save fixtures:
- Seven secure staging/parser tests; successful private store patch + full
  ELF32 game build.
- Reserved Breath receipt initialized exactly once; 50 committed Breath
  travel debits to zero; exhaustion denied; timed recovery.
- Ordinary native saves preserved depleted Breath.
- Exact expected-state/revision CAS denies stale updates.
- before_rename failed writes denied, after_rename uncertain writes can be
  reconciled by re-reading the record without duplicate charges.
- Existing Necromancer pet save retained; name reuse gets a distinct epoch.
- Production PID and production executable unchanged; deployment NONE.

**Still not integrated:** native movement debit, the real timed regen
callback, the numeric Breath HUD or mount ownership. A native Breath
storage PASS is not a playable Breath PASS.

### Next safety gate — room and Breath must agree across crashes

The existing wilderness wrappers call move()/go() and compare the
previous and current room. That is good for detecting successful moves
but is NOT, by itself, enough for atomic Breath spending: a crash
between position persistence and receipt persistence could leave the
character in a different room with incorrect remaining Breath.

Round 79I source-only tooling:
- native_movement_atomicity_audit.py locates native definitions of
  move(), go(), wilderness map post-move handling, player update
  heartbeat, player save serialization and native exit structures
  from the verified private Breath-enabled ELF32 source.
- test_native_movement_atomicity_audit.py denies production locations,
  symlinks, wrong binary architectures and unrelated temp builds.
- private_movement_atomicity_audit.sh uses that tested private build
  only and checks production binary/service PID are unchanged.

The next implementation must arrange a single durable save transaction
for the player's resulting room and Breath charge, or a verified
equivalent recovery journal that preserves the same invariant under
fail injection. Pre-move gating must account for the resolved
destination, including locked/secret exits and safe retreat into
non-wilderness rooms; the post-move path must not charge aborted moves.
The native timer must not award repeatable recovery on command spam.

Mount travel will then choose between two saved resources: foot player
Breath and the currently ridden mount's Endurance. Mount stabling,
ownership and riding commands remain future integrations.


### Round 79I private read-only source audit — verified

The user reported this isolated Linode result:
- 6/6 source/parser/path-security unit tests passed.
- Read-only native move()/go(), room-commit, atomic-save source audit PASS.
- Private Breath-enabled ELF32 baseline and production service/binary unchanged.
- Production deployment: NONE.

This is an audit success only, not native movement/gameplay integration.
The full private movement-atomicity-report.txt has not been supplied in
the test output and should not be committed to GitHub. Review its
destination-resolution, authorization, room-change, and player-record
transaction excerpts before choosing an ABI-safe hook. Preserve
correctness across aborted movement, safe retreat, normal save, restart,
rename/short-write faults, pet/Conjure receipts, and player reconnect.
Do not charge just because a direction command was attempted, and do
not debit Breath separately from durable movement position without
a verified failure/recovery protocol.

Remaining: native wilderness movement Breath charging, timed regeneration,
numeric prompt, and mount ownership/Endurance/stables. No live deployment
or restart without explicit user approval.


## Round 79J — Private atomic room + Breath co-checkpoint

The uploaded Round 79I source inspection confirmed:
- Native update_ply() is the periodic player update function, with
  LT_HEALS controlling existing HP/MP recovery; this is NOT evidence that
  Breath recovery should fire on every command.
- The existing hd_wilderness_move()/hd_wilderness_go() wrappers call native
  move()/go(), then run hd_wilderness_after_move() only after the call.
  The existing callback checks previous/current room and redraws the map
  only for changed wilderness rooms. It is not an atomic save.
- The native hd_player_store.c calls write_crt_to_mem(), hd_receipt_encode(),
  hd_compress_bounded() and hd_atomic_player_snapshot() inside an exclusive
  player-directory lock. This is a proven single-file atomic boundary for
  both the serialized player room and the new Breath receipt.
- The uploaded report begins midway through command6.c due to text
  truncation. The exact move()/go() definitions and their exit decisions
  were NOT visible in the uploaded portion. Claiming a completed
  pre-move exhaustion hook on that evidence would be unsafe.

This milestone adds a **source-gated private native co-checkpoint API**
without connecting the gameplay command table yet:

- hd_breath_move_checkpoint.h/.inc implements a new atomic store operation
  accepting a post-success live player, the previously saved room, the
  previously read Breath receipt, validated wilderness membership and time.
- Under the original player directory lock, it rejects unexpected
  original room or stale Breath receipt. It calculates the Breath debit
  and serializes BOTH the moved player's new room and the resulting HDTR1
  Breath receipt into one hd_atomic_player_snapshot() call.
- On failure, no state is acknowledged; uncertain rename returns
  UNCERTAIN and requires re-reading BOTH room and Breath before
  allowing another move. An exhausted player can checkpoint a move
  into a non-wilderness interior for zero Breath cost.
- It preserves equipped/inventory pointers through the same snapshot
  normalization as hd_store_save_live_player(). It never changes the
  ELF32 creature ABI and retains all existing receipt entries.
- stage_breath_move_checkpoint.py copies the verified private Round79H
  store into a fresh private Round79J build. It changes only the native
  player-store include and Makefile feature gates, and refuses private
  path symlinks, duplicate stages, or source-anchor drift.
- test_native_breath_move_checkpoint.c uses the established synthetic
  native pet/player fixture. It exercises combined room and Breath
  commits, stale old room, stale receipt, failed rename, uncertain
  rename, exhaustion, and a free indoor return.
- native_move_go_precise.py fixes the excessive source output from
  Round79I by extracting only the exact K&R move()/go() function bodies
  with a small fixed-size output limit. It refuses production code.
- private_room_breath_checkpoint.sh compiles the ELF32 store tests,
  builds the candidate engine with feature gates, runs the read-only
  move/go audit, and checks the live service PID/hash are unchanged.

**Round79J storage is staged, not yet validated on Linode; actual gameplay
movement still does not consume Breath.** The checkpoint helper does
not authorize an exit, roll back a live moved character after a denied
write, or reconcile on-disk state after an uncertain commit; those
responsibilities need native movement integration and real socket tests.
It would be incorrect to connect it to movement before inspecting the
full move/go bodies, and before proving no room or inventory desync can
occur on a failed update.

Mount Endurance and ownership will use the same verified durability
principle. No live-world changes or service restart are authorized.


### Round 79J private atomic room+Breath acceptance — verified

Private Linode results (reported after running the pinned Round 79J
checkpoint runner):
- 13/13 Python staging/security/K&R parser tests passed.
- Native ELF32 atomic co-checkpoint fixture passed, and the native
  game rebuilt privately with movement hookup still disabled.
- One atomic snapshot preserved the new room 10001 and Breath 98.
- Stale old-room and expected-Breath-revision conflicts were denied.
- before_rename failure saved neither moved room nor spent Breath.
- after_rename uncertainty persisted both room and charge exactly once,
  and stale replay was denied.
- Exhausted wilderness travel failed; returning to an ordinary room
  persisted at zero Breath cost.
- Exact native move()/go() source extraction succeeded in the private
  candidate. The stdout line showing a zero count for go() belongs to a
  *negative parser unit test*; it is not a native gameplay failure.
- Production PID/binary and the Round 79H baseline remained unchanged.
  No production deployment was performed.

The exact-move-go-report.txt generated on Linode is PRIVATE and was
not supplied in the passing test output. The full native move()/go()
resolution paths remain necessary for safe gameplay integration:
determine the destination before exhaustion gating, preserve locked or
invisible exits and all existing game restrictions, detect confirmed
successful movement, reconcile failed/uncertain writes with in-memory
room state, and choose an actual native timed-recovery hook.

The Breath gameplay HUD currently shows "--" rather than a numeric
resource; mounts, endurance and stables are not playable yet. Do not
confuse the passing durable test fixture with a native movement feature.


## Round 79K — Native wilderness Breath travel and saved HUD private candidate

**Status: staged on the GitHub playtest branch; not yet compiled or
socket-tested on Linode. Production remains unchanged.**

The Round 79J native co-checkpoint fixture passed. A fresh private
source report then provided the actual legacy K&R implementations:
- command2.c move(), lines 203–487: resolves directional exits,
  checks class/lock/flight/time/guards/authorization/inventory/fall,
  loads the destination room, checks level and occupancy, THEN
  broadcasts departures, moves room occupants/followers and handles
  traps. The last eligibility point precedes the class-specific
  departure broadcast around line 417.
- command6.c go(), lines 85–329: handles named exits, validates
  exit locks, class/flight, time, guards, identity/sex, equipment,
  climb/fall, room loading, level and capacity before departure
  broadcast around line 267, entity transfers and traps.
- Existing wilderness.c wrappers run *after* these native handlers,
  so a simple post-hoc Breath debit would risk a free step or a
  position/save mismatch on failure.

Private feature-gated implementation, currently UNTESTED:
- stage_breath_travel.py copies ONLY an already verified private
  Round 79J candidate and inserts a checked hd79_breath_precommit
  call in the two real native move/go handlers **after all native
  eligibility tests but before any room transfer/announcement**.
  This preserves the existing exit rules and avoids charging for
  locked/blocked destinations.
- hd79_breath_travel_runtime.c/.h validates a real destination tile
  through hd79_wilderness_tile (wilderness.map HDW1 parser, not
  simply a high room number), reads or initializes a character's
  saved Breath once, checks exhaustion, and builds a temporary
  proposed player snapshot at the destination.
- The previously verified hd_breath_store_checkpoint_move atomically
  saves BOTH resulting room and Breath before the native in-memory
  transfer occurs. Failed writes deny movement; uncertain writes
  re-read both persistent room and expected Breath before acknowledging
  the original command.
- Ordinary interior transfers also checkpoint the new room for
  consistency but charge 0 Breath. Retreat to an interior remains
  possible at 0 Breath. The player receives an error on unavailable
  wilderness map or unverifiable save.
- The Round79E ANSI/plain status formatter now obtains the actual
  persisted Breath reading, including lazily initializing an absent
  legacy/new-character record after a valid character save exists.
  It never overwrites an exhausted existing record.
- The native update_ply() callback includes a bounded +5 recovery
  attempt after at least 45 elapsed seconds since the last saved
  Breath recovery timestamp. This is not triggered directly by a
  command and cannot be spammed faster than the durable interval.
  Resting +15 remains pending exact native rest-state verification;
  it is NOT secretly treated as normal recovery.
- Feature gate: BREATH_TRAVEL_PLAYTEST=1, requiring prior
  BREATH_STORE_PLAYTEST=1 and BREATH_MOVE_CHECKPOINT_TEST=1.
  The native creature/player binary structure is unchanged.

Added test coverage:
- test_stage_breath_travel.py: private path protection, no original
  mutation, exact ordering of permission/capacity checks and atomic
  pre-transfer save, tile reader, HUD and pulse hook staging.
- test_native_breath_travel.c: synthetic ELF32 native player file,
  one-time save migration and initial HUD, normal move, failed rename,
  uncertain rename recovery, timed +5 pulse, depletion, exhaustion
  and free indoor retreat.
- check_breath_travel_socket.py: real native ELF32 game running as an
  unprivileged process in a separate network namespace and disposable
  chroot. The test builds synthetic native binary rooms, a proper
  HDW1 wilderness map with two tiles, directional/named exits,
  checks Breath 100 -> 98 -> 96 -> 94, zero cost on indoor return
  and refused exit, and save/logout/reconnect persistence.
- private_breath_travel.sh: consolidated stage, tests, ELF32 compile,
  socket replay and PID/hash no-production-change checks.

Remaining safety risks to validate before promotion:
- Any teleport, GM relocation or alternate room-change entrypoint
  not using native move/go must synchronize its persistent room
  separately. The current patch may reject a subsequent normal step
  rather than silently bypass a stale room, which is fail-closed.
- Crashes after the atomic room+Breath precommit but before a
  follower/trap side effect can leave the character durably at the
  destination without that side effect. User-facing travel must
  not be declared fully playable without validating this behavior.
- Immediate durability costs an atomic save per actual player step,
  including ordinary interior travel. Benchmark throughput and
  ensure no regressions with larger inventories and pets.
- A status lookup may initialize missing Breath on first
  authenticated prompt and performs a durable read per prompt;
  validate cost under normal player load.
- Resting +15, mounted travel, mount Endurance/ownership, stables,
  dragon flight and route permissions are future milestones.
- Production deployment requires explicit user approval and a
  separate verified rollout.

This private milestone does NOT deploy to the live service,
edit the live world, restart hollowdeep.service, or expose
private logs/fixtures/credentials in GitHub.


### Round 79K first Linode stage failure — K&R update_ply formatting

The first private Round79K attempt ran 7/7 staging and live-path
regression tests successfully, but stopped before modifying the
disposable candidate because stage_breath_travel.py required an exact
whitespace match for the native player.c update_ply() clock and
LT_HOURS interval statement. The actual Mordor source uses different
tab/space formatting. There was no compile, socket run, gameplay
test, production deployment or service restart in that attempt.

The staging patch now finds the single actual update_ply() entry
and its opening time(0) assignment with whitespace-tolerant matching.
It still requires the *immediately following native statement* to
be the LT_HOURS interval update, and rejects ambiguous clock
assignments, nonadjacent statements, altered native entry points,
symlinks and production paths. It inserts only the feature-gated
Breath pulse and does not edit the original native statements.
Additional tests cover K&R tab indentation, multiple clock
assignments and reordered LT_HOURS updates.

The revised patch has NOT YET BEEN RUN on Linode. Do not label native
Breath movement or recovery PASS until the private ELF32 build
and actual socket travel tests succeed. The live world and MUD
service remain unchanged.


### Round 79K second Linode run — native runtime include order repair

Second isolated Round79K attempt results:
- **10/10** Python staging/path/K&R source regressions PASS.
- Private source staged correctly under a new disposable Round79K tree.
- ELF32 compile of the native Breath pre-transfer fixture FAIL due to
  native type declarations missing before mextern.h in
  hd79_breath_travel_runtime.c: iobuf, extra, creature, room, exit_
  and HD_STORE_OK were unavailable at that point. These are compile
  errors, not live game errors. Unrelated files3.c fgets warnings
  were also printed but are not the cause of this failure.
- Native game build, isolated real socket gameplay and persistence
  regressions did not run. No deployment occurred.

The follow-up native source patch now includes hd_player_store.h
before mextern.h in the standalone Breath travel runtime translation
unit, matching the ordering used by the already passing native
player-store fixture. The staging regression asserts this order and
preserves all fail-closed private-source guards. This is an
**unverified compile fix** until Linode runs the updated native tests.

No live world, production service, player save or binary was changed.


### Round 79K native ELF32 successful build; socket path repair

A subsequent private Linode execution confirmed:
- 11/11 source-staging/security tests passed.
- Private native Breath hooks staged successfully.
- **ELF32 pre-transfer receipt fixture compiled and passed**:
  initial saved Breath 100, atomic movement room+Breath checkpoint,
  refusal on injected pre-rename failure, post-rename uncertainty
  reconciliation, non-spammable +5 timed recovery, exhausted
  wilderness denial and free indoor retreat.
- **Full ELF32 MUD executable compiled with actual move()/go() hooks**.
- The real socket replay did NOT start: its Python harness resolved the
  Necromancer helper files relative to the repository root rather than
  the correct tools/necromancer directory.
- No live deployment or restart was performed; successful socket gameplay
  is still pending.

The fix sets the socket harness helper root to
tools/necromancer, verifies existence of the two committed Python
fixtures and native help directory, and adds a regression test.
A dedicated private_breath_socket_only.sh reuses the already compiled
and fixture-verified Round79K ELF32 candidate (under the restricted
/tmp/hd-army-game-round79travel-* path) to run ONLY the isolated
network-namespace/chroot gameplay socket test. It rechecks production
binary/service PID and the private executable fingerprint. This
avoids repeating the previously successful full ELF32 compile.

**This is a harness path fix, not proof that socket gameplay works.**
Do not claim live Breath playable until directional and named movement,
HUD, save and reconnect pass within an isolated real MUD socket.
Migrations, timed recovery and all mounts remain private/unpublished
to the production server.


### Round 79K socket replay — successful gameplay, stale login-room harness

The private socket-only replay progressed through the real ELF32 MUD,
with native ANSI prompt and actual player moves:
- Wilderness entry and subsequent movement displayed saved Breath
  **100 -> 98 -> 96 -> 94**.
- A named `go west` exit returned to the synthetic
  **Necromancer Trial Annex** without a Breath debit.
- `go north` against a missing exit was refused and did not change
  Breath 94/100.
- Native `save` responded `Player saved.`; `quit` closed the
  original socket after its normal cooldown.
- On reconnect the game displayed the saved **Necromancer Trial
  Annex** and **Breath 94/100**, demonstrating both values persisted.
- The replay's generic Necromancer fixture login helper erroneously
  required the original seed-room text **Necromancer Grave Trial**
  and therefore raised an exception before its final PASS marker.
  This is a test expectation mismatch, not a native Breath regression.
- The socket-only runner verified the production PID, binary and
  private ELF32 executable were unchanged. Deployment: NONE.

A new small helper `breath_socket_reconnect.py` verifies *both* saved
room and Breath directly in the actual native login banner, with ANSI
and telnet bytes tolerated. The socket test now performs its standard
login prompts, then requires the correct **Annex** and Breath **94/100**;
it no longer calls the prior helper with the original-room assumption.
New unit tests reject wrong room, wrong stamina, missing text,
invalid expected values and non-socket input. The existing socket-only
runner now executes these tests before replay, reusing the tested
private ELF32 executable and never touching production.

**The updated full socket replay has not been rerun yet.** Do not label
Round79K finished until the final
`ROUND 79K: SOCKET BREATH TRAVEL AND HUD PASS` line appears.
Resting +15, mount Endurance, ownership/stables and dragon flight
remain unimplemented, as does any production deployment.


### Round 79K FINAL PRIVATE SOCKET ACCEPTANCE — PASS

The user's final private Linode result on the pinned Round79K socket-only
runner reports:
- 8/8 private socket-support/reconnect regression tests PASS.
- Reused the previously compiled and fixture-verified private ELF32 native
  game. Full private socket replay reported:
  \`ROUND 79K: PRIVATE SOCKET BREATH TRAVEL + HUD PASS\`
  and \`ROUND 79K: SOCKET BREATH TRAVEL AND HUD PASS\`.
- Real directional and named wilderness movement spent Breath by exact
  2-point steps (100 -> 98 -> 96 -> 94); interior retreat and failed exits
  did not spend Breath.
- Real ANSI/plain numeric HP/MP/Breath prompts worked.
- Real player save, logout, re-login restored both the saved room
  (Necromancer Trial Annex) and Breath 94/100.
- The runner verified the production service PID, live executable hash,
  and private ELF32 baseline hash unchanged.
- **PRODUCTION DEPLOYMENT: NONE.**

Round79K is therefore accepted for *isolated gameplay behavior* and
durable Breath storage, NOT for production rollout. Known remaining
integration gates include rest-specific +15 recovery, crash windows
between precommitting position/Breath and followers/traps, unhooked
teleports/GM relocation, per-step save throughput, mounted Endurance,
ownership, stables and flying mount restrictions. No private test
fixture, user data, server configuration or operational logs are
published to GitHub.


### Round 79L first private audit test: callback source omitted

First Round79L Linode run was limited to the Python source-audit
unit test. The private fixture exposed a native rest() handler setting
a pose flag, a stand() handler clearing it, the update_ply() time
statement, and a separately defined hd79_breath_pulse(). The test
failed because the audit scanned for REST/SLEEP words before entering
each source file, so it omitted the existing Breath callback source
(which does not itself contain those tokens).

A second issue was a ResourceWarning for a readable ELF32 executable
file handle that was not closed immediately after the first five-byte
identity check.

The patched audit always includes the Breath pulse implementation,
prints the native update_ply() and Breath callback before the bounded
command excerpts, and uses an explicit with block to close the ELF32
file. The test runner now treats ResourceWarnings as errors.
This is an **audit/reporting fix only**. No new rest recovery logic
has been installed or gameplay-tested. Production was not modified.


### Round 79L verified resting-state source audit — PASS

The private Linode run \`round79l-fSr2pVy0\` confirms:
- Six read-only source-audit tests PASS.
- \`ROUND 79L: PRIVATE NATIVE REST/UPDATE SOURCE AUDIT PASS\`.
- Production service PID, binary, and accepted private ELF32 baseline unchanged; deployment NONE.
- In \`player.c\` native \`update_ply()\` at approximately lines 443–457, the existing feature-gated Breath callback executes after \`t = time(0)\` and before \`LT_HOURS\` advancement. Existing non-poisoned HP/MP updates use \`LT_HEALS\`.
- In \`hd79_breath_travel_runtime.c\`, the native
  \`hd79_breath_pulse()\` checks the durable elapsed-time interval
  and calls \`hd_breath_store_step(...HD_BREATH_OP_RECOVER,0,0,...)\`,
  with resting explicitly false.
- The private \`global.c\` command table routes \`sleep\`, \`sit\`,
  and \`stand\` to the generic \`action\` command (ID 100), with no
  audited pose-setting implementation. The Monk-only \`meditate\`
  command is separate, not a universal rest state.
- The audit did NOT verify any reliable persistent rest/sleep pose
  that could be passed into the already tested +15 Breath policy.
  Mapping generic social/emote commands to resting without verifying
  their implementation would permit unintended recovery.

Round79L is therefore **accepted as a read-only audit**, not as a
playable +15 recovery feature. The next milestone must inspect the
actual generic action() implementation and command dispatcher, then
add an explicit, session-safe resting state with rest/stand/reset
semantics and one durable +15 award per eligible timed pulse. Avoid
changing native creature ABI or old save formats. All private source
excerpts/reports stay outside GitHub.


### Round 79M staged — exact native action() and social command audit

Round79L established the native update_ply() timing and the generic
social-command routing of sleep/sit/stand to action. A normal +5 Breath
pulse is already tested in isolated gameplay, but +15 recovery requires
a real verified resting state that the current native source audit has
not demonstrated. Implementing recovery from the social command name
alone could let a player continue fighting or moving while getting
a resting bonus.

This milestone publishes a PRIVATE read-only action audit:
- audit_native_rest_actions.py locates exactly one actual K&R/native
  action() implementation among all private native C modules, extracts
  its body and checks command-table mappings to reveal actual
  side effects. The script also inspects native command fields and
  relevant P-flag definitions, and refuses unsafe input.
- test_audit_native_rest_actions.py checks action detection even when
  comments/strings contain braces, ambiguous/missing definitions,
  invalid ELF32 candidates, production-source paths and symlink input.
- private_rest_actions_audit.sh reuses the Round79K accepted private
  ELF32 tree and records the action report outside GitHub, with live
  PID/binary and accepted private executable unchanged.

**Round79M audit is staged, not yet executed on Linode.**
Native +15 resting recovery, special/rest movement restrictions,
mounts and mounts' separate Endurance are not installed. Review
the private action report before modifying gameplay command routing,
player session state, or the next native timer hook. No production
deployment is authorized.


### Round79M FINAL PRIVATE ACTION AUDIT — PASS

The user's private Linode report \`round79m-dAs0cj3Q\` confirms:
- Seven read-only command-scanner/security regressions PASS.
- \`ROUND 79M: PRIVATE ACTION COMMAND AUDIT PASS\`.
- Exactly one native \`action()\` definition was verified in
  \`action.c:40-661\`.
- \`global.c\` dispatches \`sleep\`, \`sit\`, and \`stand\` through
  the generic social \`action\` command (ID 100); **no** \`rest\` or
  \`wake\` entry was found.
- The \`sleep\` branch emits a nap message, while \`relax\` emits
  a deep-breath social message; neither visible body establishes a
  persistent rest state. No dedicated REST/SLEEP/SIT/STAND/WAKE
  P-flag definition was found.
- The MUD's normal \`meditate\` is a Monk-specific ability and must
  not be conflated with generic resting.
- Production PID, binary and accepted Round79K private ELF32
  baseline verified unchanged; production deployment NONE.

**Conclusion:** There is no verified authoritative resting state for
native +15 Breath recovery. A new explicit \`rest\` state is needed,
with a timer-based minimum uninterrupted duration, interruption on
real player actions/combat/movement, logout/disconnect/death cleanup,
and no binary creature-struct ABI change. Inspect the real command
dispatcher and lifecycle before wiring hooks. The already tested
default +5 remains the only native recovery rate.


### Round79N staged — explicit rest-session policy and dispatch/lifecycle audit

**Status: committed to the private-playtest branch as source/test
scaffolding; not yet run on Linode and NOT wired to the native game.**

Round79M's private report verifies one real action() function in
action.c and sleep/sit/stand mapped to the social action handler.
Neither those emotes nor relax define a durable/resting pose.
There are no registered rest/wake commands or native REST/POS state
flags. Granting +15 from the emote name alone would allow recovery
while performing other actions.

Round79N introduces a standalone C99, no-I/O, ABI-independent state:
- hd79_rest_session.h/.c defines an explicit per-session pose with
  begin, interrupt/init and eligibility checks. It does **not** store
  state in the native creature struct, any character file, Conjure
  pet roster or mount data; it is not connected to a live session yet.
- A bonus cannot be eligible until **45 uninterrupted seconds**
  after the true rest start AND the existing durable Breath receipt's
  last recovery time was at least 45 seconds ago. The repeated rest
  command is idempotent. Movement/combat/casting/other activity must
  call interrupt before executing. Logout/death/disconnect must clear
  the active pose; login initializes new state. If any required fact
  cannot be verified, only ordinary +5 is allowed.
- test_hd79_rest_session.c checks the contract: no instant +15,
  repeated-rest spam, timed receipts, movement interruption,
  reconnect reset and clock rollback fail closed.
- audit_native_rest_dispatch.py plus Python tests reads only
  accepted isolated ELF32 source and extracts native dispatcher
  evidence, action/command routing, update_ply and logout/death
  cleanup candidates. It does NOT alter production or private source.
- private_rest_dispatch_and_policy.sh runs the Python audit tests,
  compiles and runs the standalone C policy fixture, generates a
  root-only private report and checks that the native ELF32 candidate
  and live production service PID/executable hash are unchanged.

This step deliberately does NOT add a native rest command,
set a per-player state in the event loop, update a real Breath
receipt with resting=1, or modify any live player or world. Exact
dispatch/lifecycle source must be inspected before those changes
can safely proceed. The 45-second rest threshold is a conservative
anti-spam implementation default to be confirmed in real gameplay.
No private source excerpts or log files are committed.
