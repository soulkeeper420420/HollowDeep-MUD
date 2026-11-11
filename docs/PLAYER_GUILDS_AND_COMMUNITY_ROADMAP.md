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

## Round 10 private three-player gameplay: 32 assertions passed; character reload BLOCKED

The owner reported successful V2 native 32-bit compile after the staging-only `PSAVES`/randomness fix, successful creation of 12 connected test-world rooms, and **32 PASS, 0 FAIL** across live isolated gameplay: no-deed founding denied; a 2,500-gold purchased/minted physical deed formed Nightfall and was consumed; 500 gold remained; the atomic `HDGUILD2` registry contained a spent token and Hall A assignment; unauthorized outsider denied Hall A; leader and invited member admitted; a second purchased deed formed Dawnwatch and claimed Hall B; cross-guild entry denied. Three test characters reported their `save` commands completed, and the private MUD restarted. **The first returning character was NOT loaded**: after sending the name, the login server prompted `Hdnlbxiba? Did I get that right?` rather than `Please enter password:`. In Mordor's native `command1.c` `login` routine, the confirmation prompt is emitted specifically when `load_ply(str, &ply_ptr) < 0`: it is the **new-character creation flow**, not a normal returning-character confirmation.

Consequently, post-restart character inventory/gold, membership and guild registry checks were not completed; Round 10 **exit status 2**. **Do not auto-answer 'yes'** on that prompt, because doing so could create a new character and falsely satisfy weaker tests. First audit disposable `rootfs/player` filenames, sizes, ownership, contents safety and server logs, and isolate whether `save_ply` wrote files that `load_ply` cannot read. Audit the native C player-save and player-load routines before changing game code. Staging source, executable, world and website remained distinct from production; the operator reported production unchanged and no live restart.

V2 still requires additional crash/failure injection and nonstandard movement bypass tests before production deployment. Do not interpret the 32 passing assertions as complete persistence or recovery coverage.

## Round 10D audit: actual root cause of zero-byte native player save identified

The operator's read-only Round 10D inspection confirmed the disposable player `Hdnlbxiba` was **0 bytes**, while `Hdnlbxiba~` was 302 bytes and two other test character files were 303 and 302 bytes. The operator created a verified private copy of the four player files at `/root/hollowdeep-round10-save-audit-5S0eKHAN`, and did not alter the originals. The two guilds, three members, and two spent charter serials remained in the `HDGUILD2` registry.

Most importantly, native `files2.c` defines the original K&R function `int save_ply(str, ply_ptr)` with **two arguments**: `char *str` and `creature *ply_ptr`. The experimental V2 social code had mistakenly used **`save_ply(player)`** (one argument) at two sites: after guild-charter redemption and during spent-deed cleanup. This is undefined behavior and a strong explanation of the invalid primary save; the underlying compressed-save implementation also renames the previous file to `~` before writing and lacks adequate short-write/error checks before deleting its backup. **The exact cause must still be confirmed with a new successful test.**

Corrected [`hollowdeep_social.c`](../engine/experiments/guild-social-v2/hollowdeep_social.c) explicitly declares `save_ply(char *, creature *)`, calls `save_ply(player->name, player)` and reports a failed native save without rolling back the already-committed unique deed redemption. [`round10e_apply_twoarg.py`](../engine/experiments/guild-social-v2/round10e_apply_twoarg.py) applies only those changes to a new private source copy. [`round10_runner.py`](../engine/experiments/guild-social-v2/round10_runner.py) now checks all three player files are nonempty before and after stopping the private game, and refuses any new-character confirmation during reconnect. [`round10e_persistence_replay.sh`](../engine/experiments/guild-social-v2/round10e_persistence_replay.sh) performs a fresh 32-bit build and isolated multi-user test against a **new empty disposable world**, preserving the failed Run 10 files and the live world.

