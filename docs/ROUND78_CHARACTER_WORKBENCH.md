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


## Round 78B: reusable progression definitions

The existing content.py schema remains unchanged, so previously authored
race/class drafts and native-preview workflows keep working. New separate
class progression JSON files capture design settings that are not yet
supported by native.py or the MUD engine:

- prime_attributes: exactly two distinct native stats.
- starting_stats: 65-point allocation (3–18 each), or explicitly bounded
  pre-race random rolls for STR, DEX, CON, INT, and PIE.
- skill_unlocks: a declared class ability, a minimum level 1–60, and
  a minimum number of rebirths 0–60.

The Warlock draft uses INT/PIE with first-life Pact Bolt and rebirth
Pactbrand. The Vampire draft uses DEX/CON with first-life Blood Drain
and rebirth Crimson Veil. These are **proposal placeholders**, not implemented skills.
The 65-point allocation rule is modeled in draft form, not installed.

### Editing and checking

    cd tools/character-content
    python3 -m unittest -v test_round78 test_progression
    python3 content.py check examples/warlock.json
    python3 progression.py check examples/warlock.json examples/warlock-progression.json
    python3 progression.py preview examples/warlock.json examples/warlock-progression.json --level 1 --rebirth 1
    python3 content.py check examples/vampire.json
    python3 progression.py check examples/vampire.json examples/vampire-progression.json

To author a new plan, create a class draft with content.py, then run
progression.py new YOUR-CLASS.json /tmp/your-progression.json --prime
intelligence --prime piety. Keep production class IDs and native saves
unchanged. Unrecognized ability references, duplicate unlocks, invalid
rebirths, unsupported fields and bool-as-integer attacks are denied.

**Round 78C prerequisite:** Examine actual native class creation and save
identity, establish IDs or durable identity markers, implement and test class
hooks and commands in an isolated ELF32 build before making new class
definitions selectable. Schema checks are not playable-class tests.


## Round 78C — Native identity and ABI audit

A critical prerequisite for a selectable Warlock is understanding how
Necromancer stores its **distinct persistent identity** while retaining
the ordinary native Mage numeric ID. A second class must not falsely
inherit the Necromancer identity, bypass Necromancer-only skills, or
invalidate existing character saves.

On Linode in a fresh checkout of round78-character-workbench:

    cd tools/character-content
    python3 -m unittest -v test_round78 test_progression test_native_identity_audit
    python3 native_identity_audit.py /tmp/hd-army-game-fyrji06g/src

This diagnostic refuses non-disposable source paths and binary drift,
prints only selected C creation/identity/serializer source excerpts,
and never accesses live player data. It is an **inspection gate**, not
a claim that Warlock native gameplay is implemented. The next stage is
an isolated Warlock creation and durable identity patch, followed by
actual ELF32 compile, socket login, persistence, skill and regression
testing. No production deployment or restart is permitted.
