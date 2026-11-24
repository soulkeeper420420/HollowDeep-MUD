# Round 79AD R6A: Native authenticated action gate (unexposed)

## Why R6A exists

R2's `hd79_ad_verified_action_plan` accepted a supplied `proof` pointer. It could only enforce a *proposed* death record and read the older three-receipt native store. R3/R5 made the fourth receipt #83 durable and demonstrated six-species combat tombstones. It would be unsafe to expose the R2 preflight unchanged or use the legacy three-receipt mount action writer, which the private R3 build explicitly disables.

R6A's `hd79_ad_authenticated_action_plan` instead reads #80/#81/#82/#83 together from the native verified player record (no supplied death proof). Missing/invalid #83, a dead mount ID, owner not exactly once in room list, duplicate/corrupted owner, wrong room or epoch, missing bound mount pointer for board/stable, and unapproved stable locations all fail closed. Existing pure `hd79_ad_private_plan_action` returns the proposed next roster/presence only. Output is untouched on denial.

## Limitations—mandatory

- **Read-only preflight.** No new command dispatch or command authentication; the native `hd79_mount_command_ac.c` still uses old fail-closed behavior for board/stable/retrieve and the old 3-receipt dismount writer is blocked by R3.
- **No four-receipt action commit**. Previewed state is not written; future locked CAS must validate the exact four canonical old wires and re-read uncertain renames.
- **No creature side effects**. Board/retrieve/dismount/stable require reversible exact-pointer bind/unbind/spawn/despawn choreography and fail-closed rollback. R6A must not be called as a user-facing mutation.
- **No reconnect survival proof**. `hd79_ad_death_reconnect_allowed` remains false. Living mounts cannot be restored without durable provenance.
- **No mounted move**. Native travel and Endurance must be checked and committed with native room movement in one coordinated transaction, preserving foot Breath.

## Safety and tests

Only two new C files and a feature flag/Makefile edit are staged in a fresh `/tmp/hd-army-game-round79adauth-*` tree; existing `creature.c`, `room.c`, `global.c`, `hd_player_store.c`, mount command, R3 four-receipt store, wilderness and lifecycle code are byte-identical. The Python suite rejects live paths, symlinks, preexisting stages, untrusted Makefile anchors and a test-only native command fixture. The private ELF32 runner then tests C owner/state/permission gates, full native engine build, stablecheck/Breath/logout socket replay, and unchanged production service.

R6A code and local staging tests can be committed to the existing **unaccepted** Round79AD fast-track candidate branch. Real Linode ELF32/socket validation and complete R6 gameplay remain pending until explicitly run and verified. Never promote to `round79-gameplay-qol` or deploy this candidate to production on the strength of R6A tests alone.
