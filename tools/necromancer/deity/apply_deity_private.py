#!/usr/bin/env python3
"""Apply private DM deity mapping to an already isolated Necromancer source.

Runs all anchored input and checksum checks before any write; never accepts
production source directories. Does not change the native player ABI.
"""
from pathlib import Path
from hashlib import sha256
import shutil
import sys

FILES = ("global.c", "hollowdeep_staff.c", "hollowdeep_help.c", "Makefile")
# Approved native source of previous Necromancer Raise Skeleton test; base
# Mordor Hashes allowed only as an entire profile so no mixed code is pasted.
PROFILES = (
    {
      "global.c": "11ddff86fff5ee56556a640a2e5571b0e9d84cf9fb8b35d069e57a127445f09a",
      "hollowdeep_staff.c": "c7d9ee86e6dee450ecc67bbaf191fc0c750dd69a4fbcaa77547b465dabc085c6",
      "hollowdeep_help.c": "69b4bd05ef8ead0912d7ea8924dc4f76523fef8526d5a12c1b9fd22fd5f2a033",
      "Makefile": "1be8c19e2b2658efed36218d5e0a55d7cad9d3b1bb9640a230641ef7d7915404"
    },
)

# Both integrated hashes were independently reconstructed from the original
# first-skill sources and published Round 74B + identity patch order.
PROFILES += ({**PROFILES[0],
    "global.c": "529df2a11ee11dc4e691e7e9ede051b13f608aecd8bbc8b48d2e54852a7410f3",
    "Makefile": "cc586e180179c353444891e0adba223e697b2570890f846ad9e0448daa2072d5",
},)


def accepted_profile(actual):
    return next((i for i, profile in enumerate(PROFILES) if actual == profile), None)


def replace1(s, old, new, name):
    count = s.count(old)
    if count != 1: raise ValueError(f"{name}: expected exact anchor once; got {count}")
    return s.replace(old, new)

