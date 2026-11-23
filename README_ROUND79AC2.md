# HollowDeep Round79AC2 — native mount identity (accepted private ELF32)

An internal, process-local world-entity attestation gate. No new player
commands and no mount spawn or award. Bind and verify only through server-side
native creature pointers and exact room membership, never monster names.

To run, use `tools/gameplay/round79/private_mount_world_identity_round79ac2.sh`
with a fresh `/root/hollowdeep-dev/round79ac2-*` directory and the accepted
Round79AC1 private ELF32 source. The runner exercises native ELF32 policy,
stages a new disposable game, fully rebuilds ELF32 and replays isolated socket
regressions. Production remains unchanged.

Next gate: explicit native mount creation/lifecycle, logout and destruction
revocation, and reliable reconnect recovery, before boarding/stable/retrieve.

Round79AC2 R2 accepted on Linode, 2026-11-22: native ELF32 policy, entire ELF32 game build, isolated stablecheck/Breath socket and no-production-change regression **PASS**, exit code 0. No game deployment. Boarding/stable/retrieve remain disabled until trusted spawn/deletion/logout hooks are validated.
