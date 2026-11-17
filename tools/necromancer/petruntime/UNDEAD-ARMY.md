# Necromancer Undead Army

Raise Corpse is the level-one Necromancer skill. A successful cast permanently
binds an eligible slain monster. The pet keeps its identity and basic combat
role, with stats capped for the playtest. Reject player, boss, and summoned
corpses. Keep the existing atomic 8 MP debit on success.

## Playtest balance

The class expansion design already records these capacity thresholds.

| Necromancer level | Active pets |
| ---: | ---: |
| 1 | 3 |
| 7 | 4 |
| 14 | 5 |
| 20 | 6 |
| 27 | 7 |
| 34 | 8 |
| 40 | 9 |
| 47 | 10 |
| 54 | 11 |
| 60 | 12 |

Revival chance is 50% plus one percentage point per Necromancer level above
one and five percentage points per level of advantage over the monster. A
monster level above the caster subtracts five points. Clamp to 10–95%. At
level 10, targets at levels 5, 10 and 15 yield 84%, 59% and 34% respectively.

Allow one roll per eligible corpse. A failed roll spends the revival
opportunity while leaving loot available. Validate capacity, ownership,
corpse eligibility, and available mana before rolling. Preserve normal XP
and loot for the original kill and award successful raises an additional
10% of the monster's base XP, subject to native XP limits. Raised pets earn
their own XP from eligible kills and drop their own loot once on combat
death. Track each award independently so it cannot repeat on replay.

## Raise Corpse cooldown and unique summons

- `rc` and `rc <id>` are aliases for `raise corpse` and `raise corpse <id>`. All forms share one 120-second cooldown per Necromancer.
- Start the cooldown when an eligible revival rolls, whether it succeeds or fails. Rejected commands such as a missing corpse, insufficient mana, or a full roster do not start it.
- On successful revival, roll independently for a 5% chance to raise a unique undead variant. Double its base attributes and maximum HP and MP, capped by the native field limits. The unique still occupies one slot and uses the usual mana cost, bonus XP, and loot rules.
- Persist the unique identity and resulting stats with the pet. Restore those values as saved on relog or restart. Private acceptance must cover both alias forms, the shared timer, and unique persistence.

## Proposed commands

| Command | Behavior |
| --- | --- |
| `raise corpse [id]` | Select a corpse in the current room and attempt to bind it. |
| `pets`, `pet status` | Show IDs, names, HP, MP, pet XP, and orders. |
| `pet attack <target>` | Order eligible pets in the room to attack a valid target. |
| `pet follow`, `pet stay` | Change the orders of the owner's available pets. |
| `pet dismiss <id>`, `pet dismiss all` | Durably remove the selected pets without a death drop. |

Use the native target-selection conventions for healing and require an
unambiguous target where names collide. Check available native command
prefixes before adding aliases.

## Persistence and validation

Keep stable pet IDs within the existing character epoch. Read the existing
single-pet record into a one-entry roster with its identity and current
stats. Retain the death state of an existing tombstone. Commit conversion
through the native atomic save path with the current revision check and
keep the old record readable until the first successful commit. Persist
each pet's identity, HP, MP, XP, inventory and behavior. Preserve location
policy for parked pets. Remove living entries on death and dismissal in a
revision-checked transaction before allowing effects that can be repeated
after a restart.

The multi-pet playtest needs separate failure-path tests for monster loot,
the one-roll corpse state, raise XP, and pet death loot. The existing
process-local corpse capture is insufficient to demonstrate crash-safe
reward delivery. Test competing writes, uncertain rename and stale
epochs against the same assertions used after clean logout. Reconnect
and restart with several living pets and confirm that a killed pet stays
dead while its surviving siblings retain exact stats and inventory.

## Private replay follow-up

Use `replay_existing_runtime.py --prepare-only` with the corrected operator
runner to inspect how many direct north moves need a cooldown wrapper. Its
positional arguments are the runner, accepted private runtime directory,
accepted binary SHA256, prior socket replay, and cache socket replay. For
the native run use the same arguments under
`unshare --net --mount --fork python3` and drop `--prepare-only`.
The replay verifies the binary checksum, stages a disposable copy, and
checks the production service MainPID before and after. Collect the
native combat death result, the final restart result, and the durable
logout and direct disk inventory assertions before accepting the candidate.

## Private ELF32 baseline verified

On November 17, 2026, the operator confirmed that both private ELF32
storage suites passed on Linode. The isolated single-pet gameplay replay
then reported `REAL NATIVE SOCKET RESTART/DEATH PASS` and exited zero.
The final durable save retained 1,013 gold and one fixture ruby, with
zero pet HP and MP after death and restart. The production service PID
was unchanged. The successful run brought up loopback inside the private
network namespace before launching the replay.

## Future class development

Graveburst remains the proposed rebirth unlock for a completed Necromancer
life. Preserve same-class mastery, Memories of Past Lives items with
stat effects, a selectable inherited skill for the next class or
subclass, and Legacy Points for gifts, special spells and utility items
such as weightless bags. Keep the recipe model for every base class, with
multiple distinct paths per class. Fighter followed by Cleric can unlock
Guardian. Special classes have their own masteries and can qualify for a
challenging quest that unlocks a unique class with upgrades and hidden
features. Track these as future mechanics alongside base class and race
expansion.
