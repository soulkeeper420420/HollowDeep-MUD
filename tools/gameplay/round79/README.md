# Round 79A - Encounter scouting (first native gameplay target)

This directory contains the pure, read-only difficulty calculation used by
the proposed `consider <monster>` command.

## Build and run the self-contained rule test

```sh
cc -std=gnu89 -Wall -Wextra -Werror -I. \
  hd_encounter_risk.c test_encounter_risk.c -o /tmp/hollowdeep-consider-rules
/tmp/hollowdeep-consider-rules
```

The test exercises 3,600 legal level combinations, edge thresholds, and
monotonic difficulty changes. It neither accesses the world nor writes files
other than the test executable.

## Native integration requirements

Before adding a `consider` command, inspect the exact private native source.
Reuse the original native command if it already exists and refuse duplicate
command IDs. The handler must reuse existing visibility-aware monster lookup,
work only in the player's current room, and use `hd_encounter_risk` for the
qualitative label. Never show exact enemy HP, level, hidden flags, loot, or
protected monster details. No combat state, player save, inventory, room,
respawn, cooldown or XP modifications.

Do not announce the command as playable until actual native ELF32 compile and
socket creation/login/consider/regressions pass on a disposable world.
This code is currently **rules-only**, with no game command registered.

The full milestone and planned next improvements are in
`docs/ROUND79_GAMEPLAY_QOL.md`.


## Round 79B — Readable status and ANSI choice

The requested status line is:

    HP 14/25 | MP 5/10 | Breath --

With ANSI selected, HP is green/yellow/red according to remaining health,
MP blue, and a verified Breath gauge cyan/yellow/red. Without ANSI, the
identical plain-text values are sent with no escape bytes.

The existing native creature record has HP and MP current/max fields but
a numeric Breath field has **not been proven**. The pure display renderer
does not invent a Breath value: it shows "Breath --" unless a genuine
current/max resource is supplied. A breathing mechanic and persistence
model need separate engine validation.

Standalone source modules:

- hd_status_hud.h/.c and test_status_hud.c
- hd_ansi_choice.h/.c and test_ansi_choice.c
- stage_ansi_creation.py and test_stage_ansi_creation.py
- native_status_ansi_probe.py

Quick tests:

    cc -std=gnu89 -Wall -Wextra -Werror -I. \
       hd_status_hud.c test_status_hud.c -o /tmp/hollowdeep-status-test
    /tmp/hollowdeep-status-test
    cc -std=gnu89 -Wall -Wextra -Werror -I. \
       hd_ansi_choice.c test_ansi_choice.c -o /tmp/hollowdeep-ansi-test
    /tmp/hollowdeep-ansi-test
    python3 -m unittest -v test_stage_ansi_creation

The strict ANSI staging tool only accepts a verified disposable private
Round 78E source at /tmp/hd-army-game-round78-*/src and a NEW destination
under /tmp/hd-army-game-round79-*/src. It adds a yes/no prompt after
race selection, before password entry, and saves the answer in the
existing PANSIC flag; it also enables PPROMP for newly created players.

Its feature gate is STATUS_ANSI_PLAYTEST=1, so other builds retain the
old creation flow. The existing private creation socket regression now
answers YES for Necromancer and NO for Mage, and its saved-character
probe checks the persisted ANSI flag.

The status renderer is **not yet connected** to player.c's native prompt:
run native_status_ansi_probe.py on the private source and inspect its
prompt buffer and breath implementation before patching. Never overwrite
production binaries, world files or character saves.


### Consolidated private Linode run

After a fresh clone pinned to the Round 79B commit, run the single
private_status_ansi.sh script with the absolute fresh checkout directory.
It performs stand-alone C unit tests, fail-closed Python staging tests,
read-only native source discovery, private ELF32 recompilation with
STATUS_ANSI_PLAYTEST=1, new-character ANSI YES/NO persistence through
save/reconnect, Warlock creation, and Necromancer help regressions.

The script captures private logs and a source-only report at:

    /root/hollowdeep-dev/round79b-*/native-status-report.txt

The report contains the native prompt buffer, code references to any
breathing mechanism, and ANSI flag handling. This evidence is required to
wire the display into player.c without breaking existing prompt behavior
or inventing a Breath meter.

No production restart or deployment is performed by this script.


## Round 79C: Breath wilderness travel meter

