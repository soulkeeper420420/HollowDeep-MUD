# Round 79T native mount ownership

The private candidate extends the accepted Round 79S six-mount roster policy and the Round 79T canonical two-receipt wire. It uses the accepted native ELF32 rest/Breath build as its source baseline.

## Commands

- **mounts** lists owned mounts, the selected mount, Endurance and stable location.
- **mount ID** selects an owned, present mount.
- **dismount** returns to foot travel.
- **stable** lists the same roster and stable commands.
- **stable buy SPECIES** buys one mount. Species 1–6 use the existing Horse, Warhorse, Dire wolf, Nightmare, Griffin and Dark dragon profiles.
- **stable deposit ID** stores an owned mount at the current verified stable.
- **stable retrieve ID** retrieves it at that same stable.

The private purchase schedule is 100 gold times species ID. This is a development choice awaiting gameplay balancing. The candidate models mounts as persistent roster companions accompanying their owner. A present mount follows its owner until deposited. Mount ownership and riding selection survive reconnect and restart. Combat stats, mount death and Endurance regeneration are outside this implementation. Deposit, retrieval, dismount and login preserve the spent Endurance.

## Stable configuration

The server supplies a game-owned regular file at rooms/stables.map, with permissions preventing group or other users from writing it. It contains HDSTABLE1 followed by one native room ID per line. The reader validates the entire file, rejects duplicate/out-of-range IDs and symlinks, and limits it to 128 stable rooms. The isolated tests configure fixture room 2. Production stable locations require a separate world review before any rollout.

## Persistence and travel

The staging script copies the accepted private native tree into a fresh /tmp/hd-army-game-round79mount-*/src directory and verifies source/build anchors. The two new reserved receipt IDs end in 7a and 7b. Ordinary treasure claims cannot use them. Both fragments are written in the same compressed player snapshot and consume two of the 64 receipt slots. A full set fails before any character or gold write.

The mount store runs inside the existing player-store translation unit. The directory lock covers reading the character, checking the authoritative Breath epoch and both expected mount fragments, serializing the normalized inventory, and publishing the snapshot. A stale epoch or revision, a missing half-record, malformed wire or failed write denies the change. Receipt bytes for other systems remain in the snapshot.

The native command parser preserves explicit numeric mount arguments. Commands save purchase gold and mount state together before confirmation. An uncertain rename is reconciled against the saved pair, room and gold. Failed reconciliation ends the session without saving an older in-memory image over the uncertain record.

Mounted movement enters through the existing destination-validated native Breath precommit boundary. It reads terrain using the same bounded wilderness parser and charges the profile's Endurance cost once. It saves the new native room and mount pair together before the ordinary room transfer. Native exit restrictions remain authoritative for flying species as well. A denied exit or terrain spends no resource. Mounted travel preserves player Breath. At zero Endurance, an interior retreat remains free. On foot, the existing Breath path handles the move.

## Source guide

| File | Responsibility |
|---|---|
| hd79_mount_store.h, hd79_mount_store.inc | Paired receipt reads, epoch/revision comparison and atomic player/mount writes |
| hd79_mount_game.c | Stable validation, native commands, uncertain-save reconciliation and travel integration |
| hd79_mount_roster.*, hd79_mount_wire.*, hd_mount_travel.* | Existing bounded ownership rules, canonical wire and terrain/Endurance profiles |
| stage_mount_native.py | Guarded edits to the native player store, command table/parser, wilderness reader and Makefile |
| test_native_mount_store.c | ELF32 real-player-store failures, competing writers, full capacity, inventory and epoch checks |
| check_mount_socket.py | Actual native purchase, ride, stable, movement and restart replay |
| check_mount_regressions.py | Prior native Breath, HUD, rest and natural recovery replay |
| private_mount_native_round79t.sh | Consolidated build, tests and production integrity checks |

Run from the repository checkout on the authorized Linode host, using a new output directory.

    bash tools/gameplay/round79/private_mount_native_round79t.sh /root/hollowdeep-dev/round79t-new-results /tmp/hd-army-game-round79rest-JQgo3wi5/src

The runner checks the accepted native binary SHA-256, compiles ELF32, runs source tests and isolated native gameplay, and verifies protected live source/room/object-monster files, running executable, service identity and accepted private source. Test fixtures and logs stay private.

## Executed validation — 2026-11-22

The consolidated Linode runner completed successfully from repository parent c4697140e2fb8af21c32f5809cb7eb2ab0a410f5. It compiled the full private ELF32 game and checked the accepted native baseline without modifying it.

- All 137 existing Python regression tests passed.
- Strict ELF32 Round 79S roster and Round 79T canonical wire tests passed.
- The real native player-store replay passed purchase/gold and paired-receipt persistence, ordinary-save preservation, pre-rename failure, uncertain post-rename readback, stale revision/epoch refusal and four concurrent submissions with exactly one successful change.
- A valid outer native receipt containing only one mount fragment failed closed. A recreated character name rejected the old epoch. A full receipt set refused purchase without publishing a partial pair.
- Native movement spent Endurance down to zero through real atomic room checkpoints. Exhaustion denied another wilderness step, while an interior retreat remained free.
- Actual socket gameplay passed buy, mount, repeated-mount denial, stable deposit/retrieval, remote-stable denial, terrain costs, denied exits, unchanged mounted player Breath, ordinary save, SIGKILL/restart, reconnect and stable persistence. Foot travel after dismount spent player Breath while retaining mount Endurance.
- A focused native save-store replay verified that a wielded test item and an existing treasure receipt survived mount writes.
- The prior rest/travel/HUD socket replay passed against the final native candidate, including a genuine connected 45-second +15 recovery event with no immediate duplicate.
- Protected production source, room and object/monster hashes, the running executable, service identity and accepted private source matched before and after. The active service PID stayed 51424.

The tested private native executable SHA-256 is 372c97fd5feca2fc4f1a4d034b573fb5c69e1ffa8804987d0c94dbfe69c4f7b6. Raw native fixtures, worlds and test logs remain on Linode.
