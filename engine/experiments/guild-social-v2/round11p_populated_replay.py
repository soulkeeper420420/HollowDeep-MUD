"""Switch a populated private replay to the pinned hook-free candidate."""
import hashlib
import os
from pathlib import Path
import runpy
import sys

baseline = runpy.run_path(str(Path(__file__).with_name("round11n_patch.py")))
replace = baseline["replace"]
stage = Path(sys.argv[1])

for variable, filename, expected in (
    ("HD_EXACT_CANDIDATE", "candidate.bin",
     "12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c"),
    ("HD_ROLLBACK_BINARY", "predecessor.bin",
     "b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5"),
):
    source = Path(os.environ[variable]).resolve(strict=True)
    binary = source.read_bytes()
    if hashlib.sha256(binary).hexdigest() != expected:
        raise SystemExit(f"Unexpected binary checksum for {variable}")
    (stage / filename).write_bytes(binary)

runner = stage / "runner.py"
replace(runner, "import socket, string, struct, subprocess, sys, time",
        "import hashlib, socket, string, struct, subprocess, sys, time")
replace(runner, "    PORT = 4042", '''    install_rehearsal_binary("candidate.bin")
    PORT = 4042''')
replace(runner, "def tested():", '''def install_rehearsal_binary(name):
    binary = ROOT / "bin/hollowdeep"
    binary.write_bytes((RUN / name).read_bytes())


def saved_state():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).digest()
            for directory in ("player", "hollowdeep-data")
            for path in (ROOT / directory).rglob("*") if path.is_file()}


def tested():''')
replace(runner, "    a = reconnect(name_a,pw_a)", '''    registry.write_bytes(b"HDINVALID\\n")
    try:
        a = reconnect(name_a,pw_a)
        location = command(a, "look")
        check("Login redirects a saved hall occupant when the ledger is invalid",
              "square" in location.lower(), location)
    finally:
        registry.write_bytes(original_registry)''')
replace(runner, "def main():", '''    staff = ROOT / "hollowdeep-data/staff.db"
    staff.write_text("INVALID\\n")
    os.chown(staff, 65534, 65534)
    staff.chmod(0o600)
    try:
        own_hall = command(b, "north")
        check("Invalid staff database falls back to valid guild membership",
              "Starter Hall A Entrance" in own_hall, own_hall)
        command(b, "south")
        cross_hall = command(b, "east")
        check("Invalid staff database does not grant cross-guild access",
              "restricted to its members" in cross_hall.lower(), cross_hall)
        staff.write_text(f"HOLLOWDEEP_STAFF 1 1 0\\n{name_b} 1 0\\n")
        staff_hall = command(b, "east")
        check("Valid moderator role grants cross-guild hall access",
              "Starter Hall B Entrance" in staff_hall, staff_hall)
    finally:
        staff.unlink()

    # Stop the private candidate, then snapshot its populated state and
    # start the exact current production predecessor from its private copy.
    server_stop()
    populated = saved_state()
    install_rehearsal_binary("predecessor.bin")
    PORT = 4043
    server_start()
    with connect() as probe:
        greeting = receive(probe, 8)
        check("Exact production predecessor starts with populated candidate state",
              "please enter name" in greeting.lower())
    server_stop()
    check("Predecessor boot preserves populated player and ledger bytes",
          saved_state() == populated and len(populated) >= 4)


def main():''')
