# Round 59 native gameplay replay

Run `bash private.sh` on the authorized Linode development host with `replay.py` beside it. The launcher copies the existing Round 57 builder and Round 58Y runtime into a new private directory, pins the engine SHA-256 and runs the builder and both disposable servers inside private mount, network and PID namespaces. The two worlds have separate, initially empty player directories. The launcher verifies production source, room and object templates, service identity and earlier private trees before and after.

The replay uses the Round 57 HTTP plan, linking, validation, export and download handlers. It uses the Round 58Y practice golem and blade template records in the copied catalog so the exported IDs resolve to the same fixtures in the native server. The original exits are compared byte for byte. Room 16 gets a synthetic preexisting creature with a carried native object before export, so inventory preservation is exercised on a nonempty record. The native serializer checks that normalized entity and inventory bytes survive both exports.

Room 14 is reached from the isolated starter room, displays the edited forge descriptions and contains the practice golem and blade. The native pickup command is `get all` for this fixture. The first rehearsal stopped because `get blade` did not match the fixture's native keyword.

## Verified Linode result

The fresh rehearsal exited zero with `ROUND 59: PASS`. The native server printed `You get a Practice Blade.`, and inventory listed the blade. Combat emitted the explicit golem kill message. The forge remained the current room, with the golem absent. The new north exit reached the gallery and the new south exit returned to the forge after a 65-second wait. The golem reappeared on that revisit. A second native process loaded the removal export into a separate world and displayed the edited forge text with neither placement.

Both archives preserved the original exits and the fixture creature's carried inventory. Round 53's three reciprocal pairs and the Round 57 builder's monster validation, four-room native export, and duplicate and invalid room rejection passed again.

| Artifact | SHA-256 |
| --- | --- |
| Round 58Y native binary | `86dd59d6d91127b9ec6c636898463b12171ecb10c3dee2de9764da5e1d3a9d77` |
| Populated export | `033979d9c25dcecd4b337b7b4e67155f87ff608a77726db31cfffa364d28f41b9` |
| Removal export | `b48956b929a9881398b78b04a4380f307797ccd734fed324d5ccee57335e0f1cc` |

ZIP timestamps can change the bundle hashes on reruns. Each run checks the returned archive and every extracted room against the export manifest. Raw private logs, templates, room records, saves and ZIPs remain on the development host. Production checksums and service identity matched before and after.

The follow-up replay also traversed the original east exits from room 14 through room 15 into room 16. The native server loaded the embedded golem, reported its carried blade on defeat, and let the player pick it up. An initial assertion failed because the pickup output listed coins before the blade. A fresh run with an order-independent pickup check passed the full replay, including respawn and the removal world.

The exit validation follow-up preserves unchanged named exits, including existing destinations outside the export area. It rejects edits to named exits and requires newly added or redirected standard exits to target a room in the plan with a matching return exit. The targeted exit tests and full Round 59 replay passed on Linode. Two earlier runs hit the combat attempt limit after repeated misses. The passing run used the existing private RNG fixture during combat only, with the same pinned engine and real respawn timing.
