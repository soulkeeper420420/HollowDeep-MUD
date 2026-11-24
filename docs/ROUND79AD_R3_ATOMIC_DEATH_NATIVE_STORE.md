# Round79AD R3 — first native four-receipt player persistence

## Change boundary

Private source-only feature `MOUNT_AD_FOUR_STORE=1` requires R2's
`MOUNT_AD_DEATH_GATE=1`. Its include operates inside existing native
`hd_player_store.c` only in a freshly staged `/tmp` copy. Source modifications
are limited to adding the 80/81/82/83 include, reserving #83 against loot,
disabling old 3-receipt init/commit and appending a Makefile feature flag.
Existing room, native action, combat, live player, wilderness and global
file structures are unchanged. The two-receipt writer is already disabled
in the accepted three-receipt private baseline.

## Native transaction contract

- A read returns ABSENT only if **all four** mount fragments are missing;
  missing #83 for a populated older roster is an error. The same applies
  to corrupt CRC, noncanonical payload or wrong owner epoch.
- Fresh initialization under the native PLAYERPATH `flock` creates all four
  records in one compressed atomic save, or inserts #83 only for a fully
  verified, truly empty old 80/81/82 triple. No populated migration.
- `mark_dead` accepts exact prior roster, presence and death evidence, under
  lock compares all four canonical wires (not structure padding), and
  advances only the death bit plus monotone serial for the specified ID.
  Repeated death, wrong ID, wrong epoch, stale four-wire receipt and
  revision conflict all fail closed.
- If the atomic rename reports an uncertain outcome, caller must re-read
  and compare #80/#81/#82/#83 before acknowledging death. There is no
  automatic replay or attempt to repair a partially corrupt set.
- The normal player-save path preserves the serialized claims. During this
  feature, legacy triple mount init/commit are disabled, so old commands
  cannot mutate mount state without #83.
- The isolated native test fixture adds `HD79_AD_FOUR_STORE_TESTING`, which
  permits **only synthetic award creation in test**. There is no equivalent
  award entry point in the full native game build.

## Native test plan

Eleven staging/isolation regressions. Build real ELF32 native compressed
player-store fixture; check four-way init, reserve-claim denial, stale CAS,
before-rename failure, after-rename read-back recovery, spent Breath,
ordinary player save preserving all four claims, recreated owner epoch
separation and no dead mount resurrection. Rebuild entire private ELF32 MUD,
run unshare-isolated stablecheck/Breath/REST socket and verify production
PID/binary and accepted R2 ELF32 unchanged.

## Open integration blockers

1. Mount combat death callbacks must authenticate exact live creature identity,
   save the death receipt, and reconcile uncertain renames **before** creature
   cleanup or client acknowledgement; power failures require fail-closed
   recovery. Current R3 has no death callback.
2. General four-receipt action CAS and native creature side effects need a
   reversible checkpoint for board/dismount/stable/retrieve, no remote actions,
   no duplicate mounts and root-owned stable authority.
3. Reconnect must prove the last native creature's survival or explicit
   durable spawn provenance; zero death bit alone cannot authorize restore.
4. Mounted wilderness travel must commit actual movement + Endurance exactly
   once, preserve foot Breath, allow free retreat and reject save failures.
5. Private isolated gameplay socket for all six species, death, logout,
   reconnect, commands, and movement must PASS before any accepted promotion.

This is **NOT** a full Round79AD gameplay release and must not be deployed.

## Linode R3 native result — PASS (private foundation only)

Exact source `e1fa35059b41330d2b437dfcc414f74bb4e45538` validated at **exit 0** on 2026-11-23. Private results: `/root/hollowdeep-dev/round79ad-F5Dos5uu`; staged ELF32 source: `/tmp/hd-army-game-round79adfour-03lRN95P/src`. Actual compressed native player save confirmed all four claims 80/81/82/83, reserved #83, old-writer denial, test-only award and stale CAS rejection, before-rename rollback, after-rename exact death receipt reconciliation, ordinary player save preservation, same-name new epoch isolation, full native ELF32 game link, and isolated REST/stablecheck/Breath/logout socket regressions. Production PID/binary and prior R2 ELF32 baseline remained unchanged.

This **does not** validate actual combat death callbacks or player commands. Login restoration and mounted wilderness movement remain disabled. Keep results, fixtures and player records private; do not promote this candidate to accepted or announce a release on Discord.
