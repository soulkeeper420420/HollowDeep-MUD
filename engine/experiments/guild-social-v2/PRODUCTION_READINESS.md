# Guild production readiness

On November 10, 2026, the retained Linode reports for Round 11N and Round 11O each showed 84 passes and zero failures. The [Round 11N report](ROUND11N_PRIVATE_REPLAY.md) covers equipment and cross-file guild recovery. The [Round 11O report](ROUND11O_NATIVE_WRITER_FAULTS.md) covers short writes and simulated character file sync failure during native gameplay.

The offline native updater suite passed 23/23 on Linode in a fresh temporary checkout under an unprivileged user. It checks backup hashes, synthetic restoration after a failed private probe, preservation of saves, refusal to roll back with an active public client, and updater integrity checks. A root invocation produced one fixture error because the simulated game account inherited UID 0. The unprivileged rerun passed the full suite.

Production readiness remains open. Restore a verified backup into an isolated root and check the native binary, rooms, character saves, guild membership, hall access, and deed ledger together. Rehearse candidate activation and rollback against that isolated restore, verifying file hashes and repeat logins. Finish the security gate with the remaining guild hall entry routes, malformed-save cases, and process termination at the ledger and character commit boundaries.
