# Guild production readiness

On November 10, 2026, the retained Linode reports for Round 11N and Round 11O each showed 84 passes and zero failures. The [Round 11N report](ROUND11N_PRIVATE_REPLAY.md) covers equipment and cross-file guild recovery. The [Round 11O report](ROUND11O_NATIVE_WRITER_FAULTS.md) covers short writes and simulated character file sync failure during native gameplay.

The offline native updater suite passed 23/23 on Linode in a fresh temporary checkout under an unprivileged user. It checks backup hashes, synthetic restoration after a failed private probe, preservation of saves, refusal to roll back with an active public client, and updater integrity checks. A root invocation produced one fixture error because the simulated game account inherited UID 0. The unprivileged rerun passed the full suite.

## Round 11O readiness rehearsal

- Verified Round 11N's original retained report against the published scripts at commit `adefa83`. The report records 84 passes, including the founding-save blade recovery, both staged transaction failures and durable spent serials.
- Restored an existing native updater world archive into a fresh root-owned private directory and verified all 4,529 archived files. The updater's rollback function restored or removed all 76 manifest targets after simulated replacements. The rehearsal checked target contents, mode and numeric ownership and rechecked the original backup files.
- Started the restored 32-bit binary with restored rooms and help in a disposable chroot and network namespace. It reached the native login prompt using empty account and ledger directories. Archived account bytes were verified on disk and kept private.
- Reran Round 11O from a fresh private stage. All 84 assertions passed, including corrupt-save refusal, malformed-ledger fail-closed behavior, hall access for members, outsider denial, spent-deed reconciliation and same-port restart. Production source and Round 11K checksums matched. The live service PID and activation timestamp also matched.

## Rollback preparation and release gaps

Before any separately approved deployment, build and identify a release binary that excludes the isolated funds, fixture and fault hooks. Create a fresh backup under the planned quiesced maintenance procedure, verify all hashes and rehearse activation and rollback of that exact build in isolation. The existing backup rehearsal verifies the historical rollback mechanism and file set. The new guild release needs its own manifest covering every changed file and the treatment of any guild data created after activation.

The final security gate remains open for the release binary. Exercise private hall entry through teleport, traps, login relocation and staff movement in addition to the covered routes. Verify role fallback, malformed-save cases beyond the two existing fixtures, and abrupt process termination at the ledger and character commit boundaries. Validate the release candidate and its rollback together before requesting production approval.
