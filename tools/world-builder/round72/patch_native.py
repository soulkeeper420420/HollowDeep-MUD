"""Stage the Round 72 build in a new copy of the reviewed native tree."""
from pathlib import Path
import re
import shutil
import sys


def patch(root, filename, old, new):
    path = root / filename
    source = path.read_text(encoding="latin-1")
    if source.count(old) != 1:
        raise ValueError(f"Expected one native anchor in {filename}")
    path.write_text(source.replace(old, new), encoding="latin-1")


source, target = map(lambda arg: Path(arg).resolve(), sys.argv[1:])
if target.exists() or not target.name.startswith("round72-native-") or source == target:
    raise SystemExit("Choose a fresh Round 72 native build directory")
if any(path.is_symlink() for path in source.rglob("*")):
    raise SystemExit("Unexpected symlink in native source")
shutil.copytree(source, target)
header = target / "mtype.h"
text = header.read_text(encoding="latin-1")
text, count = re.subn(r"(?m)^(#define RMAX[ \t]+)(?:9000|16000)\b", r"\g<1>16000", text)
if count != 1:
    raise SystemExit("Unexpected native room capacity")
header.write_text(text, encoding="latin-1")
patch(target, "global.c", '#include "hollowdeep_help.h"',
      '#include "hollowdeep_help.h"\n\nextern int hd_wilderness_map();')
patch(target, "global.c", '\t{ "look", 2, look },',
      '\t{ "look", 2, look },\n\t{ "map", 98, hd_wilderness_map },')
patch(target, "Makefile", "hollowdeep_help.o", "hollowdeep_help.o wilderness.o")
patch(target, "hollowdeep_build.c", "strlen(text) > 4", "strlen(text) > 5")
patch(target, "hollowdeep_build.c", 'if (!strcmp(action, "create") && (id = number(rest)) >= 2) {',
      'if (!strcmp(action, "create") && (id = number(rest)) >= 2) {\n'
      '        if (id >= 9000 && id < 10000) { print(player->fd, "Room ID is reserved.\\n"); return 0; }')
for filename in ("hollowdeep_build.c", "hollowdeep_ranges.c"):
    path = target / filename
    path.write_bytes(path.read_bytes().replace(b"2-8999", b"2-15999 (9000-9999 reserved)"))
patch(target, "hollowdeep_ranges.c", "strlen(text) > 4", "strlen(text) > 5")
path = target / "hollowdeep_ranges.c"
old = b"count > 500 || last >= RMAX"
if path.read_bytes().count(old) != 1:
    raise SystemExit("Unexpected builder assignment check")
path.write_bytes(path.read_bytes().replace(old, old + b" || (first < 10000 && last >= 9000)"))
patch(target, "dm2.c",
      'if(cmnd->val[1] < 2) {\n\t\tprint(fd, "Add what?\\n");',
      'if(cmnd->val[1] < 2 || cmnd->val[1] >= RMAX ||\n'
      '\t   (cmnd->val[1] >= 9000 && cmnd->val[1] < 10000)) {\n'
      '\t\tprint(fd, "Choose an unreserved room ID from 2 through 15999.\\n");')
patch(target, "dm4.c", "num > RMAX", "num >= RMAX")
path = target / "magic4.c"
old = b"mrand(1, RMAX-1)"
if path.read_bytes().count(old) != 2:
    raise SystemExit("Unexpected random teleport paths")
path.write_bytes(path.read_bytes().replace(old, b"mrand(1, 8999)"))
shutil.copyfile(Path(__file__).with_name("wilderness.c"), target / "wilderness.c")
