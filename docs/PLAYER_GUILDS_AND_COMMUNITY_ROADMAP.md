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
