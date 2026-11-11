#!/usr/bin/env python3
"""Round 11K: private-only equipment-preserving guild saves.

Follows the engine's native savegame() clone/unready/restore approach, while
returning save_ply() errors to guild callers. Never patches live source.
"""
from pathlib import Path
import sys

ROOT=Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv)!=2:
    raise SystemExit("STOP: Supply fresh Round11K stage path")
work=Path(sys.argv[1]).resolve(strict=True)
if work.parent!=ROOT or not work.name.startswith("round11-equip-"):
    raise SystemExit("STOP: Not a fresh Round11K private workspace")
path=work/"src/hollowdeep_social.c"
native=work/"src/command8.c"
if any(not p.is_file() or p.is_symlink() for p in (path,native)):
    raise SystemExit("STOP: Required staged C sources missing or symlinked")

c=path.read_text()
command=native.read_text()
if c.count("save_ply(player->name, player)")!=2:
    raise SystemExit("STOP: Expected exactly 2 direct guild save calls")
for exact in (
    "int savegame(ply_ptr, cmnd)",
    "dum_ptr = (creature *)malloc(sizeof(creature));",
    "add_obj_crt(dum_ptr->ready[i], dum_ptr);",
    "del_obj_crt(obj[i], dum_ptr);",
):
    if exact not in command:
        raise SystemExit("STOP: Native equipment-saving contract changed: "+exact)
if "static int hd_guild_save_equipped" in c:
    raise SystemExit("STOP: Guild equipment helper already exists")
anchor="/* A saved but already-redeemed deed may survive a crash after the guild ledger"
if c.count(anchor)!=1:
    raise SystemExit("STOP: Unexpected guild reconciliation function")
helper=r"""/*
 * Private Round11K: preserve the native ready[] equipment-save semantics.
 * Native savegame clones the creature, temporarily adds each equipped item
 * to the clone's inventory, clears its ready slots, then saves and cleans up.
 * This helper does the same while propagating the real save_ply status.
 *
 * The cloned object references are never freed here (the original player
 * still owns those items); only the temporary clone inventory tags are
 * removed, exactly as in native command8.c:savegame.
 */
static int hd_guild_save_equipped(creature *player)
{
    creature *copy;
    object *added[MAXWEAR];
    int i, num_added = 0, result;
    if (!player || !player->name[0])
        return(-1);
    copy = (creature *)malloc(sizeof(creature));
    if (!copy)
        return(-1);
    *copy = *player;
    for (i=0; i<MAXWEAR; i++) {
        if (copy->ready[i]) {
            added[num_added++] = copy->ready[i];
            add_obj_crt(copy->ready[i], copy);
            copy->ready[i] = 0;
        }
    }
    result = save_ply(copy->name, copy);
    for (i=0; i<num_added; i++)
        del_obj_crt(added[i], copy);
    free(copy);
    return(result);
}

"""
c=c.replace(anchor,helper+anchor,1)
c=c.replace("save_ply(player->name, player)",
            "hd_guild_save_equipped(player)")
assert c.count("hd_guild_save_equipped(player)") == 2
assert c.count("static int hd_guild_save_equipped") == 1
assert c.count("save_ply(copy->name, copy)") == 1
backup=path.with_name("hollowdeep_social.c.before-round11k")
if backup.exists() or backup.is_symlink():
    raise SystemExit("STOP: Private source backup exists")
backup.write_text(path.read_text())
backup.chmod(0o600)
path.write_text(c)
print("Private guild save paths normalized for equipped items: 2 of 2")
print("Native files2.c loader and atomic saver: UNCHANGED")
print("Original native command8.c savegame: UNCHANGED")
print("Production and prior test characters/binaries: NOT ACCESSED")
