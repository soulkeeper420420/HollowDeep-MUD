# Round 11 — Native character save crash recovery and guild security gate

Status: **NOT TESTED / NOT APPROVED FOR PRODUCTION**. Baseline Round 10G completed 50/50 isolated native gameplay checks (private workspace `round10-graceful-NylI8Od3`), including all three characters surviving a graceful disconnect and restart. This does **not** cover forced termination mid-save, filesystem failures, or all room transfer paths.

## Stage 11A — Read-only implementation audit
Inspect the **private** `round10-persist-PE4PRFyX/src` implementation of `files2.c` save/load, the compression function and its input/output buffer contract, the `savegame` command and shutdown/disconnect paths, and current compiler settings. Do not edit existing test or production files. Use the supplied read-only script. Save its output under the owner's private development directory if desired; do not publish real player records.

Known risks from native `files2.c`: `save_ply(str,ply_ptr)` rotates `player/name` to `player/name~`, opens a new primary, writes compressed data, closes and deletes backup. The compressed write branch does not robustly validate `size`, short write, `close` or `fsync`; an abrupt SIGTERM can leave an empty primary. Recovery from backup is not currently automatic. Existing code's compression output buffer allocation and upper bounds require review against the actual `compress` implementation before rewriting.

## Stage 11B — Candidate native save implementation in a *new* disposable source copy
Only after 11A verifies the native binary format and compressor contract:
1. Make the existing primary untouched while writing a new securely created temporary file in the same directory. Validate owner, regular-file type, path, and length.
2. Validate compression bounds and every write, including EINTR/short writes. Validate close/fsync and then atomically rename the completed temporary file over primary, with directory fsync where supported.
3. Preserve a recoverable last-known-good copy without exposing passwords or data; never delete the only valid primary until a complete replacement is durable. Verify compatibility with original `load_ply`.
4. Do not enable the `HD_ROUND9_ISOLATED_FUNDS` test-money macro or `HD_GUILD_STAGING_FREE_CREATE` in any production executable. Do not overwrite live player files or world source.

## Stage 11C — Fault injection and recovery acceptance tests
- Native load/save/reload round trips with inventory and balances for at least three disposable characters.
- Kill the private server at predetermined stages of save; confirm each player retains either the old valid character or the committed new one, never a zero-byte primary.
- Inject `EINTR`, `ENOSPC`, `EIO`, partial writes, failed `fsync`, failed `rename`, and temporary file creation failure. Confirm fail-closed operation without gold, item, or guild data loss.
- Confirm guild spent-token ledger and inventory reconciliation across interrupted saves; prevent duplicate deed redemption.
- Verify no real player data or production rooms were copied into the disposable chroot.
- Audit every entry to private guild rooms (ordinary exits, sneak, login relocation, teleport, traps and staff commands), including malformed/unreadable guild registry and role database.
- Keep failed artifacts and exact test logs. Roll back untested changes from staging only.

## Release
Production promotion is **not authorized** by Round 10G. Require full 11B/11C tests, separate production backup, staged rollback rehearsal, manual operator approval, and source checksum comparison. Post redacted changelog to GitHub and Discord only after review. Never include private configuration, user credentials or player-save contents.