**Round 10E has not yet run.** Do not treat the preexisting 32 gameplay assertions as persistence proof, and do not ship this experiment to production. Even if Round 10E succeeds, additional compressed-save atomicity hardening, injected failures, unique-token replay verification and movement bypass tests are prerequisites for deployment.

## Round 10E isolated persistence test — shutdown-time save corruption confirmed

In the freshly created private world `/root/hollowdeep-dev/guild-social-batch1/round10-persist-PE4PRFyX`, the corrected two-argument guild `save_ply(name, player)` calls compiled successfully. The guild founding, purchased physical deeds, two hall assignments, invitations, and member-only gates passed again. The runner confirmed all **three native character files were nonempty immediately before stopping the test MUD**. After its controlled `server_stop()`, character `Hddaknzma` became **0 bytes**, while `Hddaknzmb` and `Hddaknzmc` remained nonempty. Test results: **37 passes, 1 failure, exit status 2**; restart/login was deliberately **not attempted**, so no false character recreation. Prior failed-run player files and original stage remained unchanged, and no production changes or service restart were reported.

This establishes a **shutdown-time save corruption** separate from the earlier guild-specific call-site bug. Native `files2.c` uses K&R `save_ply(char *name, creature *player)`, rotates a primary file to `~`, and in `#ifdef COMPRESS` does not check `write()` outcome before removing its backup. Other call sites—including global shutdown, `save_all_ply`, `savegame`, disconnect, and signal paths—must now be inspected for one-argument misuse and interrupted writes. **Do not restore from `~` or edit the live save routine yet.** Audit the staged C definitions/callers and the new disposable file sizes first, then patch **only a fresh private copy** and test shutdown plus fault recovery.

The deployment gate remains CLOSED. Experimental test-money code must not be enabled on the live MUD, and the production world, characters, guild rooms and site remain unchanged.

## Round 10F: all native direct save calls correct; test harness SIGTERM race identified

The owner performed the read-only Round10F audit and confirmed disposable `Hddaknzma` became a zero-byte primary with a 308-byte `Hddaknzma~` recovery copy, while the other two players had intact 302/308-byte primary files. The audit found that **all staged direct calls to native `save_ply(str, creature *)` use two arguments**, including both new guild paths, native account / disconnect paths, and the `savegame` wrapper. Native `io.c` explicitly installs **`signal(SIGTERM, SIG_DFL)`**. `io.c` calls `save_ply` during player disconnect. Meanwhile, the **Round10E test runner closed all three client sockets and immediately sent SIGTERM to the private server**, without waiting for the MUD to finish asynchronous disconnect-save operations. This is a plausible and testable runner-induced save interruption; it does not yet prove all native save code is safe.

A new [`round10g_graceful_runner.py`](../engine/experiments/guild-social-v2/round10g_graceful_runner.py) half-closes each disposable test socket, waits for the server to close all three connections, verifies that each native character file was **replaced with a new inode, is nonempty, and has no `~` backup remaining**, waits for that condition to remain stable for two seconds, and only then sends SIGTERM and checks the files again. It refuses to restart or recreate players if any save fails. It additionally verifies the other two characters can log back in and retain their correct guild status, assigned hall, deed and gold. The [`round10g_graceful_replay.sh`](../engine/experiments/guild-social-v2/round10g_graceful_replay.sh) reuses the already compiled, corrected Round10E native executable in a **fresh disposable private chroot and network namespace**, so no rebuild or modification of production, previous test data, or native serialization is required.

**Round10G has not yet been executed.** Even a passing graceful test is not sufficient to claim crash-safe native saves: the current `files2.c` compressed `save_ply` branch still needs a separate guarded test of partial writes, failed compression, power loss and an atomic temp-file/fsync/rename migration before the production rollout gate can open.

## Round 10G — 50/50 isolated native guild, housing and restart persistence PASS

