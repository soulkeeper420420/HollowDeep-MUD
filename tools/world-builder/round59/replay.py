"""Exercise Round 57 ZIP exports with the Round 58Y native engine."""
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import string
import struct
import sys
import threading
import time
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer

stage = Path(sys.argv[1]).resolve(strict=True)
if stage.parent != Path("/root/hollowdeep-dev/world-forge") or not stage.name.startswith("round59-"):
    raise SystemExit("Expected a fresh Round 59 rehearsal directory")
sys.path.insert(0, str(stage / "builder"))
import app
import round55_http
import round57_http

runner = Path(sys.argv[2])
allowed = {"verify", "private_loopback", "restricted", "start_server", "stop_server", "connect",
           "receive", "send", "in_game", "new_character", "command", "existing_character"}
tree = ast.parse(runner.read_text())
tree.body = [node for node in tree.body
             if isinstance(node, (ast.Import, ast.ImportFrom))
             or isinstance(node, ast.FunctionDef) and node.name in allowed]
for function in tree.body:
    if isinstance(function, ast.FunctionDef) and function.name == "start_server":
        for node in ast.walk(function):
            if isinstance(node, ast.List):
                for index, item in enumerate(node.elts):
                    if isinstance(item, ast.Constant) and item.value == "/bin/hollowdeep":
                        node.elts[index:index] = [ast.copy_location(ast.Constant(value), item)
                                                 for value in ("/lib/ld-linux.so.2", "--preload",
                                                               "/bin/replay-rng.so")]
                        break
scope = {"__name__": "round59", "PORT": 4041, "process": None, "clients": [],
         "passed": 0, "failed": 0}
exec(compile(tree, str(runner), "exec"), scope)


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    print("PASS:", label, flush=True)


def request(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}), timeout=40) as response:
        return response.read()


def add_inventory_fixture():
    # Use native template records with one carried object, serialized using the
    # exact sizes and count boundaries already validated by Round 57.
    rid = 16
    baseline = app.area.r50.baseline
    data, _ = baseline(rid)
    _, offset = app.area.r51.original_exits(data)
    before = app.area.parse(data)
    assert before["creatures_count"] == 0
    monster_size = app.ABI["creature"]
    object_size = json.loads((app.ROOT / "object_layout.json").read_text())[2]
    monster = (app.ROOT / "templates/m00").read_bytes()[monster_size:2 * monster_size]
    obj = (app.ROOT / "templates/o00").read_bytes()[object_size:2 * object_size]
    assert len(monster) == monster_size and len(obj) == object_size
    fixture = (data[:offset] + struct.pack("<i", 1) + monster + struct.pack("<i", 1)
               + obj + struct.pack("<i", 0) + data[offset + 4:])
    parsed = app.area.parse(fixture)
    assert parsed["creatures_count"] == 1 and len(parsed["creatures"]) > monster_size + 4
    app.area.INDEX[str(rid)] = hashlib.sha256(fixture).hexdigest()
    app.area.r50.baseline = lambda room: (fixture, parsed) if int(room) == rid else baseline(room)
    return parsed


def install(url, plan, root, label, fixture, redirects=None):
    result = json.loads(request(url + "/api/export", plan))
    bundle = request(url + result["download"])
    digest = hashlib.sha256(bundle).hexdigest()
    check(digest == result["bundle_sha256"], f"{label} ZIP checksum {digest}")
    (stage / f"{label}.zip").write_bytes(bundle)
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read("manifest.json"))
        expected = {"manifest.json", *(f"r{rid:05d}.native-candidate" for rid in (14, 15, 16))}
        assert len(archive.namelist()) == len(expected) and set(archive.namelist()) == expected
        for entry in plan["rooms"]:
            rid = entry["room_id"]
            data = archive.read(f"r{rid:05d}.native-candidate")
            report = manifest["rooms"][str(rid)]
            assert hashlib.sha256(data).hexdigest() == report["candidate_sha256"]
            assert all(report["checks"].values())
            original, _ = app.area.r50.baseline(rid)
            old, _ = app.area.r51.original_exits(original)
            new, _ = app.area.r51.original_exits(data)
            if redirects and rid in redirects:
                direction, destination = redirects[rid]
                old = [record[:20] + struct.pack("<h", destination) + record[22:]
                       if app.area.r51.fields(record)["direction"] == direction else record
                       for record in old]
            assert all(record in new for record in old)
            if rid == 16:
                assert app.area.parse(data)["creatures"] == fixture["creatures"]
            target = root / "rooms" / f"r{rid:05d}"
            target.write_bytes(data)
            shutil.copystat(root / "rooms/r00001", target)
            os.chown(target, 65534, 65534)
    check(True, f"{label} preserves unrelated exit bytes and the existing creature with carried inventory")


