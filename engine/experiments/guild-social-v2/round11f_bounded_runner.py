#!/usr/bin/env python3
"""
Round 11F: bounded native load + strict corruption test, guild halls and deed redemption.
Only run in a private net/pid/mount namespace against a disposable rootfs.
No live server, live credentials, or production world files are used.
"""
import fcntl, os, re, resource, secrets, select, signal
import socket, string, struct, subprocess, sys, time
from pathlib import Path

PORT = 4041
BASE = Path("/root/hollowdeep-dev/guild-social-batch1")
PROMPT = re.compile(r"\(\s*\d+\s*H\s+\d+\s*M\s*\)", re.I)
ROOT = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("/nonexistent")
RUN = ROOT.parent
PASS = 0
FAIL = 0
PROCESS = None
CLIENTS = []

def check(label, success, detail=""):
    global PASS, FAIL
    print(("PASS: " if success else "FAIL: ") + label, flush=True)
    if success:
        PASS += 1
    else:
        FAIL += 1
        if detail:
            print("  RESPONSE: " + repr(detail[-420:]), flush=True)

def loopback():
    control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        req = struct.pack("16sH14s", b"lo", 0, b"\0" * 14)
        result = fcntl.ioctl(control, 0x8913, req)
        interface, flags, pad = struct.unpack("16sH14s", result)
        fcntl.ioctl(control, 0x8914,
                    struct.pack("16sH14s", interface, flags | 1, pad))
    finally:
        control.close()

def limits():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

def server_start():
    global PROCESS
    with (RUN / "server.log").open("ab") as log:
        PROCESS = subprocess.Popen(
            ["chroot", "--userspec=65534:65534", str(ROOT),
             "/bin/hollowdeep", str(PORT)],
            cwd=str(ROOT), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, preexec_fn=limits,
        )
    for _ in range(100):
        if PROCESS.poll() is not None:
            raise RuntimeError("Isolated game exited before opening port")
        try:
            connection = socket.create_connection(("127.0.0.1", PORT), timeout=.3)
            connection.close()
            print("Isolated native MUD listener: READY", flush=True)
            return
        except OSError:
            time.sleep(.15)
    raise RuntimeError("Isolated game did not bind private TCP 4041")

