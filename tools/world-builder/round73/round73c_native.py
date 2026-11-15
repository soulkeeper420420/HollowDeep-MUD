"""Round 73C disposable gameplay: carry map -> locate clue; drop -> denial.

No treasure rewards, guardian kills or player-save changes are made here.
Executed only inside the existing Round 59–72 unshare/native replay harness.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import string
import zipfile

import app
from round71_wilderness import grid


def replay(stage, scope, check):
    token = lambda n: "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))
    owner = "Hd" + token(7)
    map_id = "map.0001"
    clue = "Beyond the cairn, seek the eastern shadow."
    root = stage / "mapped/rootfs"
    assert root.is_dir() and root.name == "rootfs"
    plan = grid(app.new_plan(14, 15), 14, 10001, 4, 4, "up", "Copperreach", seed=42)
    assert app.OBJECT_TEMPLATES.get(999) is None, "Use a nonoccupied test template ID"
    plan["custom_templates"] = {"objects": [{
        "id": 999, "base_id": 1, "name": "Treasure Map [map.0001]"
    }]}
    room = next(r for r in plan["rooms"] if r["room_id"] == 10001)
    room["objects"] = [{"id": 999, "count": 1, "respawn": 3600}]
    app.clean(plan)
    app.area.EXPORTS = stage / "exports"
    app.area.EXPORTS.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = app.area.generate(plan, persist=True)
    zpath = app.area.EXPORTS / (result["export_id"] + ".zip")
    check(hashlib.sha256(zpath.read_bytes()).hexdigest() == result["bundle_sha256"],
          "Round 73C native test map ZIP SHA-256")
    with zipfile.ZipFile(zpath) as archive:
        assert archive.testzip() is None
        meta = json.loads(archive.read("manifest.json"))
        for name in archive.namelist():
            if name.startswith("objmon/"):
                assert hashlib.sha256(archive.read(name)).hexdigest() == meta["template_banks"][name]
                dst = root / name
            elif name.startswith("rooms/"):
                dst = root / name
            elif name.endswith(".native-candidate") and name.startswith("r"):
                rid = int(name[1:6]); dst = root / "rooms" / f"r{rid:05d}"
                assert hashlib.sha256(archive.read(name)).hexdigest() == meta["rooms"][str(rid)]["candidate_sha256"]
            elif name == "manifest.json":
                continue
            else:
                raise AssertionError("Unexpected native ZIP entry: " + name)
            dst.write_bytes(archive.read(name))
            os.chown(dst, 65534, 65534)
            dst.chmod(0o600 if dst.name.startswith("r") else 0o644)
    # Fixture-only trusted clue grant: not populated by player or browser.
    clue_path = root / "rooms/treasure_locate.map"
    clue_path.write_text("HDLOC1\n" + owner + "\t" + map_id + "\t" + clue + "\n", encoding="ascii")
    clue_path.chmod(0o644)
    scope.update(root=root, PORT=4049, process=None, clients=[])
    scope["start_server"]()
    try:
        player = scope["new_character"](owner, "Test" + token(9))
        command = lambda text: scope["command"](player, text).lower()
        check("must carry" in command("locate"), "Native locate refuses without a carried map")
        check("goldenrod" in command("north"), "Native locate test enters old world")
        check("copperreach" in command("up"), "Native locate test enters wilderness")
        look = command("look")
        check("treasure map [map.0001]" in look, "Native test map physically spawned")
        check("must carry" in command("locate"), "Nearby map does not reveal clues")
        pickup = command("get hdo999")
        check("treasure map" in pickup or "treasure map" in command("inventory"),
              "Player picks up specific native map object")
        check("treasure map [map.0001]" in command("inventory"),
              "Map is carried in native inventory")
        check("seek the eastern shadow" in command("locate"),
              "Locate reveals matching held-map clue")
        check("seek the eastern shadow" in command("locate map.0001"),
              "Locate accepts matching held map ID")
        check("must carry" in command("locate map.other"),
              "Locate denies unheld map ID")
        # Wrong owner fails even if the physical map object is present.
        original = clue_path.read_text(encoding="ascii")
        clue_path.write_text("HDLOC1\nOtherPlayer\tmap.0001\t" + clue + "\n", encoding="ascii")
        check("cannot be deciphered" in command("locate"),
              "Locate denies clue belonging to another owner")
        clue_path.write_text(original, encoding="ascii")
        check("seek the eastern shadow" in command("locate"),
              "Locate recovers from changed sidecar without state mutation")
        dropped = command("drop hdo999")
        check("treasure map" in dropped or "treasure map" not in command("inventory"),
              "Physical map can be dropped")
        check("treasure map [map.0001]" not in command("inventory"),
              "Dropped map leaves native inventory")
        check("must carry" in command("locate"),
              "Locate denies clues after dropping the map")
    finally:
        for client in scope["clients"]:
            client.close()
        scope["stop_server"]()
    print("ROUND 73C: native held-map locate, lost-map denial and owner isolation PASS", flush=True)