The operator successfully ran [`round10g_graceful_replay.sh`](../engine/experiments/guild-social-v2/round10g_graceful_replay.sh) in **new private workspace** `/root/hollowdeep-dev/guild-social-batch1/round10-graceful-NylI8Od3`, retaining the corrected Round10E 32-bit binary and using the new graceful disconnect / native save barrier. **50 assertions passed, zero failed, exit status 0.** Full private log: `/root/hollowdeep-dev/guild-social-batch1/round10-graceful-NylI8Od3/results.log`.

Native gameplay confirmed no-deed guild creation is denied, the 2,500-gold physical minted Clan Deed buys and redeems exactly once, and 500 gold remains. Nightfall and Dawnwatch were founded with distinct spent serials and distinct private halls (6003 and 6006). Outsiders cannot enter assigned halls; invited members can, and cross-guild entry is denied. Three native characters saved successfully before disconnect. The runner then waited for all three native disconnect acknowledgments, verified each new save inode was **nonempty**, had **no `~` backup**, and remained stable. Three example byte sizes after disconnect: 302, 297, 299. After isolated `SIGTERM` and private restart all three files remained nonempty, and all three player reloads confirmed the guilds, member roster, halls, remaining 500 gold, consumed deeds, and spent serials persisted. The private MUD listener restarted and the complete playtest exited with zero errors.

**Root cause of earlier observed zero-byte saves:** a strong indication of the old test-runner race, which sent SIGTERM immediately after closing client connections while native disconnect saves could be in progress. The passing graceful test demonstrates the race no longer occurs on this path, but does **not** prove full crash consistency or that native compressed `save_ply` is safe after arbitrary interruption.

The operator's final integrity checks confirmed production C source and rooms unchanged, previous failed-run characters/compiled engine unchanged, no production MUD restart, and public website unchanged. All V2 source and test-only gold funding remain **PRIVATE STAGING**. **Production deployment gate remains CLOSED** pending a separate crash-safe compressed-save implementation and fault injection, guild ledger failure / spent-token replay tests, and additional hall ACL bypass and privilege checks.

## Round 11A read-only native save audit — verified hazards and Round 11B prerequisites

The owner supplied the Round 11A audit result from the checksum-verified private `round10-persist-PE4PRFyX/src`. `files2.c:516` confirms native two-parameter `save_ply`; in the `COMPRESS` build, it first renames the player primary file to `~`, creates a replacement, and calls `write(fd, b_buf, size)`, **without checking this write's result, fsync/close, or whether compression output fits in `malloc(n)`** where `n` is the original uncompressed serialized byte count. Then it deletes the backup and returns success. An interrupted/short compressed write can destroy the primary while the function reports success. `load_ply` uses a 50,000-byte compressed input buffer and a 100,000-byte uncompressed buffer, with limited validation of short reads and decompression.

The audit also shows `command8.c:657` `savegame` creates a temporary creature duplicate, moves worn items into its inventory before serialization, and still prints `Player saved.` even if `save_ply` reports failure. The V2 charter guild code directly invokes `save_ply`, bypassing that equipment normalization; this needs equipment persistence regression tests.

**No production files were changed, no server was started, and this audit did not itself create a safe save patch.** New [Round 11B save-hardening design](../engine/experiments/guild-social-v2/ROUND11B_ATOMIC_SAVE_DESIGN.md) requires a proven custom compressor output-size bound and serializer contract, then a private atomic temp/write/fsync/rename candidate plus crash/failure injection. The corresponding [read-only compressor-contract source audit](../engine/experiments/guild-social-v2/round11b_compressor_contract_audit.sh) gathers those exact functions. Production deployment remains CLOSED, even though Round10G passed 50/50 graceful gameplay checks.

## Round 11B compressor contract — unbounded 12-bit LZW output confirmed

