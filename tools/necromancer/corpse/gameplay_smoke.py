#!/usr/bin/env python3
"""Private real-game corpse acceptance replay using the accepted ELF32 source.
Requires root in a fresh network namespace; launches only a disposable chroot.
The previous corpse bundle is loaded as data, without invoking its main().
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import resource
import re
import runpy
import shutil
import stat
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

/* Fixture writer only: native file helpers may reference lifecycle cleanup.
   The game listener itself uses the original accepted executable, not stubs. */
void hd_necro_skeleton_on_free(creature *who) { (void)who; }
void merror(const char *what, int severity)
{
    fprintf(stderr, "Private native fixture: %s (%d)\n", what, severity);
    abort();
}
int main(void)
{
    room site = {0};
    creature mob[3] = {{0}}, mage = {0};
    ctag mon[3] = {{0}};
    object item[3] = {{0}};
    otag loot[3] = {{0}};
    const char *victims[] = {"trialwretch", "trialghoul", "trialshade"};
    const char *treasures[] = {"rubyfixture", "amberfixture", "jadefixture"};
    int i, fd;

    strcpy(site.name, "Necromancer Grave Trial");
    site.long_desc = "An isolated and disposable Necromancer trial chamber.";
    site.rom_num = 1;
    site.lolevel = 0;
    site.hilevel = 60;

    for (i = 0; i < 3; ++i) {
        creature *v = &mob[i];
        strcpy(v->name, victims[i]);
        strcpy(v->description, victims[i]);
        v->type = MONSTER; v->class = FIGHTER; v->race = HUMAN;
        v->fd = -1; v->level = 2; v->rom_num = 1;
        v->hpmax = 147 + i; v->hpcur = 1;
        v->mpmax = v->mpcur = 51 + i;
        v->ndice = 1; v->sdice = 1; v->thaco = 20; v->armor = 0;
        strcpy(item[i].name, treasures[i]);
        item[i].parent_crt = v;
        loot[i].obj = &item[i]; v->first_obj = &loot[i];
        mon[i].crt = v;
        if (i < 2) mon[i].next_tag = &mon[i+1];
    }
    site.first_mon = &mon[0];
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
    strcpy(mage.name, "Hdfaithqa");
    assert(hd_store_create_player(mage.name, &mage) == HD_STORE_OK);
    assert(!hd_store_is_necromancer(mage.name));
    puts("PASS: native fixture with three distinct loot-bearing victims and two saved accounts");
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


def login(client: socket.socket, name="Hdnecroqa"):
    recv_until(client, b"Please enter name:")
    send(client, name)
    recv_until(client, b"Please enter password:")
    send(client, "Fixturepass")
    recv_until(client, b"Necromancer Grave Trial")


def collect(client, quiet=0.7, limit=8):
    out = bytearray()
    end = time.monotonic() + limit
    while time.monotonic() < end:
        client.settimeout(min(quiet, max(0.01, end-time.monotonic())))
        try:
            data = client.recv(8192)
        except socket.timeout:
            if out:
                break
            continue
        if not data:
            break
        out.extend(data)
        if len(out) > 262144:
            raise RuntimeError("Unexpected oversized socket response")
    return bytes(out).decode("latin-1", errors="replace")


def command(client, line):
    send(client, line)
    result = collect(client)
    print("COMMAND: " + line + "\n" + result, flush=True)
    return result


def require(text, marker):
    if marker.lower() not in text.lower():
        raise RuntimeError("Missing " + repr(marker) + " in " + repr(text[-1400:]))


def room_view(client):
    return command(client, "look").lower()


def kill_and_find(client, victim, treasure):
    pattern = r"the corpse of\s+" + re.escape(victim) + r"\s+lies here\.\s*\[corpse (\d+)\]"
    for _ in range(6):
        view = room_view(client)
        match = re.search(pattern, view)
        if match:
            if treasure in view:
                raise RuntimeError("Loot appeared before corpse consumption: " + treasure)
            return int(match.group(1))
        command(client, "attack " + victim)
        time.sleep(3.2)
    raise RuntimeError("No visible corpse produced for " + victim)


def after_release(client, corpse, treasure):
    view = room_view(client)
    if f"[corpse {corpse}]" in view or treasure not in view:
        raise RuntimeError("Corpse not consumed or expected loot absent")
    # Repeating a consumed ID must be rejected; room item count may be
    # abbreviated by the native display. Exact multiplicity is a C-test gate.
    require(command(client, f"loot corpse {corpse}"), "No such corpse is here.")
    require(room_view(client), treasure)


def prepare_chroot(exe, stage):
    if os.geteuid() != 0:
        raise RuntimeError("Run from the private root console")
    target = stage / "bin/hollowdeep"
    shutil.copyfile(exe, target)
    target.chmod(0o755)
    report = subprocess.check_output(["ldd", str(exe)], text=True)
    for line in report.splitlines():
        if "not found" in line:
            raise RuntimeError("Missing executable dependency: " + line)
        match = re.search(r"(?:=>\s*|^\s*)(/[^ \t]+)\s+\(", line)
        if not match:
            continue
        lib = Path(match.group(1))
        dest = stage / str(lib).lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(lib.resolve(strict=True), dest)
        dest.chmod(0o755)
    (stage/"dev").mkdir()
    os.mknod(stage/"dev/urandom", stat.S_IFCHR | 0o444, os.makedev(1,9))
    (stage/"dev/urandom").chmod(0o444)
    (stage/"etc").mkdir()
    (stage/"etc/hosts").write_text("127.0.0.1 localhost\n")
    # Only the private fixture is writable by the unprivileged listener.
    os.chown(stage, 65534, 65534)
    stage.chmod(0o700)
    for folder in ("rooms", "player", "log", "objmon", "post", "help", "hollowdeep-data"):
        directory = stage / folder
        for path in [directory, *directory.rglob("*")]:
            os.chown(path, 65534, 65534)
            path.chmod(0o700 if path.is_dir() else 0o600)


def run_socket_replay(exe: Path, stage: Path) -> None:
    prepare_chroot(exe, stage)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    log_path = stage / "isolated-game.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen(["chroot", "--userspec=65534:65534", "--groups=65534",
                                    str(stage), "/bin/hollowdeep", str(port)],
                                   cwd=stage, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   env={"PATH": "/usr/bin:/bin", "HOLLOWDEEP_BIND": "127.0.0.1"})
        try:
            with connect_game(port, process) as sock:
                login(sock)
                collect(sock)
                require(command(sock, "help corpse"), "MONSTER CORPSES")
                require(command(sock, "help deity"), "DEITIES AND CORPSE SACRIFICE")
                require(command(sock, "help raise skeleton"), "RAISE SKELETON")
                first = kill_and_find(sock, "trialwretch", "rubyfixture")
                require(command(sock, f"sacrifice corpse {first}"), "assigned deity")
                require(room_view(sock), f"[corpse {first}]")
                if "rubyfixture" in room_view(sock):
                    raise RuntimeError("Denied sacrifice released loot")
                raised = command(sock, f"raise corpse {first}")
                require(raised, "You raise a skeleton (147 HP / 51 MP).")
                require(raised, "loot falls to the ground")
                after_release(sock, first, "rubyfixture")
                print("PASS: native kill, deity denial, corpse raise, inherited HP/MP and visible loot")
                second = kill_and_find(sock, "trialghoul", "amberfixture")
                require(command(sock, f"raise corpse {second}"), "already command a skeleton")
                require(room_view(sock), f"[corpse {second}]")
                require(command(sock, f"loot corpse {second}"), "loot falls to the ground")
                after_release(sock, second, "amberfixture")
                print("PASS: one-skeleton limit preserves another corpse; ordinary loot releases it once")
                third = kill_and_find(sock, "trialshade", "jadefixture")
                # Keep the Necromancer logged in so the room stays active.
                with connect_game(port, process) as faithful:
                    login(faithful, "Hdfaithqa")
                    collect(faithful)
                    require(command(faithful, f"raise corpse {third}"), "Only Necromancers")
                    require(room_view(faithful), f"[corpse {third}]")
                    require(command(faithful, f"sacrifice corpse {third}"), "You sacrifice the corpse")
                    after_release(faithful, third, "jadefixture")
                    print("PASS: assigned deity sacrifices a real corpse; repeat ID rejected")
                    send(sock, "quit")
                    recv_until(sock, b"Goodbye!")
                    with connect_game(port, process) as rejoined:
                        login(rejoined)
                        require(room_view(rejoined), "skeleton")
                        print("PASS: surviving skeleton visible after same-process reconnect")
            print("CORPSE: REAL NATIVE SOCKET RAISE/SACRIFICE/LOOT/HELP PASS", flush=True)
        except Exception:
            print("PRIVATE LISTENER LOG (tail):\n" + log_path.read_text(errors="replace")[-3200:], flush=True)
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
    parser.add_argument("bundle", type=Path, help="pinned corpse onepass bundle, read only for exact source and help files")
    args = parser.parse_args()
    root = Path("/root/hollowdeep-dev")
    if args.source.is_symlink():
        raise SystemExit("Refusing symlinked source input")
    src = args.source.resolve(strict=True)
    if (not str(src).startswith(str(root) + "/necromancer-playtest-")
            or src.name != "src" or not src.is_dir() or src.is_symlink()):
        raise SystemExit("Refusing non-disposable source directory")
    if src.parent.name != "necromancer-playtest-corpse-3nl5y8b7":
        raise SystemExit("Run against the operator-verified corpse ELF32 candidate")
    if os.geteuid() != 0 or os.readlink("/proc/self/ns/net") == os.readlink("/proc/1/ns/net"):
        raise SystemExit("Run in a separate network namespace with loopback enabled")
    payload = runpy.run_path(str(args.bundle.resolve(strict=True)))["PAYLOAD"]
    for filename in ("hd_corpse.c", "hd_corpse.h"):
        p = src / filename
        if p.is_symlink() or p.read_bytes() != payload[filename].encode("utf-8"):
            raise SystemExit("Private corpse source mismatch: " + filename)
    for filename, marker in (("creature.c", "hd_corpse_capture"),
                             ("hd_necro_skeleton.c", "hd_necro_raise_from_corpse"),
                             ("hollowdeep_help.c", "necromancer-corpses"),
                             ("Makefile", "HD_CORPSE_PLAYTEST")):
        p = src / filename
        if p.is_symlink() or marker not in p.read_text("latin-1"):
            raise SystemExit("Missing private native hook: " + filename)
    exe = src / "frp.new"
    abi = "-m32"
    if not exe.is_file() or exe.is_symlink() or not os.access(exe, os.X_OK):
        raise SystemExit("Missing private executable")
    expected_header = b"\x7fELF\x01"
    with exe.open("rb") as f:
        if f.read(5) != expected_header:
            raise SystemExit("Private engine ELF class mismatch")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    stage = Path(tempfile.mkdtemp(prefix="necromancer-socket-", dir=root))
    print(f"Private disposable world: {stage}", flush=True)
    for dirname in ("rooms", "player", "log", "objmon", "post", "help", "bin", "hollowdeep-data"):
        (stage / dirname).mkdir(mode=0o700)
    print("Accepted executable SHA256: " + hashlib.sha256(exe.read_bytes()).hexdigest(), flush=True)
    for name, body in payload.items():
        if name.startswith("help/") and "/" not in name[5:]:
            (stage / name).write_bytes(body.encode("utf-8"))
    # Only an isolated fixture assignment; DM command itself was covered by
    # its native C test. No production faith record is read or changed.
    (stage/"hollowdeep-data/deities.db").write_text("HOLLOWDEEP_DEITIES 1 1\nHdfaithqa 3\n")
    fixture_exe = compile_fixture(src, stage, abi)
    subprocess.run([str(fixture_exe)], check=True, cwd=stage)
    run_socket_replay(exe, stage)
    print("PRODUCTION DEPLOYMENT: NONE", flush=True)
    print(f"Private test logs and fixtures: {stage}", flush=True)


if __name__ == "__main__":
    main()
