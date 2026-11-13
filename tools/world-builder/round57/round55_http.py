"""Round 55 HTTP extension for native-backed multi-room plans."""

import copy
import json
import sys

import app


def add_native_room(plan, room_id):
    if not isinstance(plan, dict):
        raise ValueError("Invalid plan")

    rooms = plan.get("rooms")
    if not isinstance(rooms, list):
        raise ValueError("Invalid room list")

    rid = app.area.valid_id(room_id)

    if len(rooms) >= 50:
        raise ValueError("Area already contains 50 rooms")

    existing = [r.get("room_id") for r in rooms]

    if len(existing) != len(set(existing)):
        raise ValueError("Duplicate room IDs")

    if rid in existing:
        raise ValueError("Room already exists")

    # Load a complete native-backed room draft through the
    # validated Round 54 builder.
    anchor = existing[0] if existing else None

    if anchor is None:
        raise ValueError("Start with a two-room area")

    native = app.new_plan(anchor, rid)

    added = next(
        r for r in native["rooms"]
        if r["room_id"] == rid
    )

    result = copy.deepcopy(plan)
    result["rooms"].append(copy.deepcopy(added))

    # Validate through the actual Round 54 cleaner.
    app.clean(result)

    return result


class Handler(app.Handler):
    def do_POST(self):
        if self.path != "/api/add-room":
            return super().do_POST()

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if not 0 < length <= 262144:
                raise ValueError("Invalid request size")

            payload = json.loads(self.rfile.read(length))

            result = add_native_room(
                payload["plan"],
                payload["room_id"]
            )

            self.reply(200, result)

        except (ValueError, KeyError, TypeError) as exc:
            self.reply(400, {"error": str(exc)})


def test():
    plan = app.new_plan(14, 15)

    plan = add_native_room(plan, 16)
    plan = add_native_room(plan, 17)

    assert len(plan["rooms"]) == 4

    ids = {r["room_id"] for r in plan["rooms"]}
    assert ids == {14, 15, 16, 17}

    print("PASS: Four native-backed rooms")

    try:
        add_native_room(plan, 16)
    except ValueError:
        print("PASS: Duplicate room rejected")
    else:
        raise AssertionError("Duplicate room accepted")

    try:
        add_native_room(plan, -1)
    except (ValueError, AssertionError):
        print("PASS: Invalid room ID rejected")
    else:
        raise AssertionError("Invalid room accepted")

    plan = app.area.link(plan, 14, 15, "north")
    plan = app.area.link(plan, 15, 16, "north")
    plan = app.area.link(plan, 16, 17, "up")

    cleaned = app.clean(plan)

    for rid, room in sorted(cleaned.items()):
        candidate, checks = app.build(rid, room)
        assert candidate and all(checks.values())

    print("PASS: Four-room native serialization")
    print("PASS: Reciprocal routing")

    result = app.area.generate(plan, persist=False)

    assert result["passed"]
    assert result["production_deployment"] is False

    print("PASS: Four-room native export")
    print("PASS: No production deployment")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        raise SystemExit(
            "Round 55 HTTP module ready; "
            "launch integration is not yet enabled"
        )
