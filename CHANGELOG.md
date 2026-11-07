# HollowDeep release notes

## 2026-11-07 — Step 99Z reusable audit health command verified

The VPS operator created root-only `/usr/local/bin/hd-audit-check` to parse private `statuses.json` and all nonempty `history.jsonl` entries, then report the audit event count. The mobile terminal returned `AUDIT HEALTH OK` and `4`. The check does not detect tampered-but-valid JSON, missing events, or transactional inconsistencies. Only documentation was published to GitHub; the private data remains on the VPS, with no native MUD changes.

## 2026-11-07 — Steps 99X–99Y backup compression and recovery-read verified

Host operator confirmed `gzip -t` returned `BACKUP OK`, then streamed the archived `investigation-reviews/statuses.json` through the JSON parser with `RECOVERY READ OK`. This provides evidence the archive's compressed stream and status JSON can be read without modifying live files. It does **not** verify a complete restoration, consistency of a backup taken during a simultaneous write, or crash-safe audit transactionality. Private backup data stays on the VPS and was not uploaded.

## 2026-11-07 — Steps 99U–99W private audit backup checks

On the VPS, a root-only backup directory was created and an approximately 550-byte compressed `investigation-reviews` archive retained privately. The statuses JSON parsed successfully and four recorded audit events were valid JSON. `tar -tzf` confirmed the archive's visible directory listing includes `history.jsonl`, `statuses.json` and `statuses.lock`. This does not establish a full restore test or transactional durability. Private backup contents were **not** uploaded to GitHub or Discord. No game files or services were touched.

## 2026-11-07 — Step 99S audit write-order improvement (VPS)

The operator installed a PHP endpoint patch moving the audit-history append to after the atomic status-file rename, with a timestamped backup and passing PHP lint. A later mobile terminal check showed four entries in `history.jsonl` (earlier verification showed two), consistent with further audit recording. The exact source of each additional entry was not independently inspected. This reduces the risk of recording a successful audit event when the status rename fails, **but is not a fully transactional update**: an audit append failure may now leave a saved status without history. The PHP change occurred on the VPS; this commit documents it only and does not deploy code or restart the MUD.

## 2026-11-07 — Step 99R mobile audit history cards verified

The VPS operator added `history-mobile.css` to the admin Audit History page after creating a backup, and `php -l` passed. The authenticated mobile screenshot confirms stacked audit cards instead of a sideways-scrolling table. Fields include timestamp, administrator, finding, previous/new status and whether notes changed. Two events are visible: `awaiting` → `follow_up`, and a later `follow_up` → `follow_up` update with notes changed. This is a VPS website change documented in GitHub, not a GitHub-driven deployment. Audit write ordering remains a separate reliability improvement; the MUD server was not modified.

## 2026-11-07 — Step 99Q mobile investigation cards verified

On the live VPS, the operator added `queue-mobile.css` and included it in `room-investigation-queue.php`, after backing up the queue. PHP lint passed. An authenticated phone screenshot verified vertical investigation cards showing priority, category, room source/destination, detail, Inspect and History links, persisted Room 1508 notes, Review status and Save without horizontal table scrolling. This was a VPS website change; GitHub documentation publication does not itself deploy PHP/CSS, and no live Mordor MUD files or services were changed. Desktop regression testing and stronger audit transactionality remain future work.

## 2026-11-07 — VPS admin investigation notes and audit history verified on mobile

Host operator verified the separate PHP investigation console on `hollowdeepmud.com`: a status Save returned HTTP 303; `statuses.json` grew from 3 to 186 bytes and `history.jsonl` from 0 to 231 bytes. The authenticated Audit History viewer displayed the event; the Admin Dashboard navigation link was added and verified in the mobile browser. The Investigation Notes field was visible, and the Room 1508 note remained after Save and refresh. Shared progress showed 609 awaiting and one Follow-up Required finding.

These results verify **basic live save, audit and mobile-navigation behavior**, not transactional audit reliability. The audit append still precedes the atomic status replacement, creating a possible phantom event if the subsequent write fails. The mobile investigation queue was subsequently improved; see the Step 99Q entry above. This changelog records the existing VPS work, not a deployment of PHP from this GitHub repository; no game source, world binaries or MUD services were changed.

## 2026-11-07 — Initial VPS investigation-console documentation (historical status)

Published [VPS investigation-console guide](docs/VPS_INVESTIGATION_CONSOLE.md) describing the separate Ubuntu/PHP administrator room diagnostics, report snapshot inputs, review workflow, safe checks and publication boundaries. The reported room analysis includes 4,030 snapshot rooms and 9,551 exits. This documentation release does not change or restart the native game or VPS website.

**Historical note:** At this stage, the first Save checks had not produced persistent data. Later live testing on the same date confirmed saves and audit records; see the verified entry above. Discord webhook posting was subsequently confirmed by the operator; automatic GitHub release announcements still require the repository secret and separate workflow verification.

