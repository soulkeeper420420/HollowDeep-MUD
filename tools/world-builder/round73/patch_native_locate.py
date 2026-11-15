"""Stage read-only `locate` in a disposable Round 72 native build tree only."""
from pathlib import Path
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_native_locate.py <disposable-round72-native-build>")
root = Path(sys.argv[1]).resolve(strict=True)
if (root.name != "round72-native-build" or
        not root.parent.name.startswith("round72-build-") or
        root.parent.parent != Path("/root/hollowdeep-dev") or
        (root / "treasure_locate.c").exists() or
        not (root / "wilderness.c").is_file() or
        not (root / "mstruct.h").is_file()):
    raise SystemExit("Refusing to alter non-disposable or already-patched native tree")
replacements = {
    "global.c": [
        ("extern int hd_wilderness_map();",
         "extern int hd_wilderness_map();\nextern int hd_treasure_locate();"),
        ('\t{ "map", 98, hd_wilderness_map },',
         '\t{ "map", 98, hd_wilderness_map },\n\t{ "locate", 99, hd_treasure_locate },'),
    ],
    "Makefile": [
        ("hollowdeep_help.o wilderness.o",
         "hollowdeep_help.o wilderness.o treasure_locate.o"),
    ],
}
prepared = {}
for name, changes in replacements.items():
    path = root / name
    contents = path.read_text(encoding="latin-1")
    for old, new in changes:
        if contents.count(old) != 1 or new in contents:
            raise SystemExit(f"Unexpected {name} patch anchor; no native changes applied")
        contents = contents.replace(old, new)
    prepared[path] = contents
source = Path(__file__).with_name("treasure_locate.c")
if not source.is_file() or source.is_symlink():
    raise SystemExit("Missing expected original treasure_locate.c")
for path, contents in prepared.items():
    path.write_text(contents, encoding="latin-1")
shutil.copyfile(source, root / "treasure_locate.c")
print("ROUND 73C: read-only locate command staged inside disposable native tree")
