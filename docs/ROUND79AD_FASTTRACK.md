# Round79AD — accelerated private six-species mount integration

One candidate branch and one full Linode runner for the new mount path. Work is
**not** accepted or production-ready until end-to-end ELF32 gameplay, death,
reconnect, stable, travel and save-failure tests all pass.

## First integrated foundation (unexposed)

`hd79_ad_private_fleet.c/.h` contains six **inert, 1-HP, zero-attack** native
creature constructors named for Horse, Warhorse, Dire Wolf, Nightmare,
Griffin and Dark Dragon. They never copy a hostile/boss/quest creature or
write a production monster-template file. The server-only spawning function
reads authoritative character receipts 80/81/82, verifies exact live owner
room-list membership, mount ownership and location, and binds the exact
new native creature pointer to the accepted AC2 identity registry. It
refuses duplicate mounts and rolls back native insertion on binding failure.

The function is **not connected** to any command, login or movement hook.
Restoration is explicitly denied because the current receipt set does not
contain a proven durable mount-death tombstone. A dead mount must never be
resurrected just because an old location receipt exists.

The figures 1 HP, level 1 and zero mana/attack are *noncombat test placeholders*
only; no gameplay stats are approved here. No creature will appear in a live
room from this code. Pre-existing production and accepted ELF32 remain unchanged.

## Remaining gates for this same candidate

- Trusted mount-death tombstone and combat/room-exit cleanup.
- Durable save/reconnect restoration with no duplicate or dead resurrection.
- Authenticated board/dismount/stable/retrieve using real native pointers,
  root-owned stable authority and atomic three-receipt CAS.
- Native wilderness move -> mount Endurance charge exactly once with
  failed-save rollback/reconciliation and free safe retreat.
- One isolated socket replay for all six species, save failures, expiry,
  logout/death/reconnect, commands and movement, plus old stablecheck/Breath.

Until those gates pass, this branch is **not for accepted promotion** and
must not be deployed. No private tests, player fixtures, credentials, or
world copies go into GitHub.

## Unified action/terrain planner (unexposed)

`hd79_ad_private_transitions.c/.h` wraps the accepted roster/presence
functions with a single server-only transition planner. It derives three-
receipt after-states for boarding, dismounting, stabling and retrieval, and
calculates mounted Endurance debit only when a native move is confirmed.
Safe non-wilderness retreat is identified separately as **no receipt write**;
the user's Breath is preserved. Native pointer/stable authority and durable
save CAS are still external requirements. The planner cannot authorize a
command or update a world on its own.

The single private runner compiles the planner against actual accepted ELF32
roster/presence/travel sources, then compiles the complete engine and replays
the isolated stablecheck/Breath socket baseline. Native integrated gameplay,
mount-death persistence and atomic movement are still pending.

## Linode private foundation verification — PASS (not gameplay acceptance)

The exact initial candidate `1e17f5c2ae5a84977c044647ad0f1df8bf9033f7` was validated on Linode. Exit code **0**. The single runner confirmed six inert native species and denied forged/dead/stabled owners and invalid receipts; real native-pointer binding/rollback; pure board, dismount, stable, retrieve, mounted Endurance and free-retreat transition planner; full 32-bit ELF32 engine linkage; existing native stablecheck, spent Breath logout/reconnect and socket REST/HUD regressions. Production PID/binary and accepted private ELF32 baseline were unchanged.

Private staged source: `/tmp/hd-army-game-round79adfleet-J8jHd6Io/src`.
Private results: `/root/hollowdeep-dev/round79ad-3fwvyedF`.
Neither path, log payload, source-world data nor credentials are published as files on GitHub.

**DO NOT PROMOTE:** The runner itself correctly reports `FULL GAMEPLAY BOARD/STABLE/RETRIEVE/DEATH/RESTORE/TRAVEL: NOT YET IMPLEMENTED`. These are not yet real player commands; no durable death receipt or authorized reconnect recreation; no atomic move+Endurance checkpoint. No production deployment.

Next implementation on this candidate branch: durable death event contract and exact-CAS native owner transition, all six species' isolated socket combat/logout/return, stable authority and movement. The same private ELF32 runner must be extended to verify these before any acceptance.
