"""Validate draft geography and serialize a bounded, versioned native map."""
import re

TERRAIN = dict(forest="F", plains=".", mountain="^", swamp="S", river="~",
               road="=", ruins="#")
LABEL = re.compile(r"[A-Za-z][A-Za-z0-9 -]{0,39}")


def tiles(plan):
    result = []
    coordinates = set()
    for room in plan["rooms"]:
        if "wilderness" not in room:
            continue
        tile = room["wilderness"]
        if not isinstance(tile, dict) or tile.keys() != {"region", "x", "y", "terrain", "landmark"}:
            raise ValueError("Invalid wilderness metadata")
        region, x, y, terrain, landmark = (tile[key] for key in
                                           ("region", "x", "y", "terrain", "landmark"))
        rid = room["room_id"]
        if (not room.get("new_room") or not 10000 <= rid < 16000 or
                not isinstance(region, str) or not LABEL.fullmatch(region) or region != region.strip() or
                type(x) is not int or type(y) is not int or not 1 <= x <= 10 or not 1 <= y <= 10 or
                not isinstance(terrain, str) or terrain not in TERRAIN or
                not isinstance(landmark, str) or (landmark and
                (not LABEL.fullmatch(landmark) or landmark != landmark.strip()))):
            raise ValueError("Invalid wilderness tile")
        coordinate = (region.casefold(), x, y)
        if coordinate in coordinates:
            raise ValueError("Duplicate wilderness coordinate")
        coordinates.add(coordinate)
        result.append((rid, region, x, y, terrain, landmark))
    index = {entry[0]: entry for entry in result}
    offsets = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for room in plan["rooms"]:
        if room["room_id"] not in index:
            continue
        _, region, x, y, _, _ = index[room["room_id"]]
        for exit_ in room["exits"]:
            target = index.get(exit_["destination"])
            offset = offsets.get(exit_["direction"])
            if target and offset and target[1:4] != (region, x + offset[0], y + offset[1]):
                raise ValueError("Wilderness exit disagrees with map coordinates")
    return sorted(result)


def assets(plan):
    mapped = tiles(plan)
    if not mapped:
        return {}
    lines = ["HDW1"] + [f"{rid}\t{x}\t{y}\t{TERRAIN[terrain]}\t{region}\t{landmark or '-'}"
                       for rid, region, x, y, terrain, landmark in mapped]
    return {"rooms/wilderness.map": ("\n".join(lines) + "\n").encode("ascii")}