Breath is now designed as **wilderness movement stamina**, not underwater
oxygen. Preliminary pure native-C rules define 100/100 maximum, -2 only on
successful moves INTO a wilderness room, +5 on a verified timed recovery
tick, +15 if resting on that same tick, and free travel to non-wilderness
rooms even when exhausted. No meter changes for indoor walking, blocked
exits, look, map redraw, login or teleport. Native runtime implementation
must honor the same policy and checkpoint the meter across reconnect.

The standalone test also feeds a real Breath value into the existing
colored/plain status renderer:

    HP 14/25 | MP 5/10 | Breath 15/100

From this directory:

    cc -std=gnu89 -Wall -Wextra -Werror -I. \
       hd_status_hud.c hd_wilderness_breath.c \
       test_wilderness_breath.c \
       -o /tmp/hollowdeep-breath-rules
    /tmp/hollowdeep-breath-rules

Inspect the exact private native movement, recovery and zone-identification
paths before staging native changes:

    python3 native_wilderness_breath_probe.py \
       /tmp/hd-army-game-round78-VibwvrvC/src

Read the complete acceptance requirements in
docs/ROUND79_GAMEPLAY_QOL.md. The standalone C code **is not yet hooked
into native wilderness travel or saved-player persistence**. Do not publish
any private audit/source output, real world data, or game credentials.


## Round 79E: Native ANSI HP/MP status line (private candidate)

The Round 79D source report identified the existing ply_prompt() in player.c,
which used a 40-byte static output buffer. Round 79E enlarges it to 256
bytes under STATUS_HUD_PLAYTEST=1, and displays actual HP/MP current/max
with ANSI colors when the saved PANSIC bit is set. For non-ANSI clients it
sends plain ASCII text with zero escape sequences. Alias and prompt
suppression paths are preserved by a conditional native patch that retains
the old handler when the feature flag is off.

The Breath label is deliberately "--" until the wilderness travel-stamina
resource has durable native storage and verified successful-move hooks.
A successful formatter unit test does not establish Breath gameplay.

Files:
- stage_status_hud.py, test_stage_status_hud.py
- private_status_hud.sh (ELF32 build and real socket acceptance)
- native_wilderness_move_exact.py (bounded read-only function audit)

Use the previously successful ANSI-enabled private Round 79 build as input.
Within a fresh checkout, run private_status_hud.sh with two parameters:
a new private results directory and that Round 79 ANSI source path. The
private runner verifies ANSI enabled and disabled, saved ANSI preference,
HUD after reconnect, Mage/Necromancer/Warlock creation and help regressions,
and unchanged production PID/binary. It also writes native-wilderness-move.txt,
which must be reviewed before adding a Breath debit/save hook.

The Round 79E patch and tests are currently unverified on Linode.
There is NO production deployment or world edit.


## Round 79F: Breath persistent-record specification and storage preflight

The verified movement wrappers in wilderness.c call native move/go, compare
the player's previous room and invoke hd_wilderness_after_move. Breath will
charge only after a completed move into a *mapped wilderness destination*,
and needs an exhaustion gate before the native move command runs. Ordinary
rooms and safe exits remain free even at zero Breath.

New hd_breath_record.c/h defines the 64-character, non-ABI-changing receipt
wire representation: version, character epoch, revision, last recovery time,
current Breath and fixed 100-point capacity. It is intentionally **only a
state and encoding contract**. Neither it nor the standalone tests writes
player saves. The existing HDTR1 receipt append/overwrite, directory lock,
CRC and atomic player checkpoint must still be integrated with a dedicated,
collision-free reserved receipt identifier.

To run just the compiled state test on a private Linux system:

    cc -m32 -std=gnu89 -Wall -Wextra -Werror -I. \
      hd_breath_record.c hd_wilderness_breath.c hd_status_hud.c \
      test_breath_record.c -o /tmp/private-breath-record
    /tmp/private-breath-record

To audit the native persistence extension points, use the read-only
native_breath_store_audit.py against the previously validated private HUD
ELF32 tree; do NOT run against production.

The consolidated private_breath_record.sh script builds and runs this test,
reruns travel rules, audits native atomic save and recovery functions,
and verifies the production PID and live binary are unchanged.

The next required milestone is real socket gameplay with debit,
recovery, atomic failure denial, save/reconnect and the actual colored
Breath counter. Do not label this milestone complete yet.


## Round 79G — Mounts as the purpose of wilderness Breath

The intended end-state is **separate rider Breath and mount Endurance**:
walking consumes the player's Breath, while riding a horse, warhorse, dire
wolf, nightmare, griffin or dark dragon consumes mount Endurance instead.
Mounts are independent of the universal Conjure companion and Necromancer
raised-undead capacity. Terrain skills depend on the validated wilderness
tile from wilderness.map; no mounts are allowed to bypass locked native
exits or room permissions, even when described as flying.

