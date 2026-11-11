#!/usr/bin/env python3
"""Round11S one-shot pre-rename EIO and post-rename dir-fsync EIO replay.

Must run only under unshare --mount --net --pid --fork against a fresh rootfs
created by round11s_fsync_private.sh. No real user data is accessed.
"""
import hashlib
import os
from pathlib import Path
import runpy
import signal
import socket
import subprocess
import sys
import time

if len(sys.argv) != 3:
    raise SystemExit("Usage: round11s_fsync_replay.py RUNNER PRIVATE_ROOTFS")
runner = Path(sys.argv[1]).resolve(strict=True)
root = Path(sys.argv[2]).resolve(strict=True)
stage = root.parent
base = Path("/root/hollowdeep-dev/guild-social-batch1")
if (root.name != "rootfs" or stage.parent != base or
        not stage.name.startswith("round11s-fsync-") or
        runner != stage / "runner.py"):
    raise SystemExit("STOP: invalid private fsync fault test workspace")

EXPECTED = "8dbd6cd1d03b763ff0f454bba11861dd9470052716e2624838f5fec919c7f446"
binary = root / "bin/hollowdeep"
if hashlib.sha256(binary.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit("STOP: private Round11S binary checksum changed")

data = root / "hollowdeep-data"
players = root / "player"
registry = data / "player-guilds.v1"
name = "Hdfsynca"
password = "Testfsynccase"
save_path = players / name
count = 0
client = None

orig_argv = sys.argv[:]
sys.argv = [str(runner), str(root)]
try:
    native = runpy.run_path(str(runner))
finally:
    sys.argv = orig_argv
runtime = native["server_start"].__globals__
command = native["command"]
stop = native["server_stop"]


def require(ok, label, detail=""):
    global count
    if not ok:
        raise RuntimeError("FAIL: " + label + (": " + repr(str(detail)[-360:]) if detail else ""))
    count += 1
    print("PASS:", label, flush=True)


def start(port):
    runtime["PORT"] = port
    with (stage / "server.log").open("ab") as log:
        process = subprocess.Popen(
            ["chroot", "--userspec=65534:65534", str(root),
             "/lib/ld-linux.so.2", "--preload",
             "/bin/round11s-fsync-fault.so", "/bin/hollowdeep", str(port)],
            cwd=str(root), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, preexec_fn=native["limits"],
        )
    runtime["PROCESS"] = process
    for _ in range(85):
        if process.poll() is not None:
            raise RuntimeError("Private MUD exited before binding: see private server.log")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.25):
                return
        except OSError:
            time.sleep(.15)
    raise RuntimeError("Private MUD listener did not start")


def marker(name):
    path = data / name
    if path.exists() or path.is_symlink():
        raise RuntimeError("STOP: leftover fault marker in fresh stage")
    path.touch(mode=0o600)
    return path


def primary_bytes():
    return registry.read_bytes() if registry.exists() else None


try:
    require(not any(players.iterdir()) and not any(data.iterdir()),
            "Disposable accounts and guild ledger initially empty")
    native["loopback"]()
    start(4042)
    client, _ = native["make_player"](name, password)
    require("gold granted: 3000" in command(client, "r9fund").lower(),
            "Test-only player funds granted")
    require("Bought." in command(client, "buy deed"),
            "Real native minted Clan Deed purchased")
    require("Clan Deed" in command(client, "inventory"),
            "Unspent physical deed initially carried")
    saved = command(client, "save")
    require("saved" in saved.lower() and save_path.is_file() and
            save_path.stat().st_size > 0, "Original character save committed")
    initial_player = save_path.read_bytes()
    initial_ledger = primary_bytes()

    rename_marker = marker("inject-ledger-rename-eio")
    pre = command(client, "clan create Nightfall")
    require("failed before commit" in pre.lower() and not rename_marker.exists(),
            "Injected pre-rename EIO reports definite failure", pre)
    require(primary_bytes() == initial_ledger and
            "Clan Deed" in command(client, "inventory") and
            save_path.read_bytes() == initial_player,
            "Pre-rename failure preserves ledger, deed and character save")

    fsync_marker = marker("inject-dir-fsync-eio")
    uncertain = command(client, "clan create Nightfall")
    require("ledger durability uncertain" in uncertain.lower() and
            "retained pending reconciliation" in uncertain.lower() and
            "guild records updated" not in uncertain.lower(),
            "Post-rename directory fsync EIO reports uncertainty, not success", uncertain)
    require(not fsync_marker.exists(), "Fault interposer actually intercepted directory fsync")
    ledger = primary_bytes()
    require(ledger is not None and
            b"HDGUILD2\n" in ledger and
            b"G Nightfall 6003\n" in ledger and
            ledger.count(b"R HDG1") == 1 and
            name.encode("ascii") in ledger,
            "Renamed ledger retains exactly one redeemed serial", ledger)
    require("Clan Deed" in command(client, "inventory") and
            save_path.read_bytes() == initial_player,
            "Uncertain commit did not consume deed or overwrite old character save")

    # A sudden process death prevents graceful disconnect/quit saving from
    # hiding whether the old character file can recover from an uncertain commit.
    process = runtime["PROCESS"]
    os.killpg(process.pid, signal.SIGKILL)
    require(process.wait(timeout=8) == -signal.SIGKILL,
            "Private native process killed before character autosave")
    runtime["PROCESS"] = None
    client.close()
    client = None
    require(save_path.read_bytes() == initial_player and primary_bytes() == ledger,
            "Uncertain ledger and old character bytes survive process termination")

    start(4043)
    client = native["reconnect"](name, password)
    require("Clan Deed" in command(client, "inventory"),
            "Old saved deed was present on restart before reconciliation")
    recovered = command(client, "clan hall")
    require("previously redeemed clan deed reconciled" in recovered.lower() and
            "6003" in recovered,
            "First clan command reconciles one spent deed and retains hall access", recovered)
    require("Clan Deed" not in command(client, "inventory") and
            save_path.read_bytes() != initial_player and
            primary_bytes() == ledger,
            "Reconciliation persists character without modifying guild ledger")
    repeat = command(client, "clan hall")
    require("previously redeemed" not in repeat.lower() and
            "6003" in repeat and primary_bytes() == ledger,
            "Second clan command is idempotent")
    other = command(client, "clan create Dawnwatch")
    require("leave your existing guild" in other.lower() and
            primary_bytes() == ledger,
            "Spent founder cannot redeem same deed into another guild", other)
    print("=== ROUND 11S FSYNC FAILURE SUMMARY ===", flush=True)
    print("Passed:", count, flush=True)
    print("Failed: 0", flush=True)
    print("No real player saves were read or modified", flush=True)
    print("Power-loss durability is NOT certified", flush=True)
finally:
    if client is not None:
        try:
            client.close()
        except OSError:
            pass
    stop()
