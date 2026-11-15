"""Patch only exact, known Round 72 source anchors in a disposable checkout."""
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
base = repo / "tools/world-builder"


def replace_once(path, old, new):
    data = path.read_text()
    if data.count(old) != 1 or data.count(new) != 0:
        raise SystemExit(f"Unsafe Round 73 patch anchor: {path}, found {data.count(old)}")
    path.write_text(data.replace(old, new, 1))

app = base / "round57/app.py"
replace_once(app, "import wilderness_map\n", "import wilderness_map\nimport treasure_sites\n")
replace_once(app,
'''def generate(plan, persist=True):
    return generate_original(plan, persist=persist,
                             extra_assets=lambda value: custom_banks(value)[1] | wilderness_map.assets(value))
''',
'''def export_assets(plan):
    ids, native_assets = custom_banks(plan)
    guardian_templates = set(TEMPLATES) | ids.get("monsters", set())
    return (native_assets | wilderness_map.assets(plan) |
            treasure_sites.assets(plan, guardian_templates))


def generate(plan, persist=True):
    return generate_original(plan, persist=persist, extra_assets=export_assets)
''')
replace_once(app,
'''    wilderness_map.tiles(plan)
    custom, _ = custom_banks(plan)
''',
'''    wilderness_map.tiles(plan)
    custom, _ = custom_banks(plan)
    treasure_sites.validate(plan, set(TEMPLATES) | custom.get("monsters", set()))
''')

area = base / "round57/area_export.py"
replace_once(area,
'''        if "rooms/wilderness.map" in assets:
            manifest["wilderness_map_sha256"] = sha(assets["rooms/wilderness.map"])
''',
'''        if "rooms/wilderness.map" in assets:
            manifest["wilderness_map_sha256"] = sha(assets["rooms/wilderness.map"])
        if "rooms/treasure_sites.json" in assets:
            manifest["treasure_sites_sha256"] = sha(assets["rooms/treasure_sites.json"])
''')

runner = base / "round72/private.sh"
replace_once(runner,
'''round69_custom.py,test_exit_validation.py,wilderness_map.py} "$TEST/builder/"''',
'''round69_custom.py,test_exit_validation.py,wilderness_map.py,treasure_sites.py} "$TEST/builder/"''')
replace_once(runner,
'''  PYTHONPATH=. python3 "$REPO/tools/world-builder/round72/test_region.py"
''',
'''  PYTHONPATH=. python3 "$REPO/tools/world-builder/round72/test_region.py"
  PYTHONPATH=. python3 "$REPO/tools/world-builder/round73/test_treasure.py"
  echo 'ROUND 73: treasure blueprint and claim unit tests PASS'
''')
replace_once(runner,
'''grep -Fxq 'ROUND 72: deterministic terrain, connected restrictions and metadata validation PASS' "$TEST/regression.log"
''',
'''grep -Fxq 'ROUND 72: deterministic terrain, connected restrictions and metadata validation PASS' "$TEST/regression.log"
grep -Fxq 'ROUND 73: treasure blueprint and claim unit tests PASS' "$TEST/regression.log"
''')
print("ROUND 73: verified source anchors patched successfully")
