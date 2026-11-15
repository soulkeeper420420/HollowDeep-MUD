"""Round 73E native mapradius replay, using isolated world only."""
from pathlib import Path
import secrets
import string


def replay(stage, scope, check):
    root = stage / "mapped/rootfs"
    assert root.name == "rootfs" and (root / "rooms/wilderness.map").is_file()
    # Round 73C/D tests reuse the mapped root. Reestablish a *known-good*
    # browser-exported map/room fixture before testing the independent radius
    # feature, rather than assuming earlier encounters did not modify it.
    # Both the sidecar and native candidate room bytes are hash-verified.
    import hashlib
    import json
    import os
    import zipfile
    verified_zip = stage / "round72-browser.zip"
    with zipfile.ZipFile(verified_zip) as zf:
        assert zf.testzip() is None, "Corrupt Round 72 browser ZIP"
        manifest = json.loads(zf.read("manifest.json"))
        sidecar = zf.read("rooms/wilderness.map")
        assert hashlib.sha256(sidecar).hexdigest() == manifest["wilderness_map_sha256"]
        assert sidecar.startswith(b"HDW1\n") and b"10001\t" in sidecar
        assert "10001" in manifest["rooms"]
        for rid, entry in manifest["rooms"].items():
            if int(rid) < 10000:
                continue
            raw = zf.read(f"r{int(rid):05d}.native-candidate")
            assert hashlib.sha256(raw).hexdigest() == entry["candidate_sha256"]
            target = root / "rooms" / f"r{int(rid):05d}"
            assert target.is_file() and not target.is_symlink()
            target.write_bytes(raw)
            os.chown(target, 65534, 65534)
            target.chmod(0o600)
    target = root / "rooms/wilderness.map"
    assert target.is_file() and not target.is_symlink()
    target.write_bytes(sidecar)
    os.chown(target, 65534, 65534)
    target.chmod(0o644)
    print("PASS: Round 73E restored checksum-verified Round 72 native map fixture", flush=True)
    scope.update(root=root, PORT=4051, process=None, clients=[])
    scope["start_server"]()
    try:
        token = lambda n: "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))
        player = scope["new_character"]("Hd" + token(7), "Test" + token(9))
        command = lambda message: scope["command"](player, message).lower()

        def map_rows(result):
            # HollowDeep emits LF+CR ("\n\r"), not only CRLF or LF.
            # splitlines() counts LF and CR separately, doubling map rows.
            # Normalize each native newline pair to one separator but DO NOT
            # discard empty rows: edge-of-region tiles render as blank rows.
            normalized = (result.replace("\r\n", "\n")
                                .replace("\n\r", "\n")
                                .replace("\r", "\n"))
            lines = normalized.split("\n")
            north = next((i for i, line in enumerate(lines)
                          if line.strip().lower() == "n"), None)
            south = (next((i for i in range(north + 1, len(lines))
                           if lines[i].strip().lower() == "s"), None)
                     if north is not None else None)
            if north is None or south is None:
                print("ROUND 73E MAP ROWS: absent compass marker:",
                      repr(result[:1800]), flush=True)
                return -1
            return south - north - 1

        check("map radius is 3" in command("mapradius"),
              "Native mapradius preserves Round 72 default radius")
        check("goldenrod avenue" in command("north"),
              "Mapradius native replay enters old-world route")
        check("copperreach" in command("up"),
              "Mapradius native replay enters wilderness")
        baseline = command("map")
        check(map_rows(baseline) == 7 and "@" in baseline,
              "Default 7x7 wilderness map still renders")
        check("map radius set to 1" in command("mapradius 1"),
              "Mapradius accepts radius 1")
        check(map_rows(command("map")) == 3,
              "Native mapradius 1 renders 3x3")
        check("map radius set to 10" in command("mapradius 10"),
              "Mapradius accepts maximum radius 10")
        wide = command("map")
        check(map_rows(wide) == 21 and "unscouted" in wide,
              "Maximum radius renders 21x21 without revealing fog")
        for invalid in ("11", "-1", "01", "99"):
            check("use mapradius 0 through 10" in command("mapradius " + invalid),
                  "Invalid radius rejected: " + invalid)
        check("map radius is 10" in command("mapradius"),
              "Invalid radius does not change stored setting")
        check("map radius set to 0" in command("mapradius 0"),
              "Mapradius 0 disables the map")
        check("map is off" in command("map"),
              "Native map suppresses terrain when disabled")
        check("map radius set to 3" in command("mapradius 3"),
              "Default radius can be restored")
        check("column 2, row 1" in command("east") + command("map"),
              "Native map tracks movement with customized radius")
    finally:
        for client in scope["clients"]:
            client.close()
        scope["stop_server"]()
    print("ROUND 73E: native mapradius 0-10 and map navigation PASS", flush=True)
