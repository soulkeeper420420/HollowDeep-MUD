"""Run two process-kill recovery cases against the pinned candidate."""
import hashlib
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import time

runner, raw_root, raw_candidate = sys.argv[1:]
root = Path(raw_root).resolve(strict=True)
if (root.name != "rootfs" or not root.parent.name.startswith("round11p-crash-")
        or root.parent.parent != Path("/root/hollowdeep-dev/guild-social-batch1")):
    raise SystemExit("Expected a disposable crash test stage")
candidate = Path(raw_candidate).read_bytes()
if hashlib.sha256(candidate).hexdigest() != (
        "12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c"):
    raise SystemExit("Unexpected candidate checksum")
sys.argv = [runner, str(root)]
native = runpy.run_path(runner)
runtime = native["server_start"].__globals__
command = native["command"]
stop = native["server_stop"]
name = "Hdcrasha"
password = "Testcrashcase"
data = root / "hollowdeep-data"
registry = data / "player-guilds.v1"
save = root / "player" / name


def require(condition, message):
    if not condition:
        raise RuntimeError(message)
    print("PASS:", message, flush=True)


def start_candidate(port, inject=False):
    runtime["PORT"] = port
    if not inject:
        native["server_start"]()
        return
    with (root.parent / "server.log").open("ab") as log:
        process = subprocess.Popen(
            ["chroot", "--userspec=65534:65534", str(root), "/lib/ld-linux.so.2",
             "--preload", "/bin/crash-rename.so", "/bin/hollowdeep", str(port)],
            cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            preexec_fn=native["limits"],
        )
    runtime["PROCESS"] = process
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError("Interposed candidate exited before login")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.25):
                return
        except OSError:
            time.sleep(.15)
    raise RuntimeError("Interposed candidate did not open its private listener")


def kill_at_rename(connection, marker, label):
    marker.touch()
    native["send"](connection, "clan create Nightfall")
    status = runtime["PROCESS"].wait(timeout=10)
    require(status == -9 and not marker.exists(), label)
    connection.close()
    stop()


try:
    native["loopback"]()
    native["server_start"]()
    connection, _ = native["make_player"](name, password)
    require("3000" in command(connection, "r9fund"), "Seeded disposable founder")
    require("Bought." in command(connection, "buy deed"), "Bought a native serialized deed")
    require("saved" in command(connection, "save").lower(), "Saved founder before the crash")
    stop()
    connection.close()
    old = save.read_bytes()
    (root / "bin/hollowdeep").write_bytes(candidate)
    old_ledger = registry.read_bytes() if registry.exists() else None

    start_candidate(4042, inject=True)
    connection = native["reconnect"](name, password)
    kill_at_rename(connection, data / "kill-before-ledger-rename",
                   "Native process died before the ledger rename")
    require((registry.read_bytes() if registry.exists() else None) == old_ledger
            and save.read_bytes() == old, "Ledger crash preserves both primary files")

    start_candidate(4043, inject=True)
    connection = native["reconnect"](name, password)
    require("Clan Deed" in command(connection, "inventory"), "Deed survives ledger crash")
    kill_at_rename(connection, data / "kill-before-character-rename",
                   "Native process died before the character rename")
    ledger = registry.read_bytes()
    require(b"G Nightfall 6003" in ledger and ledger.count(b"R HDG1") == 1
            and save.read_bytes() == old, "Character crash leaves one committed redemption and the old save")

    start_candidate(4044)
    connection = native["reconnect"](name, password)
    require("6003" in command(connection, "clan hall"), "Committed guild loads after the crash")
    require("Clan Deed" not in command(connection, "inventory"), "Spent deed is reconciled after restart")
    require(registry.read_bytes() == ledger and save.read_bytes() != old,
            "Reconciliation persists without changing the spent ledger")
finally:
    stop()
