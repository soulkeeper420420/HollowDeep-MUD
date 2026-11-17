#!/usr/bin/env python3
"""Guarded, source-only Raise Skeleton patch atop the published Necromancer prototype.

Works only in a disposable necromancer-playtest-*/src directory. Verifies
all exact anchors before any source write. No live files or process changes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sys

FILES = ("Makefile", "global.c", "command5.c", "command2.c", "player.c",
         "creature.c", "update.c", "files1.c")
ARTIFACTS = ("hd_necro_skeleton.c", "hd_necro_skeleton.h")


def replace_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise ValueError(f"{label}: expected exactly one known anchor, got {n}")
    return text.replace(old, new)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: apply_private.py DISPOSABLE_NECROMANCER_SRC PACKAGE_DIR")
    raw = Path(sys.argv[1]); src = raw.resolve(strict=True)
    pkg = Path(sys.argv[2]).resolve(strict=True)
    if (raw.is_symlink() or src.is_symlink() or src.name != "src" or
        not src.parent.name.startswith("necromancer-playtest-") or
        not src.parent.parent.is_dir() or
        any(str(src).startswith(prefix) for prefix in
            ("/srv/", "/var/www/", "/usr/", "/etc/", "/opt/"))):
        raise SystemExit("Refusing non-disposable source tree")
    for name in (*FILES, "hd_player_store.c", "command1.c"):
        path = src / name
        if path.is_symlink() or not path.is_file():
            raise SystemExit("Missing or symlinked input: " + name)
    for name in ARTIFACTS:
        if (src / name).exists() or not (pkg / name).is_file() or (pkg / name).is_symlink():
            raise SystemExit("Missing package or existing target: " + name)

    originals = {name: (src / name).read_text(encoding="latin-1") for name in FILES}
    out = dict(originals)
    # Explicitly assert the pinned Necromancer identity and the private
    # compile switch are already installed. No numeric class-ID modification.
    assert_markers = {
        "Makefile": "CFLAGS += -DHD_NECROMANCER_PLAYTEST",
        "command1.c": "hd_store_create_necromancer(",
        "hd_player_store.c": "hd_store_is_necromancer(",
    }
    for file, text in assert_markers.items():
        body = originals[file] if file in originals else (src/file).read_text(encoding="latin-1")
        if text not in body:
            raise SystemExit(f"Necromancer prototype missing in {file}")

    f = "Makefile"; text = out[f]
    text = replace_one(text,
        "CFLAGS += -DHD_NECROMANCER_PLAYTEST\n",
        "CFLAGS += -DHD_NECROMANCER_PLAYTEST\nOBJECTS += hd_necro_skeleton.o\n", f)
    out[f] = text

    f = "global.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text, '\t{ "raise", 100, action },',
        '#ifdef HD_NECROMANCER_PLAYTEST\n'
        '\t{ "raise", 100, hd_necro_raise_or_action },\n'
        '\t{ "raiseskeleton", 150, hd_necro_raise },\n'
        '#else\n\t{ "raise", 100, action },\n#endif', f+" command")
    out[f] = text

    f = "command5.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text, '    attack_crt(ply_ptr, crt_ptr);',
        '#ifdef HD_NECROMANCER_PLAYTEST\n'
        '    /* Never use a freed target after the native killing blow. */\n'
        '    if (!attack_crt(ply_ptr, crt_ptr))\n'
        '        hd_necro_skeleton_assist(ply_ptr, crt_ptr);\n'
        '#else\n    attack_crt(ply_ptr, crt_ptr);\n#endif', f+" attack")
    out[f] = text

    f = "command2.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text, '\t\tadd_ply_rom(ply_ptr, rom_ptr);',
        '\t\tadd_ply_rom(ply_ptr, rom_ptr);\n'
        '#ifdef HD_NECROMANCER_PLAYTEST\n'
        '\t\thd_necro_skeleton_follow(ply_ptr, old_rom_ptr, rom_ptr);\n'
        '#endif', f+" follow")
    out[f] = text

    f = "player.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text,
        'void uninit_ply(ply_ptr)\ncreature\t*ply_ptr;\n{',
        'void uninit_ply(ply_ptr)\ncreature\t*ply_ptr;\n{', f+" signature")
    # Keep the K&R declarations at the top of the function body.
    text = replace_one(text,
        '\tint\t\ti;\n\n\n\tif(ply_ptr->parent_rom)',
        '\tint\t\ti;\n\n#ifdef HD_NECROMANCER_PLAYTEST\n'
        '\thd_necro_skeleton_logout(ply_ptr);\n#endif\n\n\tif(ply_ptr->parent_rom)', f+" logout")
    out[f] = text

    f = "creature.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text, '    else if(crt_ptr->type == PLAYER) {',
        '    else if(crt_ptr->type == PLAYER) {\n'
        '#ifdef HD_NECROMANCER_PLAYTEST\n'
        '        hd_necro_skeleton_logout(crt_ptr);\n'
        '#endif', f+" owner death")
    out[f] = text

    f = "update.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    text = replace_one(text, '    last_update = t;\n    if(t - last_user_update >= 20)',
        '    last_update = t;\n#ifdef HD_NECROMANCER_PLAYTEST\n'
        '    hd_necro_skeleton_tick(t);\n#endif\n'
        '    if(t - last_user_update >= 20)', f+" expiry")
    out[f] = text

    f = "files1.c"; text = out[f]
    text = replace_one(text, '#include "mextern.h"',
        '#include "mextern.h"\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif', f+" header")
    anchor = ('void free_crt(crt_ptr)\ncreature\t*crt_ptr;\n{\n'
              '\totag\t*op, *tempo;\n\tetag\t*ep, *tempe;\n'
              '\tctag\t*cp, *tempc;\n\tttag\t*tp, *tempt;\n\tint\ti;')
    text = replace_one(text, anchor, anchor +
        '\n#ifdef HD_NECROMANCER_PLAYTEST\n'
        '\thd_necro_skeleton_on_free(crt_ptr);\n'
        '#endif', f+" free callback")
    out[f] = text

    for name in FILES:
        if out[name] == originals[name]:
            raise SystemExit("No patch: " + name)
    # Stage hashes first; write only after all anchors matched and inputs
    # were verified. This tool is exclusively for a freshly copied candidate.
    for name in FILES:
        (src / name).write_text(out[name], encoding="latin-1")
    for name in ARTIFACTS:
        shutil.copyfile(pkg / name, src / name)
    for name in (*FILES, *ARTIFACTS):
        print(f"PRIVATE PATCH: {name}: {hashlib.sha256((src/name).read_bytes()).hexdigest()[:16]}")
    print("NECROMANCER: guarded one-skeleton combat/follow lifecycle staged privately")
    print("PRODUCTION: UNCHANGED")

if __name__ == "__main__":
    main()
