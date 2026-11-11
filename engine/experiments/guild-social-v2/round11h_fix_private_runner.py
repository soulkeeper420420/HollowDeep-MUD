#!/usr/bin/env python3
"""Patch only a NEW Round11H private copy of Round11F source and runner.

1) Deliver corrupt-account refusal directly to the test socket before closing.
2) Use a fresh isolated TCP port for the second private server start, to
   distinguish socket rebinding from actual player-load failures.
No native save/load format edits; no production or previous test mutations.
"""
from pathlib import Path
import sys

ROOT = Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv) != 2:
    raise SystemExit("STOP: Give only the freshly copied Round11H workspace")
stage = Path(sys.argv[1]).resolve(strict=True)
if (stage.parent != ROOT or
        not stage.name.startswith("round11-fixed-")):
    raise SystemExit("STOP: Must be a fresh private Round11H workspace")
source = stage / "src/command1.c"
runner = stage / "round11h_runner.py"
for path in (source, runner):
    if not path.is_file() or path.is_symlink():
        raise SystemExit("STOP: Missing/symlink private candidate: " + str(path))
c = source.read_text()
py = runner.read_text()

old_message = r'print(fd,"Existing character data cannot be loaded. Contact staff.\n");'
new_message = (
    r'scwrite(fd, "Existing character data cannot be loaded. Contact staff.\n", '
    r'sizeof("Existing character data cannot be loaded. Contact staff.\n") - 1);'
)
if c.count(old_message) != 1 or new_message in c:
    raise SystemExit("STOP: The exact private corrupt-account branch changed")
c = c.replace(old_message, new_message, 1)

old_guard = '''if (ROOT.name != "rootfs" or ROOT.parent.parent != BASE or
            not ROOT.parent.name.startswith("round11-load-") or
            ROOT.resolve(strict=True) != ROOT):
        raise RuntimeError("Round 11F private workspace guard rejected the path")'''
new_guard = '''if (ROOT.name != "rootfs" or ROOT.parent.parent != BASE or
            not ROOT.parent.name.startswith("round11-fixed-") or
            ROOT.resolve(strict=True) != ROOT):
        raise RuntimeError("Round 11H private workspace guard rejected the path")'''
if py.count(old_guard) != 1:
    raise SystemExit("STOP: Round11F runner guard has changed")
py = py.replace(old_guard,new_guard,1)

old_test = '''def tested():
    if (ROOT.name'''
new_test = '''def tested():
    global PORT
    if (ROOT.name'''
if py.count(old_test) != 1:
    raise SystemExit("STOP: Runner startup/PORT scope changed")
py = py.replace(old_test,new_test,1)

old_restart = '''    verify_native_saves("after stop")
    server_start()
    a = reconnect(name_a, pw_a)'''
new_restart = '''    verify_native_saves("after stop")
    # Separate the next login/load test from native socket rebinding.
    # This is a fresh port in the same private network namespace, not
    # a production networking or service configuration change.
    PORT = 4042
    print("Private restart using fresh isolated test port: 4042", flush=True)
    server_start()
    a = reconnect(name_a, pw_a)'''
if py.count(old_restart) != 1:
    raise SystemExit("STOP: Graceful post-stop / restart anchor changed")
py = py.replace(old_restart,new_restart,1)

old_failure = 'raise RuntimeError("Isolated game exited before opening port")'
new_failure = ('raise RuntimeError("Isolated game exited before opening port "'
               '+ str(PORT) + " with exit status " + str(PROCESS.poll()))')
if py.count(old_failure) != 1:
    raise SystemExit("STOP: Native startup diagnostic anchor changed")
py = py.replace(old_failure,new_failure,1)

if 'CORRUPT ACCOUNT LOAD MUST FAIL CLOSED' not in py:
    raise SystemExit("STOP: Corruption tests absent")
if 'All three disconnect saves completed and stable' not in py:
    raise SystemExit("STOP: Graceful save barrier absent")
if 'round11-load-' in py or 'Round 11F private workspace guard' in py:
    raise SystemExit("STOP: Old workspace guard remained")
py = py.replace("=== ROUND 11F BOUNDED NATIVE LOAD SUMMARY ===",
                "=== ROUND 11H BOUNDED NATIVE LOAD SUMMARY ===")

backup = source.with_name(source.name + ".before-round11h")
if backup.exists() or backup.is_symlink():
    raise SystemExit("STOP: Private source backup already exists")
backup.write_text(source.read_text())
backup.chmod(0o600)
source.write_text(c)
runner.write_text(py)

print("Private corrupt-account reply: DIRECT SOCKET WRITE BEFORE DISCONNECT")
print("Private runner: PORT 4042 ON RESTART + BETTER EXIT DIAGNOSTICS")
print("Original Round11F bounded load/save logic: PRESERVED")
print("Fresh Round11H private workspace: PATCHED")
print("Production and previous test workspaces: NOT MODIFIED")