The owner's checksum-verified Round11B read-only audit exposed the complete `compress.c` implementation. Its 12-bit LZW compressor has a 4096-entry dictionary; `writec` and `flushout` unconditionally write through `*outbuf` without capacity checks. A poorly compressible input can produce approximately 1.5× its input size, while native `save_ply` allocates compressed output with `malloc(n)` (uncompressed input size). The decoder shares the same unchecked output writer, and the native `files3.c` character serializer recursively writes to a 100,000-byte allocation without receiving a capacity argument. Therefore **both compressed writes and decompressed reads can overflow their buffers**, independent of any disk atomicity improvements.

The audit covered `write_crt_to_mem` starting at `files3.c:70`, but omitted the recursive `write_obj_to_mem` function preceding it and the remainder of `read_crt_from_mem`. The next narrow [Round 11C read-only recursive serializer audit](../engine/experiments/guild-social-v2/round11c_recursive_serializer_audit.sh) retrieves those exact source sections before implementation of bounded serialization, bounded LZW, atomic save/rename, and failure injection. No crash-safe implementation has been approved or run. Production remains unchanged and the deployment gate stays **CLOSED**.

## Round 11C recursive serialization audit and Round 11D staging candidate

The owner supplied the checksum-verified Round 11C native source audit. The original `files3.c` writer emits `sizeof(creature)`, a native `int` direct-inventory count, and recursively `sizeof(object)` plus direct-child `int` count for each nested object. Neither writer has a capacity argument or recursion/cycle guard. The reader performs the reverse based on untrusted counts, recursively allocating objects, without an input-size boundary. This confirms **bounded serialization and bounded deserialization must be treated as separate requirements**; an atomic file rename cannot fix the native memory-overrun vulnerabilities.

A new **save-only, private** [Round11D patcher](../engine/experiments/guild-social-v2/round11d_stage_atomic_save.py) has been committed. It verifies the original K&R `save_ply` and LZW source signatures, then applies changes only to a newly created `round11-atomic-*/src` source copy: (1) a recursive native-format serializer with checked byte capacity, object count and recursion depth; (2) a guarded LZW output writer and `hd11_compress_bounded` API (cap 49,999 bytes, native loader limit); and (3) same-directory private temp writes, short write/EINTR retry, fsync, checked close, atomic rename and parent-directory fsync while retaining the prior primary until commit. It makes no production edits; the original `load_ply` remains unchanged and therefore **is not yet safe against malformed input or arbitrary decompression output**.

A [Round11D private smoke runner](../engine/experiments/guild-social-v2/round11d_private_atomic_smoke.sh) will rebuild the 32-bit experimental engine, install the 12 verified guild rooms into a fresh disposable game root, and replay the known 50 Guild/Deed/Hall/graceful restart assertions in an isolated PID/mount/net namespace, with live source checksum checks before and after. It preserves previous Round 10 test data and binaries. **This new code has been published but has not compiled or run on the owner's server.** Do not claim the candidate is crash-safe or release-ready. Round11E still requires bounded native player load, equipped-item inventory regression, hostile/malformed input tests, simulated write/fsync/rename failures, SIGKILL injection at save checkpoints, and gold/charter sidecar transaction recovery. The production gate remains CLOSED.

## Round 11D smoke initial result — compiled; runner path guard prevented gameplay

The owner executed the Round 11D candidate smoke wrapper in private staging `/root/hollowdeep-dev/guild-social-batch1/round11-atomic-pGqKMYDt`. The bounded recursive native-format save serializer, output-checked LZW compressor, and private temporary-file/fsync/rename player saver **patched and compiled** into a 32-bit staged MUD. Its 12-room disposable world was created successfully. Gameplay did **not** start: the reused Round10G Python test runner rejected the Round11D workspace at `tested()` because its guard required a path beginning with `round10-`. The initial smoke report: **0 passed, 0 failed, gameplay exit 2**. The operator's integrity checks confirmed production engine/rooms untouched, previous 50/50 private baseline preserved, no production server restart, no website change. This is a **test-runner path guard**, not evidence of an engine compile or gameplay error.

