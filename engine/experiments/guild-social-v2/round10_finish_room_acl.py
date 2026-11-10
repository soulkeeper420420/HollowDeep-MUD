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

# An ANSI prototype has a brace immediately; a K&R definition has one or
# more typed parameter declarations before the opening brace.
body_tail = code[match.end():match.end() + 850]
opening = re.search(r"\{", body_tail)
if not opening:
    raise SystemExit("STOP: Native function body brace not found")
body_open = match.end() + opening.end()

# Do not insert after an arbitrary brace in a distant function. There must
# be a native ASSERTLOG(ply_ptr); statement shortly after this body brace.
subsection = code[body_open:body_open + 1100]
precondition = re.search(r"\bASSERTLOG\s*\(\s*ply_ptr\s*\)\s*;", subsection)
if not precondition:
    raise SystemExit("STOP: Native player precondition not found after body brace")
absolute = body_open + precondition.end()
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
