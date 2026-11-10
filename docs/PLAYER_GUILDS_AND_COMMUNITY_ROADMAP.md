# HollowDeep player clans/guilds and community — implementation roadmap

**Planning status:** design approved as priority on November 9, 2026, **not deployed**. The user chose this development order: player clans/guilds **inside the native MUD first**, community website second, secure MUD-to-website integration third, website features affecting game play fourth, and web GM/admin tools later.

## Existing systems that must be preserved

- Native Mordor group/party commands already exist. A player guild is **persistent social membership**, not a combat party.
- `gtalk` is an existing game command and must not be repurposed.
- `staffclan` / `hstaffclan` exists as a **staff-only** feature in `engine/extensions/hollowdeep_staff.c` with its own roles and chat. New player guilds must not grant or alter staff roles, badges, staff-only chat or management permissions.
- `pledge` and `rescind` are original registered commands; inspect their semantics before selecting command names or implementing new behavior.
- The native C game writes old character/world binary structures. Preserve binary layouts unless separately approved and proven migration-safe.
- PHP preview V6 and its launch candidate are not the live homepage. Never conflate website-only activities with real character progression.

## Phase 1: Native MUD guild MVP (first implementation)

Define `clan` and `guild` as aliases for the same **player guild** system, if neither conflicts with registered commands. Proposed commands, subject to engine audit:

| Command | Intended function |
| --- | --- |
| `clan` or `clan help` | Help and current membership |
| `clan list` | Public directory of guilds |
| `clan info <name>` | Public description and recruitment status |
| `clan create <name>` | Create guild, subject to name validation and rate limits |
| `clan invite <player>` | Invite a player; may require online target initially |
| `clan invites` | View pending invitations |
| `clan accept <name>` | Join one invited guild |
| `clan decline <name>` | Decline an invite |
| `clan roster` | Read members and ranks |
| `clan leave` | Leave a guild; leader must transfer leadership or disband |
| `clan promote <player>` / `clan demote <player>` | Leader-controlled officer permissions |
| `clan kick <player>` | Authorized removal of a member |
| `clan motd [text]` | View/edit member announcement (permissions enforced) |
| `clanchat <message>` | Guild-only online chat; enforce mutes and length limits |

Ranks for MVP: **Leader**, **Officer**, **Member**. One guild membership per character. No fee, vault, territory, character buffs, inventory transfers, or game gold in phase 1. Permission matrix is explicit. Account/character identity matching, rename handling, offline invites, and bans require inspection of actual native identity and save lifecycle.

Persistence recommendation: a separate versioned registry / per-character sidecar **only if** the audit confirms the engine can read and write it safely. Atomic writes, durable flush, bounds checks, escaping of names/text, backups, safe file ownership, and collision/duplicate protection are essential. Do not assume MariaDB is available to the 32-bit game process. Never insert fields into raw Mordor `creature` structures without a carefully tested binary compatibility plan.

Tests in an isolated disposable test environment: create, invite, accept, leave, kick, officer restrictions, leader succession, reconnect persistence, malformed input, two-player simultaneous changes, staff-only isolation, save integrity, and rollback. No live game execution or restarts until explicitly approved.

## Phase 2: Website community (PHP V7 preview)

- Discoverable guild directory with a recruitment flag, short lore, badges and public rosters **only when members consent**.
- Guild profile pages, officer-posted updates, and public recruitment applications with moderation.
- Community news and event calendar; guild challenges that do not change the game initially.
- Responsive navigation; report/block/moderation; privacy controls and basic abuse controls.
- Public directory may start from clearly labeled **sample/placeholder data** but must never imply an actual guild was created in the MUD.
- Keep website admin/database access separately permissioned.

## Phase 3: Secure MUD ↔ website bridge