[`round11d_resume_runner.py`](../engine/experiments/guild-social-v2/round11d_resume_runner.py) adjusts the runner's single workspace guard to accept **only** the verified existing Round11D disposable `round11-atomic-pGqKMYDt/rootfs`; it retains the existing graceful disconnect barrier, 3-character reload, and guild/hall/deed assertions. [`round11d_resume_existing_stage.sh`](../engine/experiments/guild-social-v2/round11d_resume_existing_stage.sh) verifies the existing compiled candidate, existing private rooms, still-empty disposable characters and ledger, production source hash and prior test integrity; then downloads only that runner and resumes isolated gameplay. It does **not** reapply the save patch or rebuild the candidate.

**Round 11D resumed gameplay is not yet run or verified.** No live deployment; bounded native `load_ply`, native equip normalization, atomicity fault injection, filesystem recovery and guild ledger failure tests remain release blockers even if normal gameplay eventually passes.

## Round 11D native atomic-save compatibility — 50 PASS / 0 FAIL (private only)

The owner successfully resumed the already-compiled Round11D candidate using the corrected, workspace-pinned runner. **Native 32-bit bounded-save binary compiled and ran:** 50 assertions passed, 0 failed, exit status 0. Exact preserved private workspace: `/root/hollowdeep-dev/guild-social-batch1/round11-atomic-pGqKMYDt`. Test report: `/root/hollowdeep-dev/guild-social-batch1/round11-atomic-pGqKMYDt/results-resume.log`.

The `HD11` save implementation's bounded recursive writer, output-bounded LZW and same-directory temp/write/fsync/rename path were exercised by normal guild founding, physical deed purchase and redemption, two distinct hall assignments, invitations and member ACL checks, and three native character saves. During graceful disconnect, all three saves were rewritten as stable nonempty files with no `~` backups. The disposable engine restarted; Nightfall and Dawnwatch membership/rosters/halls, 500 remaining gold for both founders, both consumed deeds and their spent-serial ledger persisted. No stale `.hd11-*` temp files remained. Final checksum verification confirmed the original production C source/rooms, previous private executables/players and website were not modified; no production service restart or deployment occurred.

**Acceptance scope: a passing normal compatibility smoke test only.** Explicitly **NOT TESTED**: forced SIGKILL mid-save, short/error/ENOSPC writes and failed fsync/rename, crash-consistent backup and recovery, malformed or adversarial save inputs, bounded decompression/player loading, equipped item persistence, and guild ledger failure recovery. Some normal saves can succeed without proving the unbounded original `load_ply` is safe. Do not promote `HD11` to production until the remaining safety gates pass and a separately approved rollback is available.

## Round 11E ready — isolated fault injection against the exact atomic save helper

The 50/50 **Round11D** native guild and atomic-save compatibility test passed, but that does not establish failure atomicity. The next stage is a dedicated, **unexecuted** [Round11E fault harness](../engine/experiments/guild-social-v2/round11e_atomic_fault_harness.py) and [one-command private launcher](../engine/experiments/guild-social-v2/round11e_private_fault_test.sh). It extracts the **actual** compiled candidate's `hd11_name_valid` and `hd11_atomic_player_write` functions from `round11-atomic-pGqKMYDt/src/files2.c`, compiles them into a standalone 32-bit test binary, and uses a test-only 32-bit `LD_PRELOAD` library to simulate interrupted, short and failed syscalls on synthetic payloads in **new disposable directories only**. Cases cover normal replacement and new-save creation, repeated one-byte writes, `EINTR`, `ENOSPC`, `EIO`, failed file fsync and rename, directory fsync reporting, SIGKILL during write/before rename/after rename, path traversal and existing symlink refusal. For every case it checks whether the complete previous or committed new payload remains and whether the expected temporary file remains; a killed process may leave an orphaned temporary file, which must not affect the valid primary.

