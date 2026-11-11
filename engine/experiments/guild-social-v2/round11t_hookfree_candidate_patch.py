#!/usr/bin/env python3
"""Round11T: patch ONLY a pinned Round11P candidate source COPY.

Add the privately proven worn-item-aware guild saves if the pinned candidate
does not already have them, then incorporate the Round11S tri-state directory
durability fix. No test hooks. Refuse unknown source versions.
"""
from pathlib import Path
import hashlib
import sys

BASE = Path("/root/hollowdeep-dev/guild-social-batch1")
OLD_SOCIAL_SHA = "4093b0fe93d4d915ca13e55ec56aa11fd3e84ed4c73fe110702647e0fb9f8ce9"
if len(sys.argv) != 2:
    raise SystemExit("Usage: round11t_hookfree_candidate_patch.py PRIVATE_STAGE")
stage = Path(sys.argv[1]).resolve(strict=True)
if stage.parent != BASE or not stage.name.startswith("round11t-hookfree-"):
    raise SystemExit("STOP: not a disposable Round11T candidate directory")
p = stage / "src/hollowdeep_social.c"
if p.is_symlink() or not p.is_file():
    raise SystemExit("STOP: candidate C source missing or symlinked")
source = p.read_bytes()
if hashlib.sha256(source).hexdigest() != OLD_SOCIAL_SHA:
    raise SystemExit("STOP: Round11P input social source hash mismatch")
s = source.decode("utf-8")

helper = r"""/*
 * Save an equipment-preserving native creature snapshot, as in savegame().
 * The temporary inventory tags reference the live equipped objects; these
 * objects remain owned by the original player and MUST NOT be freed here.
 */
static int hd_guild_save_equipped(creature *player)
{
    creature *copy;
    object *added[MAXWEAR];
    int i, count = 0, result;
    if (!player || !player->name[0]) return -1;
    copy = (creature *)malloc(sizeof(creature));
    if (!copy) return -1;
    *copy = *player;
    for (i = 0; i < MAXWEAR; i++) {
        if (copy->ready[i]) {
            added[count++] = copy->ready[i];
            add_obj_crt(copy->ready[i], copy);
            copy->ready[i] = 0;
        }
    }
    result = save_ply(copy->name, copy);
    for (i = 0; i < count; i++)
        del_obj_crt(added[i], copy);
    free(copy);
    return result;
}

"""
calls = s.count("save_ply(player->name, player)")
if calls == 2 and "static int hd_guild_save_equipped" not in s:
    anchor = "/* A saved but already-redeemed deed may survive a crash after the guild ledger"
    if s.count(anchor) != 1:
        raise SystemExit("STOP: equipment-save helper insertion anchor changed")
    s = s.replace(anchor, helper + anchor, 1)
    s = s.replace("save_ply(player->name, player)",
                  "hd_guild_save_equipped(player)")
elif calls == 0 and s.count("hd_guild_save_equipped(player)") == 2:
    pass
else:
    raise SystemExit("STOP: unexpected equipment-save call topology")
assert s.count("hd_guild_save_equipped(player)") == 2
assert s.count("static int hd_guild_save_equipped") == 1

changes = [
(
"""    if (ok) {
        dirfd = open(HOLLOWDEEP_DATA_DIR, O_RDONLY | O_DIRECTORY);
        if (dirfd >= 0) { fsync(dirfd); close(dirfd); }
    }
    return ok;
}""",
"""    if (ok) {
        /*
         * Rename already replaced the primary ledger. If directory syncing
         * fails, treat durability as UNKNOWN, never a confirmed abort.
         */
        dirfd = open(HOLLOWDEEP_DATA_DIR, O_RDONLY | O_DIRECTORY);
        if (dirfd < 0) return -1;
        if (fsync(dirfd) < 0) { close(dirfd); return -1; }
        if (close(dirfd) < 0) return -1;
    }
    return ok;
}"""
),
(
"""            if (!save_guilds(s)) {
                print(player->fd, "Guild storage failed; Clan Deed not consumed.\\n");
            } else {""",
"""            result = save_guilds(s);
            if (result == 0) {
                print(player->fd, "Guild storage failed before commit; Clan Deed not consumed.\\n");
            } else if (result < 0) {
                /* Uncertain ledger state: retain deed, do not acknowledge.
                 * The next clan command checks the redeemed serial first. */
                print(player->fd, "Guild ledger durability uncertain; Clan Deed retained pending reconciliation. Contact staff.\\n");
            } else {"""
),
(
"""        result = save_guilds(s);
        print(player->fd, result ? "Guild records updated.\\n" :
              "Guild storage failed; change was not committed.\\n");""",
"""        result = save_guilds(s);
        if (result > 0)
            print(player->fd, "Guild records updated.\\n");
        else if (result < 0)
            print(player->fd, "Guild ledger durability uncertain; verify records before further changes. Contact staff.\\n");
        else
            print(player->fd, "Guild storage failed before commit; change was not committed.\\n");"""
)]
for a,b in changes:
    if s.count(a) != 1:
        raise SystemExit("STOP: durability source anchor mismatch: " + a[:65])
for a,b in changes:
    s = s.replace(a,b,1)
if s.count("save_guilds(s)") != 2 or s.count("if (fsync(dirfd) < 0)") != 1:
    raise SystemExit("STOP: durability postcondition mismatch")
if "HD_ROUND9_ISOLATED_FUNDS" in s or "round11n-ledger-fail" in s or "r9fund fixture" in s:
    raise SystemExit("STOP: test-only hook found in release social C source")
p.write_text(s)
print("Round11T pinned hook-free candidate source: VERIFIED")
print("Equipment-aware guild save: 2 callers")
print("Directory fsync durability: tri-state")
print("Private source update: APPLIED")
print("Original candidate source and production: UNCHANGED")
