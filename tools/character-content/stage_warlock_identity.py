#!/usr/bin/env python3
"""Round 78E: stage private Warlock identity and creation hooks, never production.

The numeric class remains MAGE; a unique HDTR1 receipt marks Warlocks.
This is an identity/creation milestone, NOT a complete Pact Bolt implementation.
"""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys

from native_identity_audit import EXPECTED_GAME_SHA256, source_dir
from stage import private_path, inventory

WARLOCK_CLAIM = "ffffffffffffffffffffffffffffff78"
WARLOCK_DIGEST = "a74d000000000000000000000000000000000000000000000000000000000001"
CHANGED = frozenset(("Makefile", "command1.c", "hd_player_store.c",
                     "hd_player_store.h", "hollowdeep_help.c"))
ADDED = frozenset(("help/warlock",))


def replace_exact(body, old, new, label):
    found = body.count(old)
    if found != 1:
        raise ValueError(f"{label}: expected one exact native anchor, found {found}")
    return body.replace(old, new, 1)


def patch_source(source, target, page):
    source = source_dir(source)
    target = private_path(target, "Staged native destination")
    if target.exists() or target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError("Destination must be fresh and separate")
    if not target.parent.is_dir():
        raise ValueError("Create the private target parent before staging")
    if hashlib.sha256((source/"frp.new").read_bytes()).hexdigest() != EXPECTED_GAME_SHA256:
        raise ValueError("Source executable differs from the tested Round 77 binary")
    before = inventory(source)
    if any(name in before for name in ADDED):
        raise ValueError("Private source already contains Warlock help; refuse overwrite")
    staged = {}
    for name in CHANGED:
        data = (source/name).read_text(encoding="latin-1")
        if "HD_WARLOCK_PLAYTEST" in data or "hd_store_create_warlock" in data:
            raise ValueError(f"Warlock already staged in {name}")
        staged[name] = data

    s = staged["hd_player_store.c"]
    s = replace_exact(s,
        'static const char conjure_id[] = "ffffffffffffffffffffffffffffff77";',
        'static const char conjure_id[] = "ffffffffffffffffffffffffffffff77";\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        'static const char warlock_id[] = "' + WARLOCK_CLAIM + '";\n'
        'static const char warlock_identity[] = "' + WARLOCK_DIGEST + '";\n'
        '#endif',
        "reserved identity constants")
    s = replace_exact(s,
        'return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id) || '
        '!strcmp(claim, pet_id) || !strcmp(claim, conjure_id);',
        'return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id) || '
        '!strcmp(claim, pet_id) || !strcmp(claim, conjure_id)\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '        || !strcmp(claim, warlock_id)\n'
        '#endif\n'
        '        ;',
        "receipt reservation")
    s = replace_exact(s,
        'enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER };',
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '#ifndef HD_NECROMANCER_PLAYTEST\n'
        '#error "Warlock requires the stable Necromancer receipt format"\n'
        '#endif\n'
        '#endif\n'
        'enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        ', PLAYER_CREATE_WARLOCK\n'
        '#endif\n'
        ' };',
        "atomic creation modes")
    s = replace_exact(s,
        '    if (claim || digest) {\n',
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '    if (action == PLAYER_CREATE_WARLOCK &&\n'
        '        (crt->class != MAGE ||\n'
        '         hd_receipt_add(&receipts, warlock_id, warlock_identity))) goto done;\n'
        '#endif\n'
        '    if (claim || digest) {\n',
        "first atomic receipt insertion")
    query = (
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '/* A second class identity must not be a plain Mage or Necromancer. */\n'
        'int hd_store_is_warlock(const char *name)\n'
        '{\n'
        '    unsigned char *raw = malloc(HD_RAW_CAPACITY);\n'
        '    size_t size = 0, used = 0;\n'
        '    hd_receipt_set receipts;\n'
        '    int result = 0;\n'
        '    if (!raw) return 0;\n'
        '    if (read_record(name, raw, &size, &used, &receipts) == 0 &&\n'
        '        ((const creature *)raw)->class == MAGE &&\n'
        '        hd_receipt_lookup(&receipts, warlock_id, warlock_identity) == 1 &&\n'
        '        hd_receipt_lookup(&receipts, necromancer_id, necromancer_identity) == 0)\n'
        '        result = 1;\n'
        '    free(raw);\n'
        '    return result;\n'
        '}\n'
        '#endif\n'
    )
    s = replace_exact(s,
        'enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        ', PLAYER_CREATE_WARLOCK\n'
        '#endif\n'
        ' };',
        query +
        'enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        ', PLAYER_CREATE_WARLOCK\n'
        '#endif\n'
        ' };',
        "identity read helper")
    # Ensure existing Necromancer identity is mutually exclusive even if a
    # corrupted or forged receipt set contains both reserved class claims.
    s = replace_exact(s,
        '        is_necromancer = hd_receipt_lookup(&receipts, necromancer_id,\n'
        '                                         necromancer_identity) == 1;',
        '        is_necromancer = hd_receipt_lookup(&receipts, necromancer_id,\n'
        '                                         necromancer_identity) == 1;\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '    if (is_necromancer &&\n'
        '        hd_receipt_lookup(&receipts, warlock_id, warlock_identity) != 0)\n'
        '        is_necromancer = 0;\n'
        '#endif',
        "mutually exclusive Necromancer identity")
    s = replace_exact(s,
        'int hd_store_save_live_player(const char *name, creature *player)',
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        'int hd_store_create_warlock(const char *name, creature *player)\n'
        '{\n'
        '    return store_internal(name, player, NULL, NULL, PLAYER_CREATE_WARLOCK);\n'
        '}\n'
        '#endif\n'
        'int hd_store_save_live_player(const char *name, creature *player)',
        "Warlock creation API")
    staged["hd_player_store.c"] = s

    s = staged["hd_player_store.h"]
    s = replace_exact(s,
        'int hd_store_save_live_player(const char *name, creature *player);',
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        'int hd_store_create_warlock(const char *name, creature *player);\n'
        'int hd_store_is_warlock(const char *name);\n'
        '#endif\n'
        'int hd_store_save_live_player(const char *name, creature *player);',
        "public native identity API")
    staged["hd_player_store.h"] = s

    s = staged["command1.c"]
    s = replace_exact(s,
        '        print(fd, "Mage, Monk, Necromancer, Paladin, Ranger, Thief\\n");',
        '        print(fd, "Mage, Monk, Necromancer, Paladin, Ranger, Thief\\n");\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '        print(fd, "Warlock\\n");\n'
        '#endif',
        "class selection menu")
    selector = (
        '        if (!strcasecmp(str, "necromancer")) {\n'
        '            Ply[fd].ply->class = MAGE;\n'
        "            Ply[fd].extr->tempstr[1][0] = 'n';\n"
        '        } else\n'
        '#endif\n'
        '        switch(low(str[0])) {'
    )
    replacement = (
        '        if (!strcasecmp(str, "necromancer")) {\n'
        '            Ply[fd].ply->class = MAGE;\n'
        "            Ply[fd].extr->tempstr[1][0] = 'n';\n"
        '        } else\n'
        '#endif\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '        if (!strcasecmp(str, "warlock")) {\n'
        '            Ply[fd].ply->class = MAGE;\n'
        "            Ply[fd].extr->tempstr[1][0] = 'w';\n"
        '        } else\n'
        '#endif\n'
        '        switch(low(str[0])) {'
    )
    s = replace_exact(s, selector, replacement, "Warlock selection routing")
    created = (
        "                if ((Ply[fd].extr->tempstr[1][0] == 'n'\n"
        '                     ? hd_store_create_necromancer(Ply[fd].ply->name, Ply[fd].ply)\n'
        '                     : hd_store_create_player(Ply[fd].ply->name, Ply[fd].ply)) != 0) {'
    )
    routed = (
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        "                if ((Ply[fd].extr->tempstr[1][0] == 'w'\n"
        '                     ? hd_store_create_warlock(Ply[fd].ply->name, Ply[fd].ply)\n'
        "                     : Ply[fd].extr->tempstr[1][0] == 'n'\n"
        '                     ? hd_store_create_necromancer(Ply[fd].ply->name, Ply[fd].ply)\n'
        '                     : hd_store_create_player(Ply[fd].ply->name, Ply[fd].ply)) != 0) {\n'
        '#else\n'
        + created + '\n'
        '#endif'
    )
    s = replace_exact(s, created, routed, "atomic class creation selector")
    staged["command1.c"] = s

    s = staged["Makefile"]
    s = replace_exact(s,
        'ifeq ($(NECROMANCER_PLAYTEST),1)\n'
        'CFLAGS += -DHD_NECROMANCER_PLAYTEST\n'
        'OBJECTS += hd_necro_skeleton.o\n'
        'endif\n',
        'ifeq ($(NECROMANCER_PLAYTEST),1)\n'
        'CFLAGS += -DHD_NECROMANCER_PLAYTEST\n'
        'OBJECTS += hd_necro_skeleton.o\n'
        'endif\n'
        'ifeq ($(WARLOCK_PLAYTEST),1)\n'
        'ifneq ($(NECROMANCER_PLAYTEST),1)\n'
        '$(error WARLOCK_PLAYTEST requires NECROMANCER_PLAYTEST=1)\n'
        'endif\n'
        'CFLAGS += -DHD_WARLOCK_PLAYTEST\n'
        'endif\n',
        "private build feature gate")
    staged["Makefile"] = s

    s = staged["hollowdeep_help.c"]
    s = replace_exact(s,
        '    if (count < 2) goto usage;',
        '    if (count < 2) goto usage;\n'
        '#ifdef HD_WARLOCK_PLAYTEST\n'
        '    if (count == 2 && !strcmp(token[1], "warlock"))\n'
        '        return show_page(player, "warlock");\n'
        '#endif',
        "Warlock class help")
    staged["hollowdeep_help.c"] = s

    shutil.copytree(source, target, symlinks=False)
    try:
        for name, body in staged.items():
            (target/name).write_text(body, encoding="latin-1")
        dest = target/"help/warlock"
        if dest.exists() or dest.is_symlink():
            raise ValueError("Warlock help would overwrite native content")
        shutil.copyfile(page, dest)
        after = inventory(target)
        if inventory(source) != before:
            raise ValueError("Input source changed during staging")
        if set(after) - set(before) != ADDED or set(before) - set(after):
            raise ValueError("Unexpected staged source inventory")
        changed = {p for p in before if after[p] != before[p]}
        if changed != CHANGED:
            raise ValueError("Unexpected source changes: " + repr(sorted(changed)))
        return sorted(changed | ADDED)
    except Exception:
        shutil.rmtree(target)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        names = patch_source(
            args.source, args.destination,
            Path(__file__).with_name("warlock-help.txt"))
    except (OSError, ValueError) as exc:
        print("ROUND 78E: DENIED:", exc, file=sys.stderr)
        return 1
    print("ROUND 78E: PRIVATE WARLOCK IDENTITY SOURCE STAGED")
    print("Modified:", ", ".join(names))
    print("Native build and gameplay: PENDING")
    print("Production deployment: NONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