def gameplay(root, port, populated):
    scope.update(root=root, PORT=port, process=None, clients=[])
    scope["start_server"]()
    try:
        token = lambda n: "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))
        player = scope["new_character"]("Hd" + token(7), "Test" + token(9))

        def command(text):
            response = scope["command"](player, text)
            print(f"> {text}\n{response[:900]}", flush=True)
            return response.lower()

        def defeat_golem():
            roll = root / "hollowdeep-data/round11q-rng"
            roll.write_text("199")
            roll.chmod(0o644)
            try:
                for _ in range(20):
                    hit = command("attack boss")
                    if "you killed the boss practice golem" in hit:
                        return hit
                    time.sleep(3)
            finally:
                roll.unlink()
            raise AssertionError("No explicit native kill message")

        arrival = command("north")
        assert "round 59 forge" in arrival
        look = command("look")
        check("round 59 forge" in look and "the forge bell rings softly." in look,
              "Builder description displays in the native room")
        if not populated:
            check("practice golem" not in look and "practice blade" not in look,
                  "Fresh native world omits both removed placements")
            check("round 59 redirect landing" in command("west"),
                  "Redirected west exit reaches room 16 from room 14")
            check("round 59 forge" in command("east"),
                  "Redirected east exit returns to room 14 from room 16")
            return
        check("boss practice golem" in look and "practice blade" in look,
              "Both exported placements appear")
        pickup = command("get all")
        check("you get a practice blade" in pickup and "practice blade" in command("inventory"),
              "Native pickup transfers exported object into inventory")
        defeat_golem()
        check(True, "Explicit monster defeat")
        look = command("look")
        check("round 59 forge" in look and "practice golem" not in look, "Defeated spawn is absent in the same room")
        check("round 59 gallery" in command("north"), "New reciprocal north exit reaches room 15")
        time.sleep(65)
        revisit = command("south")
        check("round 59 forge" in revisit, "New reciprocal south exit returns to room 14")
        check("boss practice golem" in revisit or "boss practice golem" in command("look"),
              "Native monster respawns after the interval and room revisit")
        check("round 59 gallery" in command("east"), "Original east exit still reaches room 15")
        destination = command("east")
        check("goldenrod avenue" in destination and "boss practice golem" in destination,
              "Original route reaches the embedded creature in room 16")
        defeat = defeat_golem()
        check("practice blade" in defeat and "carrying" in defeat,
              "Defeated embedded creature drops its serialized carried blade")
        check(any("you get" in line and "practice blade" in line
                  for line in command("get all").splitlines()),
              "Player picks up the preserved carried blade")
    finally:
        for client in scope["clients"]:
            client.close()
        scope["stop_server"]()


scope["private_loopback"]()
app.area.EXPORTS.mkdir(mode=0o700, exist_ok=True)
server = ThreadingHTTPServer(("127.0.0.1", 0), round57_http.Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    url = f"http://127.0.0.1:{server.server_port}"
    fixture = add_inventory_fixture()
    plan = json.loads(request(url + "/api/new?a=14&b=15"))
    plan = json.loads(request(url + "/api/add-room", {"plan": plan, "room_id": 16}))
    plan = json.loads(request(url + "/api/link", {"plan": plan, "a": 14, "b": 15, "direction": "north"}))
    forge, gallery = plan["rooms"][:2]
    forge.update(name="Round 59 Forge", short_description="The forge bell rings softly.",
                 long_description="A quiet anvil marks the isolated forge.",
                 monsters=[{"id": 1, "count": 1, "respawn": 60}],
                 objects=[{"id": 1, "count": 1, "respawn": 60}])
    gallery.update(name="Round 59 Gallery")
    check(json.loads(request(url + "/api/validate", plan))["passed"], "Builder validates complete plan")
    install(url, plan, stage / "populated/rootfs", "populated", fixture)
    cleared = copy.deepcopy(plan)
    cleared["rooms"][0].update(monsters=[], objects=[])
    redirects = {14: ("west", 16), 16: ("east", 14)}
    for room in cleared["rooms"]:
        if room["room_id"] in redirects:
            direction, destination = redirects[room["room_id"]]
            next(entry for entry in room["exits"] if entry["direction"] == direction)["destination"] = destination
        if room["room_id"] == 16:
            room["name"] = "Round 59 Redirect Landing"
    install(url, cleared, stage / "cleared/rootfs", "redirected", fixture, redirects)
finally:
    server.shutdown()
    server.server_close()
    thread.join()

gameplay(stage / "populated/rootfs", 4041, True)
gameplay(stage / "cleared/rootfs", 4042, False)
print("ROUND 59: PASS", flush=True)