- Export a minimal **read-only** versioned snapshot/API of player guilds, opt-in public roster data, and public server status.
- Cross-check data freshness. Hide invisible characters and private staff/game information.
- When web logins are needed, link accounts to characters using a time-limited, one-time in-game verification flow; never ask for or copy native Telnet passwords into PHP.
- Separate authentication, authorization, audit logs and CSRF protection for website write actions.
- Any website command affecting the MUD goes through a narrow authenticated request/approval protocol; never direct writes to raw world or player files.

## Phase 4: Website features with in-game consequences

- Guild quests, achievements, tournaments and guild halls, **only** after native server logic authoritatively validates them.
- Connected character pages and opt-in leaderboards.
- A secure authenticated TLS bridge for browser play, distinct from guild/website data sync.
- No claim that Tavern mini-games award XP, gold, or items unless an approved engine integration exists.

## Phase 5: Website administration / GM toolkit

- Builder drafts for rooms, NPCs, items and quests; staging validation; approval gates and rollback.
- Explicit role-based permission boundary separate from player guild roles and staffclan membership.
- No direct production binary world modifications from a public PHP request.

## Immediate next step

Run a **read-only, bounded source audit** on the actual Linode native C source to locate registered commands, `pledge`/`rescind` semantics, staff clan isolation, identity handling and persistence functions. Use the results to write an exact patch against a checksum-verified private copy. The public GitHub `engine/extensions` tree may not represent the currently deployed build; do not treat it as proof of live installation.

## Safe publishing

Documentation and reviewed source can go to GitHub. Never publish private player saves, server credentials, private config, guild private chat, IP lists or database dumps. Announce features as **planned/staging** until native tests and separately approved production release pass.

## Additional approved requirements: chat channels, charter merchant, and clan housing

### Distinct readable game chat channels

Introduce **`chat <message>`** for optional game-wide player conversation, separate from the existing privileged `broadcast` handler. Add **`clanchat <message>`** (optionally `gc`) restricted to members of the same player guild. Do not alias or repurpose existing `gtalk` (party), `say`, `tell`, `broadcast`, or `staffclan`. Proposed **default** palette, to be checked against the engine's actual ANSI palette:

| Channel | Proposed color | Distinct prefix | Audience |
| --- | --- | --- | --- |
| Ordinary `say` / gameplay | Original coloring, unchanged | Existing | Local room |
| Global `chat` | Bright cyan | `[Global]` | Opted-in online players |
| Guild `clanchat` | Bright magenta / violet | `[Guild: Name]` | Same-guild online members |
| `broadcast` | Existing color, unchanged | Existing | Existing broadcast audience |
| `staffclan` | Existing color, unchanged | Existing | Authorized staff only |

Render with existing engine color helpers when supported, respect client ANSI/color settings and never leak escape codes to no-color users. The channel **label must carry meaning without color**. Preserve mute/ignore rules; add per-channel opt-out for global chat, bounded printable message size and rate limits. Recheck sender identity and clan membership on every send. Prevent unauthorized raw ANSI injection and multiline spoofing. Global chat must **not** call the broadcast function: it needs its own permission, recipient filtering and output presentation.

### Guild charter shop

Build a normal in-game NPC vendor (tentatively **Charter Clerk**) in a **Guild Registry / Charter Hall** location. Sell a physical **Clan Deed / Charter** through the existing item/shop purchase mechanism; buying it spends real in-game gold using the engine's original secure purchase path. `clan create <name>` requires an owned, unspent valid deed, valid unique guild name, and character eligibility; create and deed consumption must succeed atomically or both fail. Avoid one-time 'consume then fail' loss, item duplication, deed resale exploits, and multiple guild ownership. The actual price, level requirements and whether the deed is tradeable are configurable decisions to confirm after examining original shop/item logic. **Do not fabricate a deployed merchant or item ID.**

### Physical clan housing areas

Reserve a **Guild District** attached to the normal world using supported exits and native room serialization. A newly created guild may claim one **Starter Hall** (entry, commons, meeting chamber) from a finite pool of allocated plots; access governed by guild membership and an explicit visitor policy. Create plot templates in disposable test rooms first. Save a mapping from stable guild ID to room/plot IDs outside raw fixed-layout room and character binaries if possible. Ensure permission checks happen server-side when entering locked private areas, not only on website buttons. No guild vault or shared item storage in first phase (high duplication and theft risk). Test how rooms load, save, and survive reboot before allowing dynamic allocation.

