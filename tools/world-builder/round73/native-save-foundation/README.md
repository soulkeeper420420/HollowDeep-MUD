# HollowDeep Round 73G — Native save foundation (source-only, not deployed)

**Source checked:** owner-uploaded Round 73G `native-save-contract` and the
repository's prior Round 11B atomic-save design. These files are **not** hooked
into the game, and they **do not give gold or items**. The new code is a tested
format/procedure foundation only. Production was not modified.

## Verified native source contract

- `files3.c` writes a native `creature`, a direct inventory count, and then
  recursively the native `object` records; `read_crt_from_mem` returns how
  many of those bytes it consumed. A trailing receipt inside the **same
  decompressed save stream** is therefore a possible backwards-readable
  extension, provided every active load/save path is updated safely.
- `files2.c::save_ply()` currently renames the primary player file to `~`
  before writing a replacement. In the `COMPRESS` branch it allocates its
  compressed buffer with `malloc(n)`, does not check the compressed length
  against that allocation, does not validate `write()`/`close()` success, and
  does not `fsync` the new file or player directory.
- `files2.c::load_ply()` reads at most 50,000 compressed bytes and calls
  the original unbounded `uncompress` into a fixed 100,000-byte allocation.
  The old recursive `read_crt_from_mem` has no input length parameter.
- The old `savegame()` normally copies readied equipment into a dummy
  creature inventory before `save_ply`. Native reward delivery must preserve
  that normalization, existing inventory, and equipment state.
- `treasure_guard.c` still binds monster pointers in memory only and prints
  that reward delivery is disabled. It does not instantiate durable unique
  guardians or grant rewards. A kill-event relay must be authenticated by the
  real engine; no player-supplied kill event can be accepted.

## Authored components

- `treasure_receipt.[ch]`: bounded codec for *same-file* receipt trailers after
  the serialized player/inventory payload. Each receipt contains a 32-character
  claim ID and a 64-character reward SHA-256 digest. The format has a 4-byte
  CRC32 for accidental corruption detection **not authentication**. Duplicate
  claim IDs with different digests fail closed. Supports up to 64 receipts;
  reaching capacity blocks additional rewards until an approved migration.
- `atomic_player_snapshot.[ch]`: Linux helper accepting only *already bounded
  and fully compressed* payload bytes. Uses same-directory `openat` exclusive
  temporary, repeated writes, file `fsync`, atomic `renameat`, and directory
  `fsync`. Return code 1 means the rename happened but directory durability is
  uncertain and the caller must independently reload/reconcile; it must never
  repeat the grant without checking the receipt.
- `test_receipt.c`: legacy empty-trailer handling, exact replay, conflicts,
  tamper detection, malformed input, buffer exhaustion, maximum entries.
- `test_atomic_snapshot.c`: protected-file replacement, partial-write loop,
  injected failures before and after rename, and symlink rejection.
- `test_native_serializer.c`: test against the **actual uploaded**
  `files3.c`, with a nested inventory object, gold and a receipt. When the
  optional original `compress.c` is present, also confirms compression and
  decompression of that combined raw payload.

### Run without modifying the game

```bash
bash tools/world-builder/round73/native-save-foundation/run.sh
```

For a stronger test against your *disposable* native source tree (must contain
`mstruct.h`, `mtype.h`, `mextern.h`, `files3.c` and preferably `compress.c`):

```bash
HD_TEST_ELF32=1 HD_SANITIZE=0 \
  bash tools/world-builder/round73/native-save-foundation/run.sh \
  /root/hollowdeep-dev/round72-build-EXAMPLE/round72-native-build
```

The `run.sh` script refuses a source path under `/srv/hollowdeep/` and performs
no writes to the supplied native source tree. The native serializer test
uses fixture objects only, never existing player files. Test compilation on
ELF32 and the full live-like native/browser regression are **not** claimed by
this standalone package.

## Mandatory next integration gate — KEEP LOOT DISABLED

1. Inspect the exact **private** `command8.c` and `compress.c` matching the
   currently tested engine, along with any Round 11 patched save candidate.
   The original nested archive supplies background but is not proof of the
   actual candidate implementation.
2. Implement a *bounded* recursive serializer and compressor/decompressor,
   including checked object count, nesting, and output buffer. Correct the
   existing primary save failure-reporting and equipment normalization.
3. Wire receipt decode/encode into `load_ply()` and `save_ply()` so every
   ordinary save retains receipts. Never store them only in a sidecar. A
   missing or malformed trailer must be rejected or require deliberate
   migration; don't silently reset old claim history.
4. Create reward items only from trusted native template records with valid
   wear slots, carry capacity, gold caps, and game-safe enchantments. Write
   inventory, gold, and the matching receipt in **one** atomic replacement of
   the same compressed player record. After successful commit, reconcile the
   in-memory player before acknowledging the SQLite claim ledger.
5. Persist guardian/map identities; reject wrong owner, wrong guardian,
   duplicate kill, map drop, and chest interactions by alternate commands.
6. Fault-inject actual native save at every boundary: before write, partial
   write, before rename, after rename, fsync error, crash, logout, reconnect,
   and restart. Confirm old-or-new playable save, no duplicate gold or gear,
   and all existing items preserved. Run Round 59–73F browser/native suite in
   isolated test roots. Keep production unchanged.

The package intentionally does **not** patch `files2.c`, start services,
modify player files, or change `treasure_guard.c`. Delivering real rewards
before the gates above risks permanent data loss or duplicate treasure.
