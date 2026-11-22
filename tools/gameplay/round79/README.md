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
