# HollowDeep private pet disk-storage foundation

Accepted input: the operator's exact archive from the extended native cache
socket PASS (native executable SHA-256
`791ca5f9d456308e4334a1819195e280b044923751c13fc854d4776730bf7d21`).
The archive SHA-256 and all 45 source file entries matched. The native source
archive itself stays private and is NOT included in this patch package.

## What this adds

- An internal, reserved HDTR1 receipt (`ffffffffffffffffffffffffffffff76`)
  storing versioned pet stats, native room number, character epoch, revision.
  It is not a treasure claim and is refused by ordinary claim APIs even
  when the storage flag is disabled. No native creature or file-layout change.
- Verified saved Necromancer only. Fresh random 96-bit character epoch,
  monotonic revision, full expected-state comparison protected by the native
  player directory lock. Reject stale updates, old epochs after name reuse,
  invalid stats, invalid class and unsafe/corrupt files; reject revision wrap.
- Raise transaction commits a normalized trusted live character snapshot
  (inventory, worn items, gold, mana minus exactly 8) and the pet record in
  the SAME atomic player-file replacement. It never mutates the in-memory
  owner. Caller may update live state only after confirmed commit.
- Checkpoint and death transactions preserve the saved native character bytes
  and existing receipts. A dead/no-pet tombstone rejects stale live updates.
  A valid subsequent raise uses the same epoch and a higher revision.
- Uses existing fsync + rename + directory fsync. A rename with uncertain
  directory sync is reported explicitly; do not acknowledge success or blindly
  retry. Read back and resolve, including durability fencing, before continuing.

## Evidence

Native C tests against the exact supplied source, with the real compression,
legacy serializer, receipt codec and atomic snapshot writer, across fresh
processes: initialize, reserve claim rejection, non-Necromancer denial, invalid
mana/room/state, before-rename/partial-write injection, exact committed mana
charge and pet stats, live ordinary save preserves state/loot/receipt, an
injected uncertain rename, concurrent compare-and-replace, death tombstone,
name reuse/stale epoch, corrupt and symlinked save refusal. Focused 64-bit C
and sanitizer runs pass locally. ELF32 and full native link remain Linode
checks. Test functions are called directly; no actual game process restore.

## Important limitations and release gates

**NO-GO for production.** This is a storage foundation only. The new API is
not called by raise, healing, follow, death, login or any other gameplay path.
The current cache behavior remains unchanged. No corpse disk persistence,
loot journal, or restart restoration is enabled. The receipt is a reserved
internal record, not a new game command. Three private ASCII help pages
explicitly retain the existing restart warning. Do not install them live.

The next integration must couple corpse ownership/consumption, native item
and gold pickups, and pet/owner state with a recoverable journal to prevent
loot or mana duplication across process crashes. It must prevent ordinary
stale player saves from rolling back mana, tie death and damage/healing to
persistence, reconcile uncertain rename and fsync, bound storage/capacity,
validate stable room identity, verify rollback and do real crash/restart
replays. Restoring an old backup or running an old binary that does not
reserve the new receipt is not a supported rollback yet. Do not treat direct
storage tests as evidence that a skeleton survives an actual server restart.

## Run

The self-contained onepass runner accepts only the exact previously tested
private cache source. It verifies all 45 source fingerprints and the accepted
ELF32 executable hash before copying to a fresh private workspace. It patches
only the player store/Makefile, installs new source-only API and test code,
stages three help files in a disposable fixture, runs direct native ELF32
storage tests and forces a full private build with all prior flags plus
`PET_STORE_PLAYTEST=1`. The failure-injection macro is present only in the
standalone test executable. Production service PID checked before/after.
