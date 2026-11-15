"""Round 73D isolated actual-native chest guard replay, no native reward grants."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import string
import time
import zipfile

import app
from round71_wilderness import grid


def replay(stage, scope, check):
    token = lambda n: "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))
    owner = "Hd" + token(7)
    map_id = "map.0001"
    room_id = 10001
    name = "Round 73 Treasure Guardian"
    clue = "Beyond the cairn, seek the eastern shadow."
    root = stage / "mapped/rootfs"
    assert root.name == "rootfs" and root.is_dir()
    assert 999 not in app.TEMPLATES and 999 not in app.OBJECT_TEMPLATES
    plan = grid(app.new_plan(14, 15), 14, room_id, 4, 4, "up", "Copperreach", seed=42)
    plan["custom_templates"] = {
        "objects": [{"id": 999, "base_id": 1, "name": "Treasure Map [map.0001]"}],
        "monsters": [{"id": 999, "base_id": 1, "name": name}],
    }
    room = next(r for r in plan["rooms"] if r["room_id"] == room_id)
    room["objects"] = [{"id": 999, "count": 1, "respawn": 3600}]
    room["monsters"] = [{"id": 999, "count": 1, "respawn": 60}]
    plan["treasure_sites"] = [{"site_id": "copper-cache", "room_id": room_id,
        "guardians": [999], "chest_label": "Copperbound Chest", "tier": "rare", "clue": clue}]
    app.clean(plan)
    app.area.EXPORTS = stage / "exports"
    app.area.EXPORTS.mkdir(parents=True, mode=0o700, exist_ok=True)
    output = app.area.generate(plan, persist=True)
    bundle = (app.area.EXPORTS / (output["export_id"] + ".zip")).read_bytes()
    check(hashlib.sha256(bundle).hexdigest() == output["bundle_sha256"],
          "Round 73D complete treasure-site ZIP checksum")
    with zipfile.ZipFile(__import__("io").BytesIO(bundle)) as archive:
        assert archive.testzip() is None
        meta = json.loads(archive.read("manifest.json"))
        assert "rooms/treasure_sites.json" in archive.namelist()
        assert hashlib.sha256(archive.read("rooms/treasure_sites.json")).hexdigest() == meta["treasure_sites_sha256"]
        for label in archive.namelist():
            if label.startswith("objmon/"):
                assert hashlib.sha256(archive.read(label)).hexdigest() == meta["template_banks"][label]
                dest = root / label
            elif label.startswith("rooms/"):
                dest = root / label
            elif label.startswith("r") and label.endswith(".native-candidate"):
                rid = int(label[1:6]); dest = root / "rooms" / f"r{rid:05d}"
                assert hashlib.sha256(archive.read(label)).hexdigest() == meta["rooms"][str(rid)]["candidate_sha256"]
            elif label == "manifest.json":
                continue
            else:
                raise AssertionError("Unrecognized native ZIP file: " + label)
            dest.write_bytes(archive.read(label))
            os.chown(dest, 65534, 65534)
            dest.chmod(0o600 if dest.name.startswith("r") else 0o644)
    # Private server-authored fixture, not a player-controlled web or CLI command.
    location = root / "rooms/treasure_locate.map"
    location.write_text("HDLOC1\n" + owner + "\t" + map_id + "\t" + clue + "\n", encoding="ascii")
    location.chmod(0o644)
    guards = root / "rooms/treasure_guardians.map"
    guards.write_text("HDGUARD1\n" + str(room_id) + "\t" + map_id + "\t" + name + "\n", encoding="ascii")
    guards.chmod(0o644)
    scope.update(root=root, PORT=4050, process=None, clients=[])
    scope["start_server"]()
    try:
        player = scope["new_character"](owner, "Test" + token(9))
        command = lambda message: scope["command"](player, message).lower()
        check("must carry" in command("open chest") or "don't see" in command("open chest"),
              "Native treasure chest denies opening without map")
        check("goldenrod avenue" in command("north"), "Round 73D starts on native old-world route")
        check("copperreach" in command("up"), "Round 73D enters native wilderness")
        look = command("look")
        check("round 73 treasure guardian" in look and "treasure map [map.0001]" in look,
              "Native guardian and physically pickupable map spawn at authored site")
        check("must carry" in command("open chest"), "Chest refuses noncarried map in its room")
        check("treasure map" in command("get hdo999") or "treasure map" in command("inventory"),
              "Player takes the true native map item")
        check("seek the eastern shadow" in command("locate"), "Read-only locate remains functional")
        opening = command("open chest")
        check("magically locked" in opening and "guardian" in opening,
              "Opening chest binds a living guardian and locks virtual chest")
        check("magically locked" in command("open chest"),
              "Unkilled guardian cannot be bypassed by reopening")
        check("treasure" not in command("inventory").replace("treasure map", ""),
              "Virtual chest is not a pickupable inventory object")
        check("chest" not in command("get chest") or "don't" in command("get chest"),
              "Native get cannot extract virtual treasure chest")
        rng = root / "hollowdeep-data/round11q-rng"
        rng.write_text("199"); rng.chmod(0o644)
        try:
            killed = False
            for _ in range(20):
                msg = command("attack hdm999")
                if "you killed" in msg and "guardian" in msg:
                    killed = True
                    break
                time.sleep(3)
            check(killed, "Owner personally defeats actual bound native guardian")
        finally:
            rng.unlink(missing_ok=True)
        check("round 73 treasure guardian" not in command("look"),
              "Guardian absent from native room after combat")
        unlocked = command("open chest")
        check("seals dissolve" in unlocked and "reward delivery is disabled" in unlocked,
              "Only trusted native guardian death unlocks virtual no-reward chest")
        check("reward delivery is disabled" in command("open chest"),
              "Repeat open cannot mint any treasure rewards")
        dropped = command("drop hdo999")
        check("treasure map" in dropped or "treasure map" not in command("inventory"),
              "Owner can physically drop map after guardian defeat")
        check("must carry" in command("open chest"),
              "Dropping map removes access even after guardian defeated")
        check("must carry" in command("locate"),
              "Locate continues denying dropped maps")
    finally:
        for client in scope["clients"]:
            client.close()
        scope["stop_server"]()
    print("ROUND 73D: native guardian-bound virtual chest, dropped-map denial, no rewards PASS", flush=True)