### Work sequence

1. Audit source for color/ANSI output, session/online-player enumeration, `broadcast`, `gtalk`, `staffclan`, and command-registration collisions.
2. Audit item templates, NPC merchant inventory, buy/purchase gold deductions, and room storage/exits.
3. Implement `chat` and `clanchat` in a checksum-verified isolated engine build with simulated two-user delivery tests.
4. Implement persisted player guilds, invitations, roles and charter-based founding; run restart/persistence/anti-duplication tests.
5. Create disposable Guild Registry shop and sample Starter Hall rooms; verify room binary integrity and access checks.
6. After verified native staging, implement the PHP V7 guild directory, recruiting, guild notices, event calendar and opt-in public guild pages, then integrate only via a restricted data bridge.

**Status:** requested and designed, **not installed**, no native files or production website changed. Do not conflate these features with the existing staff-only `staffclan`.

## Native source reconnaissance — November 9, 2026

The owner ran the read-only source scan on the Linode Mordor 3.00 tree and supplied the results. These are **source locations**, not installed features:

| Concern | Native source evidence | Implication |
| --- | --- | --- |
| Command dispatch | `global.c`: `buy` (258), `gtalk` (278), `broadcast` (281), `pledge` (294), `rescind` (295), `purchase` (296), `staffclan` (319) | Do not reuse existing verbs or handlers; new `chat`, `clan`, and `clanchat` require independent registrations |
| Existing group chat | `command10.c` around line 251 | Maintain current party semantics |
| Broadcast system | `io.c` around line 848 and `command4.c` around line 437 | New global chat must not invoke broadcast |
| ANSI colors | `ANSI(fd, CYAN)`, `ANSI(fd, MAGENTA)`, `ANSI(fd, WHITE)`, `PANSIC` used in multiple sources | Distinct colored chat appears feasible; inspect how color preference and resets work first |
| Shop implementation | `command7.c` `list` around 163 and `buy` around 205; `RSHOPP` in `mtype.h` | Reuse validated native shop inventory/gold path, don't guess deed item ID or price |
| Existing unrelated purchase | `command10.c` `purchase` at 674 | Inspect semantics; not presumed to be ordinary shop purchase |
| Binary world files | `files1.c` `write_rom` around 250, `read_rom` around 498; `mstruct.h` `exit_` | Guild district must be tested in disposable rooms, with validated exit serialization |
| Character persistence | `files2.c` around 539 and 603; `files1.c` `write_crt` around 118 and `read_crt` around 429 | Prefer external versioned guild registry instead of changing existing creature binary layout |
| Existing staff clan | `hollowdeep_staff.c` around 240 | Keep its role-controlled membership/chat isolated from player guilds |
| Room inventory | Read-only scan counted 4,043 `r[0-9]*` room files | Do not assume unallocated room IDs or modify production world files |

The audit reported: production source and world unchanged; no game-server restart; no player-file or website modifications. **No guild, global chat, charter deed or housing features have yet been implemented.**

**Next probe required:** bounded source context for `global.c` command table, `io.c` broadcast formatting/color rules, `command7.c` buy/list semantics, `hollowdeep_staff.c` muted-chat rules, `mstruct.h` command structure, and room/character allocation. Then build/test patches on private checksum-verified copies only.

## Experimental combined development build — November 9, 2026

A new **unverified staging-only** original C module is published under [`engine/experiments/guild-social-v1/`](../engine/experiments/guild-social-v1/README.md). It combines proposed cyan global chat, separate magenta guild chat, file-backed guild registration/invites/ranks, and a read-only staff-role hub. It is **not yet compiled against the user's current C source**, not live and not gameplay-tested. The staged compile must confirm native type compatibility before anything else.

