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

## Compiler compatibility fix (Round 4)

The owner's native `mstruct.h` does not expose a usable `plystruct` typedef to this extension module. The corrected social module uses two minimal read/output adapters implemented in the **staging copy** of `io.c`, which already knows the native `Ply` representation:

```c
creature *hd_social_online_player(int fd)
{
    if (fd < 0 || fd >= Tablesize || !Ply[fd].ply ||
        Ply[fd].ply->fd != fd) return NULL;
    return Ply[fd].ply;
}

void hd_social_color(int fd, int color)
{
    if (!hd_social_online_player(fd)) return;
    ANSI(fd, color);
}
```

The source defines external declarations for these functions; the installer must add the adapters to the **copied staging `io.c`** before compiling. The stage-specific `HD_GUILD_STAGING_FREE_CREATE` flag remains unsafe for production.

## Round 8 private Guild District room generator

The original C file [`guild_district_gen.c`](./guild_district_gen.c) is a **disposable-world-only** serializer generator that builds 12 native-ABI room files `r06000` to `r06011`, including a flagged `RSHOPP` Guild Registry in room 6000 and its item stockroom 6001. The stockroom contains a **prototype** physical `Clan Deed` at **2500 gold** with inert marker `HdGuildDeedV1` in `key[2]`. It writes the original Mordor `write_rom` / `write_obj`-compatible 32-bit stream layout (matching the audited room/exit/object sizes). This is **a separate writer, not the engine's own `write_rom` function**; native loader round-trip and gameplay must be verified before adoption.

The three example starter halls are disconnected from the public square, because no server-side membership-gated movement is implemented yet. The stockroom has no public exit or entrance. The generator refuses any output path outside a `/root/hollowdeep-dev/guild-social-batch1/round8-*/test-world/rooms` workspace, refuses unsafe output directories or any preexisting target file, and validates its own output. It **must not be used for production world creation**.

**Important:** The `clan create` handler in the Round 6 deed-gated build currently denies all founding. The prototype item is not yet consumed by, or integrated with, the guild registry. Guild housing claims and restricted entry are not implemented, and the sample rooms are not connected to the production world. Passing a binary structure readback is not a native gameplay proof.

Next milestone: use a completely disposable game rootfs with the Round 6 deed-gated binary to verify native room loading, `list`, purchase value and inventory, then integrate server-validated deed ownership/consumption/rollback and house access checks. Preserve the 18/18 Round 5 guild/chat regression suite. Report all findings before a live deployment.
