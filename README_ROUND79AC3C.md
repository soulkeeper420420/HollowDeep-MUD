# Round79AC3C — trusted, unexposed native mount template-spawn backend

This private feature-gated HollowDeep accepted private source validates a live owner,
reads canonical authoritative mount receipts 80/81/82, checks a **trusted C
catalog** of native template IDs, loads a native creature, inserts it into the
owner's exact room, and registers exact-pointer mount identity. A failed bind
rolls the creature out of the room and frees it. A repeat request to an
already bound mount cannot create a duplicate. No player command or login
path calls the new function, and **no template IDs are configured** on behalf
of production. No public mounting/spawning or stable/ride logic is enabled.

The standalone native test compiles real accepted ELF32 roster, presence,
world identity, travel and spawn policy with synthetic native load/add/free
functions and a synthetic player-save reader. The full private ELF32 game build, spawn/rollback fixture and isolated socket replay **PASS** on Linode (exit code 0).

The next milestones must authenticate template mapping against vetted native
monster templates, remove/restore transient NPCs on logout/reconnect and
handle room transitions and death before gameplay mounting can be enabled.
Do not deploy to live or expose this API directly to player commands.

Acceptance: 2026-11-22. No mount templates configured, no gameplay spawning exposed and no production deployment. Private results are retained only on Linode under `/root/hollowdeep-dev/round79ac3c-R3JagCC3`.
