# Round79AD R3 — private four-receipt native atomic death storage

**Candidate only; not a playable mount release.** This extends the same
`round79ad-fasttrack-integration-candidate-20261122` branch and is based on
R2's accepted private, disposable ELF32 source.

R2 passed on Linode: private exit 0, six-species fleet, death-receipt wire,
verified native action preflight, complete ELF32 build, old Breath/stablecheck
socket regressions and unchanged production PID/binary.
Private R2 results stay on Linode under `/root/hollowdeep-dev/round79ad-o5SzhW1S`.

R3 adds the **first actual native player save path** for death receipt #83:
`hd79_ad_four_store.inc` links inside the disposable `hd_player_store.c`,
reusing the existing root-owned locked player-directory, compressed save
snapshot, exact epoch from durable Breath, native receipt codec and one atomic
rename. It initializes the entire 80/81/82/83 record set for an empty roster,
or safely upgrades only an already verified **empty** triple. It must not
manufacture a death history for a populated legacy roster. Read-only calls
fail closed on partial, corrupt, missing or epoch-mismatched receipts.

The only R3 mutation callable in the private whole engine is **monotone
mark-dead** with all four expected receipt wires compared under the same
native player lock. Before-rename failure must leave all prior receipts
unchanged; uncertain rename requires read-back and cannot be retried blindly.
The native test fixture has an extra compile-time-only `TESTING` award helper
for creating synthetic owned mounts in a disposable player directory. That
helper is **not linked into the complete private MUD**. Legacy two/three
mount record write calls fail closed under the new feature flag, and #83 is
reserved against ordinary item/loot claims.

One runner: `tools/gameplay/round79/private_mount_ad_four_store.sh WORK SOURCE`.
`SOURCE` must be the untouched R2 staged source at
`/tmp/hd-army-game-round79adgate-MquoMVsW/src` and `WORK` a fresh
`/root/hollowdeep-dev/round79ad-*`. R3's complete native ELF32, compressed
player fault replay, six-species baseline and socket checks must all pass.

**Still disabled:** combat-death hook, player-facing mount commands, generic
owner awards, four-way board/stable/retrieve movement commits, reconnect
rehydration and atomic wilderness move/Endurance writes. No production or
live world/player/service writes; no private fixtures/logs/credentials in Git.

## Linode R3 native result — PASS (private foundation only)

Exact source `e1fa35059b41330d2b437dfcc414f74bb4e45538` validated at **exit 0** on 2026-11-23. Private results: `/root/hollowdeep-dev/round79ad-F5Dos5uu`; staged ELF32 source: `/tmp/hd-army-game-round79adfour-03lRN95P/src`. Actual compressed native player save confirmed all four claims 80/81/82/83, reserved #83, old-writer denial, test-only award and stale CAS rejection, before-rename rollback, after-rename exact death receipt reconciliation, ordinary player save preservation, same-name new epoch isolation, full native ELF32 game link, and isolated REST/stablecheck/Breath/logout socket regressions. Production PID/binary and prior R2 ELF32 baseline remained unchanged.

This **does not** validate actual combat death callbacks or player commands. Login restoration and mounted wilderness movement remain disabled. Keep results, fixtures and player records private; do not promote this candidate to accepted or announce a release on Discord.
