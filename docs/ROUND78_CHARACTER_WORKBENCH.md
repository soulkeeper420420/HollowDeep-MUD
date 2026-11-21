# Round 78A — HollowDeep Race & Class Workbench

**Status: development branch only.** This does not change the live Round 77
Necromancer public beta, restart hollowdeep.service, modify game saves, or
make Warlock/Vampire selectable.

## Create or edit a design draft

From tools/character-content:

    python3 content.py new class warlock 'Warlock' /tmp/warlock.json
    python3 content.py new class vampire 'Vampire' /tmp/vampire.json
    python3 content.py new race deep-dwarf 'Deep Dwarf' /tmp/deep-dwarf.json
    python3 content.py check /tmp/warlock.json
    python3 content.py preview /tmp/warlock.json

New definitions default to selectable=false and have no native class/race ID.
The example JSON files for Warlock and Vampire are **draft concepts only**.
Their ability names are symbolic design references without gameplay effects.
New playable IDs require additional C integration and save-ABI review.

## Edit a supported existing native race or class

Use the private Round 77 source, not the production tree:

    cd /root/hollowdeep-dev/round78-character-workbench/tools/character-content
    python3 -m unittest -v test_round78
    python3 native.py export /tmp/hd-army-game-fyrji06g/src class mage /tmp/mage.json
    cp /tmp/mage.json /tmp/mage-edited.json
    # Edit the copied JSON: change a supported label or hp/mp growth value.
    python3 content.py check /tmp/mage-edited.json
    python3 content.py preview /tmp/mage-edited.json --against /tmp/mage.json
    python3 native.py preview /tmp/hd-army-game-fyrji06g/src /tmp/mage-edited.json
    python3 stage.py /tmp/hd-army-game-fyrji06g/src /tmp/mage-edited.json /root/hollowdeep-dev/round78-mage-candidate

The stage command uses a new, independent private directory, checks the
generated patch without fuzz, rejects symlinks and special files, confirms
only supported files changed, and checks source immutability. It will not
compile, start a game listener, deploy, change IDs or alter existing saves.

It deliberately rejects edits that the current native-preview tool cannot
implement: new playable keys, ability/skill lists, equipment, class access
lists, random starting stats, or arbitrary attributes. Only existing native
display labels, existing racial attribute offsets, and class HP/MP growth
can be staged. Class growth changes affect future level gains only.

Any staged source must then pass the private ELF32 build, isolated native
login/creation, save/reload, skill tests, and cumulative regression before
considering deployment. A JSON validation or source-stage pass by itself
does not establish playable correctness.

## File-by-file source guide

| File | What it controls |
|---|---|
| mtype.h | Numeric class/race IDs. Never renumber existing saved IDs |
| global.c | Native labels, class growth, and command dispatch |
| command1.c | Character creation, race adjustments and class selection |
| hollowdeep_help.c, help/ | Class descriptions, skills, native help text |
| hd_necro_creation.h | Necromancer randomized starting stats |
| hd_necro_skeleton.c, hd_army_restore.c | Undead pets and restoration |
| hd_conjure_runtime.c | Universal Conjure gameplay |
| hd_player_store.c, treasure_receipt.c | Durable player and companion save format |
| tools/character-content/content.py | JSON schema, checking and draft diff |
| tools/character-content/native.py | Existing native export and preview |
| tools/character-content/stage.py | Strict private source staging |
| tools/character-content/test_round78.py | Positive and fail-closed tests |

## Round 78B planned native additions

Warlock and Vampire need dedicated design approvals and implementation:
unique identity and/or IDs, 65-point creation policy, HP/MP advancement,
prime attributes, starting stats, early skills and rebirth-only skills,
race/class interactions, help, save migration and live compatibility checks.
Preserve existing characters, Necromancer/Raise Corpse, and Universal Conjure
without modifying production until a tested release is explicitly approved.

No secrets, credentials, private player fixtures, server configuration, or
local build logs belong in GitHub.
