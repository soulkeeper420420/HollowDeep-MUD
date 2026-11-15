"""Round 73 treasure encounter BLUEPRINTS; NOT a live pickup/loot gate.

World Builder exports inert site metadata only. Native gameplay must separately
instantiate guardians, authorize kills, and enforce chest locks before use.
"""

import json
import re

TIERS = ("common", "uncommon", "rare", "epic", "legendary")
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{2,39}\Z")
LABEL = re.compile(r"[A-Za-z][A-Za-z0-9 '-]{0,39}\Z")
CLUE = re.compile(r"[A-Za-z0-9 .,;:'!?()/-]{1,180}\Z")
FIELDS = {"site_id", "room_id", "guardians", "chest_label", "tier", "clue"}


def reject_if(condition, message):
    if condition:
        raise ValueError(message)


def validate(plan, available_guardians):
    """Return normalized site list or reject the *entire* draft.

    Only wilderness rooms already present in this plan can host treasure.
    Guardian IDs identify *templates*, not spawned or killed instances.
    """
    reject_if(not isinstance(plan, dict) or not isinstance(plan.get("rooms"), list),
              "Invalid treasure area plan")
    entries = plan.get("treasure_sites", [])
    reject_if(not isinstance(entries, list) or len(entries) > 30,
              "Treasure plan must contain at most 30 sites")
    available = set(available_guardians)
    rooms = {room.get("room_id"): room for room in plan["rooms"]
             if isinstance(room, dict) and type(room.get("room_id")) is int}
    ids, locations = set(), set()
    normalized = []
    for entry in entries:
        reject_if(not isinstance(entry, dict) or set(entry) != FIELDS,
                  "Invalid treasure site fields")
        sid, rid, guardians, chest, tier, clue = (
            entry[key] for key in ("site_id", "room_id", "guardians", "chest_label", "tier", "clue")
        )
        reject_if(not isinstance(sid, str) or not IDENTIFIER.fullmatch(sid) or sid in ids,
                  "Invalid or duplicate treasure site ID")
        reject_if(type(rid) is not int or rid not in rooms or
                  not 10000 <= rid < 16000 or
                  not isinstance(rooms[rid].get("wilderness"), dict),
                  "Treasure site must reference a mapped wilderness room in this draft")
        reject_if(rid in locations, "Only one treasure encounter is allowed per room")
        reject_if(not isinstance(guardians, list) or not 1 <= len(guardians) <= 5 or
                  any(type(g) is not int or g not in available for g in guardians) or
                  len(set(guardians)) != len(guardians),
                  "Treasure guardian templates must be 1-5 distinct existing monsters")
        reject_if(not isinstance(chest, str) or not LABEL.fullmatch(chest),
                  "Invalid treasure chest label")
        reject_if(type(tier) is not str or tier not in TIERS,
                  "Unknown treasure rarity tier")
        reject_if(not isinstance(clue, str) or not CLUE.fullmatch(clue),
                  "Invalid treasure-map clue")
        tile = rooms[rid]["wilderness"]
        normalized.append({
            "site_id": sid, "room_id": rid,
            "region": tile["region"], "column": tile["x"], "row": tile["y"],
            "guardians": list(guardians), "chest_label": chest,
            "tier": tier, "clue": clue,
        })
        ids.add(sid)
        locations.add(rid)
    return sorted(normalized, key=lambda row: row["site_id"])


def assets(plan, available_guardians):
    """Produce inert, versioned metadata; native runtime must enforce locking."""
    rows = validate(plan, available_guardians)
    if not rows:
        return {}
    data = {"format": "HD-TREASURE-BLUEPRINT-V1", "sites": rows}
    return {"rooms/treasure_sites.json":
            (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")}
