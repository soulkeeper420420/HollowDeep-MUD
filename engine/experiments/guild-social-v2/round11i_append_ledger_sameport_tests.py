#!/usr/bin/env python3
"""Create a fresh Round11I runner from passed Round11H private runner.

Adds three invalid-ledger fail-closed tests plus access/recovery checks,
then a SECOND rapid restart on the SAME private port (4042) with
all three player files checked and all three players reloaded.
No C code patches and no real game files.
"""
from pathlib import Path
import sys

HOME=Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv)!=2:
    raise SystemExit("STOP: Provide fresh private Round11I directory")
work=Path(sys.argv[1]).resolve(strict=True)
if (work.parent!=HOME or not work.name.startswith("round11-fixed-")
        or not (work/"rootfs").is_dir()):
    raise SystemExit("STOP: Runner path not a new private Round11I world")

runner=work/"round11i_runner.py"
if not runner.is_file() or runner.is_symlink():
    raise SystemExit("STOP: Missing newly copied private runner")
s=runner.read_text()
anchor='''    check("Spent deed serials durable for both founders",
          state2.count("R HDG1") == 2 and "G Dawnwatch 6006" in state2,
          state2)

def main():'''
if s.count(anchor)!=1:
    raise SystemExit("STOP: Expected original Round11H final test anchor absent")
for label in (
    "Round 11H private workspace guard rejected the path",
    "Private restart using fresh isolated test port: 4042",
    "=== CORRUPT ACCOUNT LOAD MUST FAIL CLOSED ===",
    "All three disconnect saves completed and stable:",
):
    if label not in s:
        raise SystemExit("STOP: Tested Round11H runner anchor absent: "+label)
if "ROUND 11I: BAD LEDGER" in s:
    raise SystemExit("STOP: Round11I tests already applied")

addition=r'''    check("Spent deed serials durable for both founders",
          state2.count("R HDG1") == 2 and "G Dawnwatch 6006" in state2,
          state2)

    print("=== ROUND 11I: BAD LEDGER MUST FAIL CLOSED ===", flush=True)
    original_registry = registry.read_bytes()
    if (not original_registry.startswith(b"HDGUILD2\n") or
            b"G Nightfall 6003\n" not in original_registry or
            b"G Dawnwatch 6006\n" not in original_registry):
        raise RuntimeError("No validated native HDGUILD2 ledger to test")
    rows = original_registry.splitlines(keepends=True)
    redeems = [line for line in rows if line.startswith(b"R HDG1")]
    member_rows = [line for line in rows
                   if line.startswith(b"M Nightfall ") and
                      line.endswith(b" 2\n")]
    if len(redeems) != 2 or len(member_rows) != 1:
        raise RuntimeError("Expected exactly two spent tokens and one Nightfall leader")
    scenarios = (
        ("invalid ledger header", b"HDINVALID\n"),
        ("duplicate redeemed serial", original_registry + redeems[0]),
        ("missing Nightfall leader",
         b"".join(line for line in rows if line != member_rows[0])),
    )
    try:
        for title, payload in scenarios:
            registry.write_bytes(payload)
            response = command(a, "clan list")
            check("Fail closed on " + title,
                  "Guild records unavailable or invalid" in response,
                  response)
            if title == "invalid ledger header":
                entry = command(a, "north")
                check("Member cannot enter Hall A with unreadable ledger",
                      "restricted to its members" in entry.lower(), entry)
    finally:
        # The file exists only in this new disposable world, and the exact
        # previously validated bytes are always restored even on exceptions.
        registry.write_bytes(original_registry)
    restored = command(a, "clan list")
    check("Original valid ledger resumes service",
          "Nightfall" in restored and "Dawnwatch" in restored, restored)
    entered = command(a, "north")
    check("Restored Nightfall leader can enter Hall A",
          "Starter Hall A Entrance" in entered, entered)
    check("Guild ledger remains byte-identical after failed operations",
          registry.read_bytes() == original_registry)

    print("=== ROUND 11I: RESTART SAME PRIVATE PORT 4042 ===", flush=True)
    # Use the exact same native save completion/EOF barrier as 11H;
    # verified native writes and old file safety must precede SIGTERM.
    old_inodes = {}
    for name in expected_players:
        st = (ROOT / "player" / name).stat()
        old_inodes[name] = (st.st_dev, st.st_ino)
    pending = list(CLIENTS)
    for client in pending:
        try: client.shutdown(socket.SHUT_WR)
        except OSError: pass
    deadline = time.monotonic() + 25
    while pending and time.monotonic() < deadline:
        if PROCESS is None or PROCESS.poll() is not None:
            raise RuntimeError("Native process exited during second disconnect")
        ready, _, _ = select.select(pending, [], [], .15)
        for client in ready:
            try: block = client.recv(8192)
            except OSError: block = b""
            if not block: pending.remove(client)
    if pending:
        raise RuntimeError("Second native disconnects did not finish")
    for client in CLIENTS:
        try: client.close()
        except OSError: pass
    CLIENTS.clear()
    stable_since = None
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        stable = True
        for name in expected_players:
            f=ROOT/"player"/name
            backup=ROOT/"player"/(name+"~")
            if not f.is_file() or backup.exists():
                stable = False
                break
            st=f.stat()
            if st.st_size<=0 or (st.st_dev,st.st_ino)==old_inodes[name]:
                stable = False
                break
        now=time.monotonic()
        if stable:
            if stable_since is None: stable_since = now
            if now-stable_since>=2: break
        else: stable_since=None
        time.sleep(.15)
    else:
        raise RuntimeError("Second restart save files did not fully commit")
    check("All three second disconnect saves fully committed", True)
    verify_native_saves("second restart before stop")
    server_stop()
    verify_native_saves("second restart after stop")
    # Do not alter PORT: test immediate rebinding of exactly the same
    # ephemeral private TCP 4042, not a new namespace or a different port.
    print("Starting native MUD again on SAME private port 4042", flush=True)
    server_start()
    check("Native second restart bound same private port 4042", True)
    a = reconnect(name_a,pw_a)
    leader_info = command(a,"clan info Nightfall")
    check("Nightfall leader loaded after same-port restart",
          "Nightfall" in leader_info and "6003" in leader_info,leader_info)
    b = reconnect(name_b,pw_b)
    roster_again = command(b,"clan roster")
    check("Invited Nightfall member reloaded on same port",
          "Nightfall" in roster_again and name_b.lower() in roster_again.lower(),
          roster_again)
    c = reconnect(name_c,pw_c)
    dawnwatch = command(c,"clan hall")
    check("Dawnwatch founder reloaded on same port",
          "6006" in dawnwatch,dawnwatch)
    check("Ledger intact after same-port restart",
          registry.read_bytes() == original_registry)

def main():'''

s=s.replace(anchor,addition,1)
s=s.replace("=== ROUND 11H BOUNDED NATIVE LOAD SUMMARY ===",
            "=== ROUND 11I FAST-TRACK GUILD SAFETY SUMMARY ===")
runner.write_text(s)
print("Private Round11I runner: LEDGER FAIL-CLOSED / RESTORE / SAME-PORT RESTART")
print("Native game engine and character data: UNMODIFIED")
print("Expected checks: 54 original + 13 new = 67")
print("Production source/rooms/service: NOT ACCESSED")
