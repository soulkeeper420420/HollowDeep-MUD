"""Smoke test the candidate and rehearse a binary rollback inside one chroot."""
import hashlib
import os
from pathlib import Path
import runpy
import secrets
import shutil
import string
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)
    print("PASS:", message, flush=True)


def state(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).digest()
        for directory in ("player", "hollowdeep-data")
        for path in (root / directory).rglob("*") if path.is_file()
    }


def main():
    runner, raw_root, previous_binary = sys.argv[1:]
    root = Path(raw_root).resolve(strict=True)
    if (root.name != "rootfs" or not root.parent.name.startswith("round11p-candidate-")
            or root.parent.parent != Path("/root/hollowdeep-dev/guild-social-batch1")):
        raise SystemExit("Expected a new private candidate root")
    sys.argv = [runner, str(root)]
    native = runpy.run_path(runner)
    native["loopback"]()
    native["server_start"]()
    try:
        suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(7))
        character = "Hd" + suffix
        password = "Test" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
        connection, _ = native["make_player"](character, password)
        with connection:
            command = native["command"]
            require("gold granted" not in command(connection, "r9fund").lower(),
                    "Candidate does not grant test funds")
            require("fixture granted" not in command(connection, "r9fund fixture").lower(),
                    "Candidate does not grant the equipment fixture")
            require("unused, purchased Clan Deed" in command(connection, "clan create Nightfall"),
                    "Candidate guild founding requires a purchased deed")
            require("saved" in command(connection, "save").lower(),
                    "Candidate accepts a native character save")
    finally:
        native["server_stop"]()

    saved = state(root)
    require(any(path.startswith("player/") for path in saved), "Candidate save exists on disk")
    binary = root / "bin/hollowdeep"
    shutil.copyfile(previous_binary, binary)
    os.chmod(binary, 0o700)
    os.chown(binary, 65534, 65534)
    native["server_start"].__globals__["PORT"] = 4042
    native["server_start"]()
    try:
        with native["connect"]() as connection:
            require("please enter name" in native["receive"](connection, 8).lower(),
                    "Restored predecessor reaches the native login prompt")
    finally:
        native["server_stop"]()
    require(state(root) == saved, "Binary rollback preserves isolated character and ledger bytes")


if __name__ == "__main__":
    main()
