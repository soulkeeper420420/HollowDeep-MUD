# HollowDeep MUD Source Atlas — Mordor 3.00-derived native engine

**Verified against the 83-entry private C/header/Makefile archive supplied for
Round 74B.** This is a *where things live* guide, not an instruction to edit the
live server. The same source also contains HollowDeep-specific improvements
from previous rounds. When in doubt, search for the symbol across the project.

## First look: what controls what?

| Want to change... | Start here | Exact symbol / note |
|---|---|---|
| New player creation, race/class/stat choices | `command1.c` | `create_ply()`, cases 2–8; original max 54 total, 3–18 each |
| Parser and command dispatch | `command1.c`, `global.c` | `parse()`, `process_cmd()`, `cmdlist[]` |
| Training / gold cost / XP requirement | `command7.c` | `train()`; original 25-entry XP table |
| XP thresholds | `global.c`, `mtype.h`, `mextern.h` | `needed_exp[]`, `MAXALVL`, `needed_exp[25]` declaration |
| XP-derived level after death | `misc.c`, `creature.c` | `exp_to_lev()`, `die()` |
| Player level-up and HP/MP/ability gains | `player.c` | `up_level()`, `down_level()` |
| Monster death and kill-credit hook | `creature.c` | `die()`; existing treasure hook before monster branch |
| Combat actions and weapon damage | `combat.c`, `command5.c`, `creature.c` | Combat helper routines, `attack()`, monster combat |
| Spells, spell learning and scrolls | `magic1.c`, `magic2.c`–`magic8.c` | `cast()`, `study()`, spell implementations |
| Native class/spell/weapon restrictions | `magic*.c`, `command*.c`, `player.c` | Audit all per-command class checks, proficiency/realm logic |
| Training progress/help and player journal | `hollowdeep.c` | `hclass()`, `training_progress()`, `hprofile()`, `hquest()` |
| Inventory pickup/drop | `command2.c` | `get()`, `inventory()`, `drop()`, `get_all_rom()` |
| Equipment and wearable items | `command3.c`, `player.c` | `wear()`, `remove_obj()`, `equipment()`, `ready()`, `compute_ac()` |
| Shops, buying, selling, training | `command7.c` | `list()`, `buy()`, `sell()`, `value()`, `train()` |
| Player character save/load | `files2.c`, `hd_player_store.c` | `save_ply()`, `load_ply()`, atomic private save engine |
| Native binary serializer | `files1.c`, `files3.c` | room/object/creature serialization, in-memory records |
| Compressed player files | `compress.c`, `hd_player_store.c` | Legacy LZW and bounded private player-store codec |
| Claim receipt co-saved with character | `treasure_receipt.c`, `atomic_player_snapshot.c` | Durable claim IDs, safe replacement helper |
| Real object and monster structures | `mstruct.h`, `mtype.h` | `object`, `creature`, `room`, constants and flags |
| Room/monster/object runtime lifecycle | `room.c`, `creature.c`, `object.c` | Runtime room and entity operations |
| Wilderness and native map | `wilderness.c` | `map`, `mapradius`, `showmap`, movement wrappers |
| Treasure location and chest guards | `treasure_locate.c`, `treasure_guard.c` | Read-only `locate`, pointer-verified guardian/chest hooks |
| Builder commands | `hollowdeep_build.c`, `dm*.c` | Native builder and administrator commands |
| Staff permissions | `hollowdeep_staff.c`, `auth.c` | Staff gates and account/security helpers |
| Player help text | `hollowdeep_help.c`, `hollowdeep.c` | HollowDeep help additions and player guides |
| Native network/input/output | `io.c`, `hollowdeep_net.c` | Socket I/O and network integration |
| Tick/update loops | `update.c` | Periodic world/player updates and autosave triggers |
| How a candidate is compiled | `Makefile` | `frp.new`, 32-bit compile flags, `OBJECTS` |
| Live PHP site | `/var/www/hollowdeep` (separate) | Not contained in the uploaded native C source archive |

## More files by subsystem

