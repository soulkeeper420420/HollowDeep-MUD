#!/usr/bin/env python3
"""Round 10 private-stage patcher. Refuses unknown anchors and unsafe flags.

Run against a NEW checksum-verified COPY of HollowDeep source only.
The resulting tree is intentionally NON-PRODUCTION until tested.
"""
from pathlib import Path
import re
import sys

src = Path(sys.argv[1]).resolve()
marker = "/root/hollowdeep-dev/guild-social-batch1/round10-"
if not str(src).startswith(marker) or src.name != "src":
    raise SystemExit("STOP: Source is not a private Round10 src copy")
for required in ("command7.c", "command6.c", "command10.c", "room.c",
                 "global.c", "Makefile", "hollowdeep_social.c"):
    if not (src / required).is_file():
        raise SystemExit("STOP: Missing required private engine file: " + required)
if "HD_GUILD_STAGING_FREE_CREATE=1" in (src / "Makefile").read_text():
    raise SystemExit("STOP: deed-free test founding must be OFF")

def one(text, old, new, label):
    occurrences = text.count(old)
    if occurrences != 1:
        raise SystemExit(f"STOP: {label}: expected one source anchor, got {occurrences}")
    return text.replace(old, new, 1)

# Native buy logic: mint unique serial only for copied deeds from the
# official Guild Registry stockroom. Do so BEFORE taking buyer's gold.
p = src / "command7.c"
code = p.read_text()
start = re.search(r"\bint\s+buy\s*\(", code)
end = re.search(r"\bint\s+sell\s*\(", code)
if not start or not end or start.start() >= end.start():
    raise SystemExit("STOP: Native buy/sell definitions not found")
segment = code[start.start():end.start()]
segment = one(
    segment, "*obj_ptr2 = *obj_ptr;",
    """*obj_ptr2 = *obj_ptr;
    if ((rom_ptr->rom_num == 6000
#ifdef HD_ROUND9_ISOLATED_FUNDS
        || rom_ptr->rom_num == 1
#endif
        ) && !strcmp(obj_ptr->key[2], "HdGuildDeedV1") &&
        !hd_guild_mint_deed(obj_ptr2)) {
        free(obj_ptr2);
        print(fd, "Guild Registry cannot issue a deed right now. No gold taken.\\n");
        return 0;
    }""", "native item copy"
)
segment = "extern int hd_guild_mint_deed(object *);\n" + segment
code = code[:start.start()] + segment + code[end.start():]
p.write_text(code)
print("Native purchase: minted deed before gold deduction")

# Ordinary go and sneak movement: refuse unauthorized hall destination.
for filename, func in (("command6.c", "go"), ("command10.c", "sneak")):
    p = src / filename
    code = p.read_text()
    match = re.search(r"\bint\s+" + func + r"\s*\(", code)
    if not match:
        raise SystemExit("STOP: Native function not found: " + func)
    after = code[match.start():]
    hit = re.search(r"(?m)^(\s*)n\s*=\s*count_vis_ply\(rom_ptr\)\s*;", after)
    if not hit:
        raise SystemExit("STOP: Destination occupancy anchor not found: " + func)
    insertion = (
        '\n' + hit.group(1) +
        'if (!hd_guild_can_enter(ply_ptr, rom_ptr->rom_num)) return 0;\n'
    )
    after = after[:hit.start()] + insertion + after[hit.start():]
    code = code[:match.start()] + after
    code = code[:match.start()] + "extern int hd_guild_can_enter(creature *, int);\n" + code[match.start():]
    p.write_text(code)
    print("Native movement gate: " + func)

# Final central guard covers other callers of add_ply_rom (login, summon,
# generic teleport, flee and traps): unauthorized hall destination is
# replaced by the safe public square BEFORE changing parent room pointers.
p = src / "room.c"
code = p.read_text()
match = re.search(r"\bvoid\s+add_ply_rom\s*\([^)]*\)\s*\{", code)
if not match:
    raise SystemExit("STOP: Central native player-room insertion not found")
tail = code[match.end():]
anchor = re.search(r"(\s*ASSERTLOG\s*\(\s*ply_ptr\s*\)\s*;)", tail)
if not anchor:
    raise SystemExit("STOP: Native room precondition not found")
insertion = """
    /* Last-resort authorization for EVERY route, including login/teleport.
     * This code only runs if destination is a protected hall.
     */
    if (rom_ptr && rom_ptr->rom_num >= 6003 && rom_ptr->rom_num <= 6011 &&
        !hd_guild_can_enter(ply_ptr, rom_ptr->rom_num)) {
        room *safe_square = NULL;
        if (load_rom(6002, &safe_square) < 0 || !safe_square)
            merror("guild hall safe-square missing", FATAL);
        rom_ptr = safe_square;
    }
"""
tail = tail[:anchor.end()] + insertion + tail[anchor.end():]
code = code[:match.end()] + tail
code = code[:match.start()] + "extern int hd_guild_can_enter(creature *, int);\n" + code[match.start():]
p.write_text(code)
print("Central native room ACL: protected hall entry redirected to public square")

print("Round 10 experimental source patch: APPLIED TO PRIVATE COPY")
