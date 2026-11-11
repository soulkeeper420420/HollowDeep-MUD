"""Test three alternate movement routes and exact rollback in a private root."""
import hashlib
import os
from pathlib import Path
import runpy
import shutil
import socket
import struct
import subprocess
import sys
import time

runner, root_arg = sys.argv[1:]
root = Path(root_arg).resolve(strict=True)
stage = root.parent
if (root.name != "rootfs" or not stage.name.startswith("round11q-")
        or stage.parent != Path("/root/hollowdeep-dev/guild-social-batch1")):
    raise SystemExit("Expected a disposable Round 11Q root")
sys.argv = [runner, str(root)]
native = runpy.run_path(runner)
runtime = native["server_start"].__globals__
stop = native["server_stop"]
command = native["command"]
reconnect = native["reconnect"]
uid, gid = root.stat().st_uid, root.stat().st_gid
chroot = ["chroot", f"--userspec={uid}:{gid}", str(root)]
data = root / "hollowdeep-data"
staff_file = data / "staff.db"
rng_file = data / "round11q-rng"
binary = root / "bin/hollowdeep"
password = "Testprivately"
walker, staff, rollback = "Hdspellqa", "Hdstaffqa", "Hdrestoreqa"
port = 4040


def require(ok, message, detail=""):
    if not ok:
        raise RuntimeError(f"{message}. Response: {detail[-380:]!r}")
    print("PASS:", message, flush=True)


def start(inject=False):
    global port
    port += 1
    runtime["PORT"] = port
    loader = ["/lib/ld-linux.so.2", "--preload", "/bin/fixture-rng.so"] if inject else []
    with (stage / "server.log").open("ab") as log:
        process = subprocess.Popen(
            [*chroot, *loader, "/bin/hollowdeep", str(port)],
            cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            preexec_fn=native["limits"],
        )
    runtime["PROCESS"] = process
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError("Native listener exited during startup")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.25):
                return
        except OSError:
            time.sleep(.15)
    raise RuntimeError("Native listener did not start")


def set_role(name=None):
    if name is None:
        staff_file.unlink(missing_ok=True)
        return
    staff_file.write_text(f"HOLLOWDEEP_STAFF 1 1 0\n{name} 1 0\n")
    os.chown(staff_file, uid, gid)
    staff_file.chmod(0o600)


def fixture(*args):
    return subprocess.check_output([*chroot, "/bin/fixture", *args],
                                   cwd=root, text=True)


def reset(name, kind):
    fixture(name, kind)


def trap_room(original, hall, trap_offset, exit_offset):
    body = bytearray(original)
    body[trap_offset] = 1
    struct.pack_into("<h", body, exit_offset, hall)
    (root / "rooms/r06000").write_bytes(body)


def state():
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in ("player", "hollowdeep-data")
        for path in (root / directory).rglob("*") if path.is_file()
    }


def restore():
    predecessor = stage / "predecessor"
    (stage / "src_3.00").rename(stage / "candidate-source")
    (root / "rooms").rename(stage / "candidate-rooms")
    for name, destination in (("src_3.00", stage), ("rooms", root)):
        subprocess.run(["cp", "-a", str(predecessor / name), str(destination)], check=True)
    binary.write_bytes((predecessor / "src_3.00/frp.new").read_bytes())


try:
    native["loopback"]()
    start()
    clients = []
    for name in (walker, staff, rollback):
        connection, _ = native["make_player"](name, password)
        clients.append(connection)
        require("saved" in command(connection, "save").lower(), f"Native save created for {name}")
    stop()
    for connection in clients:
        connection.close()
    original = (root / "rooms/r06000").read_bytes()
    trap_offset, exit_offset = map(int, fixture().split())
    for hall, letter in ((6003, "A"), (6006, "B"), (6009, "C")):
        title = f"Starter Hall {letter} Entrance"
        set_role()
        reset(walker, "spell")
        reset(staff, "staff")
        trap_room(original, hall, trap_offset, exit_offset)
        rng_file.write_text(str((hall - 1) * 10))
        rng_file.chmod(0o644)
        start(inject=True)
        with reconnect(walker, password) as connection:
            spell = command(connection, "cast teleport")
            require("Teleport spell cast" in spell and "restricted to its members" in spell
                    and title not in spell, f"Spell teleport denied to hall {letter}", spell)
            set_role(walker)
            spell = command(connection, "cast teleport")
            require("Teleport spell cast" in spell and title in spell,
                    f"Authorized spell teleport reaches hall {letter}", spell)
            command(connection, {"A": "south", "B": "west", "C": "north"}[letter])
            set_role()
            rng_file.write_text("500")
            trap = command(connection, "west")
            require("fell into a pit trap" in trap and "restricted to its members" in trap
                    and title not in trap, f"Pit trap denied to hall {letter}", trap)
            set_role(walker)
            trap = command(connection, "west")
            require("fell into a pit trap" in trap and title in trap,
                    f"Authorized pit trap reaches hall {letter}", trap)
        set_role()
        with reconnect(staff, password) as connection:
            teleport = command(connection, f"*teleport {hall}")
            require("restricted to its members" in teleport and title not in teleport,
                    f"Native staff teleport denied without guild or sidecar role for hall {letter}", teleport)
            set_role(staff)
            teleport = command(connection, f"*teleport {hall}")
            require(title in teleport, f"Authorized native staff teleport reaches hall {letter}", teleport)
        stop()
    set_role()
    rng_file.unlink()
    before = state()
    restore()
    require(state() == before, "Full isolated rollback preserves saved state bytes")
    start()
    with reconnect(rollback, password) as connection:
        response = command(connection, "score")
        require("gold pieces" in response.lower(), "Saved candidate character logs in on the exact predecessor", response)
finally:
    stop()
