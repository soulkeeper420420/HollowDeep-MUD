# Round79AD R2 — private native death receipt + trusted action preflight

This is an **unaccepted** addition to the Round79AD candidate, not a new live game feature. It defines an epoch-bound, monotonic 64-hex death receipt for a future reserved internal record #83, plus a server-only native pointer/stable/owner action preflight for board, dismount, stable and retrieve. Neither is connected to player saves, combat deaths, login, player-facing commands or gameplay movement.

Synthetic local checks: eight Python staging tests; C death wire tests (epoch/CRC, deceased IDs, no automatic restoration), and C native action-preflight tests (dead/forged/invalid owners, exact presence, verified stable). Real native ELF32 build and isolated socket validation must be run on Linode before claiming even a private foundation PASS.

**Run:** `tools/gameplay/round79/private_mount_ad_death_gate.sh WORK /tmp/hd-army-game-round79adfleet-J8jHd6Io/src`, with a fresh `WORK=/root/hollowdeep-dev/round79ad-XXXXXXXX` directory.

The accepted `round79-gameplay-qol` branch and production service/world/player files remain unchanged. The fast-track issue is #8; the full playable mount integration is still blocked by authenticated four-receipt CAS, durable death save, reversible creature effects, reconnect crash recovery, native travel commit and six-species socket gameplay.
