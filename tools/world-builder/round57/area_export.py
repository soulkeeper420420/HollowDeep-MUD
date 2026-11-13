import hashlib
import importlib.util
import io
import json
import re
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path("/root/hollowdeep-dev/world-forge")
ROOT = BASE / "round53-area-builder"
DB = ROOT / "areas.sqlite3"
EXPORTS = ROOT / "exports"

spec = importlib.util.spec_from_file_location(
    "r51_for_53", BASE / "round51-native/export.py"
)
r51 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r51)

r50 = r51.r50
INDEX = r50.INDEX
from entity_records import normalize_entities


def parse(data):
    return normalize_entities(r51.parse(data))

PAIRS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up"
}
LOCK = threading.RLock()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def init():
    with sqlite3.connect(DB) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id TEXT PRIMARY KEY,
                plan_json TEXT NOT NULL
            )
        """)

def valid_id(value):
    require(type(value) is int, "Room ID must be an integer")
    require(str(value) in INDEX, "Room not export-eligible")
    return value

def native_exits(rid):
    data, _ = r50.baseline(rid)
    records, _ = r51.original_exits(data)
    return [r51.fields(x) for x in records]

def clean_plan(plan):
    require(isinstance(plan, dict), "Invalid plan")
    rooms = plan.get("rooms")
    require(isinstance(rooms, list), "Invalid room list")
    require(2 <= len(rooms) <= 50, "Area must have 2–50 rooms")

    cleaned = {}
    for entry in rooms:
        require(isinstance(entry, dict), "Invalid room")
        rid = valid_id(entry.get("room_id"))
        require(rid not in cleaned, "Duplicate room ID")

        name = entry.get("name")
        require(isinstance(name, str), "Invalid room name")
        r51.encode_name(name, 80)

        exits = entry.get("exits")
        require(isinstance(exits, list), "Invalid exit list")
        require(len(exits) <= 20, "Too many exits")

        original = native_exits(rid)
        original_names = {x["direction"] for x in original}
        require(
            len(original_names) == len(original),
            "Duplicate original exit names"
        )

        normalized = []
        seen = set()

        for exit_entry in exits:
            require(isinstance(exit_entry, dict), "Invalid exit")
            require(
                set(exit_entry) == {"direction", "destination"},
                "Unsupported exit properties"
            )
            direction = exit_entry["direction"]
            destination = exit_entry["destination"]

            require(isinstance(direction, str), "Invalid exit direction")
            require(direction not in seen, "Duplicate exit direction")
            require(
                type(destination) is int
                and -32768 <= destination <= 32767,
                "Invalid native exit destination"
            )

            original_entry = next(
                (
                    old for old in original
                    if old["direction"] == direction
                ),
                None
            )

            if original_entry != exit_entry:
                require(direction in PAIRS, "New or redirected exits need a standard direction")
                require(
                    str(destination) in INDEX,
                    "New or redirected exit destination "
                    "is not export-eligible"
                )

            seen.add(direction)

            normalized.append({
                "direction": direction,
                "destination": destination
            })

        # Existing exits with nonstandard names must be preserved
        # unchanged. They cannot be represented as new standard exits.
        for old in original:
            if old["direction"] not in PAIRS:
                require(
                    old in normalized,
                    "Nonstandard original exit cannot be removed"
                )

        cleaned[rid] = {"room_id": rid, "name": name, "exits": normalized}

    # Every new or redirected exit between rooms in this plan
    # must have a matching reverse exit.
    for rid, room in cleaned.items():
        original = native_exits(rid)
        for e in room["exits"]:
            if e in original:
                continue
            dest = e["destination"]
            require(
                dest in cleaned,
                "New or redirected exits must target a room in this area"
            )
            reverse = PAIRS[e["direction"]]
            require(
                {"direction": reverse, "destination": rid}
                in cleaned[dest]["exits"],
                f"Missing reciprocal {reverse} exit in room {dest}"
            )

    return cleaned

def make_exit(direction, destination):
    # Restricted plain-exit template.
    # 20-byte name, int16 destination, remaining 22 bytes zero.
    name = direction.encode("ascii")
    require(len(name) < 20, "Exit name too long")
    return (
        name + bytes(20 - len(name))
        + struct.pack("<h", destination)
        + bytes(22)
    )

def build_room(rid, room):
    original, _ = r50.baseline(rid)
    before = parse(original)
    records, end = r51.original_exits(original)
    old = {r51.fields(record)["direction"]: record
           for record in records}

    require(len(old) == len(records), "Duplicate native exits")

    output = []
    for entry in room["exits"]:
        direction = entry["direction"]
        destination = entry["destination"]

        if direction in old:
            record = bytearray(old[direction])
            struct.pack_into("<h", record, 20, destination)
            output.append(bytes(record))
        else:
            output.append(make_exit(direction, destination))

    header = bytearray(original[:480])
    header[2:82] = r51.encode_name(room["name"], 80)

    descriptions = before["descriptions"].copy()
    for index, key in enumerate(("short_description", "long_description")):
        if key in room:
            descriptions[index] = room[key]
    description_bytes = b"".join(struct.pack("<i", len(value)) + value for value in descriptions)

    edited = (
        bytes(header)
        + struct.pack("<i", len(output))
        + b"".join(output)
        + original[end:before["desc_start"]]
        + description_bytes
    )

    with tempfile.TemporaryDirectory(prefix="round53-native-") as tmp:
        tmp = Path(tmp)
        input_path = tmp / "input"
        output_path = tmp / "output"
        input_path.write_bytes(edited)

        result = subprocess.run(
            [str(r51.HARNESS), str(input_path), str(output_path)],
            capture_output=True,
            text=True,
            timeout=15,
            preexec_fn=r51.restrict
        )
        require(
            result.returncode == 0,
            "Native serializer failed: " + result.stderr[-300:]
        )
        candidate = output_path.read_bytes()

    after = parse(candidate)
    actual_records, _ = r51.original_exits(candidate)

    checks = {
        "room_id": after["id"] == before["id"] == rid,
        "name": (
            after["name"].split(b"\x00", 1)[0]
            == room["name"].encode("utf-8", "surrogateescape")
        ),
        "exits": actual_records == output,
        "creatures": after["creatures"] == before["creatures"],
        "objects": after["objects"] == before["objects"],
        "descriptions": after["descriptions"] == descriptions,
    }
    require(all(checks.values()), "Native validation failed: " +
            ",".join(k for k, ok in checks.items() if not ok))

    return candidate, checks

def generate(plan, persist=True):
    rooms = clean_plan(plan)
    outputs = {}
    reports = {}

    for rid, room in sorted(rooms.items()):
        candidate, checks = build_room(rid, room)
        filename = f"r{rid:05d}.native-candidate"
        outputs[filename] = candidate
        reports[str(rid)] = {
            "source_sha256": INDEX[str(rid)],
            "candidate_sha256": sha(candidate),
            "checks": checks
        }

    manifest = {
        "round": 54,
        "room_count": len(rooms),
        "rooms": reports,
        "production_deployment": False,
        "gameplay_validation": False
    }

    with io.BytesIO() as stream:
        with zipfile.ZipFile(
            stream, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for filename, data in sorted(outputs.items()):
                archive.writestr(filename, data)
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, indent=2) + "\n"
            )
        bundle = stream.getvalue()

    bundle_sha = sha(bundle)
    export_id = bundle_sha[:24]

    if persist:
        path = EXPORTS / f"{export_id}.zip"
        with LOCK:
            if path.exists():
                require(
                    not path.is_symlink()
                    and sha(path.read_bytes()) == bundle_sha,
                    "Existing export mismatch"
                )
            else:
                with path.open("xb") as f:
                    f.write(bundle)
                path.chmod(0o600)

    return {
        "passed": True,
        "export_id": export_id,
        "bundle_sha256": bundle_sha,
        "rooms": reports,
        "download": "/api/download?id=" + export_id,
        "production_deployment": False
    }

def new_plan(a, b):
    a = valid_id(a)
    b = valid_id(b)
    require(a != b, "Rooms must differ")

    rooms = []
    for rid in (a, b):
        draft = r50.current(rid)
        rooms.append({
            "room_id": rid,
            "name": draft["name"],
            "exits": draft["exits"]
        })

    return {"rooms": rooms}

def link(plan, a, b, direction):
    require(direction in PAIRS, "Invalid direction")
    a = valid_id(a)
    b = valid_id(b)
    require(a != b, "Cannot link a room to itself")

    rooms = {
        room["room_id"]: room
        for room in plan["rooms"]
    }
    require(a in rooms and b in rooms, "Both rooms must be in area")

    for rid, name, dest in (
        (a, direction, b),
        (b, PAIRS[direction], a)
    ):
        exits = rooms[rid]["exits"]
        existing = next(
            (e for e in exits if e["direction"] == name), None
        )
        if existing:
            require(
                existing["destination"] == dest,
                f"Room {rid} already has conflicting {name} exit"
            )
        else:
            exits.append({
                "direction": name,
                "destination": dest
            })

    clean_plan(plan)
    return plan

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>HollowDeep Round 53 Area Builder</title>
<style>
body{background:#111827;color:#fff;font:16px system-ui;
max-width:950px;margin:25px auto;padding:20px}
input,textarea,button{font:inherit;padding:9px;margin:4px;
border-radius:6px}
textarea{width:100%;min-height:400px;box-sizing:border-box;
background:#1f2937;color:white}
button{background:#2563eb;color:white;border:0}
pre{white-space:pre-wrap;overflow-wrap:anywhere}
a{color:#93c5fd}
</style></head><body>
<h1>HollowDeep Round 53 — Area Builder</h1>
<p>Isolated multi-room native export. No production deployment.</p>
<p>Room A <input id="a" type="number" value="14">
Room B <input id="b" type="number" value="15"></p>
<button onclick="create()">Load Two-Room Area</button>
<p>Link direction from A to B
<select id="direction">
<option>north</option><option>south</option>
<option>east</option><option>west</option>
<option>up</option><option>down</option>
</select>
<button onclick="connect()">Create Two-Way Link</button></p>
<p>Area plan (JSON)</p>
<textarea id="plan"></textarea>
<p><button onclick="generate()">Validate and Export Area</button></p>
<pre id="status"></pre><div id="download"></div>
<script>
const el=id=>document.getElementById(id);
async function api(path,data){
 const options=data===undefined?{}:{
  method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify(data)
 };
 const r=await fetch(path,options);
 const j=await r.json();
 if(!r.ok)throw Error(j.error||"Request failed");
 return j;
}
async function create(){
 try{
  const p=await api("/api/new?a="+el("a").value+
                    "&b="+el("b").value);
  el("plan").value=JSON.stringify(p,null,2);
  el("status").textContent="Area loaded";
 }catch(e){el("status").textContent=e.message}
}
async function connect(){
 try{
  const p=await api("/api/link",{
   plan:JSON.parse(el("plan").value),
   a:Number(el("a").value),b:Number(el("b").value),
   direction:el("direction").value
  });
  el("plan").value=JSON.stringify(p,null,2);
  el("status").textContent="Bidirectional link created";
 }catch(e){el("status").textContent=e.message}
}
async function generate(){
 try{
  const r=await api("/api/export",JSON.parse(el("plan").value));
  el("status").textContent=JSON.stringify(r,null,2);
  const link=document.createElement("a");
  link.href=r.download;
  link.textContent="Download verified area ZIP";
  el("download").replaceChildren(link);
 }catch(e){el("status").textContent=e.message}
}
create();
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            url = urlparse(self.path)
            q = parse_qs(url.query)

            if url.path == "/":
                body = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif url.path == "/api/new":
                self.reply(200, new_plan(
                    int(q["a"][0]), int(q["b"][0])
                ))
            elif url.path == "/api/download":
                eid = q["id"][0]
                require(
                    re.fullmatch("[0-9a-f]{24}", eid),
                    "Invalid export ID"
                )
                path = EXPORTS / (eid + ".zip")
                require(
                    path.is_file() and not path.is_symlink(),
                    "Export not found"
                )
                data = path.read_bytes()
                require(
                    sha(data).startswith(eid),
                    "Export checksum mismatch"
                )
                self.send_response(200)
                self.send_header(
                    "Content-Type", "application/zip"
                )
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="hollowdeep-area-{eid}.zip"'
                )
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.reply(404, {"error": "Not found"})
        except (ValueError, KeyError, TypeError) as e:
            self.reply(400, {"error": str(e)})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            require(0 < length <= 262144, "Invalid request size")
            payload = json.loads(self.rfile.read(length))

            if self.path == "/api/link":
                result = link(
                    payload["plan"],
                    payload["a"],
                    payload["b"],
                    payload["direction"]
                )
            elif self.path == "/api/export":
                result = generate(payload)
            else:
                self.reply(404, {"error": "Not found"})
                return
            self.reply(200, result)
        except (ValueError, KeyError, TypeError) as e:
            self.reply(400, {"error": str(e)})

def test():
    print("=== ROUND 53 ISOLATED ACCEPTANCE ===")
    pairs = [(14, 15), (3, 4), (16, 17)]
    passed = 0

    for a, b in pairs:
        plan = new_plan(a, b)
        directions_a = {
            e["direction"] for e in plan["rooms"][0]["exits"]
        }
        directions_b = {
            e["direction"] for e in plan["rooms"][1]["exits"]
        }

        direction = next(
            (
                d for d, reverse in PAIRS.items()
                if d not in directions_a
                and reverse not in directions_b
            ),
            None
        )
        require(
            direction is not None,
            f"No available reciprocal directions for {a}/{b}"
        )

        linked = link(plan, a, b, direction)
        result = generate(linked, persist=False)
        require(result["passed"], "Area export failed")
        require(len(result["rooms"]) == 2, "Missing room candidate")

        print(f"PASS: {a} <-> {b} via {direction}")
        passed += 1

    print(f"PASS: {passed} reciprocal area exports")
    print("PASS: Native serialization and integrity checks")
    print("Production files: UNCHANGED")
    print("Existing drafts: UNCHANGED")
    print("Live MUD restart: NONE")

if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        init()
        ThreadingHTTPServer(
            ("127.0.0.1", 8781), Handler
        ).serve_forever()
