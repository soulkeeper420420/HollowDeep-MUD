"""Apply staged virtual chest code only to the verified disposable Round 72 tree."""
from pathlib import Path
import re
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_native_guard.py <disposable-round72-native-build>")
root = Path(sys.argv[1]).resolve(strict=True)
if (root.name != "round72-native-build" or
        not root.parent.name.startswith("round72-build-") or
        root.parent.parent != Path("/root/hollowdeep-dev") or
        (root / "treasure_guard.c").exists() or
        not (root / "treasure_locate.c").is_file() or
        not (root / "wilderness.c").is_file()):
    raise SystemExit("Refusing non-disposable or incompletely staged native tree")
source = Path(__file__).with_name("treasure_guard.c")
if not source.is_file() or source.is_symlink():
    raise SystemExit("Treasure guard source missing or symlinked")

prepared = {}
for name in ("global.c", "Makefile", "creature.c"):
    path = root / name
    content = path.read_text(encoding="latin-1")
    if name == "global.c":
        if content.count("extern int hd_treasure_locate();") != 1:
            raise SystemExit("Unexpected locate native command declaration")
        content = content.replace("extern int hd_treasure_locate();",
            "extern int hd_treasure_locate();\nextern int hd_treasure_open();")
        pattern = r'(?m)^(\s*\{\s*"open"\s*,\s*31\s*,\s*)openexit(\s*\},)'
        content, n = re.subn(pattern, r'\g<1>hd_treasure_open\2', content)
        if n != 1:
            raise SystemExit("Unexpected native openexit dispatch")
    elif name == "Makefile":
        needle = "treasure_locate.o"
        if content.count(needle) != 1:
            raise SystemExit("Unexpected native Makefile object list")
        content = content.replace(needle, needle + " treasure_guard.o")
    else:
        marker = "void die(crt_ptr, att_ptr)"
        if content.count(marker) != 1:
            raise SystemExit("Unexpected native die() definition")
        pos = content.index(marker)
        hook = re.compile(r'(?m)^([ \t]*)if\s*\(crt_ptr->type\s*==\s*MONSTER\)\s*\{')
        matches = list(hook.finditer(content, pos, pos + 1600))
        if len(matches) != 1:
            raise SystemExit("Unexpected monster death branch in die()")
        m = matches[0]
        content = (content[:m.start()] + m.group(1) +
                   "hd_treasure_guardian_death(crt_ptr, att_ptr);\n" + content[m.start():])
        content = content[:pos] + "extern void hd_treasure_guardian_death();\n" + content[pos:]
    prepared[path] = content

for path, content in prepared.items():
    path.write_text(content, encoding="latin-1")
shutil.copyfile(source, root / "treasure_guard.c")
print("ROUND 73D: virtual chest and trusted guardian-death hook staged privately")
