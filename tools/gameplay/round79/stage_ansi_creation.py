#!/usr/bin/env python3
"""Stage creation-time ANSI choice on a verified disposable native source tree.

Round 79B: changes only command1.c, Makefile and adds a pure ANSI parser.
Does not change production, player structure, or saved character files.
The status prompt renderer is staged separately after its native audit.
"""
import argparse
from pathlib import Path
import os
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_ROOT=Path("/tmp")
NEW=frozenset(("hd_ansi_choice.c","hd_ansi_choice.h"))
MODIFIED=frozenset(("Makefile","command1.c"))
PASSWORD_ANCHOR=re.compile(
    r'(?P<ind>[ \t]*)print\(fd, "%c%c%c\\nChoose a password '
    r'\(up to 14 chars\): ", 255, 251, 1\);[ \t]*\n'
    r'(?P<ret>[ \t]*)RETURN\(fd, create_ply, 8\);[ \t]*\n'
    r'(?P<cas>[ \t]*)case 8:',
    re.M,
)

def validate(root,prefix,allow_nonexistent=False):
    root=Path(root)
    if (root.is_symlink() or root.name!="src" or
        root.parent.parent!=SOURCE_ROOT or
        not root.parent.name.startswith(prefix)):
        raise ValueError("Expected private /tmp/"+prefix+"*/src")
    if allow_nonexistent:
        if root.exists() or root.parent.is_symlink() or not root.parent.is_dir():
            raise ValueError("Target must be new under an existing private build directory")
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError("Source is not a real private directory")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private engine executable missing")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected private ELF32 source")
    for file in ("Makefile","command1.c","mtype.h"):
        if (root/file).is_symlink() or not (root/file).is_file():
            raise ValueError("Required native source missing: "+file)
    make=(root/"Makefile").read_text(encoding="latin-1")
    if "HD_WARLOCK_PLAYTEST" not in make:
        raise ValueError("Expected verified Round 78E Warlock build")
    if "PANSIC" not in (root/"mtype.h").read_text(encoding="latin-1"):
        raise ValueError("Native saved ANSI flag missing")
    for directory, dirs, files in os.walk(root,followlinks=False):
        for name in dirs+files:
            if (Path(directory)/name).is_symlink():
                raise ValueError("Source tree symlink denied")
    if any((root/name).exists() for name in NEW):
        raise ValueError("ANSI creation helper already installed")
    return root

def exact(source,pattern,replacement,label):
    if source.count(pattern)!=1:
        raise ValueError(label+": exact native anchor drift")
    return source.replace(pattern,replacement,1)

def staged_creation(source,target):
    source=validate(source,"hd-army-game-round78-")
    target=validate(target,"hd-army-game-round79-",True)
    if "HD79_STATUS_ANSI_PLAYTEST" in (source/"command1.c").read_text(encoding="latin-1"):
        raise ValueError("ANSI creation already installed")
    before={}
    for path in MODIFIED:
        before[path]=(source/path).read_text(encoding="latin-1")

    make=exact(before["Makefile"],
        "CFLAGS += -DHD74_PRIVATE_NATIVE\n",
        "CFLAGS += -DHD74_PRIVATE_NATIVE\n"
        "ifeq ($(STATUS_ANSI_PLAYTEST),1)\n"
        "CFLAGS += -DHD79_STATUS_ANSI_PLAYTEST\n"
        "OBJECTS += hd_ansi_choice.o\n"
        "endif\n",
        "private Makefile feature flag")

    c=exact(before["command1.c"],
        '#include "mextern.h"',
        '#include "mextern.h"\n'
        '#ifdef HD79_STATUS_ANSI_PLAYTEST\n'
        '#include "hd_ansi_choice.h"\n'
        '#endif',
        "native player command header")

    matches=list(PASSWORD_ANCHOR.finditer(c))
    if len(matches)!=1:
        raise ValueError("Creation password/state anchor drift: "+str(len(matches)))
    match=matches[0]
    ind,ret,cas=match.group("ind","ret","cas")
    replacement=(
        '#ifdef HD79_STATUS_ANSI_PLAYTEST\n'
        +ind+'print(fd, "\\nEnable ANSI colors and colored status? (yes/no): ");\n'
        +ret+'RETURN(fd, create_ply, 9);\n'
        +cas+'case 9:\n'
        +cas+'{\n'
        +cas+'    int chosen = hd_parse_ansi_choice(str);\n'
        +cas+'    if (chosen < 0) {\n'
        +cas+'        print(fd, "Please answer yes or no.\\nEnable ANSI colors and colored status? (yes/no): ");\n'
        +cas+'        RETURN(fd, create_ply, 9);\n'
        +cas+'    }\n'
        +cas+'    if (chosen) F_SET(Ply[fd].ply, PANSIC);\n'
        +cas+'    else F_CLR(Ply[fd].ply, PANSIC);\n'
        +cas+'    F_SET(Ply[fd].ply, PPROMP);\n'
        +ind+'    print(fd, "%c%c%c\\nChoose a password (up to 14 chars): ", 255, 251, 1);\n'
        +ret+'    RETURN(fd, create_ply, 8);\n'
        +cas+'}\n'
        '#else\n'
        +match.group(0).rsplit('case 8:',1)[0].rstrip('\n')+'\n'
        '#endif\n'
        +cas+'case 8:'
    )
    c=c[:match.start()]+replacement+c[match.end():]

    shutil.copytree(source,target,symlinks=False)
    try:
        (target/"Makefile").write_text(make,encoding="latin-1")
        (target/"command1.c").write_text(c,encoding="latin-1")
        for name in NEW:
            shutil.copyfile(HERE/name,target/name)
        for name in MODIFIED:
            if (source/name).read_text(encoding="latin-1")!=before[name]:
                raise ValueError("Source changed during stage")
        if not (target/"hd_ansi_choice.c").is_file():
            raise ValueError("ANSI parser missing")
    except Exception:
        shutil.rmtree(target)
        raise
    return sorted(NEW | MODIFIED)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("destination",type=Path)
    a=p.parse_args()
    try:
        names=staged_creation(a.source,a.destination)
    except (OSError,ValueError) as exc:
        print("ROUND 79B ANSI CREATION: DENIED",exc,file=sys.stderr)
        return 1
    print("ROUND 79B: PRIVATE ANSI CREATION STAGED",", ".join(names))
    print("NATIVE BUILD / SOCKET VALIDATION: PENDING")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
