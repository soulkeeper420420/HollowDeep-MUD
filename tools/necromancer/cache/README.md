# HollowDeep private Necromancer/corpse room-cache persistence

Baseline: operator-reported native gameplay PASS at replay `4b959e7`, using
combined ELF32 binary SHA-256
`26c806cf59b159555f8c0ec73f5daa0c0b0516d99bced49487c30cde0397bde7`.

This milestone preserves corpses and living skeletons **within a single
process** across ordinary native room-cache eviction/reload. It does not
implement cross-process/disk persistence, and is **NO-GO for production**.

- Corpses are per-room-number linked records, not pointers to a freed room.
  Original inventory tags (including nested objects), gold and corpse IDs
  survive eviction until consumed. No old 1024-record global fixed ceiling;
  heap allocation failure still falls back to native drops, and ID exhaustion
  is refused. Explicit storage quotas/backpressure and room-ID retirement are
  still required for long-running production use.
- Living pets detach from the native monster/active lists prior to room
  free, retain owner and existing live HP/MP in the process, and reattach
  when that room is loaded or the owner reconnects/moves. Native real-death
  cleanup is unchanged. Both ALLITEMS and permanent-only room monster
  serializers exclude registered pets, preventing accidental ordinary monster
  copies from those room saves. This is not persistent ownership across
  account deletion/recreation; identity binding and other monster-export
  paths still need audit.
- The legacy level 7-9 Mage title `Necromancer` is replaced by `Conjurer`
  under the corpse playtest flag. The verified identity-specific native
  `title_ply()` hook still returns `Necromancer` for the real class. The
  original legacy Mage titles are unchanged outside the private compile flag.
- Seven revised native help pages use plain ASCII (no broken em dash glyphs)
  and accurately describe the new in-process scope. They are staged only in
  the private fixture; they have not been installed into production.

## Run

Use the pinned branch package `onepass_linode.py` with the exact previously
validated private corpse source tree. It guards the executable SHA, six-file
coupled input fingerprints, the verified title hook, and six output hashes.
It copies source to a fresh private test workspace, applies the contextual
patch with zero fuzz, stages help, runs focused native C tests and a full
forced ELF32 build, and compares the production service PID before/after.
A source mismatch is a safe stop. Do not force or apply against live source.

## Local evidence

Reconstructed source fixture: actual native `free_rom`, room tag insertion
and `write_rom`/`read_rom` plus `load_rom` LRU eviction (601 room files through
the 600-entry cache), both native `reload_rom` replacement paths, retained
live damaged pet HP/MP, nested escrow, denied cross-room/double consumption,
1,100 simultaneous corpse records, no pet duplication in ALLITEMS save,
and no resurrection after native free/registry cleanup. The fixture wraps
`load_obj` for its gold template and `add_permcrt_rom` to assert no permanent
spawn templates. Title test links the known Codex title branch reconstructed
locally; the server runner links the actual `player.c` and checks its marker.
Actual native healing and help tests, syntax, duplicate-patch rejection,
ASan/UBSan (native fixture built with global data instrumentation disabled to
permit GC of unrelated native command tables), and a fresh self-contained
64-bit bundle replay passed. Full Linode ELF32 and socket regression on the
new candidate are pending. The previous candidate's combined socket pass
remains valid but is not a pass for this patch.

## Next release gates

Use a versioned persistent corpse/pet transaction format anchored to saved
character identity and room identity. Commit corpse capture/consumption,
loot ownership, mana debit and summon/death records with recoverable
ordering; preserve existing room and character binary layouts, and reject
corrupt/replayed records. Test crash windows, restart restore with exact
current HP/MP, death tombstones, name reuse, room reassignment, ordinary
loot collection, rollback compatibility, and capacity limits. Do not claim
crash-safe exactly-once behavior from process-local tests. No production
restart or deployment authorized.

## Operator-reported Linode ELF32 acceptance

At pinned commit `afbe9da970a8e1493706776f663dfebc5ef908f1`, the maintainer reported PASS for the exact private input/output fingerprints, seven ASCII native help pages, native free/serialization, suspended pet stats, corpse ID and escrow retention, 1100 simultaneous corpses, no duplicate or resurrected pets, actual LRU/reload paths, class title identity, corpse/healing/help regressions, both native syntax modes, and the full ELF32 build. Accepted private candidate: `necromancer-playtest-cache-jyf14lkl/src`. The service PID was reported unchanged; production deployment NONE. This confirms the focused native room-cache tests on Linode; it does not establish disk/restart persistence or a real socket pass for the new executable. Keep production NO-GO.

## Extended cache gameplay and next durable-storage source handoff

Run `cache_gameplay.py PRIVATE_CACHE_SRC PRIOR_GAMEPLAY_PY CACHE_BUNDLE_PY` in a fresh network namespace with loopback enabled. Use the exact previously accepted private `necromancer-playtest-cache-jyf14lkl/src`. The prior gameplay harness comes from commit `4b959e7` (its native fixture and socket/chroot helpers passed on the previous combined executable), the cache bundle from `afbe9da`. The extended test verifies six output fingerprints, records the new executable SHA, writes a private allowlisted ZIP of source only, then runs a two-room native fixture against the cache executable inside an unprivileged chroot. It checks actual gold/item pickup, skeleton movement, ordinary Mage/Necromancer titles, corpse gates and repeat-denial, native help and reconnect. It has not yet run on Linode. The private source ZIP must be uploaded to the development conversation (not GitHub) for the exact player-store and native save hooks needed to implement safe cross-process persistence; it contains no world files, player saves, credentials databases, logs, binary or config files. Review private source before sharing. Local Python syntax, pinned fingerprint and ZIP allowlist/permissions/manifest checks passed. A live rollout or restart is not authorized. Disk persistence and crash-safe loot consumption remain unimplemented.
