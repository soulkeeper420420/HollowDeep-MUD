#!/usr/bin/env bash
# Print only the failed private Round11U movement replay and associated Python
# exception from the wrapper's captured stderr. Never open live player files,
# production guild ledger, or private raw server logs.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
echo "=== ROUND 11U MOVEMENT ERROR (WRAPPER STDERR) ==="
test "$(id -u)" -eq 0
test -d "$BASE"
python3 - "$BASE" <<'PY'
from pathlib import Path
import sys
base=Path(sys.argv[1])
packs=[]
for p in base.glob("round11u-toolpack-*"):
    log=p/"exact_candidate_replay.log"
    if (p.is_dir() and not p.is_symlink() and
            log.is_file() and not log.is_symlink()):
        packs.append((log.stat().st_mtime,log))
if not packs:
    raise SystemExit("STOP: no private Round11U wrapper log")
log=max(packs)[1]
if log.stat().st_size > 2_000_000:
    raise SystemExit("STOP: unusual private test log size")
lines=log.read_text(errors="replace").splitlines()
print("Source:", log)
print("Private wrapper log lines:", len(lines))
anchors=[i for i,x in enumerate(lines) if (
    "ROUND11U 23 ALTERNATE ENTRY" in x or
    "ROUND11U 23" in x or
    "23 ALTERNATE" in x or
    "Native save created for Hdspellqa" in x)]
start=anchors[-1] if anchors else max(0,len(lines)-75)
print("=== MOVEMENT SECTION AND EXCEPTION ===")
for i in range(start,min(len(lines),start+95)):
    line=lines[i]
    for secret in ("Testprivately","Testfsynccase","Testcrashcase"):
        line=line.replace(secret,"[synthetic-test-secret]")
    print(f"{i+1}: {line[:700]}")
print("=== SHORT PRIVATE 23.LOG ===")
folders=[p for p in base.glob("round11u-tools-*")
         if p.is_dir() and not p.is_symlink()
         and (p/"23.log").is_file() and not (p/"23.log").is_symlink()]
if folders:
    test=max(folders,key=lambda p:(p/"23.log").stat().st_mtime)/"23.log"
    print("Source:",test)
    if test.stat().st_size>30000:
        print("STOP: 23.log unexpectedly large")
    else:
        for i,x in enumerate(test.read_text(errors="replace").splitlines()[:25],1):
            print(f"{i}: {x[:350]}")
print("=== NO SERVER LOG, LIVE ACCOUNTS OR LEDGER READ ===")
PY
