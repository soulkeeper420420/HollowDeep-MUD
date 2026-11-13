"""Exercise native exit validation without changing any saved plans."""
import copy
import hashlib
import json
import tempfile
from unittest.mock import patch
import zipfile

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

    native = app.new_plan(8, 14)
    native["rooms"][0]["short_description"] = "Round 59 named exit regression."
    baseline, _ = area.r50.baseline(8)
    original, _ = area.r51.original_exits(baseline)
    assert any(area.r51.fields(record) == {"direction": "northeast", "destination": 23}
               for record in original)
    with tempfile.TemporaryDirectory(prefix="named-exit-export-") as directory:
        with patch.object(area, "EXPORTS", area.Path(directory)):
            result = area.generate(native)
        bundle = area.Path(directory) / (result["export_id"] + ".zip")
        assert hashlib.sha256(bundle.read_bytes()).hexdigest() == result["bundle_sha256"]
        with zipfile.ZipFile(bundle) as archive:
            assert archive.testzip() is None
            manifest = json.loads(archive.read("manifest.json"))
            candidate = archive.read("r00008.native-candidate")
            assert hashlib.sha256(candidate).hexdigest() == manifest["rooms"]["8"]["candidate_sha256"]
            assert area.r51.original_exits(candidate)[0] == original
            assert b"Round 59 named exit regression." in candidate
    print("PASS: Native room 8 northeast exit to room 23 survives description edit and ZIP export byte for byte")


if __name__ == "__main__":
    test()
