#!/usr/bin/env python3
"""Finish only the missing Round 10 central player-room ACL patch.

The first Round 10 patcher already applied purchase/go/sneak changes and
aborted before writing room.c. This intentionally does not replay them.
Use solely on the named private Round 10 staged source copy.
"""
from pathlib import Path
import re
import sys

EXPECTED = "/root/hollowdeep-dev/guild-social-batch1/round10-PpNpn17k/src"
if len(sys.argv) != 2 or str(Path(sys.argv[1]).resolve()) != EXPECTED:
    raise SystemExit("STOP: Refusing any path other than the private Round 10 src directory")
source = Path(EXPECTED)
target = source / "room.c"
if not target.is_file() or target.is_symlink():
    raise SystemExit("STOP: Missing or symlinked private room.c")
code = target.read_text()
if "hd_guild_can_enter" in code:
    raise SystemExit("STOP: room.c already mentions the guild gate; review before retry")
if "void add_ply_rom" not in code:
    raise SystemExit("STOP: Native add_ply_rom declaration absent")

matches = list(re.finditer(
    r"(?m)^[ \t]*void[ \t]+add_ply_rom[ \t]*\([^(){};]*\)",
    code
))
if len(matches) != 1:
    raise SystemExit("STOP: Expected a single native add_ply_rom definition, found " +
                     str(len(matches)))
match = matches[0]

# Match the assignment that actually commits a player to a room.
# HollowDeep's native function body may have custom preamble code and need
# not contain ASSERTLOG at all. Stop if the exact assignment is ambiguous.
# Limit the scan to this function's first 8 KiB, and check the companion
# room-number update so we do not accidentally patch a later function.
body = code[match.end():match.end() + 8192]
assignments = list(re.finditer(
    r"(?m)^[ \\t]*ply_ptr->parent_rom[ \\t]*=[ \\t]*rom_ptr[ \\t]*;",
    body,
))
if len(assignments) != 1:
    print("=== NATIVE add_ply_rom CONTEXT FOR REVIEW ===")
    for line in code[match.start():match.start() + 2400].splitlines()[:50]:
        print(line)
    raise SystemExit("STOP: Expected one room assignment in add_ply_rom, found " +
                     str(len(assignments)))
assignment = assignments[0]
after_assignment = body[assignment.end():assignment.end() + 300]
if not re.search(
    r"ply_ptr->rom_num[ \\t]*=[ \\t]*rom_ptr->rom_num[ \\t]*;",
    after_assignment,
):
    raise SystemExit("STOP: Native player room-number update not found after parent assignment")
# Ensure the matched assignment is inside the function body.
prefix = body[:assignment.start()]
if "{" not in prefix:
    raise SystemExit("STOP: No function body before native room assignment")
absolute = match.end() + assignment.start()
patch = r"""

    /* Defense-in-depth for all player-room insertion paths, including
     * reconnect, teleport, trap moves and directions not handled by go.
     * Test-world halls are IDs 6003..6011 and safe square is 6002.
     */
    if (rom_ptr && rom_ptr->rom_num >= 6003 && rom_ptr->rom_num <= 6011 &&
        !hd_guild_can_enter(ply_ptr, rom_ptr->rom_num)) {
        room *safe_square = NULL;
        if (load_rom(6002, &safe_square) < 0 || !safe_square)
            merror("guild hall safe-square missing", FATAL);
        rom_ptr = safe_square;
    }
"""
code = code[:absolute] + patch + code[absolute:]
code = code[:match.start()] + (
    "extern int hd_guild_can_enter(creature *, int);\n"
) + code[match.start():]

assert code.count("extern int hd_guild_can_enter(creature *, int);") == 1
assert code.count("!hd_guild_can_enter(ply_ptr, rom_ptr->rom_num))") == 1
target.write_text(code)
print("Native player-room function layout: ACCEPTED")
print("Central room ACL: PATCHED IN PRIVATE STAGING")
print("Original live room.c: NOT MODIFIED")