For isolated smoke tests, `HD_GUILD_STAGING_FREE_CREATE` bypasses the still-unimplemented physical deed validation. **The test flag must never be used in a production deployment.** Without that flag, guild founding denies access, deliberately. The physical deed merchant and new guild housing rooms are **not implemented** by this experiment, and their integration remains mandatory before a public launch. The current `staffclan`, `hmoderate`, native `broadcast` and party `gtalk` are intentionally unchanged.

The publicly visible [Atlas MUD website](https://www.atlasmud.com/) documents clans, shops, homes, and builder/staff concepts, but does not establish a reusable compatible staff implementation or grant permission to copy proprietary code. The `staffhub` experiment is an original read-only menu over the existing HollowDeep staff roles, not an Atlas source port.

## Round 4 combined native build result (reported November 9, 2026)

The owner compiled the current experimental `guild-social-v1` module against a checksum-verified **private** copy of their live C source. The earlier command-table declaration and `plystruct` dependency errors were resolved by adding minimal `io.c` adapters to staging only. The 32-bit PIE executable `frp.new` was produced, and the six requested symbols (`hd_global_chat`, `hd_player_clan`, `hd_clan_chat`, `hd_staff_hub`, `hd_social_online_player`, `hd_social_color`) were found in compiled objects. Production source/executable, players, world, database and website were reported unchanged. The executable has **not been run** or tested in gameplay.

Next acceptance gate: run the candidate binary only inside an existing disposable rootfs with a private network namespace, private throwaway players and bounded automation. Verify real global/guild chat delivery, two-character invitations, ranks, mutes, restart/reconnect and persistence. `-DHD_GUILD_STAGING_FREE_CREATE=1` makes it unsuitable for live deployment even if those tests pass. Guild deeds and housing are still unimplemented.

## Round 5 — isolated two-character gameplay passed (reported November 9, 2026)

The owner ran the combined experimental 32-bit build in a disposable rootfs within a private network namespace. **18/18 automated gameplay checks passed, 0 failed**: two throwaway players online; global delivery, sender identity, independence from broadcast and opt-out; staging-only guild creation, directory, invitations, acceptance and roster; guild chat, promotion, officer rank, staff-hub denial for a regular player; character save, guild registry persistence and membership after game restart. Exit code 0.

The test used **deed-free guild creation**, enabled strictly with `HD_GUILD_STAGING_FREE_CREATE=1`; **this build must never be deployed to production**. The player's report verified production source, executable, world, database, website and original test players unchanged. The tests did not prove native deed purchase/consumption, guild house creation or access restrictions, optional muted-message behavior, high load resilience, or complete guild storage corruption recovery.

Next combined milestone: design and stage a native `RSHOPP` Guild Registry room and its `room_num+1` deed-stock room with a unique non-resellable deed object, plus multiple preallocated Starter Hall room templates. Prove all chosen IDs are free; use the native `write_rom` serializer. Replace test-only founding with physical deed ownership and an audited safe transaction design; verify refund/recovery behavior before any production release.

## Round 6 — private deed-gated compile and housing plan (reported November 9, 2026)

The owner verified 18/18 Round 5 isolated guild gameplay checks again, copied source to a new private Round 6 workspace, removed the `HD_GUILD_STAGING_FREE_CREATE` flag, and compiled the 32-bit deed-gated executable successfully. This **does not implement deed checking**: `clan create` currently fails closed without the staging flag. The merchant/item and physical rooms remain pending. Production source, executable, players, rooms, database, website and service state were reported untouched.

Round 6 proposed rooms 22000–22011, with registry shop at 22000 and stockroom at 22001 (stock is read by `RSHOPP` via room ID plus one). **These room numbers are planning placeholders only.** A critical incompatibility surfaced in the audit: the current `hbuild` command accepts room IDs **2–8999**; the 22000-series falls outside that builder range. Select and revalidate a genuinely unused in-range set or explicitly extend and test all relevant engine range checks before creating any room files. Do not consider the listed IDs reserved.

The public website can launch separately from this game feature. Any community/marketing page must describe clan deeds, guild housing, and in-game guild integration as **coming soon**, not live.

## Round 7 audit and Round 8 private-world generator (November 9, 2026)

The owner reported Round 7 source audit completed with production untouched; confirmed three public website URLs HTTP 200; revalidated the Round 6 deed-gated compile and 18/18 previous gameplay tests; selected **proposed IDs 6000–6011** (within the `hbuild` range). These are not reserved or deployed. Native shop logic uses `RSHOPP` in room N and persistent stock from room N+1. Purchases copy a template object to inventory and deduct its `value` from player gold. Native room and object files are fixed-layout binary, so manual text files are invalid.

Original staged C source is now published as [`guild_district_gen.c`](../engine/experiments/guild-social-v1/guild_district_gen.c), to be compiled on the actual server's 32-bit source headers and run **only inside a protected private Round 8 directory**. It creates twelve candidate native-layout room files, including the Guild Registry shop (6000), inaccessible stockroom (6001), Guild District Square (6002), three separate starter-hall clusters (6003–6011), and a prototype deed valued at 2500 gold. The sample halls are intentionally **not connected to the square**: there is still no guild-member authorization on movement. This source has not been compiled or game-loaded as of this roadmap update. Actual physical deed validation and atomic consumption remain unimplemented; `clan create` is still disabled without the test-only flag. The public server and public website must not be changed by this generator.

## Round 8 generated native-layout room files verified (reported November 9, 2026)

The operator compiled the original 32-bit [private Guild District generator](../engine/experiments/guild-social-v1/guild_district_gen.c) and ran it in a private staging workspace. It created twelve test-world files `r06000`–`r06011`, emitted and rechecked their checksums, and passed its own binary readback checks. The Guild Registry room and isolated stockroom include a prototype physical Clan Deed with 2,500-gold price. Three separate hall suites are present without exits from the public district. No production source, binary, rooms, character inventory, player gold, website or database were modified. **This only validates the generator's own serialization/readback, not native game loading, actual purchases, deed consumption, or guild-house access control.**

## Round 9 planned isolated native shop gameplay verification

Original test assets published under [`engine/experiments/guild-social-v1/`](../engine/experiments/guild-social-v1/README.md): `round9_test_funds.c` is guarded by `HD_ROUND9_ISOLATED_FUNDS`, limited to disposable `Hd*` characters in private entry room 1 and grants one-time 3,000 test gold; `round9_shop_runner.py` drives a private network-namespace MUD and tests shop listing, 2,500-gold purchase, zero-gold refusal, character inventory, remaining gold, the disabled clan-founding gate, disconnected housing, and native save/restart persistence. **These Round 9 tests have not yet run.**

The staging runner must use a private copy of the known V19 disposable rootfs, copied Round 6 deed-gated C source, the twelve new staging rooms and a copied, overwritten **private** entry room 1 for shop access. Do not add test funding code or modify any world room in the production tree. Approval for public gameplay deployment remains contingent on physical deed entitlement/consumption integration, recovery behavior, guild hall movement ACLs and a successful full isolated regression.

## Round 9 native Guild Registry playtest — 18 checks passed, reconnect unresolved

The owner ran the isolated 32-bit native shop playtest against the generated Round 8 district rooms in a disposable private network namespace. **18 assertions passed before the reconnect step**, including the Guild Registry loading; stockroom and 2,500-gold Clan Deed visibility; zero-gold purchase denial; one-time staging-only 3,000-gold award; successful native item purchase, inventory addition and exactly 500 gold remaining; `clan create` correctly failing closed despite carrying a deed; district square navigation and stockroom/housing being disconnected; and a successful `save` response. The test game restarted and opened its private listener, but the client then reported **`Reconnect password prompt missing`**. Consequently the overall Round 9 exit status was 2, **not a complete pass**. Physical deed persistence and 500-gold persistence after restart are **not yet verified**. The user's output confirmed production source, executable, rooms, characters, website and prior staging datasets unchanged.

The [round9_shop_runner.py](../engine/experiments/guild-social-v1/round9_shop_runner.py) has been updated to verify the native saved player file and to print sanitized login prompt context when reconnect fails, with extended bounded waits. Resume against a **new disposable rootfs** with the existing compiled test-only executable, not the original production game. Do not promote the test funding command or disconnected guild halls live. If the reconnect prompt continues to fail, inspect the diagnostic response and the saved player record rather than treating the 18 passes as sufficient.

## Round 9B — native deed shop and restart persistence passed (November 9, 2026)

The owner reran Round 9 with a newly disposable private MUD, the same staged 32-bit native shop executable, and better reconnect handling. **21/21 assertions passed; 0 failed; exit status 0.** Verified: native Registry room loads; 2,500-gold deed appears in the `RSHOPP` stock listing; insufficient-gold purchase is denied without adding the deed; one-time staging-only 3,000 gold grant; valid purchase adds a physical deed and leaves 500 gold; deed possession does *not* bypass the incomplete founding gate; District Square navigation works with no public exits to stockroom/halls; native player save created a 398-byte character file; after a private server restart, the physical deed and remaining 500 gold survived. Original production engine, rooms, characters, website, prior staging builds were reported unchanged and no production restart occurred.

**Next acceptance gate:** integrate purchased deed into an auditable, crash-safe guild charter activation transaction, demonstrate failure recovery without duplicate guilds, double spending or orphaned hall ownership; add three hall assignments and native movement access controls for nonmembers. No production promotion of `r9fund` or the test-only founding bypass, and no public connection to starter halls until membership checks pass.

## Round 10 V2 experimental source published — not yet compiled/gameplay tested

Following the successful 21/21 Round 9B native shop and restart test, new standalone [V2 guild-social C source](../engine/experiments/guild-social-v2/README.md) and a one-command staging orchestrator [`round10_stage.sh`](../engine/experiments/guild-social-v2/round10_stage.sh) were published.

The V2 experiment adds purchase-time **128-bit random deed serials**, an atomic `HDGUILD2` record that commits guild, founding leader, a first-available hall among 6003/6006/6009 and a **spent deed serial**, immediate native inventory item removal/save after commit, and idempotent cleanup of spent deeds surviving a crash. New room movement checks in the private native `go`, `sneak`, and central `add_ply_rom` code protect guild hall entry and redirect unauthorized entry to the public square; staff exception uses the existing role database. A private connected Guild District generator and 3-player runner test founding, invitations, access denial/permission, two guild hall claims, and persistence over restart.

**V2 implementation and its loader have not yet been compiled or game-tested; the next Round 10 command will do so in a disposable private rootfs and private network namespace.** There may be compiler or gameplay issues to repair. The `HD_ROUND9_ISOLATED_FUNDS` test-money command is included **only in a private build**; production must not receive the source or test-money flag.

Before a production rollout, explicitly test injected guild storage and character-save failures, simulated crashes at each commit phase, deed serial uniqueness/non-replay, all movement/teleport/trap/login bypass paths, staff and role fallback, migration, concurrency, house allocation limits, and rollback. This remains a feature prototype, not a security-certified production release.

## Round 10 first staging patch stopped on a legacy C function layout

The owner ran the pinned Round 10 script. The original production checksum passed, the prior private test candidate was verified, and the V2 experimental C sources downloaded. In the new private workspace, the staged merchant `command7.c` patch and the `go`/`sneak` destination checks applied. The patcher then stopped with **`STOP: Central native player-room insertion not found`**, before compilation or gameplay. This is a patch-matching issue: the patcher required a function-body opening brace immediately after `add_ply_rom(...)`, whereas the legacy engine may use K&R-style parameter declarations. It does **not** prove that guild entitlements or housing work.

The [corrected patcher](../engine/experiments/guild-social-v2/round10_apply.py) now accepts legacy declarations, and [`round10_finish_room_acl.py`](../engine/experiments/guild-social-v2/round10_finish_room_acl.py) can install **only** the missing central ACL into the existing private stage. [`round10_resume.sh`](../engine/experiments/guild-social-v2/round10_resume.sh) resumes the compile, room generation and isolated gameplay test without reapplying the successful merchant/go/sneak patches. All fixes are **staging-only, untested until the owner returns compile and gameplay output**, and production must remain unchanged.

## Round 10 central ACL repair retry — source assignment anchor (November 9, 2026)

The operator retried the private Round 10 staged build. Live source checks passed, and the previously patched merchant/`go`/`sneak` source files were verified. The patcher found `add_ply_rom` but stopped with **`Native player precondition not found after body brace`**, without compiling or running gameplay. This indicates its expected `ASSERTLOG(ply_ptr)` anchor was not present at the location sought; it does not imply production code changed.

The updated [central ACL patch helper](../engine/experiments/guild-social-v2/round10_finish_room_acl.py) now locates the native `ply_ptr->parent_rom = rom_ptr;` assignment and adjacent `rom_num` update inside `add_ply_rom`, rather than expecting a particular assertion statement. It refuses zero or multiple matches and prints limited source context on mismatch. The updated [one-command resume wrapper](../engine/experiments/guild-social-v2/round10_resume.sh) is pinned to this repair and continues only in the existing private workspace. **A successful compile or game playtest has not yet been reported for Round 10.**

## Round 10 staging compilation blocked by undefined native PSAVES flag

The owner ran the revised room ACL repair in the private Round 10 workspace. The player-room function layout was accepted, the central ACL was inserted into **staging only**, and 32-bit compilation began. Compilation stopped at two `PSAVES` references in `hollowdeep_social.c` (lines 416, 547), because the actual native HollowDeep `mtype.h` does not define this flag. No gameplay ran and production stayed unchanged.

The V2 experimental source now calls the native `save_ply(player)` directly, matching the native saving pattern; and uses Linux `getrandom` rather than expecting `/dev/urandom` inside the disposable chroot. A guarded [`round10_fix_native_save.py`](../engine/experiments/guild-social-v2/round10_fix_native_save.py) fixes only these two issues in the exact pre-existing staged directory and keeps a private source backup. The [`round10_savefix_resume.sh`](../engine/experiments/guild-social-v2/round10_savefix_resume.sh) resumes native compilation, staging room generation and three-player guild/deed/housing tests without reapplying the previously successful source patches.

**Compilation and gameplay remain UNVERIFIED for V2** pending the owner's next result. The code's `save_ply` error handling, interrupted dual-store redemption recovery and all possible hall movement paths still require fault-injection and bypass tests; production deployment remains forbidden.

## Round 10 native-save helper runtime bug corrected

The operator reran the private Round 10 native-save fix after the central ACL patch had successfully applied. It stopped in `round10_fix_native_save.py` with `AttributeError: '_io.TextIOWrapper' object has no attribute 'write_text'` while creating the backup. This is a Python helper mistake: an open file handle uses `.write()`, whereas `.write_text()` belongs to a `Path`. The exception occurred **before the experimental C source replacement**, although the exclusive-create operation may have left an **empty backup file**. No compilation or gameplay occurred on that retry; no production deployment was requested.

The [revised helper](../engine/experiments/guild-social-v2/round10_fix_native_save.py) now uses `write()` and fsync, and permits recovery only when that exact private backup is a zero-byte regular file owned by the current user. It aborts on existing nonempty or unsafe backups. [`round10_savefix_resume.sh`](../engine/experiments/guild-social-v2/round10_savefix_resume.sh) is pinned to the corrected helper and continues in the original private Round 10 workspace; reapplication of merchant/go/sneak/room-ACL patches is prohibited.

**Round 10 V2 compile and gameplay status: not yet verified.** Do not deploy deeds, hall ACLs, test-money commands or guild founding to production.