**Player commands:** `command1.c` login/creation; `command2.c` look/movement,
get/drop; `command3.c` equipment; `command4.c` health/score/information/help,
follow/group and tracking; `command5.c` attack/who/search/hide/quit;
`command6.c` other character commands; `command7.c` shops/train/backstab/flee;
`command8.c` save and additional commands; `command9.c` and
`command10.c` additional game actions; `command11.c`, `command12.c` legacy
commands. Use `global.c`'s `cmdlist[]` to locate the precise handler.

**World/game runtime:** `global.c` shared data, XP table, registries;
`room.c` room state; `object.c` object state; `creature.c` monster life/death;
`player.c` player state and stats; `action.c` social/action behavior;
`special1.c` special command handling; `logic.c` game logic;
`update.c` scheduled runtime updates; `misc.c` helpers; `memory.c` memory
helpers; `hollowdeep.c` HollowDeep player features; `hollowdeep_ranges.c`,
`hollowdeep_bonus.c`, `hollowdeep_stance.c` specialized gameplay features.

**Storage and service:** `files1.c`, `files2.c`, `files3.c`, `compress.c`,
`hd_player_store.c`, `treasure_receipt.c`, `atomic_player_snapshot.c`;
`io.c` and `hollowdeep_net.c` network; `post.c` game mail;
`hollowdeep_build.c`, `hollowdeep_help.c`, `hollowdeep_staff.c` custom
systems; `auth.c` login/security.

**Tools/legacy utilities:** `gstat.c`, `psearch.c`, `plist.c`, `finger.c`,
`luck.c`, `strstr.c`, `main.c`. Some are standalone utilities, not objects in
`frp.new`; see `Makefile` before assuming they are part of the running MUD.

## Round 74: future integration sequence

1. **74A:** pure progression model validated in native ELF32. Nothing live.
2. **74B private hooks:** new-character stat parser and read-only `hprogress`
   command under a private-only compile switch. Original XP/training unchanged.
3. **Future training migration:** update *all* XP readers and writers together,
   include death/training/quest cases, preserve old characters, check 32-bit XP
   overflow, prove cap and level-up safety.
4. **Rebirth persistence:** trusted kill events, server-side deadline/owner,
   character class change and progression receipt in one player save, race and
   stat normalization, class spell/skill permission audits.
5. **Legacy equipment:** native object template and carry checks, saved
   character-bound ownership and restrictions. Never substitute `No Save` for
   a permanently retained item.
6. **Divine Favor and sacrifice:** item deletion + credit in one durable
   transaction; independent from Legacy Points.

## Known pitfalls from real source

- Increasing `MAXALVL` alone is unsafe. The 25 threshold entries are declared
  separately, and other code computes level losses and XP from that table.
- Original production `create_ply()` allows five stats from 3 to 18 totaling **up to 54**; the guarded Round 74B development build raises the ceiling to **65** without changing the per-stat bounds.
  it is not the Round 74A base-10-plus-20 system.
- `creature.level`, `creature.class`, and stats are signed one-byte fields;
  `experience` and `gold` are signed 32-bit `long` in the 32-bit binary.
- `gstat.c` uses `cls_lvl[11][26]` and indexes by `player->level - 1`.
  Level 60 would overrun that utility unless it is migrated too.
- `mstruct.h` does **not** have an include guard. Including it twice within
  one C translation unit redefines native structures. Forward-declare in
  new headers, and include it once in each `.c`.
- Existing `player.c` `title_ply()` caps title index at 7, and
  `compute_thaco()` caps level index at 19; check other level-sensitive
  calculations when upgrading the cap.
- The uploaded private game build contains a safer `hd_player_store`, but
  the Round 74A progression receipt is not yet appended to the same save.
- The compressed native player ABI must never be changed by inserting fields
  into `creature` or `object` without a compatible migration.
- A successful unit test or build is not authorization to restart production.

## Working safely and learning as the project advances

The assistant is responsible for source edits, patches, tests, GitHub review,
and documentation; the maintainer does **not** need to hand-edit files now.
Every milestone should update this atlas and explain the reason for each changed
source. Only run the combined private Linode validation after a candidate is
ready. Production stays untouched until a separately reviewed deployment.

For hands-on lessons later, see `docs/ROUND74B_EDITING_GUIDE.md` and
`docs/ROUND74B_PROGRESSION_CUSTOMIZATION_GUIDE.md`.
