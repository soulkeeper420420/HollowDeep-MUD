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