The harness never starts the native MUD, reads no character-save contents or credentials, does not modify the engine source, preserves the existing private 50/50 test and live production source by checksum checks. **It has not run yet.** Results validate the extracted save-commit helper under injected failures but **cannot certify** whole-engine serialization, player loading, filesystem power-loss behavior, backup recovery, equipped inventory, or guild ledger consistency. The production rollout gate stays CLOSED until those later tests pass.

## Round 11E — 14/14 isolated atomic-save fault simulations PASS

The owner ran `round11e_private_fault_test.sh` successfully. The 32-bit extracted native `hd11_atomic_player_write` helper and the **test-only** syscall interception library compiled, and **all 14 checks passed with 0 failures**, exit status 0. The synthetic payload test covered clean existing and new-character saves, repeated one-byte/short writes, EINTR retry, ENOSPC and EIO, failed file fsync, failed rename, forced SIGKILL during writes and immediately before/after rename, failed parent-directory fsync reporting, existing symlink rejection, and path traversal refusal. Under the injected conditions, checks confirmed either the prior complete payload or the fully committed new payload; orphaned temporary files were permitted only for pre-rename kills, and never replaced the valid primary.

The disposable fault workspace is `/root/hollowdeep-dev/guild-social-batch1/round11-fault-_8nlt8cx`, and the launcher report is `/root/hollowdeep-round11e-launch-hYJY10vD/results.log`. The checksum recheck confirmed the original production C source unchanged and the private 50/50 Round11D native engine and player files untouched. The live service and website were not modified or restarted.

This is **unit-level fault injection of the extracted atomic commit helper**, not a live-guild transaction fault test, power-loss durability proof or a bound on the legacy LZW deserializer. Release gate remains CLOSED: next is strict/length-bounded native character loading, corrupt-save tests without accidental account recreation, equipped-item persistence and the character/guild-ledger interleaving tests. No production deployment authorized.

## Round 11F bounded native player loader — private candidate prepared, NOT TESTED

After the operator's Round11E **14/14** synthetic syscall-fault PASS, the next stage is the native loader. The [guarded Round11F patcher](../engine/experiments/guild-social-v2/round11f_stage_bounded_loader.py) verifies the **already-tested Round11D** staged `files2.c`, `compress.c` and `command1.c` source signatures, then updates only a new `round11-load-*/src` copy. It introduces `hd11_uncompress_bounded` with an output byte limit, a required valid initial LZW dictionary code, bounded dictionary/stack walks, and a capacity-checked raw player+recursive object **preflight** before calling the original native-format object allocator. It preserves the character file format, and rejects files that are unsafe, oversized, truncated, have excessive object nesting/counts, or have a header name mismatch. A separate native-login guard refuses to treat an existing but unreadable save file as an unregistered account, preventing accidental overwrite via the name-confirmation/new-character path.

The [Round11F gameplay script](../engine/experiments/guild-social-v2/round11f_private_bounded_load_smoke.sh) creates a **new private source and empty disposable world**, applies the candidate, builds the 32-bit MUD and runs a new [Round11F runner](../engine/experiments/guild-social-v2/round11f_bounded_runner.py) inside a private mount/net/PID namespace. The runner adds four corrupt-file safety assertions (two malformed-file cases each must refuse account creation and leave the bad file unchanged), deletes only its disposable malicious test files, then replays the prior **50 native guild, deed, hall, character-save and graceful-restart tests**. Expected scope is **54 checks**. The script verifies the live source hash and existing Round11D character/binary integrity before/after. **No Round11F compilation or test has yet occurred on the owner's Linode**.

**Limitations:** this is candidate hardening, not a proof of safe arbitrary parser inputs or decompressor fuzz-hardening. The legacy underlying `read_crt_from_mem` allocation remains; preflight checks aim to constrain it, but malicious LZW streams, all equipment/ready-object persistence, and guild ledger crash interleavings still need separate adversarial tests. Round11F may fail compilation or checks and must be debugged privately, without deploying. Original production source, rooms, characters, service and website remain outside the test.

