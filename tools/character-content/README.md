# HollowDeep race and class definitions

Use these editable JSON drafts to plan and review character content. The
same commands support a new definition and edits to an existing JSON
definition. They leave the MUD source, native IDs, and game saves alone.

```sh
python3 content.py new race deep-dwarf 'Deep Dwarf' deep-dwarf.json
python3 content.py new class spellblade 'Spellblade' spellblade.json
python3 content.py check deep-dwarf.json
python3 content.py preview spellblade.json
```

To edit, copy the accepted JSON to a draft, keep its kind and key, and
change the desired fields. Review it with
`python3 content.py preview draft.json --against accepted.json`.
Definitions start with `selectable: false`. Ability, trait, equipment and
allowed class entries are symbolic keys for review. Reference resolution and generating brand-new native entries belong to
the next integration step.

## Import and preview an existing native entry

Use a development source directory containing `mtype.h`, `global.c` and
`command1.c`.

```sh
python3 native.py export ./src race dwarf dwarf.json
python3 native.py export ./src class mage mage.json
python3 native.py preview ./src dwarf.json
```

Permitted native edits currently include display labels, starting racial
attribute offsets, and class HP/MP gained per level. Keep the exported key
when renaming a display label. The existing creation menu text, input
selectors, adjectival race names, and saved numeric IDs remain the same.
Class growth edits apply to future level gains and preserve existing saved
HP/MP. Unsupported field changes and new native keys are rejected.
The preview prints a unified diff and leaves the source directory alone.


## Round 78A safe staging and automated tests

See [Round 78 Workbench Guide](../../docs/ROUND78_CHARACTER_WORKBENCH.md).
Run the test suite with:

    python3 -m unittest -v test_round78

To stage a **supported edit to an existing native entry** in a new private
directory, review the diff first and then run:

    python3 native.py preview PRIVATE_SRC EDITED.json
    python3 stage.py PRIVATE_SRC EDITED.json NEW_PRIVATE_SRC

The source and the live game are not modified. Staging is **not** a gameplay
build or release. Warlock and Vampire under examples/ are nonselectable
design drafts, not new playable classes.


## Round 78B: Prime attributes, starting stats and rebirth skills

A new class can have a **separate progression JSON** without changing the
backwards-compatible class definition schema. For example:

    python3 progression.py check examples/warlock.json examples/warlock-progression.json
    python3 progression.py preview examples/warlock.json examples/warlock-progression.json --level 1 --rebirth 0
    python3 progression.py preview examples/warlock.json examples/warlock-progression.json --level 1 --rebirth 1
    python3 progression.py check examples/vampire.json examples/vampire-progression.json

Generate a new plan for a class definition:

    python3 progression.py new MY_CLASS.json /tmp/MY_CLASS-progression.json --prime intelligence --prime piety

Then edit the plan. The current schema supports two distinct native prime
attributes, **65 allocated points** (3–18 per attribute), or explicit random
base ranges (3–18); level 1–60 skill unlocks and minimum rebirth count 0–60.

Every unlock references an ability key from the matching class JSON. A
first-life ability uses rebirth 0; a post-rebirth ability uses rebirth 1.
For example, the Warlock concept unlocks "pact-bolt" immediately and "pactbrand"
after one rebirth. The Vampire concept unlocks "blood-drain" immediately
and "crimson-veil" after one rebirth. These are design labels with no native command,
damage, spell, ID or player-save implementation yet.

Run both suites:

    python3 -m unittest -v test_round78 test_progression

**This is planning and schema validation, not native gameplay implementation.**
Do not change "selectable" to true or announce these classes as playable
until their C hooks, numeric/persistent identity, creation, skills, HP/MP
growth, save/load, and isolated gameplay tests are complete.


## Round 78C: read-only native identity audit

Run this on Linode, **against the exact verified disposable Round 77 source**:

    python3 -m unittest -v test_round78 test_progression test_native_identity_audit
    python3 native_identity_audit.py /tmp/hd-army-game-fyrji06g/src

The audit validates the expected 32-bit candidate fingerprint, checks
creation and persistent Necromancer identity hooks, and prints bounded,
source-code-only excerpts from native class definitions and save interfaces.
It never opens player saves, reads the production world, starts or restarts
the game, or changes native C files.

The Warlock and Vampire examples now use the skill names from
docs/design/base-class-and-race-expansion.md: Pact Bolt / Pactbrand, and
Blood Drain / Crimson Veil. Their code and durable class identity are **not**
implemented by these draft JSON files. Actual native creation and save
integration must follow this audit in an isolated build.


## Round 78E: private Warlock native identity and creation

Following the verified Round 78D report, the private Warlock stage now
protects a distinct HDTR1 receipt without modifying legacy numeric class
IDs. The exact new receipt is reserved against ordinary reward grants,
and creation stores it in the first atomic save. Existing Mage,
Necromancer and Conjure behavior remains available in the private candidate.

The source-only patch tool is stage_warlock_identity.py. It copies the
exact Round 77 candidate into a fresh /tmp/hd-army-game-round78-*/src
directory, adds a Warlock menu option and class help, and rejects drift,
unexpected source layouts, symlinks, and already-patched destinations.

The private test suite includes:
- test_stage_warlock_identity: source staging and fail-closed anchors.
- test_native_warlock_identity.c: native save, load, receipt reservation,
  Mage and Necromancer isolation, and refusal of wrong native class.
- check_warlock_socket.py: real native character creation, save, class
  help, persistent receipt, quit/reconnect, and forbidden Raise Corpse.

Run the following only in a disposable worktree, never production:

    python3 -m unittest -v test_stage_warlock_identity

Then stage with stage_warlock_identity.py, compile with
WARLOCK_PLAYTEST=1 plus existing Necromancer flags and run the ELF32
native fixture and socket replay under a separate network namespace.

**Not yet playable:** Pact Bolt/Pactbrand combat and Warlock-specific
score display are outside this identity-only milestone. No production
deployment, service restart or migration is authorized.
