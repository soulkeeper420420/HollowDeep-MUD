# HollowDeep — Round 74B production release gate

**Status: BLOCKED. ELF32 private build PASS; production eligibility NOT YET ESTABLISHED.**

The maintainer requested that Round 74B go live before starting Round 74C, **if it is successful**. Treat this as approval to prepare a conditional deployment, **not** evidence that a test-only binary is ready to replace the live MUD. Do not deploy, modify live files, restart the service, or announce changed gameplay until every hard gate below has been explicitly satisfied and reviewed.

## Current verified evidence (operator output, 2026-11-16)

- Verified private source-archive SHA: `ac3a6f59e2126ddd344d068976fb89a3501c4c5446ecce49108190a3ca93ca50`.
- Exact combined Round 74B GitHub baseline: `13623d21c04da67ad760b3bbf43c57fbd207fb9e` (following the Round 74B XP and five-bank development stages).
- Private workspace: `/root/hollowdeep-dev/round74b-SVnpPdcJ`.
- Reported native ELF32 build: `ROUND 74B COMBINED ELF32 BUILD: PASS`.
- Reported unit and native `train()` tests: 65-point creator, first-life half XP/gold (in test bridge), standard cost after rebirth, unknown-life standard cost, five-level XP bank, **exactly one level per train command**.
- Reported production deployment: `NONE`.
- This evidence covers the **compiled, private candidate plus focused tests**, not a complete isolated game-login/character-save/restart/legacy-player regression.

## Hard stops — all must pass before activation

| Gate | Status | Evidence / reason |
|---|---|---|
| ELF32 native candidate compiles | **PASS** | Operator-reported Round 74B combined build |
| Source integrity and private-only staging | **PASS in reported test** | SHA-pinned private patch scripts; no production paths touched |
| First-life status has authoritative durable save/load | **BLOCKED** | In `hd74_xp.c`, `hd74_verified_remorts()` returns `-1` without `HD74_LIFE_TEST_BRIDGE`; it explicitly disallows guessing. The 50% first-life discount is unavailable in real gameplay until a trustworthy atomic native save/read bridge exists |
| Existing characters have defined migration policy | **BLOCKED** | Existing saves have no verified remort count; never mark every legacy character as first-life by default. Level/XP changes require explicit, tested policy preserving their achievements, inventory and status |
| All XP/death/training paths agree | **NOT VERIFIED IN GAME** | `command7.c::train`, `command4.c::info`, `misc.c::exp_to_lev`, `creature.c::die`, `player.c::up_level`, `hollowdeep.c::training_progress`, and quests/pledges need native runtime tests; the tool-only `gstat.c` also contains legacy fixed-size level assumptions |
| Real private game creation, training and save/reconnect | **NOT RUN** | Need isolated MUD login, 65-point new character, exact 1-level train command, five separate trains with banked XP, money/XP checks, cap denial, disconnect/restart reload, no duplicate level/grant |
| Full isolated game/browser regressions | **NOT RUN** | Must rerun world/room/loot/admin/serialization regressions (including Round 59–73J) using the candidate, not only standalone helper tests |
| Production executable/data/website backup and one-step rollback | **NOT PREPARED** | Preflight file hashes, permissions, timestamps, immutable binary backup and tested rollback are required before any deployment |
| Approved release configuration | **NOT FINALIZED** | Level 60 is a proposed development configuration. Production life-count migration, first-life pricing policy, gold handling and max-5 bank behavior must be explicitly committed as release settings |
| Production restart and gameplay smoke | **NOT AUTHORIZED BY GATE** | Conditional deployment request acknowledged; actual restart must happen only after the above gates pass, with a validated rollback and service health checks |

## Critical native source details

- The **test-only** `Makefile` adds `-DHD74_PRIVATE_NATIVE`. Without that compile flag, the original production path still has the 54-point / 25-entry training rules. Copying just the helper objects or omitting the flag does not turn on the new rules; copying the whole private binary without full regressions is unsafe.
- `hd74_xp.c::hd74_verified_remorts()` currently has no persistent native bridge and returns `-1` outside an isolated test compile. Safe default: full price. Do not infer remort state from `level`, class, name, or an editable sidecar file.
- First-life pricing is **half the cumulative XP threshold, not XP subtraction**; gold costs **half the former normal gold price**. Bank capacity is **up to five future thresholds**, while each `train` invocation calls `up_level` exactly once.
- A level cap cannot be raised by editing only `mtype.h::MAXALVL`; the 25-entry `needed_exp[]` array and other readers have legacy index assumptions. `gstat.c` and other utility/GM flows need review as well.
- Round 73G/73J private player-save/treasure code and the Round 74A 512-byte progression snapshot are useful building blocks but **not proof that remort state is committed atomically with the live compressed player save**.

