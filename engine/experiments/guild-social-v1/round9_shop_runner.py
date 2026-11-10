#!/usr/bin/env python3
"""
Round 9: private native shop + Clan Deed smoke test.
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
    if not str(ROOT).startswith(str(BASE) + "/round9-") or ROOT.name != "rootfs":
        raise RuntimeError("Round 9 private workspace guard rejected the path")
    if not (ROOT / "bin/hollowdeep").is_file():
        raise RuntimeError("Disposable test executable missing")
    if not (ROOT / "rooms/r06000").is_file():
        raise RuntimeError("Guild Registry room missing")
    if not (ROOT / "rooms/r06001").is_file():
        raise RuntimeError("Guild stockroom missing")
    loopback()
    print("Private network namespace: ENABLED", flush=True)
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(6))
    name = "Hd" + suffix + "a"
    password = "Test" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(9))
    server_start()
    player, arrival = make_player(name, password)
    shown = arrival + command(player, "look")
    check("Native Guild Registry loads at disposable entry",
          "Guild Registry" in shown, shown)

    print("=== SHOP LIST AND INSUFFICIENT GOLD ===", flush=True)
    stock = command(player, "list")
    check("Native shop lists physical Clan Deed",
          "Clan Deed" in stock, stock)
    check("Native shop advertises 2500 gold",
          bool(re.search(r"Cost:\s*2500\b", stock, re.I)), stock)
    funds_before = command(player, "score")
    check("Fresh character starts with zero gold",
          bool(re.search(r"\b0\s+Gold Pieces\b", funds_before, re.I)), funds_before)
    declined = command(player, "buy deed")
    check("Native purchase rejects insufficient gold",
          "enough gold" in declined.lower(), declined)
    inv_before = command(player, "inventory")
    check("Rejected purchase grants no deed",
          "clan deed" not in inv_before.lower(), inv_before)

    print("=== PRIVATE STAGING-ONLY FUNDS AND PURCHASE ===", flush=True)
    grant = command(player, "r9fund")
    check("Test-only 3000 gold grant succeeds",
          "Round9 isolated test gold granted: 3000" in grant, grant)
    funds = command(player, "score")
    check("Granted gold reflected in character score",
          bool(re.search(r"\b3000\s+Gold Pieces\b", funds, re.I)), funds)
    bought = command(player, "buy deed")
    check("Native merchant completes purchase",
          "Bought." in bought, bought)
    inv = command(player, "inventory")
    check("Purchased physical deed appears in inventory",
          "Clan Deed" in inv, inv)
    funds_after = command(player, "score")
    check("Native merchant deducts exactly 2500 gold",
          bool(re.search(r"\b500\s+Gold Pieces\b", funds_after, re.I)), funds_after)

    print("=== GUILD FOUNDING SAFETY GATE ===", flush=True)
    attempt = command(player, "clan create Nightfall")
    check("Deed in inventory cannot bypass unfinished founding gate",
          ("requires a physical clan deed" in attempt.lower() or
           "not enabled" in attempt.lower()) and
           "guild records updated" not in attempt.lower(), attempt)
    guilds = command(player, "clan list")
    check("No guild created while entitlement is unfinished",
          "Nightfall" not in guilds, guilds)

    print("=== GUILD DISTRICT NAVIGATION ===", flush=True)
    square = command(player, "east")
    check("Registry-to-Square native link works",
          "Guild District Square" in square, square)
    look = command(player, "look")
    check("Square has no public stockroom or guild hall exits",
          "Guild District Square" in look
          and re.search(r"Obvious exits:\s*west\b", look, re.I) is not None, look)
    back = command(player, "west")
    check("Square-to-Registry native link works",
          "Guild Registry" in back, back)
    again = command(player, "list")
    check("Room 6000 shop reads room 6001 inventory",
          "Clan Deed" in again, again)

    print("=== NATIVE SAVE / RESTART PERSISTENCE ===", flush=True)
    saved = command(player, "save")
    check("Test character saved after purchase",
          "saved" in saved.lower(), saved)
    saved_file = ROOT / "player" / name
    check("Disposable native character file exists after save",
          saved_file.is_file() and saved_file.stat().st_size > 0)
    if saved_file.is_file():
        print("Native player file size:", saved_file.stat().st_size, flush=True)
    for client in CLIENTS:
        try: client.close()
        except OSError: pass
    CLIENTS.clear()
    server_stop()
    server_start()
    player = reconnect(name, password)
    inv2 = command(player, "inventory")
    check("Physical deed survives native game restart",
          "Clan Deed" in inv2, inv2)
    score2 = command(player, "score")
    check("500 remaining gold survives restart",
          bool(re.search(r"\b500\s+Gold Pieces\b", score2, re.I)), score2)

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
    print("=== ROUND 9 SUMMARY ===", flush=True)
    print("Passed:", PASS, flush=True)
    print("Failed:", FAIL, flush=True)
    print("Shop + room gameplay:", "PASS" if status == 0 else "NEEDS REVIEW", flush=True)
    print("Production MUD: NEVER ACCESSED", flush=True)
    return status

if __name__ == "__main__":
    sys.exit(main())
