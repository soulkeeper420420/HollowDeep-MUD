"""Round 54 permanent monster placements over the existing area exporter."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("round53", ROOT.parent / "round53-area-builder/app.py")
area = importlib.util.module_from_spec(spec)
spec.loader.exec_module(area)
area.ROOT = ROOT
area.DB = ROOT / "areas.sqlite3"
area.EXPORTS = ROOT / "exports"
ABI = json.loads((ROOT / "layout.json").read_text())
if (ABI["header"], ABI["exits"]) != (480, 44):
    raise RuntimeError("Native room ABI differs from Round 53")


def catalog():
    templates = {}
    for group in range((ABI["maximum"] - 1) // ABI["per_file"] + 1):
        path = ROOT / "templates" / f"m{group:02d}"
        if not path.is_file():
            continue
        data = path.read_bytes()
        size = ABI["creature"]
        for index in range(min(len(data) // size, ABI["per_file"])):
            identifier = group * ABI["per_file"] + index
            record = data[index * size:(index + 1) * size]
            name = record[ABI["name"]:ABI["name"] + ABI["name_size"]].split(b"\0", 1)[0]
            if 0 < identifier < ABI["maximum"] and name and record[ABI["type"]] == ABI["monster"]:
                templates[identifier] = name.decode("utf-8", "replace")
    return templates


TEMPLATES = catalog()
clean_original, build_original = area.clean_plan, area.build_room
new_original = area.new_plan


def existing(data):
    groups = {}
    for index in range(ABI["slots"]):
        offset = ABI["table"] + index * ABI["slot"]
        identifier, = struct.unpack_from("<h", data, offset + ABI["id"])
        if identifier:
            interval, = struct.unpack_from("<i", data, offset + ABI["interval"])
            groups.setdefault((identifier, interval), []).append(data[offset:offset + ABI["slot"]])
    return groups


def new_plan(a, b):
    plan = new_original(a, b)
    for room in plan["rooms"]:
        data, _ = area.r50.baseline(room["room_id"])
        room["monsters"] = [{"id": identifier, "respawn": seconds, "count": len(slots)}
                            for (identifier, seconds), slots in existing(data).items()]
    return plan


def placements(value):
    area.require(isinstance(value, list) and len(value) <= ABI["slots"], "Invalid placement list")
    ids = set()
    used = 0
    for entry in value:
        area.require(isinstance(entry, dict) and set(entry) == {"id", "count", "respawn"},
                     "Unsupported placement fields")
        monster, count, interval = (entry[k] for k in ("id", "count", "respawn"))
        area.require(all(type(v) is int for v in (monster, count, interval)), "Expected integer placement fields")
        area.require(monster in TEMPLATES and monster not in ids, "Unknown or duplicate monster template")
        area.require(1 <= count <= ABI["slots"] and 1 <= interval <= 86400,
                     "Count or respawn seconds out of range")
        used += count
        ids.add(monster)
    area.require(used <= ABI["slots"], "Permanent spawn table is full")
    return value


def clean(plan):
    rooms = clean_original(plan)
    for entry in plan["rooms"]:
        if "monsters" in entry:
            rid = area.valid_id(entry["room_id"])
            baseline = new_plan_monsters(rid)
            if entry["monsters"] != baseline:
                rooms[rid]["monsters"] = placements(entry["monsters"])
    return rooms


def new_plan_monsters(rid):
    data, _ = area.r50.baseline(rid)
    return [{"id": identifier, "respawn": seconds, "count": len(slots)}
            for (identifier, seconds), slots in existing(data).items()]


def build(rid, room):
    original, checks = build_original(rid, room)
    if "monsters" not in room:
        return original, checks
    start = ABI["table"]
    end = start + ABI["slots"] * ABI["slot"]
    area.require(0 <= start < end <= ABI["header"], "Invalid spawn table extent")
    edited = bytearray(original)
    edited[start:end] = bytes(end - start)
    offset = start
    previous = existing(original)
    for entry in room["monsters"]:
        preserved = previous.get((entry["id"], entry["respawn"]), ())
        for index in range(entry["count"]):
            if index < len(preserved):
                edited[offset:offset + ABI["slot"]] = preserved[index]
            else:
                struct.pack_into("<i", edited, offset + ABI["interval"], entry["respawn"])
                struct.pack_into("<h", edited, offset + ABI["id"], entry["id"])
            offset += ABI["slot"]
    with tempfile.TemporaryDirectory(prefix="round54-native-") as tmp:
        source, output = Path(tmp) / "input", Path(tmp) / "output"
        source.write_bytes(edited)
        result = subprocess.run([str(area.r51.HARNESS), str(source), str(output)],
                                capture_output=True, timeout=15, preexec_fn=area.r51.restrict)
        area.require(result.returncode == 0, "Native spawn round trip failed")
        candidate = output.read_bytes()
    before, after = area.parse(original), area.parse(candidate)
    area.require(candidate[start:end] == edited[start:end] and
                 area.r51.original_exits(candidate) == area.r51.original_exits(original) and
                 all(before[key] == after[key] for key in
                     ("id", "name", "creatures", "objects", "descriptions")),
                 "Native round trip changed spawn or unrelated room records")
    checks["permanent_monster_slots"] = True
    return candidate, checks


area.clean_plan = clean
area.build_room = build
area.new_plan = new_plan
area.PAGE = area.PAGE.replace("Round 53", "Round 54").replace(
    "<p>Area plan (JSON)</p>", """<fieldset><legend>Permanent monster placements</legend>