## Round 11F initial native loader test — 43 PASS, 2 FAIL, restart blocked

The owner ran the new private Round11F bounded-decompress/recursive-native-player-load candidate in `/root/hollowdeep-dev/guild-social-batch1/round11-load-UuprVvCZ`. The 32-bit engine **compiled**, the private namespace started, and ordinary guild founding, deed redemption, Nightfall/Dawnwatch hall access, invitations, and pre-shutdown saves passed. Two intentionally corrupt disposable player files (`bad 12-bit LZW header` and `50,000-byte oversize save`) **remained byte-for-byte unchanged**, but their login attempts did not produce the expected `Existing character data cannot be loaded` message; those two refusal-message checks **failed**. The runner continued and three normal player files (300, 293, 297 bytes) completed disconnect saves and survived SIGTERM. On restarting the isolated native listener, it **exited before opening port**, so no post-restart reload/roster/gold/deed/ledger checks completed. Result: **43 PASS, 2 FAIL, exit status 2**.

The failure-message issue may be buffered I/O: the candidate's `command1.c` corrupt-account branch calls `print()` followed immediately by `disconnect(fd)` without a buffer flush; the exact response was empty in the runner log. This is a hypothesis, not yet tested. The second-start process exit is unexplained and must be diagnosed independently using the intact private workspace, including server process return code, source logs and startup/bind behavior. **Do not treat the initial test as a verified character-load success or deploy the new loader.**

The owner verified live C source/rooms unchanged, previous Round11D 50/50 test source and characters unchanged, no production service restart or website change. The existing failed-run private source, binary, 3 player files, and guild registry should be preserved for diagnostics. Next step: read-only inspection and, if needed, boot-only probing from **new private copies in isolated net/PID/mount namespaces** before an additional code patch or runner replay.

### Round 11G next: isolated boot-only diagnosis, no stage modification

A guarded [Round 11G boot-only diagnostic script](../engine/experiments/guild-social-v2/round11g_boot_diagnostics.sh) now checks the exact failed Round11F private workspace `round11-load-UuprVvCZ`, snapshots hashes of its existing three disposable character files and compiled 32-bit engine, and creates two **brand-new** private chroot copies. Each copy uses the **identical Round11F binary** and runs in its own mount/PID/network namespace: one starts with a known-empty disposable character/ledger baseline, and one contains copies of the Round11F saved character and guild ledger. It checks only whether TCP 4041 becomes ready or the native process exits, reports the exit code and the size of private server stdout, and stores stdout privately without printing potential credentials or character data. Both instances are stopped; no player creation, save modification of the original stage, source patch or live service action is attempted. This is intended to distinguish failed-run data startup from a process/lifecycle issue. **The script has not yet run.**

The two missing corrupt-account refusal responses are consistent with the staged `command1.c` guard using buffered `print()` followed immediately by `disconnect(fd)`, but this is not confirmed and must be corrected only in a further fresh private copy after diagnosis. Do not alter the successfully passing Round11D or Round11E baselines. Production release gate stays CLOSED.

### Faster private test workflow from Round 11G onward

Operator requested fewer manual terminal cycles. For the current Round11F failure, start with the already-published [Round11G boot diagnostics](../engine/experiments/guild-social-v2/round11g_boot_diagnostics.sh) **once**. It compares clean disposable boot against a copied-state boot in separate private namespaces while preserving the original three characters and source. Do not rerun the failed Round11F installer.

After its two boot results are known, bundle fixes into **one fresh private, checksum-guarded build-and-retest script**: account-rejection output flush (if confirmed), native startup fix (only if evidenced), malformed-file assertions, the 50 normal guild/restart checks, and source/character integrity verification. Every batch should print a concise pass/fail summary plus the report path, preserve failed artifacts, fail closed, and avoid requiring an extra shell paste between each small step. Do not blindly alter the native loader based on speculation. The production gate stays CLOSED until the full loader, equipment, and guild-ledger tests pass.
