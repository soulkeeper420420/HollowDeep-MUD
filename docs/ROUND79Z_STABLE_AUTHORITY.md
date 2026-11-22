# HollowDeep MUD — Round79Z verified stable authority

Accepted on private native ELF32 game and isolated socket, 2026-11-22.
Production world, players and service were not changed.

- Root-owned, non-world-writable `hollowdeep-data/mount-stables.hds`
  contains a bounded canonical `HDST1` registry of world room IDs.
- Symlinks, malformed records, duplicate/unsorted IDs, invalid ownership
  and writable registry directories/files are rejected.
- `stablecheck` validates a native player's current room against the
  verified registry; it performs no writes to the mount roster.
- Isolated socket tests verified stable and non-stable rooms and preserved
  depleted Breath through save, logout and reconnect.
- Native mount boarding, stabling, retrieval and ridden movement remain
  deliberately **disabled** pending physical mount-presence verification.

Source is staged only into a disposable ELF32 build via
`stage_stablecheck_round79z.py`. The private runner uses a separate
`stable-mock/` header set so previous Round79Y mock tests are not changed.
