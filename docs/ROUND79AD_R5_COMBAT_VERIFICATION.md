# Round 79AD R5 — Private Mount Combat Validation

## Verified private tests

- Full native ELF32 engine and isolated socket combat replay passed.
- Six mount species were killed through native combat.
- Permanent death receipts survived save, logout and private restart.
- Dead mounts and duplicate spawns were denied.
- Atomic write-failure and uncertain-rename recovery were exercised.
- World Builder Rounds 59–71 passed their isolated replay.
- Native monster death, loot, exits and wilderness movement passed.
- Production was not deployed or restarted by these tests.

## Source guide

- `hd79_ad_species.c/.h`: Six private mount-species definitions.
- `hd79_ad_combat_death.c`: Native combat-death persistence handling.
- `hd79_ad_death_identity.inc`: Registered mount/owner death identity.
- `hd79_ad_private_fleet.c`: Private native mount construction.
- `stage_mount_ad_combat_death.py`: Disposable native source staging.
- `private_mount_ad_combat_gameplay.sh`: Isolated gameplay validation.
- `build_ad_combat_socket_replay.py`: Combat socket replay generation.
- `build_ad_builder_driver.py`: Legacy builder test compatibility.
- `round69_custom.py`: Living monster versus corpse/loot assertions.

## Outstanding blockers

Player-facing four-receipt mount actions, mounted-state death,
atomic Endurance and native room movement, and durable restoration
of surviving mounts remain incomplete.

This is a private development candidate, not a production release.