See docs/ROUND79G_MOUNTS_AND_BREATH.md for the proposed six mount profiles,
commands, stabling, persistence, safe retreat and balance constraints.

Native-independent files:
- hd_mount_travel.h/.c: species profiles, destination terrain checks,
  foot-Breath/mount-Endurance movement preview and successful-step charge.
- test_mount_travel.c: exhaustion, terrain restrictions, safe retreat,
  aborted movement, stale values and riding with exhausted foot Breath.
- native_mount_command_audit.py: read-only private command/terrain audit.
- private_mount_rules.sh: private ELF32 C test, audit and production safety.

Quick standalone test (no native MUD integration):

    cc -m32 -std=gnu89 -O1 -Wall -Wextra -Werror -I. \
      hd_mount_travel.c hd_wilderness_breath.c test_mount_travel.c \
      -o /tmp/hd-mount-travel-test
    /tmp/hd-mount-travel-test

The isolated Round 79G mount rules are **new and not yet validated on
Linode**. No command, mount ownership, stabling, flying, movement speed,
Endurance persistence or game-native Breath debit has been added to the
running game. The atomic Breath-store source audit remains the gate before
implementation. Do not publish private source reports or player data.


## Round 79H — Native, atomic Breath receipt storage (new private candidate)

The newly supplied Round 79F source audit confirms the existing native
HDTR1 receipt IDs 74–78 and flock-protected atomic player-save pipeline.
Round 79G's standalone foot/mount travel rules also PASS on private ELF32.

Round 79H adds a strict storage-only extension using receipt suffix 79:
- hd_breath_store.h / hd_breath_store.inc: native locked read, init, and
  exact-expected-state CAS debit/recovery receipt operations.
- stage_breath_store.py / test_stage_breath_store.py: secure, fail-closed
  private copying from tested HUD source to a new disposable candidate.
- test_native_breath_store.c: native real compressed player record, 50
  debits, exhausted move denial, timed recovery, ordinary saves,
  stale revisions, before/after rename failures, independent undead
  receipt, and owner-epoch replay tests.
- private_breath_store.sh: isolated ELF32 fixture/native game compile
  and production PID/executable checksum guard.

The patch is enabled only with BREATH_STORE_PLAYTEST=1 and the already
verified PET_STORE_PLAYTEST=1 feature gate. It reuses the existing
HDTR1 trailer without changing the serialized creature structure.

To run in a *new* private Linode checkout pinned to the released commit:

    bash tools/gameplay/round79/private_breath_store.sh \
      /root/hollowdeep-dev/round79h-PRIVATE \
      /tmp/hd-army-game-round79hud-VERIFIED/src

The private work directory must contain the pinned checkout at repo/.
The script is not yet tested on the actual Linode private native build.
It intentionally does not modify wilderness movement, player prompt,
rest timer, mount ownership or stable commands. Running it does not
deploy a service or touch production world/player files.

A future gameplay hook must reconcile both player room and Breath
atomically, including failed writes, interrupted moves, logged-out
recovery and locked/hidden exit validation. Merely debiting the
receipt after a successful movement without position persistence
is not sufficient for crash-safe gameplay.


## Round 79I: inspect atomic native room and Breath movement

The Round 79H **native atomic Breath receipt test passed** on the
isolated ELF32 Linode candidate. Real movement, regeneration and HUD
updates are still pending.

Rather than changing the old Mordor movement functions blindly, this
milestone provides a bounded, READ-ONLY inspection of the verified
private Round 79H source:
- native_movement_atomicity_audit.py extracts native move() and go()
  definitions and their destination/commit operations, wilderness
  callbacks, atomic player save functions and legacy timed recovery.
- test_native_movement_atomicity_audit.py enforces private ELF32-only
  input and rejects production locations and symlinked code.
- private_movement_atomicity_audit.sh runs those checks without
  rebuilding the game or touching any live player/world data.

Use the previously tested Round 79H source and a fresh private results
directory:

    bash tools/gameplay/round79/private_movement_atomicity_audit.sh \
      /root/hollowdeep-dev/round79i-PRIVATE \
      /tmp/hd-army-game-round79store-VERIFIED/src

The resulting movement-atomicity-report.txt is for private review and
must NOT be committed to the public repository. Before connecting a
wilderness move debit to gameplay, verify that the new destination room
and Breath receipt are committed consistently under fail injection.
Unmounting/dismounting, save/reconnect and changing owned mounts must
not reset either rider Breath or mount Endurance.


