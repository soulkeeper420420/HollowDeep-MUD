# Round 79AD R6B — Private native four-receipt action CAS

## Scope

R6A proved ownership, exact native creature identity, stable-room authority,
and death receipt #83 using read-only native preflight. R6B adds a private,
feature-gated **atomic action save boundary** using that same verified preflight
and the existing R3 `PLAYERPATH` native compression, lock and atomic rename.

The new function is `hd79_ad_four_action_commit_native` in
`tools/gameplay/round79/hd79_ad_four_action_store.inc`. It takes a *native
creature pointer and action/ID*, never caller-supplied room IDs, death proofs,
stable booleans, physical-presence claims, or proposed roster data.

1. Run R6A's full owner, location, #83 and exact-pointer preflight.
2. Open and exclusively lock the native player save directory.
3. Load the player, validate the authoritative character epoch, and compare
   all four old canonical saved receipts (80, 81, 82, 83).
4. Rerun R6A's native authorization while the save lock is held.
5. Recalculate the only legal action transition, comparing all four resulting
   canonical wires with the authenticated preflight outcome.
6. Save all four receipts in one compressed native player snapshot; preserve
   death serial/bits, Breath, inventory, owner identity, and other claims.
7. Return success only after a confirmed atomic snapshot. On a pre-rename
   failure, refuse the change. On an uncertain rename, do **not** acknowledge
   any native creature side effect or retry blindly; caller must reconnect and
   inspect the four canonical records.

## Private staging and test source

`stage_mount_ad_four_action.py` copies a clean, private R6A ELF32 source to a
fresh `/tmp/hd-army-game-round79adcas-*/src`; it only changes that clone's
`Makefile`, `hd_player_store.c` include block, and adds the reviewed header/inc.
Neither R3's atomic writer nor the native command table, room/creature code,
wilderness movement, mount constructor, or world templates are edited.
`MOUNT_AD_ACTION_CAS=1` requires `MOUNT_AD_AUTH_ACTION=1`.

`private_mount_ad_four_action.sh` additionally builds a **separate test-only
ELF32** with the R5 synthetic `adfixture` command. The test checks a
successful native board/dismount save and exact revision, before-rename
failure with unchanged four records, uncertain-rename no-acknowledge followed
by canonical readback, duplicate transition rejection, then reruns six R5
real native combat deaths, permanent tombstones, and restart verification.
The normal R6B candidate must not contain the synthetic fixture/grant.

## Safety and non-goals

This is **not yet a playable mount system**. Even a successful four-receipt
save does not atomically remove/create a physical mount monster. No production
commands call this function. Do not deploy the candidate or enable player
board/stable/retrieve actions until R6C can stage/rollback physical creature
lifecycle, resolve uncertain post-rename states without duplication, enforce
no teleport or duplicate pointers, and test all four actions and failures.

R6B also does **not** implement login recovery, mounted combat death, or
native mounted Endurance/movement coordination. These are later gates.

## Status

Local Python staging/generator tests and host C99 type/syntax checks pass.
The real native ELF32/isolated socket replay on Linode is a separate gate;
this document does not assert that it has passed until its test log confirms.
Production world/player/service must remain unchanged.
