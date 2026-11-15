"""Round 54 permanent monster placements over the existing area exporter."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import wilderness_map
import treasure_sites
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("round53", ROOT / "area_export.py")
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
OBJECT_TABLE, object_slots, object_size, name_size, maximum, per_file = json.loads(
    (ROOT / "object_layout.json").read_text())
if object_slots != ABI["slots"] or object_size != 352:
    raise RuntimeError("Unsupported native object ABI")


def object_catalog():
    templates = {}
    for group in range((maximum - 1) // per_file + 1):
        path = ROOT / "templates" / f"o{group:02d}"
        if not path.is_file():
            continue
        data = path.read_bytes()
        for index in range(min(per_file, len(data) // object_size)):
            identifier = group * per_file + index
            start = index * object_size
            name, separator, _ = data[start:start + name_size].partition(bytes(1))
            if 0 < identifier < maximum and name and separator:
                templates[identifier] = name.decode("utf-8", "replace")
    return templates


OBJECT_TEMPLATES = object_catalog()

clean_original, build_original = area.clean_plan, area.build_room
new_original = area.new_plan
generate_original = area.generate


def custom_banks(plan):
    custom = plan.get("custom_templates", {})
    kinds = {"monsters": (TEMPLATES, "m", ABI["creature"], ABI["per_file"], ABI["maximum"]),
             "objects": (OBJECT_TEMPLATES, "o", object_size, per_file, maximum)}
    area.require(isinstance(custom, dict) and custom.keys() <= kinds.keys(),
                 "Invalid custom template types")
    assets = {}
    ids = {}
    for kind, definitions in custom.items():
        catalog, prefix, size, records, limit = kinds[kind]
        area.require(isinstance(definitions, list) and len(definitions) <= 50,
                     "Use at most 50 custom templates per type")
        ids[kind] = set()
        banks = {}

        def bank(number):
            if number not in banks:
                path = ROOT / "templates" / f"{prefix}{number:02d}"
                data = path.read_bytes() if path.exists() else b""
                area.require(len(data) <= records * size and len(data) % size == 0,
                             "Invalid native template bank")
                banks[number] = bytearray(data.ljust(records * size, b"\0"))
            return banks[number]

        changed = set()
        for entry in definitions:
            area.require(isinstance(entry, dict) and set(entry) == {"id", "base_id", "name"},
                         "Invalid custom template definition")
            identifier, base, name = (entry[key] for key in ("id", "base_id", "name"))
            area.require(type(identifier) is int and 0 < identifier < limit and
                         identifier not in catalog and identifier not in ids[kind],
                         "Custom template ID collides with another record")
            area.require(type(base) is int and base in catalog, "Unknown base template")
            area.require(isinstance(name, str) and name == name.strip() and name.isprintable(),
                         "Invalid custom template name")
            encoded = area.r51.encode_name(name, 80)
            target_group, target_slot = divmod(identifier, records)
            source_group, source_slot = divmod(base, records)
            target = bank(target_group)
            start = target_slot * size
            area.require(not any(target[start:start + size]), "Custom template ID occupies a native record")
            source = bank(source_group)
            start_source = source_slot * size
            record = bytearray(source[start_source:start_source + size])
            # Replace the complete ABI-defined name field; preserve other record bytes.
            name_offset = ABI["name"] if kind == "monsters" else 0
            name_width = ABI["name_size"] if kind == "monsters" else name_size
            area.require(name_offset + name_width <= size, "Invalid native name field")
            name_record = area.r51.encode_name(name, name_width)
            record[name_offset:name_offset + name_width] = name_record

            # Add an unambiguous lowercase native command keyword.
            # Preserve every existing keyword and all unrelated bytes.
            key_offset = 255 if kind == "monsters" else 160
            alias = (("hdm" if kind == "monsters" else "hdo")
                     + str(identifier)).encode("ascii")
            area.require(key_offset + 60 <= size,
                         "Invalid native keyword layout")
            free = next((
                key_offset + 20 * index
                for index in range(3)
                if not record[key_offset + 20 * index:
                              key_offset + 20 * (index + 1)].split(
                                  bytes(1), 1)[0]
            ), None)
            area.require(free is not None,
                         "No unused native keyword slot")
            record[free:free + 20] = alias.ljust(20, bytes(1))
            target[start:start + size] = record
            ids[kind].add(identifier)
            changed.add(target_group)
        for group in changed:
            assets[f"objmon/{prefix}{group:02d}"] = bytes(banks[group])
    return ids, assets


def export_assets(plan):
    ids, native_assets = custom_banks(plan)
    guardian_templates = set(TEMPLATES) | ids.get("monsters", set())
    return (native_assets | wilderness_map.assets(plan) |
            treasure_sites.assets(plan, guardian_templates))


def generate(plan, persist=True):
    return generate_original(plan, persist=persist, extra_assets=export_assets)


def existing(data, table=ABI["table"]):
    groups = {}
    for index in range(ABI["slots"]):
        offset = table + index * ABI["slot"]
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
        room["objects"] = [{"id": identifier, "respawn": seconds, "count": len(slots)}
                           for (identifier, seconds), slots in existing(data, OBJECT_TABLE).items()]
    return plan


def placements(value, templates=TEMPLATES):
    area.require(isinstance(value, list) and len(value) <= ABI["slots"], "Invalid placement list")
    ids = set()
    used = 0
    for entry in value:
        area.require(isinstance(entry, dict) and set(entry) == {"id", "count", "respawn"},
                     "Unsupported placement fields")
        monster, count, interval = (entry[k] for k in ("id", "count", "respawn"))
        area.require(all(type(v) is int for v in (monster, count, interval)), "Expected integer placement fields")
        area.require(monster in templates and monster not in ids, "Unknown or duplicate placement template")
        area.require(1 <= count <= ABI["slots"] and 1 <= interval <= 86400,
                     "Count or respawn seconds out of range")
        used += count
        ids.add(monster)
    area.require(used <= ABI["slots"], "Permanent spawn table is full")
    return value


def clean(plan):
    rooms = clean_original(plan)
    wilderness_map.tiles(plan)
    custom, _ = custom_banks(plan)
    treasure_sites.validate(plan, set(TEMPLATES) | custom.get("monsters", set()))
    for entry in plan["rooms"]:
        if "monsters" in entry:
            rid = entry["room_id"]
            baseline = [] if entry.get("new_room") else new_plan_monsters(rid)
            if entry["monsters"] != baseline:
                rooms[rid]["monsters"] = placements(entry["monsters"], TEMPLATES.keys() | custom.get("monsters", set()))
    for entry in plan["rooms"]:
        for key in ("short_description", "long_description"):
            if key not in entry:
                continue
            value = entry[key]
            area.require(isinstance(value, str), "Description must be text")
            area.require(all(c.isprintable() or c == chr(10) for c in value), "Invalid description character")
            encoded = value.encode("utf-8")
            area.require(len(encoded) <= 4096, "Description exceeds 4096 bytes")
            rooms[entry["room_id"]][key] = encoded + bytes(1) if encoded else b""
    for entry in plan["rooms"]:
        if "objects" in entry:
            rid = entry["room_id"]
            baseline = []
            if not entry.get("new_room"):
                data, _ = area.r50.baseline(rid)
                baseline = [{"id": identifier, "respawn": seconds, "count": len(slots)}
                            for (identifier, seconds), slots in existing(data, OBJECT_TABLE).items()]
            if entry["objects"] != baseline:
                rooms[rid]["objects"] = placements(entry["objects"], OBJECT_TEMPLATES.keys() | custom.get("objects", set()))
    return rooms


def new_plan_monsters(rid):
    data, _ = area.r50.baseline(rid)
    return [{"id": identifier, "respawn": seconds, "count": len(slots)}
            for (identifier, seconds), slots in existing(data).items()]


def build(rid, room):
    candidate, checks = build_original(rid, room)
    candidate, checks = apply_slots(candidate, checks, room, "monsters", ABI["table"])
    return apply_slots(candidate, checks, room, "objects", OBJECT_TABLE)


def apply_slots(original, checks, room, field, start):
    if field not in room:
        return original, checks
    end = start + ABI["slots"] * ABI["slot"]
    area.require(0 <= start < end <= ABI["header"], "Invalid spawn table extent")
    edited = bytearray(original)
    edited[start:end] = bytes(end - start)
    offset = start
    previous = existing(original, start)
    for entry in room[field]:
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
    checks["permanent_monster_slots" if field == "monsters" else "permanent_object_slots"] = True
    return candidate, checks


area.clean_plan = clean
area.build_room = build
area.new_plan = new_plan
area.generate = generate
area.PAGE = area.PAGE.replace("Round 53", "Round 54").replace(
    "<p>Area plan (JSON)</p>", """<fieldset><legend>Room edits and permanent placements</legend>
