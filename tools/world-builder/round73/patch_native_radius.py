"""Install adjustable mapradius into the disposable Round 72 native build only."""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_native_radius.py <disposable-round72-native-build>")
root = Path(sys.argv[1]).resolve(strict=True)
if (root.name != "round72-native-build" or
    not root.parent.name.startswith("round72-build-") or
    root.parent.parent != Path("/root/hollowdeep-dev") or
    not (root / "treasure_guard.c").is_file() or
    not (root / "treasure_locate.c").is_file()):
    raise SystemExit("Refusing non-disposable/incompletely patched native source")
repo_root = Path(__file__).resolve().parents[1]
original = repo_root / "round72" / "wilderness.c"
source = Path(__file__).with_name("wilderness_radius.c")
target = root / "wilderness.c"
if any(p.is_symlink() or not p.is_file() for p in (source, original, target)):
    raise SystemExit("Missing or symlinked original/replacement map source")
if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(original.read_bytes()).digest():
    raise SystemExit("Unexpected existing wilderness.c; refusing to replace it")
if "hd_wilderness_mapradius" in target.read_text(encoding="latin-1"):
    raise SystemExit("Map radius already patched")
command = root / "global.c"
if not command.is_file() or command.is_symlink():
    raise SystemExit("Missing native command registry")
code = command.read_text(encoding="latin-1")
anchors = (
    ("extern int hd_wilderness_map();",
     "extern int hd_wilderness_map();\nextern int hd_wilderness_mapradius();"),
    ('\t{ "map", 98, hd_wilderness_map },',
     '\t{ "mapradius", 100, hd_wilderness_mapradius },\n\t{ "map", 98, hd_wilderness_map },'),
)
for old, new in anchors:
    if code.count(old) != 1 or new in code:
        raise SystemExit("Unexpected native mapradius dispatch anchors")
    code = code.replace(old, new)
# No changes until ALL checks above have succeeded.
command.write_text(code, encoding="latin-1")
shutil.copyfile(source, target)
print("ROUND 73E: adjustable mapradius staged in disposable native tree")
