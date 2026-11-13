"""Round 55 multi-room plan operations.

Pure plan editing only. Native room serialization remains in
the existing validated exporter.
"""

import copy

REVERSE = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up",
}

def room_index(plan):
    rooms = plan.get("rooms")
    if not isinstance(rooms, list):
        raise ValueError("Plan must contain a rooms list")

    result = {}
    for room in rooms:
        rid = room.get("room_id")
        if not isinstance(rid, int) or isinstance(rid, bool):
            raise ValueError("Invalid room ID")
        if rid in result:
            raise ValueError("Duplicate room ID")
        result[rid] = room

    return result

def add_room(plan, room):
    result = copy.deepcopy(plan)
    index = room_index(result)

    rid = room.get("room_id")
    if not isinstance(rid, int) or isinstance(rid, bool):
        raise ValueError("Invalid room ID")
    if rid in index:
        raise ValueError("Room already exists")

    result["rooms"].append(copy.deepcopy(room))
    return result

def connect(plan, a, b, direction):
    result = copy.deepcopy(plan)
    index = room_index(result)

    if a == b:
        raise ValueError("Cannot connect a room to itself")
    if a not in index or b not in index:
        raise ValueError("Both rooms must exist")
    if direction not in REVERSE:
        raise ValueError("Invalid direction")

    reverse = REVERSE[direction]

    for rid, d in ((a, direction), (b, reverse)):
        exits = index[rid].setdefault("exits", [])
        if any(x["direction"] == d for x in exits):
            raise ValueError("Exit direction already occupied")

    index[a]["exits"].append({
        "direction": direction,
        "destination": b
    })
    index[b]["exits"].append({
        "direction": reverse,
        "destination": a
    })

    return result

def validate(plan):
    index = room_index(plan)

    for rid, room in index.items():
        directions = set()

        for exit_ in room.get("exits", []):
            direction = exit_["direction"]
            destination = exit_["destination"]

            if direction not in REVERSE:
                raise ValueError("Invalid direction")
            if direction in directions:
                raise ValueError("Duplicate exit direction")

            directions.add(direction)

            if destination in index:
                reverse = REVERSE[direction]
                matches = [
                    e for e in index[destination].get("exits", [])
                    if e["direction"] == reverse
                    and e["destination"] == rid
                ]
                if len(matches) != 1:
                    raise ValueError("Missing reciprocal exit")

    return True
