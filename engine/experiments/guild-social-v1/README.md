# Experimental Guild & Social Build — Round 1

**NOT TESTED, NOT INSTALLED, NOT PRODUCTION-READY.**

This package contains original C source for the user's HollowDeep Mordor 3.00 development tree. It does **not** contain or copy code from Atlas MUD; its `staffhub` command is an Atlas-inspired menu that reads HollowDeep's existing roles. No permissions are granted by this menu.

## Features implemented in this experimental source

- `chat <message>` global chat (cyan, `[Global]`, not native `broadcast`)
- `chat on`, `chat off`, `chat status` (session/process-local preference)
- `clan` and `guild` aliases with help/list/info/create/invite/invites/accept/decline/roster/promote/demote/transfer/kick/leave
- `clanchat <message>` magenta chat restricted to current guild members
- `staffhub` read-only Atlas-inspired menu gated by existing HollowDeep staff roles
- New versioned, separate guild registry `hollowdeep-data/player-guilds.v1`, with owned-directory and file checks and atomic file replacement
- Existing `gtalk`, `broadcast`, `staffclan` and binary player/room structure layouts are intentionally unchanged

## CRITICAL test-only founding rule

For the staging build only, compile with `-DHD_GUILD_STAGING_FREE_CREATE=1`; it allows **deed-free test clan founding** so invite/roster/chat logic can be tested. **Never install this test build in the production game.** When compiled without the flag, `clan create` fails closed until a valid physical Clan Deed check, atomic deed consumption and inventory/registry transaction design are implemented.

## Still required before any live promotion

- Real Clan Deed item in original Mordor shop inventory, Guild Registry shop room, item ID verification, purchase/consumption rollback, fraud and duplication tests.
- Real guild housing rooms with safe room-ID allocation, exit integration, private-access server checks and restart/persistence tests.
- Simulated two-player tests, malformed registry tests, mute/ignore tests, save compatibility, isolated 32-bit game playtest and rollback.
- The current file-based registry is designed for a **single** running MUD process. Parallel processes sharing it are not supported.
- Runtime guild records must be stored in private files on the isolated test server, not in the public website or GitHub.
- Future moderation and staff extensions must retain existing authenticated role, audit and staffclan boundaries.

## Installation

Do not copy directly into the live source tree. Use the guided checksum-verified private staging script from the associated HollowDeep development conversation to copy actual Linode source into a private staging directory, add the module to its Makefile/command table, and compile **without executing the game**.

## Public reference

[Atlas MUD](https://www.atlasmud.com/) documents public guild, shop, home, staff and builder concepts. These are inspiration, not verified or licensed reusable implementation files.
