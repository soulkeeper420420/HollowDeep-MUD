#!/usr/bin/env python3
"""Fix the two incorrect native save_ply calls in a fresh private Round 10E
source copy only. Nothing in the original Round 10 / production trees changes.
"""
from pathlib import Path
import re
import sys

BASE = Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv) != 2:
    raise SystemExit("STOP: Expected private staged src path")
src = Path(sys.argv[1]).resolve(strict=True)
if (src.name != "src" or
        not src.parent.name.startswith("round10-persist-") or
        src.parent.parent != BASE):
    raise SystemExit("STOP: Refusing non-Round10E private source path")
if any(p.is_symlink() for p in (src, src / "hollowdeep_social.c",
                                src / "files2.c")):
    raise SystemExit("STOP: No symlink source files allowed")

social_path = src / "hollowdeep_social.c"
native_path = src / "files2.c"
social = social_path.read_text()
native = native_path.read_text()

signature = (
    r"\bint\s+save_ply\s*\(\s*str\s*,\s*ply_ptr\s*\)\s*"
    r"char\s*\*\s*str\s*;\s*creature\s*\*\s*ply_ptr\s*;"
)
if not re.search(signature, native):
    raise SystemExit("STOP: Native save_ply(str, creature *) signature not proven")

old_call = "save_ply(player);"
if social.count(old_call) != 2:
    raise SystemExit("STOP: Expected exactly two incorrect one-argument calls")
if social.count("extern void print(int fd, const char *format, ...);") != 1:
    raise SystemExit("STOP: Social source prototype insertion point is ambiguous")
if "extern int save_ply(" in social:
    raise SystemExit("STOP: save_ply prototype already present; review manually")
if "HDGUILD2" not in social or "hd_guild_mint_deed" not in social:
    raise SystemExit("STOP: Source is not the expected guild social V2")

social = social.replace(
    "extern void print(int fd, const char *format, ...);",
    "extern void print(int fd, const char *format, ...);\n"
    "extern int save_ply(char *str, creature *ply_ptr);",
    1
)

# The committed guild registry and spent token are authoritative; a failed
# character save is reported without undoing the spent token.
social = social.replace(
    "        save_ply(player);",
    '        if (save_ply(player->name, player) < 0)\n'
    '            print(player->fd, '
    '"Spent deed reconciled, but player save failed. Contact staff.\\n");',
    1
)
social = social.replace(
    "                save_ply(player);",
    '                if (save_ply(player->name, player) < 0)\n'
    '                    print(player->fd, '
    '"Guild registered; character save failed. Report to staff.\\n");',
    1
)
if social.count("save_ply(player->name, player)") != 2 or old_call in social:
    raise SystemExit("STOP: Native save correction was incomplete")

backup = src / "hollowdeep_social.c.before-twoarg-fix"
if backup.exists() or backup.is_symlink():
    raise SystemExit("STOP: Private source backup already exists")
backup.write_text(social_path.read_text())
backup.chmod(0o600)
social_path.write_text(social)

print("Native save_ply signature: VERIFIED (two arguments)")
print("Incorrect guild save calls: FIXED (2)")
print("Native files2.c: UNMODIFIED")
print("Private source backup: CREATED")
print("Production and original Round 10 source: UNTOUCHED")
