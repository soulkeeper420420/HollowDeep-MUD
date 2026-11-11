#!/usr/bin/env python3
"""Patch a fresh, private copy of the Round11K guild C source only.

Post-rename directory fsync failure is an uncertain commit; keep deed, never
acknowledge durable success. Do not use this script on live source.
"""
import sys
from pathlib import Path
ROOT = Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv) != 2:
    raise SystemExit("Usage: round11s_patch_ledger_durability.py PRIVATE_STAGE")
stage = Path(sys.argv[1]).resolve(strict=True)
if stage.parent != ROOT or not stage.name.startswith("round11s-durability-"):
    raise SystemExit("STOP: expected private Round11S stage")
p = stage / "src/hollowdeep_social.c"
if p.is_symlink() or not p.is_file():
    raise SystemExit("STOP: private source missing or symlinked")
s = p.read_text()
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
         * After rename the primary ledger may already contain the new
         * transaction. Failed directory durability is UNKNOWN, never a
         * confirmed abort or a confirmed durable commit.
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
                /* Deed retained. On next clan command reconcile spent serial
                 * from valid ledger; never blindly retry this founding. */
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
for old,new in changes:
    if s.count(old)!=1:
        raise SystemExit("STOP: Unexpected guild source anchor, no files changed: "+old[:48])
for old,new in changes:
    s=s.replace(old,new,1)
if s.count("save_guilds(s)")!=2 or s.count("if (fsync(dirfd) < 0)")!=1:
    raise SystemExit("STOP: postpatch checks failed")
if not (s.count("hd_guild_save_equipped(player)") == 2):
    raise SystemExit("STOP: This stage must retain the Round11K worn-item-safe guild saves")
p.write_text(s)
print("Round11S private tri-state ledger commit patch: 3 anchors, PASS")
print("Founding: success / precommit failure / post-rename uncertainty distinguished")
print("Other guild mutations: success / failure / uncertainty distinguished")
print("Worn-item safe character saves: PRESERVED")
print("No live source or existing private stages touched")
