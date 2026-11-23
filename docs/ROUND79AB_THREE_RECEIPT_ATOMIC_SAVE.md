# HollowDeep MUD — Round 79AB private atomic 3-receipt mount persistence

Input: native accepted Round79Z ELF32 candidate under `/tmp/hd-army-game-round79stable-*/src`, GitHub `round79-gameplay-qol` **pinned** at `4c6f86c73dc4a0e5dd71b3b91ba8082f590689db`, and the already tested Round79AA physical-location policy.

This candidate reserves ID ending `82` for physical positions and stages all three receipts (`80`, `81`, `82`) into a **single compressed, atomic native player snapshot** under `PLAYERPATH`'s exclusive lock. It checks canonical wire, authoritative Breath character epoch, expected revision and the exact prior three receipts before each mutation.

- A fresh empty roster is initialized with all three receipts together. Repeating initialization conflicts.
- The only permitted legacy migration is an EMPTY two-receipt roster; zero owned mounts cannot be teleported. A populated legacy roster lacking 82 fails closed.
- Existing `hd79_mount_store_init` and `hd79_mount_store_commit` are entirely disabled when `MOUNT_PRESENCE_STORE_PLAYTEST=1`; no old code may mutate only 80 and 81. This temporarily disables old in-game dismount until its command adapter is converted to the three-receipt transaction.
- Ordinary player saves, Necromancer pet receipts, Breath receipts and character epoch must survive.
- Crash/fault simulation: before-rename rolls back all three; after-rename returns uncertain, and the caller must re-read the **whole** state. Stale revisions and recycled character names cannot replay old writes.
- The fixture's synthetic award assigns a room provided by the test ONLY; it does not imply a safe public-world award implementation. Real mount creature identity, stable matching, logout/reconnect, movement and entity death are later separate gates.
- Strictly private source copy and fixture; no socket listener, production world, service, players, authentication, secrets or fixture logs are published.

Accepted on Linode (private ELF32, exit code 0), 2026-11-22: 80/81/82 one-snapshot save, same-room presence policy, before-/after-rename replay, stale CAS denial, preserved Breath/Necromancer receipts and full native game build PASS. Results: `/root/hollowdeep-dev/round79ab-oPXa64jA` (private, not published). R2 fixed Makefile target prerequisite expansion to build the new `.o` before link.

Use a fresh isolated copy of the accepted native Round79Z source and `tools/gameplay/round79/private_mount_presence_store_round79ab.sh` to reproduce. The runner intentionally pins the historical Round79Z commit; do not silently repoint it to this new head.

**No live deployment.** Native mount creature binding, boarding/stabling/retrieval, and ridden travel remain disabled.
