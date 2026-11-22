"""Apply Round 79T only to a fresh copy of the verified private native tree."""
from pathlib import Path
import hashlib
import shutil
import sys

source, target = map(Path, sys.argv[1:])
if source.is_symlink() or source.parent.is_symlink():
    raise SystemExit("Refusing symlinked source")
source = source.resolve(strict=True)
if (target.is_symlink() or target.parent.is_symlink() or
        not target.parent.is_dir() or target.parent.resolve() != target.parent.absolute()):
    raise SystemExit("Expected a real disposable parent directory")
if (source.parent.parent != Path("/tmp") or source.name != "src" or
        not source.parent.name.startswith("hd-army-game-round79rest-") or
        target.exists() or target.parent.parent != Path("/tmp") or
        target.name != "src" or not target.parent.name.startswith("hd-army-game-round79mount-")):
    raise SystemExit("Use an accepted private baseline and a new disposable mount tree")
if any(p.is_symlink() for p in source.rglob("*")):
    raise SystemExit("Refusing symlinked native source")
if hashlib.sha256((source / "frp.new").read_bytes()).hexdigest() != (
        "e8aa9e09f325460f2ad8a463d0324f86ef7f2bab8a972f6a534d506eec8d1f5b"):
    raise SystemExit("Expected the accepted ELF32 baseline digest")
changes = {}


def patch(name, before, after):
    text = changes.get(name, (source / name).read_text(encoding="latin-1"))
    if text.count(before) != 1:
        raise ValueError("Unexpected native anchor in " + name)
    changes[name] = text.replace(before, after)


patch("hd_player_store.c", "static int reserved_receipt(const char *claim)",
      'static const char mount_first_id[] = "ffffffffffffffffffffffffffffff7a";\n'
      'static const char mount_second_id[] = "ffffffffffffffffffffffffffffff7b";\n\n'
      "static int reserved_receipt(const char *claim)")
patch("hd_player_store.c", "return !strcmp(claim, life_id)",
      "return !strcmp(claim,mount_first_id) || !strcmp(claim,mount_second_id) || !strcmp(claim, life_id)")
patch("hd_player_store.c", '#include "hd_breath_store.inc"',
      '#include "hd_breath_store.inc"\n#include "hd79_breath_travel_runtime.h"\n#include "hd79_mount_store.inc"')
patch("hd79_breath_travel_runtime.c", '#include "hd_breath_store.h"',
      '#include "hd_breath_store.h"\n#include "hd79_mount_store.h"')
patch("hd79_breath_travel_runtime.c", "    if (hd79_ensure_breath(player,now,&before)) {",
      '    rc=hd79_mount_precommit(player,destination);\n'
      '    if (rc) return rc==1 ? 0:-1;\n'
      "    if (hd79_ensure_breath(player,now,&before)) {")
patch("global.c", '#include "mextern.h"',
      '#include "mextern.h"\nextern int hd79_mount_command();')
# Reuse native callback registration, giving the four commands one dispatch group.
patch("global.c", '{ "look", 2, look },',
      '{ "mounts", 211, hd79_mount_command },\n'
      '    { "mount", 211, hd79_mount_command },\n'
      '    { "dismount", 211, hd79_mount_command },\n'
      '    { "stable", 211, hd79_mount_command },\n'
      '    { "look", 2, look },')
patch("command1.c", "\tj = strlen(str);", """    {
        char verb[21], tail[2];
        int tokens;
        if (sscanf(str,"%20s",verb)==1 &&
            (!strcmp(verb,"mount") || !strcmp(verb,"mounts") ||
             !strcmp(verb,"dismount") || !strcmp(verb,"stable"))) {
            memset(cmnd,0,sizeof *cmnd);
            tokens=sscanf(str,"%20s %20s %20s %1s",
                         cmnd->str[0],cmnd->str[1],cmnd->str[2],tail);
            cmnd->num=tokens;
            return;
        }
    }
\tj = strlen(str);""")
patch("Makefile", "OBJECTS += hd79_breath_travel_runtime.o",
      "OBJECTS += hd79_breath_travel_runtime.o hd79_mount_game.o")
# Read the terrain through the exact existing bounded native metadata parser.
wild = (source / "wilderness.c").read_text(encoding="latin-1")
start = wild.index("int hd79_wilderness_tile(int id)")
end = wild.index("\n#endif", start)
terrain = wild[start:end].replace("hd79_wilderness_tile", "hd79_wilderness_terrain")
terrain = terrain.replace("found=1;", "found=(unsigned char)tile.terrain;")
terrain = terrain.replace("return found ? 1:-1;", "return found ? found:-1;")
changes["wilderness.c"] = wild[:end] + "\n" + terrain + wild[end:]
shutil.copytree(source, target)
here = Path(__file__).resolve().parent
for name in ("hd79_mount_store.h", "hd79_mount_store.inc", "hd79_mount_game.c",
             "hd79_mount_roster.c", "hd79_mount_roster.h", "hd79_mount_wire.c",
             "hd79_mount_wire.h", "hd_mount_travel.c", "hd_mount_travel.h"):
    shutil.copyfile(here / name, target / name)
for name, text in changes.items():
    (target / name).write_text(text, encoding="latin-1")
