#!/usr/bin/env python3
"""Stage central native entity revocation into an isolated ELF32 source tree.

No spawn, award, game command, ride/travel, or live-world mutation. The feature
gate is opt-in and requires the accepted AC2 world identity module.
"""
from pathlib import Path
import argparse
import os
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX="hd-army-game-round79worldproof-"
TARGET_PREFIX="hd-army-game-round79lifecycle-"
FLAG="HD79_MOUNT_LIFECYCLE_PLAYTEST"
FILES=("Makefile","room.c","files1.c","hd79_mount_world_identity.c",
       "hd79_mount_world_identity.h")
NEEDED=("frp.new","Makefile","room.c","files1.c","global.c",
        "hd_player_store.c","hd79_mount_command.c",
        "hd79_mount_world_identity.c","hd79_mount_world_identity.h",
        "hd79_mount_presence_store.inc","wilderness.c","command1.c",
        "command2.c","command5.c","command6.c")
MAKE_ANCHOR="OBJECTS += hd79_mount_world_identity.o\nendif\n"
HOOK_INCLUDE=('#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST\n'
              '#include "hd79_mount_world_identity.h"\n'
              '#endif\n')

DEFINITIONS={
    "add_crt_rom": (r"creature\s*\*\s*crt_ptr\s*,\s*room\s*\*\s*rom_ptr\s*,\s*int\s+num",
                    "hd79_world_mount_unbind_creature(crt_ptr);"),
    "del_crt_rom": (r"creature\s*\*\s*crt_ptr\s*,\s*room\s*\*\s*rom_ptr",
                    "hd79_world_mount_unbind_creature(crt_ptr);"),
    "add_ply_rom": (r"creature\s*\*\s*ply_ptr\s*,\s*room\s*\*\s*rom_ptr",
                    "hd79_world_mount_unbind_owner(ply_ptr);"),
    "del_ply_rom": (r"creature\s*\*\s*ply_ptr\s*,\s*room\s*\*\s*rom_ptr",
                    "hd79_world_mount_unbind_owner(ply_ptr);"),
    "free_crt": (r"creature\s*\*\s*crt_ptr",
                 "hd79_world_mount_unbind_creature(crt_ptr);\n"
                 "    hd79_world_mount_unbind_owner(crt_ptr);"),
    # Conservative fail-closed rule: unloading ANY room clears every
    # ephemeral binding; later optimized runtime can rehydrate explicitly.
    "free_rom": (r"room\s*\*\s*rom_ptr",
                 "hd79_world_mount_unbind_all();")
}

def private(root,prefix,exists):
    root=Path(root)
    if (root.name!="src" or root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.absolute()!=root.resolve(strict=False)):
        raise ValueError("Disposable /tmp/"+prefix+"*/src required")
    if not exists:
        if root.exists() or not root.parent.is_dir():
            raise ValueError("Destination must be a fresh private source path")
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError("Accepted private native source absent")
    for name in NEEDED:
        f=root/name
        if f.is_symlink() or not f.is_file():
            raise ValueError("Missing/symlink native prerequisite "+name)
    with (root/"frp.new").open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected accepted private ELF32 executable")
    for parent,dirs,files in os.walk(root,followlinks=False):
        if any((Path(parent)/x).is_symlink() for x in dirs+files):
            raise ValueError("Symlink found in accepted source")
    if any(FLAG in (root/x).read_text(encoding="latin-1")
           for x in FILES):
        raise ValueError("Lifecycle hooks already staged")
    return root

def add_hook(body,fn,params,stmt):
    # Accepted Mordor 3.00 uses native, one-line function signatures,
    # brace on the next line. Refuse rather than guessing at drift.
    exp=re.compile(r"(?m)^[ \t]*void[ \t]+"+re.escape(fn)+
                   r"[ \t]*\([ \t]*"+params+
                   r"[ \t]*\)[ \t]*\r?\n[ \t]*\{")
    ms=list(exp.finditer(body))
    if len(ms)!=1:
        raise ValueError("Native lifecycle function signature drift: "+fn)
    position=ms[0].end()
    addition="\n#ifdef "+FLAG+"\n    "+stmt+"\n#endif\n"
    return body[:position]+addition+body[position:]

