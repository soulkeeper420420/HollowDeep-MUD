"""Round 71: atomic, private-only rectangular wilderness-region generation."""
import copy
import re
from pathlib import Path

import app

FIRST_HIGH_ID = 10000
LAST_HIGH_ID = 15999
MAX_SIDE = 10
OPPOSITE = app.area.PAIRS


def grid(plan, anchor_id, first_id, rows, columns, direction, prefix):
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

    candidate = copy.deepcopy(plan)
    app.clean(candidate)  # Reject stale/invalid plans before modifying the copy.
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

    source["exits"].append({"direction": direction, "destination": first_id})
    for y in range(rows):
        for x in range(columns):
            rid = first_id + y * columns + x
            exits = []
            if y > 0:
                exits.append({"direction": "north", "destination": rid - columns})
            if y + 1 < rows:
                exits.append({"direction": "south", "destination": rid + columns})
            if x > 0:
                exits.append({"direction": "west", "destination": rid - 1})
            if x + 1 < columns:
                exits.append({"direction": "east", "destination": rid + 1})
            if rid == first_id:
                exits.append({"direction": OPPOSITE[direction], "destination": anchor_id})
            name = f"{prefix} {y + 1},{x + 1}"
            candidate["rooms"].append({
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
            })
    app.clean(candidate)  # All-or-nothing validation; caller commits only on success.
    return candidate
