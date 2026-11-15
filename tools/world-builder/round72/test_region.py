"""Check seeded topology, draft validation, and sidecar generation."""
import copy

import app
from round71_private import expect_failure
from round71_wilderness import grid
from wilderness_map import TERRAIN, assets, tiles


def test():
    original = app.new_plan(14, 15)
    args = (original, 14, 15900, 10, 10, "up", "Redwood Basin")
    plan = grid(*args, seed=42)
    assert plan == grid(*args, seed=42)
    assert assets(plan) != assets(grid(*args, seed=43))
    assert len(original["rooms"]) == 2
    index = {room["room_id"]: room for room in plan["rooms"]}
    mapped = tiles(plan)
    assert len(mapped) == 100 and mapped[-1][:4] == (15999, "Redwood Basin", 10, 10)
    assert {tile[4] for tile in mapped} == set(TERRAIN)
    visited, pending = set(), [15900]
    restricted = 0
    for rid in range(15900, 16000):
        room = index[rid]
        neighbors = {exit_["destination"] for exit_ in room["exits"]}
        for neighbor in neighbors:
            assert any(exit_["destination"] == rid for exit_ in index[neighbor]["exits"])
        tile = room["wilderness"]
        if tile["x"] > 1 and tile["y"] < 10 and tile["terrain"] in {"river", "mountain"}:
            assert rid + 10 not in neighbors
            restricted += 1
    assert restricted
    while pending:
        rid = pending.pop()
        if rid in visited:
            continue
        visited.add(rid)
        pending.extend(exit_["destination"] for exit_ in index[rid]["exits"]
                       if exit_["destination"] >= 15900)
    assert len(visited) == 100
    assert len(assets(plan)["rooms/wilderness.map"].splitlines()) == 101
    broken = copy.deepcopy(plan)
    broken["rooms"][3]["wilderness"]["x"] = 1
    expect_failure("overlapping wilderness coordinates", lambda: app.clean(broken))
    broken = copy.deepcopy(plan)
    broken["rooms"][2]["wilderness"]["x"] = 2
    broken["rooms"][3]["wilderness"]["x"] = 1
    expect_failure("wilderness exit and coordinate mismatch", lambda: app.clean(broken))
    expect_failure("invalid wilderness seed", lambda: grid(*args, seed=True))
    print("ROUND 72: deterministic terrain, connected restrictions and metadata validation PASS")


if __name__ == "__main__":
    test()
