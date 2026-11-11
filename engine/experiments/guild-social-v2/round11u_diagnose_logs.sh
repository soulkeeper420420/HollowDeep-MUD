#!/usr/bin/env bash
# Read-only diagnostic of the most recent private Round11U toolpack.
# Does not inspect real player saves, guild ledger, raw server logs or credentials.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
echo "=== ROUND 11U SAFE DIAGNOSTICS ==="
test "$(id -u)" -eq 0
test -d "$BASE"
python3 - "$BASE" <<'PY'
from pathlib import Path
import re,sys
base=Path(sys.argv[1])
packs=[p for p in base.glob("round11u-toolpack-*") if p.is_dir() and not p.is_symlink()
       and (p/"exact_candidate_replay.log").is_file()]
if not packs:
    raise SystemExit("STOP: no completed Round11U toolpack log found")
pack=max(packs,key=lambda p:(p/"exact_candidate_replay.log").stat().st_mtime)
print("Latest private toolpack:",pack)
print("=== 1. MAIN CANDIDATE REPLAY ===")
def show(path):
    if not path.is_file() or path.is_symlink():
        print(path.name+": no separate log")
        return
    if path.stat().st_size>5_000_000:
        print(path.name+": log too large; not reading")
        return
    s=path.read_text(errors="replace")
    lines=s.splitlines()
    print("File:",path.name,"lines:",len(lines))
    keys=("===","Passed:","Failed:","PASS:","FAIL:","STOP:","RuntimeError:",
          "AssertionError:","SystemExit:","FileNotFoundError:","PermissionError:",
          "OSError:","ValueError:","SyntaxError:","TypeError:","ImportError:",
          "Traceback","Candidate stage:","Pinned candidate SHA-256:",
          "Private report:","Production decision:","Round11U candidate suite:")
    hits=[line.strip() for line in lines if line.strip().startswith(keys)]
    if hits:
        for line in hits[-38:]:
            # Never print whole 3rd party/server outputs or arbitrary traceback.
            print(line[:250])
    else:
        print("No standard pass/fail/error markers. Last nonblank lines:")
        for line in [x.strip() for x in lines if x.strip()][-12:]:
            print(line[:220])
show(pack/"exact_candidate_replay.log")
print("=== 2. INDIVIDUAL TEST SUITES (IF CREATED) ===")
private=[p for p in base.glob("round11u-tools-*") if p.is_dir() and not p.is_symlink()]
private.sort(key=lambda p:p.stat().st_mtime,reverse=True)
for folder in private[:3]:
    if not any((folder/n).exists() for n in ("90.log","11.log","23.log","18.log")):
        continue
    print("Suite stage:",folder)
    for name in ("90.log","11.log","23.log","18.log"):
        show(folder/name)
print("=== 3. READ-ONLY TOWN SQUARE IDENTIFICATION ===")
town=pack/"town_square_probe.log"
if town.is_file() and town.stat().st_size<2_000_000:
    lines=town.read_text(errors="replace").splitlines()
    for l in lines:
        if (l.startswith("Possible Town Square file:") or
            l.startswith("Matched native room files:") or
            l.startswith("=== ROUND11U") or
            "Room and source bytes" in l):
            print(l[:250])
print("=== 4. PRIVATE CANDIDATE MANIFESTS ===")
stages=[p for p in base.glob("round11t-hookfree-*") if p.is_dir() and not p.is_symlink()]
for stage in sorted(stages,key=lambda p:p.stat().st_mtime,reverse=True)[:5]:
    path=stage/"candidate.sha256"
    if not path.is_file() or path.is_symlink():
        continue
    lines=path.read_text(errors="replace").splitlines()
    if len(lines)==1 and re.fullmatch(r"[a-f0-9]{64}  /root/hollowdeep-dev/guild-social-batch1/round11t-hookfree-[A-Za-z0-9]+/src/frp\.new",lines[0]):
        print(stage.name,lines[0].split("  ",1)[0])
    else:
        print(stage.name,"manifest format unexpected; SHA not displayed")
print("=== ROUND 11U DIAGNOSTIC COMPLETE (READ-ONLY) ===")
PY
