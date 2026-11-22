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
