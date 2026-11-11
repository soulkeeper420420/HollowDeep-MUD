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

## Round 11P candidate and binary rollback

The private candidate was built from the checksum-protected Round 11K source with a full rebuild after removing the test funds source, command and compiler flag. Binary symbols, strings and build output were checked for the test funds, fixture, fault hooks and free-founding bypass. Candidate SHA-256 was `12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c`.

Seven smoke assertions passed. The exact candidate denied both test grants, required a purchased deed, and saved a disposable character. Swapping the executable for the verified archived predecessor reached the login prompt and preserved the isolated character and ledger bytes. This covered a binary swap with a disposable save and empty guild state. A full rollback still needs the candidate's room, source and data manifest and a policy for populated guild state. The source scan found the centralized player-room insertion check and the live room scan found IDs 6000–6011 unused. Dynamic alternate-entry and transaction crash tests remain open.

Run the private build and smoke test with `bash round11p_private_candidate.sh <restored-predecessor-binary>` and keep `round11p_candidate_smoke.py` alongside it. The launcher verifies production source, the Round 11K private tree and live service identity before and after the rehearsal.
