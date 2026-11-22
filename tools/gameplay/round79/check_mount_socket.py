"""Create a synthetic native world using the existing Round 79P fixture."""
from pathlib import Path
import os
import runpy
import sys
import time

here = Path(__file__).resolve().parent
original = here / "check_breath_rest_socket.py"
text = original.read_text()
text = text.replace('hd-army-game-round79rest-', 'hd-army-game-round79mount-')
cut = text.index("\ntry:\n    with log.open")
scope = {"__file__": str(original), "__name__": "round79t_fixture"}
exec(compile(text[:cut], str(original), "exec"), scope)
world, prior = scope["world"], scope["prior"]
ask, clean = scope["ask"], scope["clean"]
source = Path(sys.argv[1])
stable = world / "rooms/stables.map"
stable.write_text("HDSTABLE1\n2\n", encoding="ascii")
os.chown(stable, 65534, 65534)
stable.chmod(0o600)
process = None


def start():
    global process
    with scope["socket"].socket() as sock:
        sock.bind(("127.0.0.1", 0))
        scope["port"] = sock.getsockname()[1]
    with scope["log"].open("ab") as out:
        process = scope["subprocess"].Popen(
            [scope["chroot"], "--userspec=65534:65534", "--groups=65534",
             str(world), "/bin/hollowdeep", str(scope["port"])],
            cwd=world, env={"PATH": "/usr/bin:/bin", "HOLLOWDEEP_BIND": "127.0.0.1"},
            stdout=out, stderr=out,
        )
    scope["process"] = process


def stop():
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except scope["subprocess"].TimeoutExpired:
            process.kill()
            process.wait()


def login():
    player = prior["connect_game"](scope["port"], process)
    prior["recv_until"](player, b"Please enter name:")
    prior["send"](player, "Hdnecroqa")
    prior["recv_until"](player, b"Please enter password:")
    prior["send"](player, "Fixturepass")
    prior["recv_until"](player, b"Breath", seconds=15)
    return player


try:
    start()
    with login() as player:
        ask(player, "mounts", "Owned mounts: 0/6")
        ask(player, "stable buy 1", "denied")
        ask(player, "north", "Necromancer Trial Annex")
        before = clean(prior["command"](player, "score"))
        ask(player, "stable buy 1", "Mount change saved.")
        ask(player, "mounts", "Horse Endurance 120/120 present")
        after = clean(prior["command"](player, "score"))
        import re
        money = lambda s: int(re.search(r"(\d+) Gold Pieces", s)[1])
        assert money(before) - money(after) == 100
        print("PASS: native purchase saves ownership with one exact gold debit", flush=True)
        ask(player, "mount 1", "Mount change saved.")
        ask(player, "mount 1", "denied")
        ask(player, "stable deposit 1", "Mount change saved.")
        ask(player, "mount 1", "denied")
        ask(player, "stable retrieve 1", "Mount change saved.")
        ask(player, "mount 1", "Mount change saved.")
        ask(player, "east", "Test Wilderness Meadow")
        ask(player, "mounts", "Horse Endurance 119/120")
        ask(player, "skills", "Breath 100/100")
        ask(player, "north", "Test Wilderness Ridge")
        ask(player, "mounts", "Horse Endurance 117/120")
        ask(player, "skills", "Breath 100/100")
        ask(player, "go east", "don't see")
        ask(player, "mounts", "Horse Endurance 117/120")
        ask(player, "stable deposit 1", "denied")
        ask(player, "save", "Player saved.")
        print("PASS: mounted native moves debit terrain Endurance, failed moves and remote stables are denied", flush=True)
        process.kill()
        process.wait(timeout=5)
    start()
    with login() as player:
        ask(player, "mounts", "Horse Endurance 117/120")
        ask(player, "mounts", "Riding: 1")
        ask(player, "south", "Test Wilderness Meadow")
        ask(player, "mounts", "Horse Endurance 116/120")
        ask(player, "go west", "Necromancer Trial Annex")
        ask(player, "mounts", "Horse Endurance 116/120")
        ask(player, "dismount", "Mount change saved.")
        ask(player, "stable deposit 1", "Mount change saved.")
        ask(player, "save", "Player saved.")
        prior["quit_with_cooldown"](player, process)
    with login() as player:
        ask(player, "mounts", "stabled at room 2")
        ask(player, "stable retrieve 1", "Mount change saved.")
        ask(player, "mounts", "Horse Endurance 116/120 present")
        ask(player, "east", "Test Wilderness Meadow")
        ask(player, "skills", "Breath 98/100")
        ask(player, "mounts", "Horse Endurance 116/120")
        print("PASS: native crash, reconnect, stable persistence, free retreat and foot Breath isolation", flush=True)
        prior["quit_with_cooldown"](player, process)
finally:
    stop()
print("ROUND79T: ISOLATED NATIVE MOUNT GAMEPLAY PASS", flush=True)
