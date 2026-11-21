"""Round 71: atomic, private-only rectangular wilderness-region generation."""
import copy
import re
import random
from pathlib import Path

import app

FIRST_HIGH_ID = 10000
LAST_HIGH_ID = 15999
MAX_SIDE = 10
OPPOSITE = app.area.PAIRS


def grid(plan, anchor_id, first_id, rows, columns, direction, prefix, seed=None):
    if not app.area.EXTENDED_ROOMS:
        raise ValueError("Wilderness generation requires private extended-room mode")
    if not isinstance(plan, dict) or not isinstance(plan.get("rooms"), list):
        raise ValueError("Invalid area plan")
    if any(type(v) is not int for v in (anchor_id, first_id, rows, columns)):
        raise ValueError("Grid coordinates and room IDs must be integers")
    if not (2 <= rows <= MAX_SIDE and 2 <= columns <= MAX_SIDE):
        raise ValueError("Grid must be 2–10 rows by 2–10 columns")
    count = rows * columns
    if first_id < FIRST_HIGH_ID or first_id + count - 1 > LAST_HIGH_ID:
        raise ValueError("New wilderness room IDs must be within 10000–15999")
    if type(direction) is not str or direction not in ("up", "down"):
        raise ValueError("Wilderness entrance must use up or down")
    if not isinstance(prefix, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 -]{0,30}", prefix):
        raise ValueError("Region name must be 1–31 safe ASCII characters")
    prefix = prefix.strip()
    if not prefix:
        raise ValueError("Enter a region name")
    if seed is not None and (type(seed) is not int or not 0 <= seed <= 2147483647):
        raise ValueError("Seed must be an integer from 0 through 2147483647")

    candidate = copy.deepcopy(plan)
    app.clean(candidate)  # Reject stale/invalid plans before modifying the copy.
    if seed is not None and any(room.get("wilderness", {}).get("region", "").casefold() == prefix.casefold()
                                for room in candidate["rooms"]):
        raise ValueError("Region name already exists")
    if len(candidate["rooms"]) + count > app.area.PLAN_CAPACITY:
        raise ValueError("Region exceeds private area plan capacity")
    source = next((r for r in candidate["rooms"] if r["room_id"] == anchor_id), None)
    if source is None:
        raise ValueError("Choose an existing room in this area as the anchor")
    if any(e["direction"] == direction for e in source["exits"]):
        raise ValueError("Source room already has a " + direction + " exit")

    used = {r["room_id"] for r in candidate["rooms"]}
    live = Path("/srv/hollowdeep/world/rooms")
    for rid in range(first_id, first_id + count):
        target = live / f"r{rid:05d}"
        if rid in used or str(rid) in app.area.INDEX or target.exists() or target.is_symlink():
            raise ValueError("Wilderness room ID is already occupied: " + str(rid))

    terrain = {}
    if seed is not None:
        rng = random.Random(seed)
        biomes = ["forest", "plains", "mountain", "swamp", "river", "road", "ruins"]
        for y in range(rows):
            for x in range(columns):
                terrain[x, y] = "road" if x == 0 else rng.choice(biomes)

    def passage(x, y, other_y):
        return x == 0 or not {"river", "mountain"} & {terrain.get((x, y)), terrain.get((x, other_y))}

    source["exits"].append({"direction": direction, "destination": first_id})
    for y in range(rows):
        for x in range(columns):
            rid = first_id + y * columns + x
            exits = []
            if y > 0 and passage(x, y, y - 1):
                exits.append({"direction": "north", "destination": rid - columns})
            if y + 1 < rows and passage(x, y, y + 1):
                exits.append({"direction": "south", "destination": rid + columns})
            if x > 0:
                exits.append({"direction": "west", "destination": rid - 1})
            if x + 1 < columns:
                exits.append({"direction": "east", "destination": rid + 1})
            if rid == first_id:
                exits.append({"direction": OPPOSITE[direction], "destination": anchor_id})
            name = f"{prefix} {y + 1},{x + 1}"
            room = {
                "room_id": rid,
                "new_room": True,
                "name": name,
                "exits": exits,
                "monsters": [],
                "objects": [],
                "short_description": "The untamed wilderness stretches in every direction.",
                "long_description": (
                    f"You are exploring {prefix}, sector {y + 1},{x + 1}. "
                    "Old trails and natural landmarks guide travelers through the region."
                )
            }
            if seed is not None:
                biome = terrain[x, y]
                landmark = "Trailhead Cairn" if x == y == 0 else ""
                room["wilderness"] = dict(region=prefix, x=x + 1, y=y + 1,
                                          terrain=biome, landmark=landmark)
                room["short_description"] = {
                    "forest": "Tall trees crowd the trail.", "plains": "Wind bends the open grass.",
                    "mountain": "Bare stone rises above the trail.", "swamp": "Reeds sway over dark pools.",
                    "river": "A flowing river follows the bank.", "road": "A worn road crosses the wilds.",
                    "ruins": "Weathered masonry lies beside the trail."
                }[biome]
                room["long_description"] = f"{prefix}, column {x + 1}, row {y + 1}. " + room["short_description"]
                if landmark:
                    room["long_description"] += f" The {landmark} marks the entrance."
            candidate["rooms"].append(room)
    app.clean(candidate)  # All-or-nothing validation; caller commits only on success.
    return candidate
