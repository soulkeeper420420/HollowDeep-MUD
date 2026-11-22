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