def update_identity(source):
    h=source["hd79_mount_world_identity.h"]
    c=source["hd79_mount_world_identity.c"]
    if (h.count("void hd79_world_mount_unbind_owner(")!=1 or
        c.count("void hd79_world_mount_unbind_owner(")!=1 or
        "hd79_world_mount_unbind_all" in h or
        "hd79_world_mount_unbind_all" in c):
        raise ValueError("Accepted native identity function drift")
    h=h.replace("#endif\n",
      "/* Fail-closed: room teardown invalidates all ephemeral bindings. */\n"
      "void hd79_world_mount_unbind_all(void);\n#endif\n",1)
    c+="\n/* Conservative room-unload/unknown cleanup: discard every token. */\n" \
       "void hd79_world_mount_unbind_all(void)\n" \
       "{\n    memset(registry,0,sizeof registry);\n}\n"
    return h,c

def modified(source):
    m=source["Makefile"]
    if (m.count(MAKE_ANCHOR)!=1 or
        "MOUNT_WORLD_IDENTITY_PLAYTEST" not in m or
        "MOUNT_LIFECYCLE_PLAYTEST" in m):
        raise ValueError("Accepted AC2 feature gate drift")
    extension=("# Round79AC3B: process-local mount identity invalidation only.\n"
               "ifeq ($(MOUNT_LIFECYCLE_PLAYTEST),1)\n"
               "ifneq ($(MOUNT_WORLD_IDENTITY_PLAYTEST),1)\n"
               "$(error MOUNT_LIFECYCLE_PLAYTEST requires MOUNT_WORLD_IDENTITY_PLAYTEST=1)\n"
               "endif\n"
               "CFLAGS += -DHD79_MOUNT_LIFECYCLE_PLAYTEST\n"
               "endif\n")
    m=m.replace(MAKE_ANCHOR,MAKE_ANCHOR+extension,1)
    if m.index("MOUNT_LIFECYCLE_PLAYTEST")>m.index("frp.new:"):
        raise ValueError("Makefile feature gate must precede executable target")
    room=source["room.c"]
    files=source["files1.c"]
    # Keep original native includes and include the authority declaration
    # only when enabled, before invoking any new symbol.
    room=HOOK_INCLUDE+room
    files=HOOK_INCLUDE+files
    for name in ("add_crt_rom","del_crt_rom","add_ply_rom","del_ply_rom"):
        params,stmt=DEFINITIONS[name]
        room=add_hook(room,name,params,stmt)
    for name in ("free_crt","free_rom"):
        params,stmt=DEFINITIONS[name]
        files=add_hook(files,name,params,stmt)
    h,c=update_identity(source)
    return {"Makefile":m,"room.c":room,"files1.c":files,
            "hd79_mount_world_identity.h":h,
            "hd79_mount_world_identity.c":c}

def stage(source,destination):
    source=private(source,SOURCE_PREFIX,True)
    destination=private(destination,TARGET_PREFIX,False)
    originals={name:(source/name).read_bytes() for name in FILES}
    data={name:(source/name).read_text(encoding="latin-1") for name in FILES}
    changes=modified(data)
    shutil.copytree(source,destination,symlinks=False)
    try:
        for name,contents in changes.items():
            (destination/name).write_text(contents,encoding="latin-1")
        for name,blob in originals.items():
            if (source/name).read_bytes()!=blob:
                raise ValueError("Accepted source changed during staging")
        for name in ("hd_player_store.c","hd79_mount_command.c",
                     "global.c","command1.c","command2.c","command5.c",
                     "command6.c","wilderness.c",
                     "hd79_mount_presence_store.inc"):
            if (destination/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError("Gameplay/save boundary edited: "+name)
    except BaseException:
        shutil.rmtree(destination)
        raise
    return destination

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("accepted_round79ac2_source",type=Path)
    p.add_argument("new_round79ac3b_source",type=Path)
    a=p.parse_args()
    try:
        target=stage(a.accepted_round79ac2_source,a.new_round79ac3b_source)
    except (OSError,ValueError) as e:
        print("ROUND79AC3B: PRIVATE STAGING REFUSED:",e,file=sys.stderr)
        return 1
    print("ROUND79AC3B: PRIVATE NATIVE LIFECYCLE REVOCATION STAGED:",target)
    print("TRUSTED SPAWNER/LOGIN REBINDING: NOT INSTALLED")
    print("BOARD/STABLE/RETRIEVE/RIDDEN MOVEMENT: NOT ENABLED")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
