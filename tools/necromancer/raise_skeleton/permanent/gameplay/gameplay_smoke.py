#!/usr/bin/env python3
"""Disposable *real-game* Raise Skeleton socket smoke; no production files used.

Pass the exact private Necromancer ELF32 source tree from the successful
Round74B-integrated build.  Creates a fresh world and test account below
/root/hollowdeep-dev, and starts a loopback-only listener on a random port.
Neither production service nor its player/room directory is accessed.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import resource
import socket
import subprocess
import tempfile
import time

SOURCE = r'''
#include "hd_player_store.h"
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

void merror(const char *what, int severity)
{
    fprintf(stderr, "Private native fixture: %s (%d)\n", what, severity);
    abort();
}
int main(void)
{
    room site = {0};
    creature victim = {0}, mage = {0};
    ctag mon = {0};
    int fd;

    strcpy(site.name, "Necromancer Grave Trial");
    site.long_desc = "An isolated and disposable Necromancer trial chamber.";
    site.rom_num = 1;
    site.lolevel = 0;
    site.hilevel = 60;

    strcpy(victim.name, "trialwretch");
    strcpy(victim.description, "A trial wretch stands here awaiting defeat.");
    victim.type = MONSTER;
    victim.class = FIGHTER;
    victim.race = HUMAN;
    victim.fd = -1;
    victim.level = 2;
    victim.rom_num = 1;
    victim.hpmax = 147;
    victim.hpcur = 1;
    victim.mpmax = 51;
    victim.mpcur = 51;
    victim.ndice = 1;
    victim.sdice = 1;
    victim.thaco = 20;
    victim.armor = 0;
    mon.crt = &victim;
    site.first_mon = &mon;
    fd = open("rooms/r00001", O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600);
    assert(fd >= 0);
    assert(write_rom(fd, &site, ALLITEMS) == 0);
    assert(fsync(fd) == 0);
    assert(close(fd) == 0);

    strcpy(mage.name, "Hdnecroqa");
    strcpy(mage.password, "Fixturepass");
    mage.type = PLAYER;
    mage.class = MAGE;
    mage.race = HUMAN;
    mage.fd = -1;
    mage.rom_num = 1;
    mage.level = 8;
    mage.experience = 10000;
    mage.hpmax = mage.hpcur = 1000;
    mage.mpmax = mage.mpcur = 110;
    mage.strength = 18;
    mage.dexterity = 18;
    mage.constitution = 18;
    mage.intelligence = 18;
    mage.piety = 10;
    mage.thaco = -40;
    mage.ndice = 5;
    mage.sdice = 20;
    mage.gold = 1000;
    assert(hd_store_create_necromancer(mage.name, &mage) == HD_STORE_OK);
    assert(hd_store_verified_remorts(mage.name) == 0);
    assert(hd_store_is_necromancer(mage.name));
    puts("PASS: fixture holds native Necromancer save and 147 HP / 51 MP victim");
    return 0;
}
'''


def compile_fixture(src: Path, stage: Path, abi: str) -> Path:
    fixture_c = stage / "seed.c"
    fixture_c.write_text(SOURCE)
    exe = stage / "seed"
    components = ("files1", "files3", "compress", "hd_player_store",
                  "treasure_receipt", "atomic_player_snapshot")
    cmd = [os.environ.get("CC", "cc"), abi, "-std=gnu89", "-O1", "-g",
           "-DCOMPRESS", "-DHD_NECROMANCER_PLAYTEST", "-fcommon",
           "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
           "-Wno-implicit-function-declaration", "-Wno-int-conversion",
           "-Wno-incompatible-pointer-types", "-I", str(src),
           str(fixture_c), *(str(src / (f + ".c")) for f in components),
           "-o", str(exe)]
    subprocess.run(cmd, check=True, cwd=stage, stdout=subprocess.DEVNULL)
    return exe


def recv_until(client: socket.socket, marker: bytes, seconds: float = 10) -> bytes:
    end = time.monotonic() + seconds
    result = bytearray()
    while time.monotonic() < end:
        client.settimeout(max(0.02, min(1, end - time.monotonic())))
        try:
            part = client.recv(8192)
        except socket.timeout:
            continue
        if not part:
            break
        result.extend(part)
        if marker.lower() in result.lower():
            return bytes(result)
    raise RuntimeError(f"Did not see {marker!r}; last reply: {bytes(result[-1100:])!r}")


def send(client: socket.socket, line: str):
    client.sendall(line.encode("ascii") + b"\r\n")


def connect_game(port: int, process: subprocess.Popen) -> socket.socket:
    end = time.monotonic() + 12
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError(f"Isolated game exited (status {process.returncode})")
        try:
            return socket.create_connection(("127.0.0.1", port), timeout=0.35)
        except OSError:
            time.sleep(0.08)
    raise RuntimeError("Isolated game listener never started")


def login(client: socket.socket):
    recv_until(client, b"Please enter name:")
    send(client, "Hdnecroqa")
    recv_until(client, b"Please enter password:")
    send(client, "Fixturepass")
    recv_until(client, b"Necromancer Grave Trial")


def run_socket_replay(exe: Path, stage: Path) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    log_path = stage / "isolated-game.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen([str(exe), str(port)], cwd=stage,
                                   stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={"PATH": "/usr/bin:/bin", "HOLLOWDEEP_BIND": "127.0.0.1"})
        try:
            with connect_game(port, process) as sock:
                login(sock)
                # Keep the native kill path intact: the target has 1 HP, 147 max HP.
                send(sock, "attack trialwretch")
                reply = recv_until(sock, b"trialwretch", seconds=10)
                # No direct monster stat writes: we retry only for a natural miss.
                for retry in range(4):
                    if b"vanquish" in reply.lower() or b"death of" in reply.lower() or b"dead" in reply.lower():
                        break
                    time.sleep(3.1)
                    send(sock, "attack trialwretch")
                    reply = recv_until(sock, b"trialwretch", seconds=9)
                # The decisive contract is an authenticated kill snapshot for raising.
                send(sock, "raise skeleton")
                reply = recv_until(sock, b"You raise a skeleton (147 HP / 51 MP).", seconds=10)
                if b"You raise a skeleton (147 HP / 51 MP)." not in reply:
                    raise RuntimeError("Native kill did not result in 147HP/51MP summon: " + repr(reply[-1300:]))
                print("PASS: socket login, native kill, 8MP raise with inherited 147HP/51MP")
                send(sock, "raise skeleton")
                reject = recv_until(sock, b"already command a skeleton", seconds=8)
                assert b"already command a skeleton" in reject.lower()
                print("PASS: second summon denied with existing living skeleton")
                send(sock, "quit")
                recv_until(sock, b"Goodbye!", seconds=8)
            with connect_game(port, process) as sock:
                login(sock)
                send(sock, "look")
                visible = recv_until(sock, b"skeleton", seconds=10)
                if b"skeleton" not in visible.lower():
                    raise RuntimeError("Skeleton absent after same-process relogin")
                print("PASS: skeleton visible on same-process reconnect")
            print("NECROMANCER: REAL NATIVE SOCKET KILL/RAISE/RECONNECT PASS")
        except Exception:
            try:
                print("PRIVATE LISTENER LOG (tail):\n" + log_path.read_text(errors="replace")[-2600:])
            except OSError:
                pass
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="private already-built native source directory")
    parser.add_argument("--native64", action="store_true", help="run a test on a specifically built ELF64 (not release acceptance)")
    args = parser.parse_args()
    root = Path("/root/hollowdeep-dev")
    if args.source.is_symlink():
        raise SystemExit("Refusing symlinked source input")
    src = args.source.resolve(strict=True)
    if (not str(src).startswith(str(root) + "/necromancer-playtest-")
            or src.name != "src" or not src.is_dir() or src.is_symlink()):
        raise SystemExit("Refusing non-disposable source directory")
    expected_skill = "1aaa3bb54dbefda6e8d706dfc42e20c55c7e1018d5ddcaa9972ad89c77da5e75"
    skill_path = src / "hd_necro_skeleton.c"
    if not skill_path.is_file() or skill_path.is_symlink() or hashlib.sha256(skill_path.read_bytes()).hexdigest() != expected_skill:
        raise SystemExit("Private skill source differs from the exact tested untimed build")
    for filename, marker in (("creature.c", "hd_necro_skeleton_record_kill"),
                             ("command1.c", "hd_necro_skeleton_reconnect"),
                             ("magic1.c", "hd_necro_skeleton_can_heal")):
        source_file = src / filename
        if source_file.is_symlink() or not source_file.is_file() or marker not in source_file.read_text(encoding="latin-1"):
            raise SystemExit("Missing expected private native hook in " + filename)
    exe = src / "frp.new"
    abi = "-m64" if args.native64 else "-m32"
    if not exe.is_file() or exe.is_symlink() or not os.access(exe, os.X_OK):
        raise SystemExit("Missing private executable")
    expected_header = b"\x7fELF\x02" if args.native64 else b"\x7fELF\x01"
    with exe.open("rb") as f:
        if f.read(5) != expected_header:
            raise SystemExit("Private engine ELF class mismatch")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    stage = Path(tempfile.mkdtemp(prefix="necromancer-socket-", dir=root))
    print(f"Private disposable world: {stage}", flush=True)
    for dirname in ("rooms", "player", "log", "objmon", "post", "help", "bin", "hollowdeep-data"):
        (stage / dirname).mkdir(mode=0o700)
    fixture_exe = compile_fixture(src, stage, abi)
    subprocess.run([str(fixture_exe)], check=True, cwd=stage)
    run_socket_replay(exe, stage)
    print("PRODUCTION DEPLOYMENT: NONE", flush=True)
    print(f"Private test logs and fixtures: {stage}", flush=True)


if __name__ == "__main__":
    main()
