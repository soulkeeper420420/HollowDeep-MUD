# HollowDeep MUD — Round 79W–Y accepted mount storage and command backend

Accepted on isolated native ELF32 builds on 2026-11-22. **Not deployed to production.** This repository contains source, strict staging tools, and synthetic test code only; never live player data, logs, or credentials.

## Round 79W — durable mount ownership

- Two reserved native receipt IDs `80` and `81`, each storing one fragment of a canonical mount-roster wire record
- Both fragments written by one locked, compressed atomic player save
- Mount identity bound to the authoritative durable character epoch
- Stale transaction, half-pair corruption, uncertain rename and recycled player name denied or reconciled
- Normal native character saves preserve mount ownership, Endurance, and existing Breath/pet receipts
- Linode native ELF32 atomic player-store test: **PASS**

## Round 79X — private authorized mount actions

- Bounded command grammar: `mount list/status/ID`, `dismount`, `stable ID`, `retrieve ID`
- Backend respects owner epoch, stable-locality context, one rider, revision CAS, and no Endurance refill on retrieval
- Missing/corrupt roster, stale CAS, forged stable context, failed save or uncertain write denied or reconciled
- Linode native ELF32 transaction and pure-policy tests: **PASS**

## Round 79Y revision 2 — native MUD commands

- Feature-gated native command table registration for `mount`, `dismount`, `stable`, `retrieve`
- Native command adapter performs read-only listing/status and durable dismount
- **Boarding, stabling and retrieving are deliberately disabled in the actual game** until independent physical-mount presence and world stable authority have been verified
- Exact full command text is parsed rather than `cmd.val[]`, which conflates missing and numeric arguments
- Revision 2 fixes over-strict `cmd` layout staging assumptions while preserving fixed-array and dispatch checks
- Linode private full ELF32 game build and isolated socket replay: **PASS**, exit code 0
- Socket verified no mount receipt was auto-created by read-only commands and that Breath survived logout/reconnect

## Remaining gates

- Verified native stable metadata and physical mount-world presence
- Actual boarding/stabling/retrieval gameplay
- Mounted wilderness Endurance precommit and terrain constraints, without bypassing existing exit rules
- Isolated native gameplay/socket tests and explicit deployment approval before any production change

The Round79T pinned test fixture checkout remains at its historical commit; later branches must not mutate that private reference.