## 2026-11-06 — One-file updater

Added `hollowdeep-update.py`: upload one file and run `python3 /root/hollowdeep-update.py`. It embeds the existing reviewed installers, verifies their hashes and chooses the matching completed installation or its own known rollback. Unknown/unfinished records are refused. Existing updater safeguards and source payloads are unchanged. Twelve launcher tests cover version selection, bundle integrity, malformed records, no-install verification and child error handling. This does not establish live installation.

## 2026-11-06 — Command discovery, staff tools and release planning

Status: tested source and installation packages. **Installation of this release on the live Linode is not verified.** The last host-confirmed completed installation is the earlier spells update. The failed builder attempt stopped in a disposable test before activation.

### Player commands and help

- `spells` / `spell` list learned spells alphabetically with current/maximum mana.
- `skills` lists existing native skills allowed by class and level; `skills all` describes the full 18-skill catalog. Cooldowns, equipment and target rules still apply.
- `help` now builds a paginated alphabetical index from all 315 registered command names/aliases. Use `help commands [page]`, `help all [page]`, `help social [page]` and `help search <text> [page]`.
- Every registered command has a help page. Exact aliases and high-position social commands work; duplicate registrations appear once. `help search` explains the native search action; `help spells` keeps the original spell catalog.
- `dmcommands` / `dmhelp` lists role and builder tools. `dmcommands native [page]` lists permitted original caretaker/DM commands. A common native-class check also protects previously unguarded `*memory` dispatch; existing target/named-operator restrictions remain.

### Staff roles, world building and events

- Implementor is a separate stored role with Moderator-level authority. Existing role IDs are preserved; permission comparisons use ranks.
- `[OWNER]`, `[ADMIN]`, `[MOD]` and `[IMPLEMENTOR]` identify staff in `who`, `whois`, rosters and announcements. Original visibility rules are retained.
- The **HollowDeep Staff** clan provides role-derived membership, a roster and private online chat through `staffclan` / `hstaffclan`. Mutes apply; revocation removes access immediately. Builder-only characters and ordinary players are excluded.
- Owners assign nonoverlapping builder room ranges, 50 rooms by default. `hbuild` edits permitted rooms; `hdm` applies scoped movement/restoration with hierarchy and combat checks. Range assignment does not imply the selected rooms are empty.
- Timed monster XP/gold events allow Moderator/Implementor **1–5× for 1–60 minutes**, Admin **1–10× for 1–1,440 minutes**, Owner **1–20× for 1–1,440 minutes**. Events persist through restart, expire by time, do not stack, and preserve creator-rank stop restrictions. Trades, quests and existing coins are excluded.
- Reward calculations and coin pickup clamp signed 32-bit overflow at their new event integration points. This is not a claim that every legacy progression path has been redesigned.

### Reliability and packaging

- Fixed the original five-word command parser overflow exposed by `hbuild name Hall of the Seven Lanterns`. Bounds and termination checks preserve full command text for extension handlers while retaining compiler fortification.
- Guarded updater variants target the completed spells, parser-repair and original legacy installations separately. They verify predecessor metadata/source/binary, test a disposable candidate before activation, preserve world/saves/settings, and retain recovery records.
- Refreshed the downloadable workshop kit and allowed its original negative-numbered push/press help page through the path validator.
- Published matching player/staff/building/server guides, a full command reference, source-derived XP research, three proposed level 1–50 curves, Atlas research and future quest-area/release designs.

### Validation

Passed: full fortified ELF32 multiplayer runtime and save/reload tests; 1,869 help/skills/staff-clan permission assertions; all 315 registered names covered by help files; 263 building/DM/event checks; 80 staff checks; 70 stance checks; 144 extension checks; 1,052 normalization assertions; 23 original input integration assertions; 14 parser regression cases; native monster reward/20×/overflow/expiry checks; 7 preparation tests; 17 runtime-client tests.

Deployment checks passed: 23 native updater, 11 console packaging, 7 public activation, 15 bridge installer and 12 historical recovery tests. Client/bridge tests passed (73), TypeScript passed, and the production website build passed. Each packaged updater's embedded engine source was checked against the reviewed release tree. GitHub CI status is separate and should be checked on the published commit.

### Planned, not activated

No XP curve, training price, level cap, new class/spell, remort or gear-gated quest area changes are activated. [Future releases](docs/FUTURE_RELEASES.md) explains dependencies; [level research](docs/LEVELS_AND_EXPERIENCE.md) documents the level-25 XP cliff, monk progression issue and stat-array bounds that need work first. Website publishing and live native installation remain separate operations.

Use the [server guide](docs/SERVER_GUIDE.md) to select the matching updater. The superseded failing builder package must not be used for this release.
