#!/usr/bin/env python3
"""Offline-only XP curve preview; not the live game configuration parser."""
import json
import pathlib
import sys

EXPECTED = {"status", "level_cap", "xp_base", "xp_growth", "stat_base",
            "stat_max", "starting_points", "remort_kills", "remort_seconds",
            "points_per_remort", "legacy_points_cap"}


def table(config):
    if type(config) is not dict or set(config) != EXPECTED or \
            config.get("status") != "DEVELOPMENT_ONLY_NOT_ACTIVE":
        raise ValueError("unrecognized or non-development configuration")
    d = {k: v for k, v in config.items() if k != "status"}
    if any(type(v) is not int for v in d.values()):
        raise ValueError("all progression settings must be integers")
    cap, base, grow = d["level_cap"], d["xp_base"], d["xp_growth"]
    assert isinstance(cap, int)
    if not (2 <= cap <= 100 and 1 <= base <= 65535 and 1 <= grow <= 65535 and
            1 <= d["stat_base"] <= d["stat_max"] <= 100 and
            1 <= d["starting_points"] <= 50 and
            5 * (d["stat_max"]-d["stat_base"]) >= d["starting_points"] and
            1 <= d["remort_kills"] <= 8 and
            60 <= d["remort_seconds"] <= 604800 and
            1 <= d["points_per_remort"] <= 10 and
            1 <= d["legacy_points_cap"] <= 100):
        raise ValueError("settings exceed native 32-bit safety bounds")
    result = [(level, base*(level-1)**2 + grow*(level-1)**3)
              for level in range(1, cap+1)]
    if result[-1][1] > 2147483647:
        raise ValueError("XP threshold exceeds native signed 32-bit long")
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 preview_xp.py progression.sample.json")
    data = json.loads(pathlib.Path(sys.argv[1]).read_text())
    print("LEVEL\tTOTAL_XP\tNEXT_LEVEL_DELTA")
    values = table(data)
    for index, (level, total) in enumerate(values):
        next_delta = values[index+1][1] - total if index+1 < len(values) else 0
        print(f"{level}\t{total}\t{next_delta}")
    print("NOTE: Preview only; this does not change the live MUD.", file=sys.stderr)


if __name__ == "__main__":
    main()