<label>Room <input id="spawn-room" type="number" value="14"></label>
<label>Placement kind <select id="placement-kind"><option value="monsters">Monster</option><option value="objects">Object</option></select></label>
<label>Template <select id="monster"></select></label>
<label>Count <input id="spawn-count" type="number" min="1" max="10" value="1"></label>
<label>Respawn seconds <input id="respawn" type="number" min="1" max="86400" value="60"></label>
<button onclick="placement(false)">Set placement</button>
<button onclick="placement(true)">Remove placement</button>
<label>Description <select id="description-kind"><option value="short_description">Short</option><option value="long_description">Long</option></select></label>
<label>Text <textarea id="description-text" rows="3"></textarea></label>
<button onclick="setDescription()">Set description</button>
</fieldset><p>Area plan (JSON)</p>""").replace("create();\n</script>", """
function editRoom(edit) {
 try {
  const plan=JSON.parse(el("plan").value);
  const room=plan.rooms.find(r=>r.room_id===Number(el("spawn-room").value));
  if(!room)throw Error("Select a room in this area");
  edit(room);
  el("plan").value=JSON.stringify(plan,null,2);
  el("status").textContent="Room plan updated";
 }catch(e){el("status").textContent=e.message}
}
function setDescription(){
 editRoom(room=>{room[el("description-kind").value]=el("description-text").value});
}
function placement(remove){
 editRoom(room=>{
  const kind=el("placement-kind").value;
  const id=Number(el("monster").value);
  if(!id)throw Error("Select a template");
  if(kind==="objects" && !Array.isArray(room.objects))
   throw Error("Create a current area plan to edit object placements");
  const entries=(room[kind]||[]).filter(item=>item.id!==id);
  if(!remove){
   for(const field of ["spawn-count","respawn"]){
    if(!el(field).value || !el(field).reportValidity())throw Error("Enter a valid count and respawn interval");
   }
   entries.push({id,count:Number(el("spawn-count").value),respawn:Number(el("respawn").value)});
  }
  room[kind]=entries;
 });
}
async function loadPlacements(){
 const kind=el("placement-kind").value;
 const select=el("monster");
 select.replaceChildren();
 try{
  const rows=await api("/api/"+kind);
  if(el("placement-kind").value!==kind)return;
  for(const {id,name} of rows)select.add(new Option(id+" — "+name,id));
 }catch(e){el("status").textContent=e.message}
}
el("placement-kind").onchange=loadPlacements;
loadPlacements();
create();
</script>""")


class Handler(area.Handler):
    def do_GET(self):
        if self.path == "/api/objects":
            self.reply(200, [{"id": identifier, "name": name}
                             for identifier, name in OBJECT_TEMPLATES.items()])
        elif self.path == "/api/monsters":
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