## Release implementation order (Round 74B stabilization, BEFORE Round 74C)

1. Implement a minimal **trusted remort/life-state record** in the same atomic compressed player save, with an explicit new-character state and fail-closed legacy migration. This is a release dependency, not full rebirth mechanics. Keep the existing player binary ABI intact.
2. Add native tests for initial save, repeated train and gold charges, player disconnect/reload, corrupted/truncated receipt, crash before/after save replacement, concurrent sessions, legacy saved character fallback, and the level-60 cap.
3. Run a disposable, real ELF32 game session with 65-point creation and five separate trainings, plus death penalties and quest XP; run the full older world/builder native/browser regression against that exact binary.
4. Review a minimal release diff and harden production configuration. Prepare backups **outside** the live source tree and a tested single-command rollback restoring previous binary/data with matching permissions.
5. After all gates PASS, deploy with an explicit before/after service PID + binary hash + saved-player integrity comparison; perform a fast game smoke, rollback immediately on failure, and then update the PHP website, GitHub release notes and Discord player guide. Do not publish a live-feature announcement until game behavior is verified.

## Where to edit — maintainer's source atlas

| File | Release responsibility |
|---|---|
| `command1.c` | Up-to-65 starting stats and character-creation prompts |
| `command7.c`, `hd74_xp.[ch]` | One-level `train`, life-based XP/gold fees and bank limits |
| `creature.c`, `command2.c`, `command8.c`, `command10.c` | Bounded combat/quest XP, death handling |
| `command4.c`, `hollowdeep.c`, `misc.c`, `player.c` | Consistent XP display, threshold, level-up and derived levels |
| `files2.c`, `hd_player_store.c`, `treasure_receipt.c`, `atomic_player_snapshot.c` | Crash-consistent native player save/load and durable remort state (not yet hooked) |
| `mstruct.h`, `mtype.h`, `mextern.h`, `global.c`, `Makefile` | ABI, legacy XP constants, command registration and production build flags |
| `/var/www/hollowdeep` | Separate PHP website; update only after verified game deployment |

## Current decision

**NO-GO for live deployment as of this review.** Continue Round 74B release stabilization; do **not** begin Round 74C or change production until a real-game PASS plus remort-save migration and rollback evidence exist. Publish this gate and changes to guides/changelog, but do not equate a GitHub push with a Linode deploy.

## Codex handoff — unpushed private release-candidate findings

The maintainer pasted interim **Codex-reported** results from a Linode/private
Round 74B stabilization attempt. **These code changes, test fixtures, and
complete final regression logs have not been uploaded or pushed to this branch.**
Therefore they are evidence to recover and revalidate, not a new verified release:

- Pinned source archive checksum matched.
- A revised ELF32 candidate reportedly passed character creation, save/restart
  and truncated-save refusal without replacing the existing save.
- A life count was placed in the existing receipt trailer, with original
  creature/inventory layout unchanged.
- Focused native tests reportedly passed five **separate** `train` commands,
  first-life gold discount, standard reborn/legacy cost, level-60 guard and
  save/restart preserving level, XP, gold, and exactly one wielded blade.
- Actual training boundary reportedly required **525 cumulative XP** on first
  life versus **1,050** for reborn/legacy fixtures.
- A private trap-death test initially showed the wrong XP curve; after a
  candidate fix the reported first-life level changed **4 → 3** and XP
  **5,175 → 3,882**.
- **New critical rollback blocker:** the old live predecessor reportedly
  reads a new-format save but *drops the life-count metadata on its next save*.
  Replacing the new binary with the old one is therefore **not a safe
  rollback**, even if the old binary can start. This must be fixed by a
  save-aware rollback build that preserves the trailer (and tested), or a
  comparably safe full player-data restoration/forward-compatibility protocol
  that guarantees no lost progress. Never silently use the old executable as
  a rollback target.
- The final regression was still running when the pasted progress ended;
  **do not mark it PASS without actual completion evidence**.

**Next actions:** recover the unpushed private Codex source patch and final
regression artifacts from its disposable workspace; review and pin exact
candidate checksums; audit that old saves still load and that the replacement
trailer is authenticated/atomic; close rollback compatibility and run a
crash/reconnect/old-binary-write test. Then execute the complete native
gameplay and Round 59–74B regressions, publish only safe tested source,
prepare a compatible rollback and explicit production cutover plan.
**Release status remains NO-GO. Production unchanged.**
