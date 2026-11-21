"""Verify the exported coordinate sidecar in the actual isolated game."""
import hashlib
import json
import os
import secrets
import string
import zipfile


def replay(stage, scope, check):
    root = stage / "mapped/rootfs"
    with zipfile.ZipFile(stage / "round72-browser.zip") as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read("manifest.json"))
        sidecar = archive.read("rooms/wilderness.map")
        assert hashlib.sha256(sidecar).hexdigest() == manifest["wilderness_map_sha256"]
        assert b"10001\t1\t1\t#\tCopperreach\tCopper Cairn\n" in sidecar
        (root / "rooms/wilderness.map").write_bytes(sidecar)
        (root / "rooms/wilderness.map").chmod(0o644)
        for rid, report in manifest["rooms"].items():
            name = f"r{int(rid):05d}"
            data = archive.read(name + ".native-candidate")
            assert hashlib.sha256(data).hexdigest() == report["candidate_sha256"]
            target = root / "rooms" / name
            target.write_bytes(data)
            os.chown(target, 65534, 65534)
            target.chmod(0o600)
    scope.update(root=root, PORT=4048, process=None, clients=[])
    scope["start_server"]()
    try:
        def token(size):
            return "".join(secrets.choice(string.ascii_lowercase) for _ in range(size))
        player = scope["new_character"]("Hd" + token(7), "Test" + token(9))
        command = lambda text: scope["command"](player, text).lower()
        check("no wilderness map" in command("map"), "Map handles an unmapped location")
        command("north")
        check("copperreach 1,1" in command("up"), "Native entry reaches mapped wilderness")
        check("\x1b[" not in command("map"), "Wilderness map defaults to plain ASCII")
        check("color ansi mode on" in command("set ansi"), "Player enables native ANSI")
        check("\x1b[33m=\x1b[0m" in command("map"), "Native ANSI colors road tiles")
        first = command("map")
        check(all(s in first for s in ("copperreach (column 1, row 1)", "@", "unscouted",
                                       "landmark: copper cairn", "forest")),
              "Native map shows location, legend, unknown tiles and landmark")
        check("copperreach 1,2" in command("east"), "Native east movement reaches second tile")
        check("column 2, row 1" in command("map"), "Native map tracks east movement")
        check("copperreach 1,1" in command("west"), "Native west movement returns to entry")
        check("column 1, row 1" in command("map"), "Native map tracks return movement")
        check("goldenrod avenue" in command("down"), "Native exit returns to old world")
    finally:
        for client in scope["clients"]:
            client.close()
        scope["stop_server"]()
    print("ROUND 72: browser-exported terrain and native map navigation PASS", flush=True)
