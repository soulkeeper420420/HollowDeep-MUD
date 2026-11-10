# Round 11B — Crash-safe native player serialization design review

**Status: design gate only; not implemented or tested. Do not deploy to production.**

## Verified from the owner's Round 11A read-only audit

- `src/files2.c:516`: native `save_ply(char *str, creature *ply_ptr)` uses the legacy K&R signature.
- `save_ply` rotates `player/<name>` to `player/<name>~`, creates a new primary and writes through the custom compressor, then deletes the backup even when the compressed write was short, zero or failed. The compressed branch does not verify `write`, `close`, or `fsync`. Arbitrary interruption can leave a zero-byte primary and a valid `~` file.
- It allocates output with `malloc(n)`, where `n` is uncompressed serialization size, while `compress()` writes to the output pointer without an explicit capacity parameter in the observed API. It is **not safe to assert a bound on the output** until `compress.c` is fully inspected. Merely replacing the primary-file write is insufficient.
- `load_ply` reads at most 50,000 compressed bytes and `uncompress()` into a 100,000-byte buffer; its return value and short reads need tighter validation without changing the native file format.
- `command8.c:657` `savegame()` clones the live creature and adds readied objects to the duplicate's inventory before calling `save_ply`. On a failure it logs `merror(..., NONFATAL)` but still prints `Player saved.`. Guild V2 currently calls `save_ply` directly at two points; this bypasses the readied-object normalization the native save command uses and needs regression coverage.

## Safety-critical open questions (block implementation)

1. Inspect the complete custom `compress.c` writer helpers `writec`, `putcode`, and `flushout` and derive/enforce a maximum output capacity; inspect the native `write_crt_to_mem` capacity contract and whether serialization can exceed 100,000 bytes. **Never invoke an unbounded compressor on an undersized buffer**.
2. Determine whether the native `compress` stream can be validated before replacement by the existing loader, and how to reject a decompressed length mismatch.
3. Examine file modes, signal paths, and login recovery behavior; do not introduce an incompatible on-disk format.

## Candidate algorithm (fresh private source only)

- Validate the player name against the native account naming rules and reject traversal, symlinks and invalid target directories.
- Serialize the player using the engine's canonical format, including readied objects, with verified bounds.
- Compress into a proven bounded buffer (or a bounds-checked compression writer), validate lengths and success.
- Use a private, same-directory temporary file with exclusive creation and safe mode. Write all bytes in a loop handling EINTR and short writes, check fsync/fdatasync and close. On any failure, remove only the candidate temporary file; the previous primary remains unchanged.
- Commit with an atomic rename of the complete temporary file over the primary and fsync the parent directory. If preserving a last-known-good backup, design crash-consistent backup rotation and recovery so it cannot remove the only readable save.
- Check all errors. Return failure to the caller; do not report `Player saved.` on failure. Keep guild spent-token redemption idempotent across a save failure.
- Make `load_ply` reject empty/malformed streams cleanly and test backup recovery without silently creating an account.

## Acceptance gates

- 32-bit private compile and native on-disk format compatibility; character, readied equipment, inventory, gold and guild records round trip.
- Inject EIO, ENOSPC, EINTR, partial write, failed fsync/rename, and forced SIGKILL at multiple commit points in a disposable chroot; old **or** new save remains readable after each point.
- Guild founding/consumption and spent serial replay tests across every interruption; denied hall entry for nonmembers through exits, teleports, traps and reconnects.
- All tests in new `round11-*` private workspaces; production engine and player files untouched, previous Round 10 test data preserved.
- Require separate operator approval, backup and rollback rehearsal before *any* production promotion. Test-only gold minting stays staging-only.

See [the Round 11B compressor contract audit](round11b_compressor_contract_audit.sh) to collect the missing source-level details without executing the game.
