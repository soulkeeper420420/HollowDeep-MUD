# Round 11S — ledger parent-directory durability correction (pending native validation)

**Production deployment: NO-GO.** The earlier Round 11P candidate SHA-256 `12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c` remains **blocked**. The operator's Round 11R isolated fault injection reproduced that the original `save_guilds` ignored failed directory `fsync` after ledger rename and incorrectly acknowledged guild founding and consumed its physical deed.

## Change prepared in source and private patcher

The experimental source `hollowdeep_social.c` has been updated so `save_guilds` reports three distinguishable outcomes: `1` for completed rename **and** successful parent directory synchronization and close, `0` for a pre-rename failure, `-1` for an uncertain **post-rename** durability failure. This conservatively treats failed directory opening, synchronization, or descriptor closure after rename as uncertain. Both guild creation and other guild mutations now propagate that uncertainty without claiming success or an abort. In the founding path a deed remains in memory on uncertainty; on the next clan command, the existing spent-deed reconciliation logic checks the actual guild ledger before reusing or removing its serial.

These semantics **do not guarantee that a rename survives a host-level power failure**, or prove fault recovery without native tests. A subsequent guild action should not proceed until it can load a structurally valid ledger; post-rename uncertainty must be visible to staff. The current candidate is still not eligible for production release.

A strict private stage patcher `round11s_patch_ledger_durability.py` uses three exact C anchors and refuses unexpected source variants. The private runner `round11s_private_build_replay.sh` copies the existing **Round 11K** 73/73 source and runtime into a new `round11s-durability-*` stage, applies this patch, recompiles only privately, and reruns the original 73 native regression checks in PID/network/mount isolation. It verifies protected production and baseline checksums and never updates real rooms, game executables, player files, site or service. **This runner has been published but not executed.**

## Required to close the release gate

1. Run private 73/73 regression and examine the output and executable checksum.
2. Inject an actual failing directory `fsync` against the rebuilt private candidate, verify uncertain-response text and that the deed was not immediately consumed, verify ledger serial state, then restart and reconcile once. Include directory `open` and `close` failure paths where safely injectable, and pre-rename failure.
3. Rebase the correction onto the **exact** hook-free Round 11P release candidate source, rebuild and record a **new** SHA-256. Re-run 90 populated, 11 kill recovery and 23 movement/full rollback checks with the new binary.
4. Finish Round 11R's **Town Square `district` exit** and reciprocal `town` exit on disposable copies of real-world rooms; never replace production starter rooms. Save canonical room hash, ACL, and return-route evidence.
5. Rehearse post-activation ledger archive, saved district-occupant relocation, rollback and reactivation using the exact new candidate and populated world. Do not discard ledger or revive a previously redeemed deed.

Codex's unfinished Round 11R changes may exist only in its previous uncommitted workspace. Do not presume they are on the GitHub branch. **No production restart or deployment is authorized.**

## First private replay attempt and launcher repair

The first executed Round11S private stage was `/root/hollowdeep-dev/guild-social-batch1/round11s-durability-0bYa1VZC`. The exact three-anchor source patch applied, its 32-bit binary built with SHA-256 `46e02ee8a7274d6083d64fe7e2db24c582a32c98c2654d3aeced756219558db9`, and the production / Round11K baseline checksums remained unchanged. However, the test summary showed **Passed: 0, Failed: 0**, so no assertions ran and this build has **not** passed the regression. The likely launcher error is that the disposable rootfs top directory was created `root:root` mode `0700`, preventing the unprivileged `65534` game process from traversing it. The private launcher now `chown -R 65534:65534` **only the new disposable rootfs** before test execution, with a symlink check and better failure log tails. The exact cause must be confirmed if the rerun still fails; the native runner has not yet been rerun with this repair.

## Round11S native replay passed; actual post-rename fsync EIO replay staged

The operator reran the repaired Round11S private launcher in `/root/hollowdeep-dev/guild-social-batch1/round11s-durability-NXKx5FiI`. It reported **73 passed, zero failed**, after rebuilding the tri-state commit source with equipment-safe saves preserved. Exact private executable SHA-256: `8dbd6cd1d03b763ff0f454bba11861dd9470052716e2624838f5fec919c7f446`. Production source and prior private test stages matched their original checksums; no live deployment/restart. The earlier 0/0 attempt is superseded by this complete private regression.

A new, **unexecuted** private one-shot fault replay is available in `round11s_fsync_private.sh` with its helpers `round11s_fsync_inject.c` and `round11s_fsync_replay.py`. It pins the known 73/73 executable and copies its clean non-player rootfs assets to a brand-new rootfs, compiles a **32-bit test-only LD_PRELOAD** module, and runs the MUD inside separate mount/network/PID namespaces. It triggers pre-rename `EIO` once (expect old ledger and deed unchanged), then a post-rename `fsync` `EIO` once (expect an uncertainty acknowledgment, exact single redeemed serial, and retained deed and native save). The replay abruptly kills the native server, restarts from the original saved character, checks that one `clan` command reconciles the spent deed without modifying ledger bytes, and checks second reconciliation and duplicate guild founding remain denied. The run has **18 expected assertions**, but **none are claimed to have passed until Linode results are supplied**.

The next pass still will **not** establish host-power-loss directory durability or certify the hook-free release build. Those, Town Square world integration, and transaction-preserving rollback remain release gates. **Production NO-GO.**