## Round 79J — Atomic player room and Breath checkpoint (private only)

The uploaded Round79I audit verifies native update_ply(), the map wrapper,
and the existing hd_atomic_player_snapshot() save boundary. It does not
supply a complete, untruncated move()/go() destination resolver.

New sources:
- hd_breath_move_checkpoint.h / .inc — co-commit one changed player
  rom_num and revised Breath receipt under a single existing native
  player-save directory lock; guard both old room and exact Breath
  revision; preserve worn items and other receipts; report uncertain
  renames for disk reconciliation
- stage_breath_move_checkpoint.py / test_stage_breath_move_checkpoint.py
  — source-only opt-in copy from verified Round79H storage candidate to
  NEW private Round79J candidate
- test_native_breath_move_checkpoint.c — native synthetic player
  assertions: old/new room+Breath, stale room/receipt, aborted write,
  uncertain write, zero-Breath wilderness denial and free retreat
- native_move_go_precise.py / test_native_move_go_precise.py — bounded
  actual K&R move()/go() definition extraction, avoiding old terminal
  transcript truncation
- private_room_breath_checkpoint.sh — all of the above plus private ELF32
  compile and unchanged-production assertions

Pass a NEW /root/hollowdeep-dev/round79j-* results directory containing
the pinned repository at repo/ and the verified Round79H source:

    bash tools/gameplay/round79/private_room_breath_checkpoint.sh \
      /root/hollowdeep-dev/round79j-PRIVATE \
      /tmp/hd-army-game-round79store-VERIFIED/src

The private runner writes exact-move-go-report.txt for review. This
script neither changes the native movement commands nor charges Breath
during real travel. It cannot be deployed as a finished player feature:
pre-move exit permission, post-move rollback/reconciliation, optional
mount Endurance, numeric HUD and recovery remain future integration.


## Round79K: Native Breath movement, true HUD and recovery private gate

The verified private Round79J ELF32 co-checkpoint and the newly
uploaded exact move()/go() report establish a safe pre-transfer
integration point: after all legacy exit, destination level/capacity
tests and before room broadcast/transfer and traps.

Native-only staged files under the new explicit private gate
BREATH_TRAVEL_PLAYTEST=1:
- stage_breath_travel.py: copy verified Round79J source to new
  /tmp/hd-army-game-round79travel-*/src; verify exact native anchors,
  deny production paths/symlinks and leave old source unchanged
- hd79_breath_travel_runtime.h/.c: validate map tile, initialize/read
  a one-time saved Breath receipt, deny exhausted wilderness entry,
  co-checkpoint room+Breath before real room movement and reconcile
  uncertain atomic renames
- wilderness.c injected exact HDW1 map tile lookup (not simply a
  wilderness room-ID guess)
- command2.c move() / command6.c go() gated pretransfer call after
  original permission checks, before player or follower transfers
- player.c saved numeric ANSI/plain Breath HUD and a guarded +5
  recovery attempt after a native update_ply callback and at least
  45 seconds of elapsed, durably recorded recovery time
- test_stage_breath_travel.py and test_native_breath_travel.c:
  source safety, native synthetic file save and fail injection
- check_breath_travel_socket.py: disposable network namespace/chroot,
  synthetic 2-tile wilderness native world, directional and named
  traversal, denied exits, HUD and reconnect
- private_breath_travel.sh: one-shot private tests and game build;
  verifies no production binary or service PID changed

The initial fixture requires root in a separate network namespace.
The private runner expects a NEW root-only Round79K work directory
containing the pinned GitHub checkout under repo/, plus the validated
Round79J source directory:

    bash tools/gameplay/round79/private_breath_travel.sh \
      /root/hollowdeep-dev/round79k-PRIVATE \
      /tmp/hd-army-game-round79move-VERIFIED/src

**The new native code is not yet tested on Linode**. No claim of
real in-game Breath debits, timed recovery or reconnecting is made
until the private ELF32 socket test passes. The rest-specific +15,
mount ownership/Endurance, stables and dragon flight are not wired.
Production deployment is neither requested nor performed.

Before any live rollout, also audit alternate teleport/admin room
changes and crash behavior after an atomic precommit but before traps
and followers finish, plus save throughput with many connected
players. Keep all socket logs, fixtures, private paths and
credentials outside public GitHub.


## Round 79K accepted, Round 79L private native resting-state audit

