"""Exercise native exit validation without changing any saved plans."""
import copy
from unittest.mock import patch

import app


def test():
    area = app.area
    originals = {
        14: [{"direction": "post office", "destination": 900},
             {"direction": "east", "destination": 17}],
        15: [{"direction": "west", "destination": 14}],
    }
    plan = {"rooms": [{"room_id": rid, "name": f"Room {rid}", "exits": copy.deepcopy(exits)}
                      for rid, exits in originals.items()]}
    with patch.object(area, "native_exits", side_effect=originals.__getitem__):
        assert area.clean_plan(plan)[14]["exits"] == originals[14]
        print("PASS: Existing named and out-of-plan exits preserved")

        def reject(candidate, expected):
            try:
                area.clean_plan(candidate)
            except ValueError as error:
                assert expected in str(error), str(error)
            else:
                raise AssertionError(f"Expected rejection: {expected}")

        edited = copy.deepcopy(plan)
        edited["rooms"][0]["exits"][0]["destination"] = 15
        reject(edited, "standard direction")
        edited = copy.deepcopy(plan)
        edited["rooms"][0]["exits"].pop(0)
        reject(edited, "Nonstandard original exit cannot be removed")
        edited = copy.deepcopy(plan)
        edited["rooms"][0]["exits"][1]["destination"] = 15
        assert area.clean_plan(edited)[14]["exits"][1]["destination"] == 15
        edited["rooms"][1]["exits"].clear()
        reject(edited, "Missing reciprocal west exit")
        edited["rooms"][0]["exits"][1]["destination"] = 16
        reject(edited, "must target a room in this area")
        print("PASS: Named exit protection and reciprocal redirect validation")


if __name__ == "__main__":
    test()