def server_stop():
    global PROCESS
    if PROCESS is None:
        return
    if PROCESS.poll() is None:
        try:
            os.killpg(PROCESS.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            PROCESS.wait(timeout=4)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(PROCESS.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            PROCESS.wait(timeout=4)
    PROCESS = None

def connect():
    connection = socket.create_connection(("127.0.0.1", PORT), timeout=3)
    CLIENTS.append(connection)
    return connection

def receive(connection, seconds=5):
    chunks = []
    deadline = time.monotonic() + seconds
    last_data = None
    while time.monotonic() < deadline:
        ready, _, _ = select.select([connection], [], [], .15)
        if ready:
            data = connection.recv(8192)
            if not data:
                break
            chunks.append(data)
            last_data = time.monotonic()
        elif last_data and time.monotonic() - last_data > .45:
            break
    return b"".join(chunks).decode("latin-1", "replace")

def send(connection, value):
    connection.sendall(value.encode("ascii") + b"\r\n")

def in_game(output):
    return bool(PROMPT.search(output)) or "type 'welcome' at prompt" in output.lower()

def make_player(name, password):
    connection = connect()
    for _ in range(24):
        response = receive(connection, 7)
        low = response.lower()
        if in_game(response):
            return connection, response
        if "please enter name" in low:
            answer = name
        elif "did i get that right" in low:
            answer = "y"
        elif "hit return" in low:
            answer = ""
        elif "male or female" in low:
            answer = "m"
        elif "available classes" in low:
            answer = "Fighter"
        elif "54 points" in low and "stats" in low:
            answer = "12 11 11 10 10"
        elif "weapons proficiency" in low:
            answer = "Sharp"
        elif "choose an alignment" in low:
            answer = "Lawful"
        elif "available races" in low:
            answer = "Human"
        elif "password" in low:
            answer = password
        else:
            raise RuntimeError("Unknown disposable player prompt: " + repr(response[-240:]))
        send(connection, answer)
    raise RuntimeError("Disposable player creation exceeded step limit")

def command(connection, text):
    response = ""
    for attempt in range(3):
        send(connection, text)
        response = receive(connection, 4)
        if "please wait" not in response.lower():
            return response
        time.sleep(2.4)
    return response

def reconnect(name, password):
    connection = connect()
    prompt = receive(connection, 8)
    if "please enter name" not in prompt.lower():
        prompt += receive(connection, 4)
    if "please enter name" not in prompt.lower():
        raise RuntimeError("Reconnect name prompt not recognized: " + repr(prompt[-350:]))
    send(connection, name)
    prompt = receive(connection, 8)
    if "password" not in prompt.lower():
        prompt += receive(connection, 4)
    if "password" not in prompt.lower():
        raise RuntimeError("Reconnect response after name (password prompt missing): "
                           + repr(prompt[-450:]))
    send(connection, password)
    response = receive(connection, 10)
    if not in_game(response):
        response += receive(connection, 4)
    if not in_game(response):
        raise RuntimeError("Login response after password not recognized: "
                           + repr(response[-450:]))
    return connection

def tested():
    if (ROOT.name != "rootfs" or ROOT.parent.parent != BASE or
            not ROOT.parent.name.startswith("round11-load-") or
            ROOT.resolve(strict=True) != ROOT):
        raise RuntimeError("Round 11F private workspace guard rejected the path")
    for filename in ("bin/hollowdeep", "rooms/r06000", "rooms/r06001",
                     "rooms/r06002", "rooms/r06003", "rooms/r06004",
                     "rooms/r06006", "rooms/r06009"):
        if not (ROOT / filename).is_file():
            raise RuntimeError("Disposable test asset missing: " + filename)
    loopback()
    print("Private network namespace: ENABLED", flush=True)
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(6))
    name_a = "Hd" + suffix + "a"
    name_b = "Hd" + suffix + "b"
    name_c = "Hd" + suffix + "c"
    pw_a = "Test" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
    pw_b = "Test" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
    pw_c = "Test" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
    server_start()
    print("=== CORRUPT ACCOUNT LOAD MUST FAIL CLOSED ===", flush=True)
    for label, candidate, payload in (
            ("bad 12-bit LZW header", "Hdzirvexa", b"\xff\xff"),
            ("oversize compressed save", "Hdzirvexb", b"\x00" * 50000)):
        path = ROOT / "player" / candidate
        if path.exists() or path.is_symlink():
            raise RuntimeError("Synthetic corrupt-account path already exists")
        path.write_bytes(payload)
        path.chmod(0o600)
        os.chown(path, 65534, 65534)
        conn = None
        try:
            conn = connect()
            prompt = receive(conn, 8)
            if "please enter name" not in prompt.lower():
                prompt += receive(conn, 4)
            if "please enter name" not in prompt.lower():
                raise RuntimeError("Corrupt test did not receive name prompt")
            send(conn, candidate)
            reply = receive(conn, 8)
            if "existing character data cannot be loaded" not in reply.lower():
                reply += receive(conn, 4)
            check("Corrupt " + label + " refused rather than created",
                  "existing character data cannot be loaded" in reply.lower(),
                  reply)
            check("Corrupt " + label + " left unchanged",
                  path.is_file() and path.read_bytes() == payload,
                  "native corrupt file preservation")
        finally:
            if conn is not None:
                try: conn.close()
                except OSError: pass
                if conn in CLIENTS: CLIENTS.remove(conn)
            if path.exists(): path.unlink()
    print("Synthetic malformed character files: REMOVED", flush=True)
    a, _ = make_player(name_a, pw_a)
    b, _ = make_player(name_b, pw_b)
    c, _ = make_player(name_c, pw_c)
    check("Three disposable characters created in Guild Registry", True)

    print("=== DEED-FREE FOUNDING MUST FAIL ===", flush=True)
    denied = command(a, "clan create Nightfall")
    check("Founding without deed fails closed",
          "unused, purchased clan deed" in denied.lower(), denied)
    listing = command(a, "clan list")
    check("No guild formed without a deed", "Nightfall" not in listing, listing)

    print("=== PURCHASE AND ATOMIC REDEMPTION ===", flush=True)
    grant = command(a, "r9fund")
    check("One-time isolated 3000 gold granted",
          "gold granted: 3000" in grant.lower(), grant)
    stock = command(a, "list")
    check("Native Guild Registry advertises Clan Deed",
          "Clan Deed" in stock, stock)
    purchase = command(a, "buy deed")
    check("Minted physical deed bought", "Bought." in purchase, purchase)
    inventory = command(a, "inventory")
    check("Minted deed initially present", "Clan Deed" in inventory, inventory)
    created = command(a, "clan create Nightfall")
    check("Purchased deed founds Nightfall",
          "guild records updated" in created.lower()
          and "redeemed" in created.lower(), created)
    inv_after = command(a, "inventory")
    check("Deed consumed after guild commit",
          "Clan Deed" not in inv_after, inv_after)
    balance = command(a, "score")
    check("Guild deed purchase left exactly 500 gold",
          bool(re.search(r"\b500\s+Gold Pieces\b", balance, re.I)), balance)
    duplicate = command(a, "clan create Another")
    check("Existing leader cannot found a second guild",
          "Leave your existing guild" in duplicate, duplicate)
    hall = command(a, "clan hall")
    check("Nightfall assigned first private hall",
          "6003" in hall, hall)

    # Inspect the native durable guild record after command success.
    registry = ROOT / "hollowdeep-data/player-guilds.v1"
    state = registry.read_text(encoding="ascii", errors="replace") if registry.exists() else ""
    check("Atomic guild registry v2 committed with spent serial",
          "HDGUILD2\n" in state and "G Nightfall 6003\n" in state
          and "R HDG1" in state and name_a in state, state)

    print("=== GUILD HALL ENTRY PERMISSIONS ===", flush=True)
    outsiders_square = command(b, "east")
    check("Outsider reaches public square",
          "Guild District Square" in outsiders_square, outsiders_square)
    refused = command(b, "north")
    check("Outsider denied Hall A",
          "restricted to its members" in refused.lower(), refused)
    outside_look = command(b, "look")
    check("Outsider remains in public square",
          "Guild District Square" in outside_look, outside_look)

    entered_square = command(a, "east")
    check("Founder enters public square",
          "Guild District Square" in entered_square, entered_square)
    hall_a = command(a, "north")
    check("Founder enters assigned Guild Hall A",
          "Starter Hall A Entrance" in hall_a, hall_a)
    commons = command(a, "east")
    check("Founder moves into Guild Hall A Commons",
          "Starter Hall A Commons" in commons, commons)
    council = command(a, "north")
    check("Founder enters private Guild Hall A Council",
          "Starter Hall A Council" in council, council)
    command(a, "south")
    command(a, "west")
    left_hall = command(a, "south")
    check("Founder exits private hall to square",
          "Guild District Square" in left_hall, left_hall)

    invited = command(a, "clan invite " + name_b)
    check("Founder invites outsider to guild",
          "guild records updated" in invited.lower(), invited)
    accepted = command(b, "clan accept Nightfall")
    check("Invitation acceptance updates registry",
          "guild records updated" in accepted.lower(), accepted)
    now_allowed = command(b, "north")
    check("New guild member now enters Hall A",
          "Starter Hall A Entrance" in now_allowed, now_allowed)
    command(b, "south")
    denied_other = command(b, "east")
    check("Guild A member blocked from unassigned Hall B",
          "restricted to its members" in denied_other.lower(), denied_other)

    print("=== SECOND GUILD: UNIQUE SERIAL AND UNIQUE HALL ===", flush=True)
    granted_c = command(c, "r9fund")
    check("Second isolated player receives test funds",
          "gold granted: 3000" in granted_c.lower(), granted_c)
    bought_c = command(c, "buy deed")
    check("Second real deed bought", "Bought." in bought_c, bought_c)
    created_c = command(c, "clan create Dawnwatch")
    check("Second unique deed founds Dawnwatch",
          "Guild records updated" in created_c, created_c)
    hall_c = command(c, "clan hall")
    check("Second guild assigned Hall B",
          "6006" in hall_c, hall_c)
    command(c, "east")
    denied_a = command(c, "north")
    check("Dawnwatch denied Nightfall hall",
          "restricted to its members" in denied_a.lower(), denied_a)
    its_hall = command(c, "east")
    check("Dawnwatch founder enters own Hall B",
          "Starter Hall B Entrance" in its_hall, its_hall)
    command(c, "west")

    print("=== GUILD/CHARACTER RESTART PERSISTENCE ===", flush=True)
    sa, sb, sc = command(a, "save"), command(b, "save"), command(c, "save")
    check("Three temporary characters saved",
          "saved" in sa.lower() and "saved" in sb.lower() and "saved" in sc.lower(),
          sa + sb + sc)
    expected_players = [name_a, name_b, name_c]

    def verify_native_saves(phase):
        sizes = {}
        for name in expected_players:
            path = ROOT / "player" / name
            sizes[name] = path.stat().st_size if path.is_file() else -1
            check(phase + " native player save " + name,
                  sizes[name] > 0, "bytes=" + str(sizes[name]))
        if any(size <= 0 for size in sizes.values()):
            raise RuntimeError(
                "Native player save empty/missing at " + phase +
                "; refusing restart or new-character login"
            )

    verify_native_saves("before restart")
    # A direct SIGTERM after client.close() can interrupt a native disconnect
    # save in progress. Wait until the server has closed each connection
    # AND replaced every character file with a completed, nonempty save.
    before_inodes = {}
    for name in expected_players:
        stat_info = (ROOT / "player" / name).stat()
        before_inodes[name] = (stat_info.st_dev, stat_info.st_ino)
    pending = list(CLIENTS)
    for client in pending:
        try:
            client.shutdown(socket.SHUT_WR)
        except OSError:
            pass
    disconnect_deadline = time.monotonic() + 25
    while pending and time.monotonic() < disconnect_deadline:
        if PROCESS is None or PROCESS.poll() is not None:
            raise RuntimeError("Native MUD exited before disconnect saves completed")
        ready, _, _ = select.select(pending, [], [], .15)
        for client in ready:
            try:
                data = client.recv(8192)
            except OSError:
                data = b""
            if not data:
                pending.remove(client)
    if pending:
        raise RuntimeError("Native server did not complete all disconnects before timeout")
    for client in CLIENTS:
        try: client.close()
        except OSError: pass
    CLIENTS.clear()
    print("Native player disconnect acknowledgments: COMPLETE", flush=True)

    stable_since = None
    save_deadline = time.monotonic() + 25
    last_state = ""
    while time.monotonic() < save_deadline:
        if PROCESS is None or PROCESS.poll() is not None:
            raise RuntimeError("Native MUD stopped while waiting for player saves")
        complete = True
        details = []
        for name in expected_players:
            path = ROOT / "player" / name
            backup = ROOT / "player" / (name + "~")
            if not path.is_file():
                complete = False
                details.append(name + ":missing")
                continue
            st = path.stat()
            changed_inode = (st.st_dev, st.st_ino) != before_inodes[name]
            clean = st.st_size > 0 and changed_inode and not backup.exists()
            if not clean:
                complete = False
            details.append(name + ":bytes=" + str(st.st_size) +
                           ",new_inode=" + str(changed_inode) +
                           ",backup=" + str(backup.exists()))
        last_state = "; ".join(details)
        now = time.monotonic()
        if complete:
            if stable_since is None:
                stable_since = now
            if now - stable_since >= 2.0:
                break
        else:
            stable_since = None
        time.sleep(.15)
    else:
        raise RuntimeError("Disconnect saves never reached a stable committed state: " +
                           last_state)
    print("All three disconnect saves completed and stable: " + last_state, flush=True)
    verify_native_saves("after disconnect")
    server_stop()
    verify_native_saves("after stop")
    server_start()
    a = reconnect(name_a, pw_a)
    guild_info = command(a, "clan info Nightfall")
    check("Nightfall and Hall A persisted after restart",
          "Nightfall" in guild_info and "6003" in guild_info, guild_info)
    roster = command(a, "clan roster")
    check("Leader and invited member persisted",
          name_a.lower() in roster.lower() and name_b.lower() in roster.lower(),
          roster)
    inventory_after = command(a, "inventory")
    check("Redeemed deed remains absent after restart",
          "Clan Deed" not in inventory_after, inventory_after)
    funds_after = command(a, "score")
    check("Remaining 500 gold survived restart",
          bool(re.search(r"\b500\s+Gold Pieces\b", funds_after, re.I)),
          funds_after)
    # Reconnect the remaining two saved native characters, not just the leader.
    b = reconnect(name_b, pw_b)
    b_roster = command(b, "clan roster")
    check("Nightfall invited member reloads after native restart",
          "Nightfall" in b_roster and name_b.lower() in b_roster.lower(), b_roster)
    c = reconnect(name_c, pw_c)
    c_hall = command(c, "clan hall")
    check("Dawnwatch founder Hall B survives native restart",
          "6006" in c_hall, c_hall)
    c_funds = command(c, "score")
    check("Dawnwatch founder keeps 500 gold after restart",
          bool(re.search(r"\b500\s+Gold Pieces\b", c_funds, re.I)), c_funds)
    c_inventory = command(c, "inventory")
    check("Second redeemed deed remains consumed after restart",
          "Clan Deed" not in c_inventory, c_inventory)
    state2 = registry.read_text(encoding="ascii", errors="replace")
    check("Spent deed serials durable for both founders",
          state2.count("R HDG1") == 2 and "G Dawnwatch 6006" in state2,
          state2)

def main():
    status = 2
    try:
        tested()
        status = 0 if FAIL == 0 else 1
    except Exception as exc:
        print("PLAYTEST ERROR:", type(exc).__name__, str(exc), flush=True)
    finally:
        for client in CLIENTS:
            try: client.close()
            except OSError: pass
        server_stop()
    print("=== ROUND 11F BOUNDED NATIVE LOAD SUMMARY ===", flush=True)
    print("Passed:", PASS, flush=True)
    print("Failed:", FAIL, flush=True)
    print("Guild + hall + restart gameplay:", "PASS" if status == 0 else "NEEDS REVIEW", flush=True)
    print("Production MUD: NEVER ACCESSED", flush=True)
    return status

if __name__ == "__main__":
    sys.exit(main())
