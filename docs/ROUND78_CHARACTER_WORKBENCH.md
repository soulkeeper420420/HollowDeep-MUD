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


## Round 78D — Native Warlock save/creation contract (after 78C audit)

The verified private Round 77 candidate has 20/20 passing Round 78C framework
tests. Exact source audit confirms these native integration points:

- command1.c class selection stores a transient 'n' for Necromancer and uses
  MAGE for legacy class compatibility. New characters are written by
  hd_store_create_necromancer() or hd_store_create_player().
- hd_player_store.c checks Necromancer identity by decoding the existing
  HDTR1 receipt within the same compressed native character save. A Mage
  numeric class ID alone is **not** proof of special-class identity.
- global.c lists fixed legacy class strings, and the creature.class field in
  mstruct.h remains a byte. Do **not** renumber native class IDs.
- A second special class must use a distinct identity receipt claim and
  digest, created **in the first atomic character snapshot**. Never create an
  ordinary Mage save and then perform an independent identity-grant write.
- Existing saves must remain byte-format compatible; player-save reads,
  existing Necromancer identity, Conjure, rebirth receipts, and the live game
  must stay unchanged while the Warlock is built privately.
- The new subclass must deny Necromancer-only Raise Corpse, preserve Mage
  class behavior for ordinary Mages, and expose Pact Bolt only to confirmed
  Warlocks. Pactbrand remains gated behind a verified rebirth, not just a
  client-supplied counter.

The planned first Warlock candidate uses the existing Mage native numeric
class ID with a new durable Warlock receipt. That is a design decision for
the isolated build, **not** a guarantee of final balance. Before patching,
inspect the exact store_internal enum/mode receipt insertion, class
selection/menu, and command/skill dispatch in the private candidate. Source
inspection is limited to the private source, never production data.

Round 78D is blocked on exact code anchoring, not a failed gameplay test.
Do not label Warlock playable until native ELF32 compile, creation,
logout/reconnect, receipt spoof/replay, ordinary Mage and Necromancer
isolation, real Pact Bolt combat, and regression suite all pass.


## Round 78E — Atomic Warlock creation candidate (private, not live)

The exact Round 78D source report identified:
- command1.c class selection and one-shot atomic creation (lines 241–258, 485–488).
- hd_player_store.c receipt reservation, existing Necromancer query, and
  store_internal's first-save receipt insertion (lines 25–45, 245–320).
- The existing native Mage ID and class help/command dispatch.
- No new native creature fields or numeric class/race IDs are needed.

The stage_warlock_identity.py tool now stages a strict private patch to
Makefile, command1.c, hd_player_store.c/.h and hollowdeep_help.c, plus the
private Warlock help page. The distinct Warlock claim is
ffffffffffffffffffffffffffffff78. It is reserved against normal reward
grants, is added within **the first atomic character save**, and is verified
with the original HDTR1 checksum/receipt decoder. An ordinary Mage and an
existing Necromancer must not acquire Warlock identity. Warlock creation
uses the original native Mage class ID, so it does not change the serialized
creature structure or existing class indexes.

This source milestone intentionally exposes only Warlock identity, creation
and status help. Pact Bolt combat, Warlock-specific visible class labels,
class-specific progression and the rebirth-earned Pactbrand are **not**
implemented or announced as playable.

### Private build and acceptance gates

On the Linode private root console, use only the exact Round 77 candidate at
/tmp/hd-army-game-fyrji06g/src with the pinned SHA256. From the
character-content directory in a fresh branch checkout:

    python3 -m unittest -v test_round78 test_progression test_native_identity_audit test_stage_warlock_identity

Create a **new** directory under /tmp/hd-army-game-round78-*/src, run
stage_warlock_identity.py PRIVATE_ROUND77_SRC NEW_PRIVATE_SRC, then build
the private source with all five accepted Necromancer/Pet flags plus
WARLOCK_PLAYTEST=1. Run the compiled test_native_warlock_identity.c against
an empty disposable player directory, followed by check_warlock_socket.py
inside a separate network namespace, and rerun existing
check_new_character.py and check_creation_help.py.

**No test touches /srv/hollowdeep/world, existing production saves, or
hollowdeep.service; never point staging or test commands at the live tree.**
No publication of private test accounts, fixtures or logs. Native compilation
and socket acceptance must pass before moving on to combat implementation.


### Round 78E receipt-test correction

The native fixture initially assumed that the general-purpose
hd_store_read_claim() interface could read the reserved Warlock class
identity receipt. The private execution had already passed
hd_store_is_warlock(), but the direct claim-read assertion failed.
The fixture now validates durable class identity through the dedicated
hd_store_is_warlock() API, tests save/reload preservation, and separately
checks that hd_store_save_claim() denies attempts to grant the reserved
Warlock class claim. The native game source and the on-disk identity format
are unchanged by this test correction.


## Round 78E validation from isolated Linode playtest

The private Round 78E retest passed:
- Native atomic Warlock identity, saved character reload, Mage and
  Necromancer isolation, guarded non-Mage creation refusal.
- Real socket creation (Warlock menu), help warlock, save, quit,
  durable receipt verification and reconnect.
- Existing Necromancer and Mage native character creation regression.
- Existing native skill catalog and help regression.
- Production service PID unchanged; deployment NONE.

Known presentation issue: legacy MUD client rendered a Unicode dash in
the help page as garbled characters. The Warlock help draft now uses
plain ASCII "3-18". The current private game binary has not been rebuilt
with this text correction.

## Round 78F — Pact Bolt combat integration, first phase

New private rules module: hd_pact_bolt_rules.h/.c, plus native test fixture
test_pact_bolt_rules.c. It evaluates **provisional** playtest values:
6 MP per successful bolt; 8-second cooldown; base damage
5 + floor(level/2) + floor(INT/3), with a 50-point normal cap;
an empowered bolt consumes one available pact charge and doubles the
result. No resource is consumed by the pure validation function itself;
native combat integration must apply validated resource changes atomically.
No pact charge earning, persistence, combat command or target damage is
implemented yet. These provisional figures can be adjusted after
isolated gameplay balance testing.

To validate this rules-only module from tools/character-content:

    cc -m32 -std=gnu89 -Wall -Wextra -Werror -DHD_WARLOCK_PLAYTEST \
       -I. hd_pact_bolt_rules.c test_pact_bolt_rules.c \
       -o /tmp/hd-pact-bolt-private-rules-test
    /tmp/hd-pact-bolt-private-rules-test

For correct native combat integration, the read-only
native_pact_bolt_probe.py scans ONLY the private Round 78E source for
actual command, spell, target, combat/death and XP-credit APIs. Its
output is private source excerpts. Never copy private logs or player
fixtures to public GitHub.

    python3 native_pact_bolt_probe.py /tmp/hd-army-game-round78-VibwvrvC/src

**Do not wire Pact Bolt to raw target->hpcur arithmetic until the native
damage and death path is verified.** Warlock-only identity gating must
remain in the command handler, including reconnect, Mage denial and
Necromancer denial. A real hostile-target socket playtest and damage,
mana, cooldown, kill-credit, save/reconnect, protected-target, and
existing class regressions are still REQUIRED before calling it playable.
Pactbrand remains rebirth-only and unimplemented.
