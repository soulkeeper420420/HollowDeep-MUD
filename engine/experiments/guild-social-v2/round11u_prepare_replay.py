#!/usr/bin/env python3
"""Adapt ONLY disposable copies of the pinned 11P/11Q/11S replay launchers.

The original replay scripts already pin SHA-256. Do not remove those checks:
replace the *one exact old* candidate SHA reference with the SHA verified by
the on-host Round11T candidate.sha256, and use the same exact candidate in
all four test suites. The initial deed purchase for fsync EIO deliberately uses
the private fixture-enabled Round11S executable, then performs the injected
failures ONLY after switching to the SHA-verified hook-free candidate.
"""
import hashlib
from pathlib import Path
import py_compile
import re
import sys

BASE=Path("/root/hollowdeep-dev/guild-social-batch1")
OLD="12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c"
PREDECESSOR="b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5"

if len(sys.argv)!=4:
    raise SystemExit("Usage: prepare PRIVATE_TOOL_DIR ROUND11T_STAGE VERIFIED_SHA256")
tools=Path(sys.argv[1]).resolve(strict=True)
candidate=Path(sys.argv[2]).resolve(strict=True)
pin=sys.argv[3]
if (tools.parent != BASE or not tools.name.startswith("round11u-tools-") or
        candidate.parent != BASE or
        not candidate.name.startswith("round11t-hookfree-") or
        not re.fullmatch(r"[a-f0-9]{64}",pin)):
    raise SystemExit("STOP: private tool path, candidate path or pin invalid")
binary=candidate/"src/frp.new"
if hashlib.sha256(binary.read_bytes()).hexdigest()!=pin:
    raise SystemExit("STOP: candidate executable disagrees with locked SHA")

def mutate(name, old, new):
    p=tools/name
    if p.is_symlink() or not p.is_file():
        raise SystemExit("STOP: missing or symlinked helper: "+name)
    s=p.read_text()
    if s.count(old)!=1:
        raise SystemExit("STOP: unexpected one-anchor input in "+name+
                         " (found "+str(s.count(old))+")")
    p.write_text(s.replace(old,new,1))

mutate("round11p_populated_replay.py",OLD,pin)
mutate("round11p_crash_replay.py",OLD,pin)
mutate("round11q_private.sh",
       'candidate=$base/round11p-candidate-IvW74AXW',
       'candidate='+str(candidate))
mutate("round11q_private.sh",OLD,pin)

# The legacy fsync replay's fixture-enabled binary can mint a deed.
# The release candidate MUST NOT implement r9fund, so switch after the
# completed disposable saved-character setup, before any EIO injections.
insert_before='''    rename_marker = marker("inject-ledger-rename-eio")'''
inject = '''    # Private Round11U: prepare test player on the old isolated fixture build,
    # then switch to the actual pinned hook-free candidate for ALL EIO tests.
    import select
    try:
        client.shutdown(socket.SHUT_WR)
    except OSError:
        pass
    deadline=time.monotonic()+25
    eof=False
    while time.monotonic()<deadline:
        if runtime["PROCESS"] is None or runtime["PROCESS"].poll() is not None:
            raise RuntimeError("Fixture process exited before completed disconnect save")
        ready,_,_=select.select([client],[],[],.25)
        if ready and not client.recv(8192):
            eof=True
            break
    if not eof:
        raise RuntimeError("STOP: disposable native character disconnect did not reach EOF")
    if not save_path.is_file() or save_path.stat().st_size<=0:
        raise RuntimeError("STOP: missing or empty disposable save")
    client.close()
    client=None
    stop()
    source=Path(os.environ["ROUND11U_CANDIDATE"]).resolve(strict=True)
    wanted=os.environ["ROUND11U_PIN"]
    if hashlib.sha256(source.read_bytes()).hexdigest()!=wanted:
        raise RuntimeError("STOP: exact release candidate checksum differs")
    binary.write_bytes(source.read_bytes())
    binary.chmod(0o755)
    initial_player=save_path.read_bytes()
    start(4045)
    client=native["reconnect"](name,password)
    if "Clan Deed" not in command(client,"inventory"):
        raise RuntimeError("STOP: stored deed missing before release-candidate EIO injection")

'''
mutate("round11s_fsync_replay.py",insert_before,inject+insert_before)

for n in ("round11p_populated_replay.py","round11p_crash_replay.py",
          "round11s_fsync_replay.py","round11q_replay.py","round11n_patch.py"):
    py_compile.compile(str(tools/n),doraise=True)
for n in ("round11p_populated_replay.py","round11p_crash_replay.py"):
    if OLD in (tools/n).read_text():
        raise SystemExit("STOP: legacy release pin still present in "+n)
assert pin in (tools/"round11q_private.sh").read_text()
assert pin in (tools/"round11p_populated_replay.py").read_text()
assert PREDECESSOR in (tools/"round11p_populated_replay.py").read_text()
print("Legacy 90/11/23 checks: copied, still SHA-256 pinned to the Round11T candidate")
print("Directory-fsync checks: prepared with fixture-first / hook-free-injection split")
print("Release candidate fixed SHA-256:",pin)
print("Original GitHub scripts and private candidate: UNMODIFIED")
