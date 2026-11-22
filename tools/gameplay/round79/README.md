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