def main():
    if len(sys.argv) != 3: raise SystemExit("Usage: apply_deity_private.py PRIVATE_NECRO_SRC PACKAGE_DIR")
    raw=Path(sys.argv[1]); src=raw.resolve(strict=True); package=Path(sys.argv[2]).resolve(strict=True)
    if (raw.is_symlink() or src.name != "src" or
        not src.parent.name.startswith("necromancer-playtest-") or
        src.parent.parent != Path('/root/hollowdeep-dev') and
        not str(src).startswith('/mnt/data/') or
        any(str(src).startswith(a) for a in ('/srv/','/var/www/','/usr/','/etc/','/opt/'))):
        raise SystemExit('Refusing non-disposable source')
    for name in (*FILES, "hd_deity.c", "hd_deity.h"):
        target=src/name
        if target.is_symlink(): raise SystemExit('Symlink refused: '+name)
    if (src/'hd_deity.c').exists() or (src/'hd_deity.h').exists():
        raise SystemExit('Already staged: refusing patch twice')
    originals={f:(src/f).read_bytes() for f in FILES}
    actual={f:sha256(originals[f]).hexdigest() for f in FILES}
    profile = accepted_profile(actual)
    if profile is None:
        for file,hashval in actual.items():
            print(f'{file}: actual {hashval}; allowed profiles: '+', '.join(x[file] for x in PROFILES))
        raise SystemExit('Rejected unknown/mixed private source profile; nothing changed')
    out={f:originals[f].decode('latin-1') for f in FILES}
    f='global.c'
    import re
    if re.search(r'\{\s*"[^"]+"\s*,\s*151\s*,', out[f]):
        raise SystemExit('Command ID 151 already occupied; nothing changed')
    out[f]=replace1(out[f], '#include "hollowdeep_help.h"',
       '#include "hollowdeep_help.h"\n#ifdef HD_DEITY_PLAYTEST\n#include "hd_deity.h"\n#endif',f)
    out[f]=replace1(out[f], '\t{ "*memory", 149, dm_memory },',
       '\t{ "*memory", 149, dm_memory },\n#ifdef HD_DEITY_PLAYTEST\n'
       '\t{ "*deity", 151, hd_dm_deity },\n#endif',f)
    f='hollowdeep_help.c'
    out[f]=replace1(out[f],
       '    case 113:\n',
       '#ifdef HD_DEITY_PLAYTEST\n'
       '    case 151: return player->class == DM &&\n'
       '        hd_staff_rank(hd_staff_role(player)) >= hd_staff_rank(HD_ROLE_ADMIN);\n'
       '#endif\n    case 113:\n',f)
    out[f]=replace1(out[f], '#include "hollowdeep_ranges.h"',
       '#include "hollowdeep_ranges.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n'
       'extern int hd_store_is_necromancer(const char *name);\n#endif', f)
    out[f]=replace1(out[f], '    if (count != 2) goto usage;\n    if (!strcmp(token[1], "topics"))',
       '#ifdef HD_NECROMANCER_PLAYTEST\n'
       '    if (count == 3 && !strcmp(token[1], "raise") && !strcmp(token[2], "skeleton"))\n'
       '        return show_page(player, "help.150");\n'
       '    if (count == 2 && !strcmp(token[1], "necromancer")) return show_page(player, "necromancer");\n'
       '#endif\n#ifdef HD_DEITY_PLAYTEST\n'
       '    if (count == 2 && !strcmp(token[1], "deity")) return show_page(player, "deity");\n'
       '    if (count == 2 && !strcmp(token[1], "*deity")) {\n'
       '        if (!hd_native_command_allowed(player, 151)) {\n'
       '            print(player->fd, "No matching command or spell. Use help search <text>.\\n"); return 0;\n'
       '        }\n'
       '        return show_page(player, "help.151");\n'
       '    }\n'
       '    if ((count == 2 && (!strcmp(token[1], "corpse") || !strcmp(token[1], "sacrifice"))) ||\n'
       '        (count == 3 && (!strcmp(token[1], "raise") || !strcmp(token[1], "sacrifice") ||\n'
       '         !strcmp(token[1], "loot")) && !strcmp(token[2], "corpse")))\n'
       '        return show_page(player, "corpses-pending");\n'
       '#endif\n'
       '    if (count != 2) goto usage;\n    if (!strcmp(token[1], "topics"))', f)
    out[f]=replace1(out[f], '        catalog(player, 0, NULL, 1); return 0;',
       '#ifdef HD_NECROMANCER_PLAYTEST\n'
       '        print(player->fd, "Class guide: help necromancer | help raise skeleton\\n");\n'
       '#endif\n#ifdef HD_DEITY_PLAYTEST\n'
       '        print(player->fd, "Faith: help deity | help corpse (development status)\\n");\n'
       '#endif\n        catalog(player, 0, NULL, 1); return 0;', f)
    out[f]=replace1(out[f], '    if (player->class >= CARETAKER) print(player->fd, "NATIVE CLASS POWERS:',
       '#ifdef HD_DEITY_PLAYTEST\n'
       '    if (hd_native_command_allowed(player, 151)) print(player->fd, "*deity <player> [0-16] | *deity list | help *deity\\n");\n'
       '#endif\n    if (player->class >= CARETAKER) print(player->fd, "NATIVE CLASS POWERS:', f)
    out[f]=replace1(out[f], '    print(player->fd, "%d skills listed. Use help <skill> for exact rules.\\n", shown);',
       '#ifdef HD_NECROMANCER_PLAYTEST\n'
       '    eligible = player->type == PLAYER && player->class == MAGE && player->level >= 1 &&\n'
       '        hd_store_is_necromancer(player->name);\n'
       '    if (eligible || all) {\n'
       '        print(player->fd, "raise skeleton [%s] - 8 mana, slain monster HP/MP, no timer\\n",\n'
       '              eligible ? "eligible" : "Necromancer"); shown++;\n'
       '    }\n'
       '#endif\n    print(player->fd, "%d skills listed. Use help <skill> for exact rules.\\n", shown);', f)
    f='hollowdeep_staff.c'
    out[f]=replace1(out[f],
       '    if ((strcmp(name, "builders.db") && strcmp(name, "bonus.db")) || !data_directory()) return -2;',
       '#ifdef HD_DEITY_PLAYTEST\n'
       '    if ((strcmp(name, "builders.db") && strcmp(name, "bonus.db") && strcmp(name, "deities.db"))\n'
       '        || !data_directory()) return -2;\n'
       '#else\n'
       '    if ((strcmp(name, "builders.db") && strcmp(name, "bonus.db")) || !data_directory()) return -2;\n'
       '#endif',f)
    f='Makefile'
    out[f]=replace1(out[f], 'frp.new: $(OBJECTS)',
       '# Test-only deity assignment. Never on without explicit DEITY_PLAYTEST=1.\n'
       'ifeq ($(DEITY_PLAYTEST),1)\n'
       'CFLAGS += -DHD_DEITY_PLAYTEST\n'
       'OBJECTS += hd_deity.o\n'
       'endif\n\nfrp.new: $(OBJECTS)', f)
    for f in FILES:
        if out[f] == originals[f].decode('latin-1'): raise ValueError('No actual patch: '+f)
    for name in ('hd_deity.c','hd_deity.h'):
        if not (package/name).is_file() or (package/name).is_symlink():
            raise SystemExit('Package missing: '+name)
    for f in FILES: (src/f).write_bytes(out[f].encode('latin-1'))
    for name in ('hd_deity.c','hd_deity.h'):
        shutil.copyfile(package/name,src/name)
    print('DEITY: exact coupled source profile accepted: '+('first-skill-only' if profile == 0 else 'round74b-integrated'))
    print('DEITY: DM command ID 151 and native help routing patched privately')
    print('PRODUCTION: UNCHANGED')

if __name__=='__main__': main()