The final isolated Linode Round79K socket replay confirmed
\`ROUND 79K: SOCKET BREATH TRAVEL AND HUD PASS\`:
- 8/8 socket/reconnect regression tests.
- Real ELF32 native wilderness moves charged Breath 100 -> 98 -> 96 -> 94.
- Interior retreat and invalid exits did not charge.
- ANSI HP/MP/Breath HUD displayed exact persisted values.
- Save/logout/reconnect restored both the saved room and Breath 94.
- The private ELF32 baseline and production service PID/binary were unchanged.
- Production deployment remains NONE.

**Round 79L is only a source audit, not a live gameplay change.**
The already tested hd_wilderness_breath.c policies specify +5 for
ordinary timed recovery and +15 while resting. No native rest/sleep
pose flag has yet been verified, so treating typing "rest" repeatedly
as recovery would be incorrect.

New read-only private tooling:
- audit_native_rest_state.py scans only a known disposable Round79K
  ELF32 source under /tmp/hd-army-game-round79travel-*/src and emits
  a bounded private report with native rest/sleep/sit/stand/wake
  declarations, relevant player flags, and update_ply() timing.
- test_audit_native_rest_state.py covers K&R rest/stand definitions,
  private path/ELF32/symlink refusal and missing source guards.
- private_rest_state_audit.sh runs only these tests and reports native
  rest-state evidence; it re-verifies production PID/binary and the
  accepted private executable fingerprint remain unchanged.

Use a fresh, pinned private repo under /root/hollowdeep-dev/round79l-*.
Supply the existing accepted Round79K source from the socket-pass:

    bash tools/gameplay/round79/private_rest_state_audit.sh \
      /root/hollowdeep-dev/round79l-PRIVATE \
      /tmp/hd-army-game-round79travel-VERIFIED/src

The generated private-rest-state-report.txt must remain off GitHub.
After reviewing it, introduce +15 only when the real native character
pose is actively resting and the durable recovery interval has
elapsed. Reuse the atomic Breath store, preserve the default +5,
and validate rest->stand->rest and death/logout/reconnect cases.
Do not restart or modify production.


## Round 79L accepted; Round 79M precise native action dispatch audit

The accepted Round79L Linode report verifies:
- Six private audit unit tests passed.
- Native update_ply() is the player update callback and runs the
  saved Breath pulse beside LT_HOURS processing.
- Existing default +5 recovery is durable. The pure Breath policy
  already supports +15 when a trusted resting boolean is supplied.
- Native global.c maps "sleep", "sit" and "stand" to the generic
  action social command; these entries do NOT, by themselves,
  prove any persistent native pose or true resting state.
- Monk meditation is a separate class skill, not general resting.
- Production service PID/binary and private ELF32 build were unchanged.

Round79M intentionally avoids installing an unsafe +15 hook based
on cosmetic emote commands. New read-only tools:
- audit_native_rest_actions.py finds the EXACT native C/K&R
  action() function and extracts its full/most relevant implementation,
  existing global.c sleep/sit/stand/rest/wake command bindings,
  relevant native command fields, and matching real pose flag
  definitions if present. It fails closed on ambiguous definitions.
- test_audit_native_rest_actions.py tests exact action detection,
  raw brace/string handling, real command mapping, and refuses
  production paths, wrong ELF32 binaries or symlinks.
- private_rest_actions_audit.sh runs the private tests and analysis,
  checks the prior accepted private build and live service are unchanged,
  and stores private-action-handler-report.txt in a root-only folder
  outside GitHub.

Next: inspect the actual action() implementation and native command
dispatch before choosing whether to introduce a dedicated rest mode
and which movement/combat/stand actions clear it. Once this is proven,
wire rest only into the existing durable 45-second Breath pulse using
resting=1; never award +15 for repeated text commands or background
recovery after death/logout. No native creature ABI or player save
format changes are authorized.

Use a new pinned private checkout with this command:

    bash tools/gameplay/round79/private_rest_actions_audit.sh \
      /root/hollowdeep-dev/round79m-PRIVATE \
      /tmp/hd-army-game-round79travel-VERIFIED/src

Generated source excerpts remain PRIVATE and must not be added to GitHub.


## Round79N: explicit rest-session eligibility and native dispatcher audit

Round79M passed on Linode: 7/7 private source-audit tests; the
actual native action() implementation is a generic social handler.
The sleep, sit and stand commands are emotes, not a trustworthy
resting pose. No dedicated rest/wake native commands or rest-state
P-flag are registered. Production and private ELF32 hashes unchanged.

The pending Round79N private milestone provides two independent
pieces of verification:

1. hd79_rest_session.h/.c and test_hd79_rest_session.c provide
   an engine-independent session model with no player-save ABI changes.
   A genuine rest must last at least 45 uninterrupted seconds before
   any +15 rate becomes eligible, and the durable Breath receipt
   still must be due for its normal 45-second tick. Repeated rest is
   idempotent. An interrupt or new login invalidates old rest state.
   This pure policy does NOT alter native gameplay or save Breath.
2. audit_native_rest_dispatch.py and
   test_audit_native_rest_dispatch.py inspect the private native
   command dispatcher and lifecycle references so the future native
   patch can start/stop rest on real actions, movement, combat,
   character logout, death and disconnection.

Run the consolidated private-only verifier:

    bash tools/gameplay/round79/private_rest_dispatch_and_policy.sh \
      /root/hollowdeep-dev/round79n-PRIVATE \
      /tmp/hd-army-game-round79travel-VERIFIED/src

The private-rest-dispatch-report.txt stays root-only on Linode.
Do not upload private native source excerpts, credentials or player
saves to GitHub. The real +15 Breath recovery and new rest command
have NOT been implemented until the native command and lifecycle
hooks are inspected and gameplay socket tests pass.


## Round79N accepted — Round79O exact native command function-pointer trace

The verified Linode Round79N run passed five private audit tests,
the standalone C99 rest-session unit test, and read-only
dispatch/lifecycle source tracing. The 45-second rest eligibility
contract is now tested in isolation, including anti-spam, interruption,
no stale rest after reconnect and durable last_recover guards.
Neither the real rest command nor +15 Breath is hooked to the MUD.

Round79O uses:
- trace_native_command_execution.py: read only, scans the accepted
  disposable ELF32 tree for the real C command-function-pointer
  invocation and its enclosing legacy K&R handler, plus nearby
  login/disconnect/death and combat callback definitions
- test_trace_native_command_execution.py: seven synthetic private
  ELF32 tests for exact dispatch recognition, refusal on missing
  or excessive candidate sites, production path/ELF64/symlink
  rejection and no native source modification
- private_trace_command_execution.sh: reruns the regressions and
  emits a bounded private report, verifying production PID,
  executable SHA256 and the private ELF32 baseline unchanged

Use:
    bash tools/gameplay/round79/private_trace_command_execution.sh \
      /root/hollowdeep-dev/round79o-PRIVATE \
      /tmp/hd-army-game-round79travel-VERIFIED/src

After confirming the real native call site, stage the explicit
rest command, interrupt before executing non-readonly commands,
reset on disconnect/login/death, and use the existing atomic
Breath recovery with resting=1 ONLY after 45 uninterrupted seconds.
Keep the report, source excerpts and all player/game fixtures
private. No live deployment without explicit approval.


## Round79P: first feature-gated native REST +15 candidate

The final Round79O private ELF32 source trace passed all seven
regression tests. It identified the real command callback in
command1.c process_cmd(): after alias and authorization checks,
before calling special_cmd() or the command function pointer.
hollowdeep_help.c merely declares the callback table.

Round79P uses that verified boundary and the earlier Round79N
rest-session timing policy to introduce, **privately only**, a new
rest command and genuine +15 Breath eligibility:
- hd79_rest_game.h/.c: transient rest slots keyed by player pointer,
  FD, name, room and original HP; new rest begins a 45-second
  uninterrupted timer; read-only look/help/skills retain rest;
  other commands interrupt, and death/free clear sessions
- stage_rest_breath.py: strict isolated source copy from accepted
  Round79K, exact native command1.c process_cmd() insertion,
  feature-gated global.c rest command, runtime receipt recovery
  rate switch, and verified K&R die()/free_crt() cleanup
- test_stage_rest_breath.py: staging and failure denials including
  original file fingerprints and shared-file lifecycle hook cases
- test_native_rest_game.c: private ELF32 synthetic player receipt
  test showing 80->95 on eligible rest (+15), then 85->90 after
  real attack interruption (+5), one grant per durable 45-second
  receipt and damage/room/logout reset
- check_breath_rest_socket.py: real native isolated socket test
  for rest entry, repeated rest anti-spam, social stand/sleep
  interruption, existing wilderness charges and reconnect
- private_native_rest_game.sh: one private staging + native
  compile + atomic fixture + full native ELF32 build + real
  network-isolated socket replay, with unchanged-production checks

The runner expects a fresh pinned checkout under
/root/hollowdeep-dev/round79p-* and the accepted private Round79K
source under /tmp/hd-army-game-round79travel-*/src:

    bash tools/gameplay/round79/private_native_rest_game.sh \
      /root/hollowdeep-dev/round79p-PRIVATE \
      /tmp/hd-army-game-round79travel-VERIFIED/src

This is an **untested candidate until Linode reports PASS**.
The short socket test establishes rest registration and
interruption, not the duration of a real 45-second server tick;
the native atomic receipt fixture establishes the +15 value.
Do not publish source excerpts, fixture data or logs to GitHub.
No production deployment is performed.


## Round79P accepted; Round79Q true connected 45-second resting recovery

The accepted Linode Round79P run completed:
- 32 safety/dispatch regression tests PASS
- New disposable private ELF32 rest-mode source staged
- Pure 45-second rest-state policy PASS
- Native atomic Breath receipt +15 from 80->95 PASS;
  after interruption, separate headroom test verified +5
- Full ELF32 private game compiled, real isolated socket rest
  registration, anti-spam, social interruption, movement, HUD,
  saved Annex room and Breath 94 after reconnect PASS
- Production PID, executable and accepted private baseline unchanged

The ONLY remaining resting acceptance is the real elapsed-time
+15 recovery award with a connected player. The prior atomic
fixture directly invoked the Breath callback, so it cannot prove
the MUD schedules that callback while connected.

Round79Q is a socket-only test of the already accepted private
Round79P executable, with no new MUD compilation or game patch.
The helper round79q_real_rest_tick.py reduces Breath through
legitimate native wilderness movement, enters a real rest session,
then observes individual native recovery jumps with read-only
skills commands over a bounded wall-clock window. It accepts
exactly +15 with sufficient headroom and no immediate duplicate;
earlier +5 normal pulses do not count. A +15 granted before
45 seconds is rejected.

private_real_rest_tick_only.sh runs the unit tests, prints a
read-only audit of exact native update_ply call sites, then
runs the same proved private chroot/network socket world with
HD79Q_TIMED_REST=1. It guards the original accepted ELF32
executable SHA256 and production service PID/binary. Its
private timed-rest-socket.log stays outside GitHub.

Use a new root-only /root/hollowdeep-dev/round79q-* checkout,
pinned to its published commit; SOURCE must be the accepted
Round79P private /tmp/hd-army-game-round79rest-JQgo3wi5/src.
Run:

    bash tools/gameplay/round79/private_real_rest_tick_only.sh \
      /root/hollowdeep-dev/round79q-PRIVATE \
      /tmp/hd-army-game-round79rest-JQgo3wi5/src

Expected ONLY if validated:
ROUND79Q: PRIVATE REAL WALL-CLOCK REST +15 SOCKET PASS.

This test may reveal that update_ply() is only called on login
or logout, rather than periodically while a player is connected.
If so, do NOT mark Round79Q PASS. The next change must inspect
and hook the actual native periodic active-player update with
the same 45-second atomic recovery/anti-spam gates in a new
disposable build. Do not modify production before explicit
approval. Mounts/Endurance/stables are still pending.


## Round79Q PASS — Round79R read-only mount foundation

Round79Q completed on private Linode with 18 passing Python
regressions and a real isolated MUD socket recovering exactly
+15 Breath after an uninterrupted natural 45-second REST tick,
without an immediate duplicate. Real \`update.c:129\` invokes
\`update_ply(Ply[i].ply)\`. This confirms the Round79P private
rest integration is actually scheduled. The full Round79K–Q
Breath/rest private gameplay sequence is accepted. No live
production deployment has occurred.

Round79R prepares for the mount milestone **without introducing
native mount gameplay yet**:
- \`native_mount_command_audit.py\` now accepts previously
  validated \`/tmp/hd-army-game-round79rest-*/src\` input
  alongside its original private source layouts.
- \`test_native_mount_command_audit.py\` verifies six
  isolated-source evidence and security cases.
- \`private_mount_foundation_round79r.sh\` recompiles the
  already designed pure terrain/Endurance rules as ELF32,
  runs the audit tests, produces a root-private native flag
  and command collision report, and compares live production
  PID/executable and accepted private ELF32 checksum.

Run from a fresh root-only pinned \`round79r-*\` checkout:
    bash tools/gameplay/round79/private_mount_foundation_round79r.sh \
      /root/hollowdeep-dev/round79r-PRIVATE \
      /tmp/hd-army-game-round79rest-JQgo3wi5/src

The Round79R source audit report is NOT a native playable
mount implementation and should not be uploaded to GitHub.
Next native feature after source validation is epoch-bound
ownership/Endurance atomic persistence and a safe stable
interaction, preserving Conjure and Raise Corpse isolation.


## Round79R accepted; Round79S epoch-bound mount-roster policy

The user's final Round79R private Linode output confirmed
eight passed source audit tests, ELF32 pure mount/Endurance
terrain rules PASS and read-only native command/flag audit PASS.
The actual native \`global.c\` has no registered mount/stable
verbs and \`mstruct.h\`/\`mtype.h\` have no match for the
candidate mount symbols. Conjure dragons and the "stable
Necromancer receipt format" preprocessor text are unrelated
to rideable mounts. Production PID, binary and private
ELF32 hashes remained unchanged.

Round79S introduces a self-contained pure C policy:
- \`hd79_mount_roster.h/.c\`: epoch-bound 6-slot max roster,
  immutable-output transitions, one active mount, explicit
  stable deposit/retrieval constrained to a verified stable
  and verified physical proximity, no Endurance refill from
  boarding/stabling, and mount-only Endurance debit for a
  successful validated native movement plan
- \`test_hd79_mount_roster.c\`: synthetic owner epoch and
  mounting, stabling, forged/stale IDs, depleted Endurance,
  duplicate/replayed movement and safe retreat regression
- \`private_mount_roster_round79s.sh\`: compile pure C
  policy together with already tested Round79G terrain rules
  as ELF32, execute tests in a root-only results directory,
  check live service PID/executable and accepted private
  ELF32 binary unchanged; no native source patch

Run a new \`round79s-*\` pinned checkout with the accepted
\`/tmp/hd-army-game-round79rest-JQgo3wi5/src\` source.

The proposed rider/stable policy is not connected to the
native MUD's character save or command tables. Real ownership
and Endurance cannot be marked playable until an atomic
player receipt/checkpoint and real private socket tests
pass. No production deployment is authorized.


## Round79S PASS — Round79T two-receipt mount wire and native store limits

Round79S passed private ELF32 deterministic tests on Linode:
6 mount species, owner-epoch validation, single active rider,
same-stable deposit/retrieval, exact Endurance-only charging,
replay/stale-state denial and exhausted safe retreat. Production
PID/binary and accepted private game unchanged.

Round79T, staged in GitHub but NOT yet run on Linode:
- \`hd79_mount_wire.h/.c\`: a canonical 64-byte on-wire
  roster representation split into **two 64-hex fragments**,
  with magic/version, 24-hex owner epoch, full revision,
  six bounded slots including 24-bit stable room, and
  CRC32 spanning both fragments.
- \`test_hd79_mount_wire.c\`: deterministic fixture for
  empty/full rosters, stable and mounted fields, bad hex,
  uppercase, mixed-generation fragments, checksum,
  rejected overwide stable ID and full revision range.
- \`audit_native_mount_receipt_capacity.py\`: read-only
  private \`hd_player_store.c\`, \`treasure_receipt.h/.c\`,
  \`hd_breath_store.inc\`, \`hd_conjure_store.inc\`
  receipt capacity, reserved ID and snapshot inspection.
- \`test_audit_native_mount_receipt_capacity.py\`: seven
  synthetic safety tests, including ELF32/production source
  and symlink denial.
- \`private_mount_wire_audit_round79t.sh\`: one command
  runs the audit regressions, native ELF32 wire fixture,
  read-only receipt audit and unchanged production checks.

Run using a fresh \`/root/hollowdeep-dev/round79t-*\` pinned
checkout and accepted private Round79P source at
\`/tmp/hd-army-game-round79rest-JQgo3wi5/src\`:

    bash tools/gameplay/round79/private_mount_wire_audit_round79t.sh \
      /root/hollowdeep-dev/round79t-PRIVATE \
      /tmp/hd-army-game-round79rest-JQgo3wi5/src

Expected marker ONLY after test execution:
\`ROUND79T: PRIVATE MOUNT WIRE AND NATIVE RECEIPT AUDIT PASS\`.

Important: The wire format is **not** a native save
implementation. The two new reserved claim IDs have not been
assigned, and the native player receipt set may have capacity
limits that must be inspected. Both fragments require ONE
atomic player snapshot/CAS alongside existing Conjure,
Necromancer and Breath receipts. CRC32 detects random
corruption/mixed fragments, not malicious spoofing;
authorization and epoch binding remain server-side.
Never copy a partially tested candidate or its fixtures to
the live world/server. Production deployment NONE.
