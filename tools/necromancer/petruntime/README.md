# HollowDeep private pet runtime persistence

## Scope

Based on the operator's successful pet-store ELF32 foundation, this separate
`PET_RUNTIME_PLAYTEST=1` builds on the existing four private feature flags.
Raises commit the native player snapshot, 8 MP debit, and saved pet receipt
before acknowledging the summon. The existing room-local corpse release
follows this commit. Failed known pre-rename writes leave the corpse intact.
Verified login restores a living pet once, at its owner's login room, with
its recorded current/max HP/MP and level; same-process logout preserves the
pet and only an authenticated reconnect can bind an offline slot. Restore
costs no mana. Native follow, room eviction, logout, command and update
boundaries checkpoint changed stats/location. A native death records a
no-pet tombstone before removing the pet. Unexplained removal of a living
registered pet and uncertain/conflicting writes stop the **private** process
rather than silently acknowledging or deleting its durable state. Ordinary
random monster wandering/despawn excludes registered pets; their native
regeneration uses widened arithmetic before saturation. Seven ASCII help
pages are included. No production deployment is permitted.

## Tests

Exact 47-file source allowlist from the accepted native storage candidate;
verify all six modified outputs. The one-pass runner copies the source to a
new private workspace, runs the previous storage foundation tests and actual
native corpse, pet lifecycle, serializer, receipt and room-tag tests across
fresh test processes. They test failure before rename, 8 MP, released loot,
restore without charge, damaged HP/MP, movement, cache unload, authenticated
reconnect, no redundant writes, uncertain-write stop, unexpected-live-free
stop, a recorded death and raising a new pet. Local native64 tests passed on
exact source, with test doubles for output, active list, deity and gold
object loading. Local syntax used the original update.h and excluded the
HD74_PRIVATE_NATIVE define because its exact integration header was absent
from the 45-file source export. Linode runs full integrated private syntax
and a forced ELF32 build. The runner then executes a real socket replay with
three distinct private listener processes inside a chroot and separate
network namespace. It raises, picks up loot, moves, logs out, stops the first
listener, restores the saved skeleton on the next listener, kills it via
native combat, and verifies no resurrection on another restart. This
socket replay has not run locally. No claim of real gameplay PASS until the
operator returns its success markers.

## Limits / NO-GO for production

Only pet state is now hooked into the runtime; corpse and released floor loot
are still **process-local**. Monsters and transient room drops may reset on
restart: the corpse/loot transaction journal, unique death/loot identity,
atomic collection and rollback are not implemented. A private listener
restart after a completed durable operation is not a power-loss test. A
crash between mutation and checkpoint can lose the most recent changes;
uncertain rename must be reconciled before any production recovery; failure
before a death commit can leave the previous living record. The private
fail-stop policy is not a production recovery policy. No concurrent live
engine or offline editing of active saves is supported. Owner name/room
retirement, capacity, storage exhaustion, full damage/healing/DM lifecycle
coverage and ordinary save rollback need further audit. A restored pet does
not appear until its verified owner logs in. Pets are single-owner, one per
owner, native-Mage identities protected by existing receipts. This patch
cannot be deployed to production or used as proof of crash-safe loot.