<label>Room <input id="spawn-room" type="number" value="14"></label>
<label>Template <select id="monster"></select></label>
<label>Count <input id="spawn-count" type="number" min="1" max="10" value="1"></label>
<label>Respawn seconds <input id="respawn" type="number" min="1" max="86400" value="60"></label>
<button onclick="placement(false)">Set placement</button>
<button onclick="placement(true)">Remove placement</button>
</fieldset><p>Area plan (JSON)</p>""").replace("create();\n</script>", """
function placement(remove) {
 try {
  const p=JSON.parse(el("plan").value);
  const room=p.rooms.find(r=>r.room_id===Number(el("spawn-room").value));
  if(!room)throw Error("Select a room in this area");
  const id=Number(el("monster").value);
  if(!id)throw Error("Select a monster template");
  room.monsters=(room.monsters||[]).filter(m=>m.id!==id);
  if(!remove)room.monsters.push({id,count:Number(el("spawn-count").value),
                               respawn:Number(el("respawn").value)});
  el("plan").value=JSON.stringify(p,null,2);
 }catch(e){el("status").textContent=e.message}
}
api("/api/monsters").then(rows=>{
 for(const {id,name} of rows)el("monster").add(new Option(id+" — "+name,id));
}).catch(e=>el("status").textContent=e.message);
create();
</script>""")


class Handler(area.Handler):
    def do_GET(self):
        if self.path == "/api/monsters":
            self.reply(200, [{"id": identifier, "name": name}
                             for identifier, name in TEMPLATES.items()])
        else:
            super().do_GET()


if __name__ == "__main__":
    if "--test" in sys.argv:
        area.test()
        plan = area.new_plan(14, 15)
        entry = plan["rooms"][0]
        monster = next(iter(TEMPLATES))
        entry["monsters"] = [{"id": monster, "count": 2, "respawn": 60}]
        assert area.generate(plan, persist=False)["rooms"]["14"]["checks"]["permanent_monster_slots"]
        entry["monsters"] = []
        assert area.generate(plan, persist=False)["passed"]
        for invalid in (-1, ABI["maximum"], True):
            entry["monsters"] = [{"id": invalid, "count": 1, "respawn": 60}]
            try:
                clean(plan)
            except ValueError:
                continue
            raise AssertionError("Accepted invalid monster ID")
        print(f"PASS: {len(TEMPLATES)} native templates, add/count/remove, invalid IDs")
    else:
        area.EXPORTS.mkdir(mode=0o700, exist_ok=True)
        area.init()
        ThreadingHTTPServer(("127.0.0.1", 8782), Handler).serve_forever()
