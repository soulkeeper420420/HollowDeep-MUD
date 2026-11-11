#!/usr/bin/env bash
# Round11U: rerun exactly the 23 native movement/rollback checks with direct logs.
# Does not patch game source or modify earlier private stages or production.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
LIVE=/srv/hollowdeep/world
OLD_SRC=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
OLD_BIN=b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
  xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
service_id() {
 systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic
}
echo '=== ROUND 11U PRIVATE MOVEMENT PIPE RECOVERY ==='
test "$(id -u)" -eq 0
test "$(hash_tree "$LIVE/src_3.00")" = "$OLD_SRC"
test "$(sha256sum "$LIVE/src_3.00/frp.new" | awk '{print $1}')" = "$OLD_BIN"
test -z "$(find "$LIVE/src_3.00" "$LIVE/rooms" -type l -print -quit)"

# Find a previous Round11U private-tool copy which completed 90+11, then
# stopped in movement; never reuse its data directories or alter its scripts.
mapfile -t candidates < <(
 find "$BASE" -mindepth 1 -maxdepth 1 -type d -name 'round11u-tools-*' -print |
 while IFS= read -r p; do
   if test -s "$p/90.log" && test -s "$p/11.log" &&
      test -s "$p/23.log" &&
      grep -Fxq 'Passed: 90' "$p/90.log" &&
      grep -Fxq 'Failed: 0' "$p/90.log" &&
      test "$(grep -c '^PASS:' "$p/11.log")" -eq 11; then
     printf '%s\n' "$p"
   fi
 done
)
test "${#candidates[@]}" -gt 0
if test -n "${ROUND11U_TOOLS:-}"; then
 PREV=$(realpath -e "$ROUND11U_TOOLS")
else
 PREV=$(python3 - "${candidates[@]}" <<'PY'
from pathlib import Path
import sys
print(max(sys.argv[1:], key=lambda x:(Path(x)/"23.log").stat().st_mtime))
PY
)
fi
[[ "$PREV" == "$BASE"/round11u-tools-* ]]
for n in round11q_private.sh round11q_replay.py round11q_fixture.c round11q_rng.c; do
 test -s "$PREV/$n"
done
test -z "$(find "$PREV" -type l -print -quit)"

# Candidate must be the exact previously-verified private Round11T binary.
CAND=$(python3 - "$PREV/round11q_private.sh" "$BASE" <<'PY'
from pathlib import Path
import hashlib,re,sys
s=Path(sys.argv[1]).read_text()
base=Path(sys.argv[2]).resolve(strict=True)
m=re.search(r'^candidate=(/root/hollowdeep-dev/guild-social-batch1/round11t-hookfree-[A-Za-z0-9]+)$',s,re.M)
if not m: raise SystemExit('STOP: prior 23 test not pinned to a Round11T stage')
stage=Path(m.group(1)).resolve(strict=True)
if stage.parent!=base: raise SystemExit('STOP: release candidate outside private stage')
b=stage/'src/frp.new'
sha=hashlib.sha256(b.read_bytes()).hexdigest()
if (stage/'candidate.sha256').read_text().splitlines()!=[sha+'  '+str(b)]:
 raise SystemExit('STOP: candidate manifest/executable mismatch')
if s.count(sha)!=1:
 raise SystemExit('STOP: private 23-test candidate SHA not pinned')
print(stage)
PY
)
echo "Pinned candidate: $CAND"
sha256sum "$CAND/src/frp.new"
SOURCE_BEFORE=$(hash_tree "$LIVE/src_3.00")
ROOMS_BEFORE=$(hash_tree "$LIVE/rooms")
SERVICE_BEFORE=$(service_id)
PREV_BEFORE=$(hash_tree "$PREV")
CAND_BEFORE=$(hash_tree "$CAND")
verify() {
 status=$?
 trap - EXIT
 if test "$(hash_tree "$LIVE/src_3.00")" != "$SOURCE_BEFORE" ||
    test "$(hash_tree "$LIVE/rooms")" != "$ROOMS_BEFORE" ||
    test "$(service_id)" != "$SERVICE_BEFORE" ||
    test "$(hash_tree "$PREV")" != "$PREV_BEFORE" ||
    test "$(hash_tree "$CAND")" != "$CAND_BEFORE"; then
   echo 'STOP: protected source, rooms, service or private stages changed' >&2
   status=1
 else
   echo 'Production source, rooms, service and prior private stages: UNCHANGED'
 fi
 echo 'Live deployment/restart: NONE'
 exit "$status"
}
trap verify EXIT

FRESH=$(mktemp -d "$BASE/round11u-movement-XXXXXXXX")
echo "New disposable movement harness: $FRESH"
for n in round11q_private.sh round11q_replay.py round11q_fixture.c round11q_rng.c; do
 cp -p "$PREV/$n" "$FRESH/$n"
done
python3 - "$FRESH/round11q_private.sh" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
old='''timeout --kill-after=3s 240s unshare --mount --net --pid --fork \\
  python3 "$here/round11q_replay.py" "$prior/round11k_runner.py" "$root" | tee "$stage/results.log"
'''
new='''# Capture native stdout/stderr directly in a private regular file.
# Preserve all assertions and return codes; never mask test failures.
set +e
timeout --signal=TERM --kill-after=5s 600s unshare --mount --net --pid --fork \\
  python3 -u "$here/round11q_replay.py" "$prior/round11k_runner.py" "$root" \\
  > "$stage/results.log" 2>&1
native_status=$?
set -e
cat "$stage/results.log"
if test "$native_status" -ne 0; then
  echo "STOP: native 23-check runner exited $native_status" >&2
  echo "Private test stage: $stage" >&2
  exit "$native_status"
fi
test "$(grep -c '^PASS:' "$stage/results.log")" -eq 23 || {
  echo "STOP: fewer than 23 native assertions completed" >&2
  exit 1
}
'''
if s.count(old)!=1:
 raise SystemExit("STOP: original movement logging anchor changed")
s=s.replace(old,new,1)
if " | tee " in s or s.count('grep -c')!=1:
 raise SystemExit("STOP: direct logging patch postcondition failed")
p.write_text(s)
PY
bash -n "$FRESH/round11q_private.sh"
python3 -m py_compile "$FRESH/round11q_replay.py"

# The single native suite logs directly to a file, then reports pass/fail.
set +e
bash "$FRESH/round11q_private.sh" >"$FRESH/replay.log" 2>&1
status=$?
set -e
echo '=== NATIVE MOVEMENT REPLAY RESULTS ==='
grep -E '^(PASS:|FAIL:|Traceback|RuntimeError:|OSError:|BrokenPipeError:|STOP:|Complete isolated|Live source|Private stage:)' "$FRESH/replay.log" | tail -n 55 || true
if test "$status" -ne 0; then
 echo "STOP: private movement replay exited $status" >&2
 tail -n 65 "$FRESH/replay.log" >&2
 echo "Private report: $FRESH/replay.log" >&2
 exit 1
fi
test "$(grep -c '^PASS:' "$FRESH/replay.log")" -eq 23
grep -Fq 'Complete isolated source, binary and room rollback verified' "$FRESH/replay.log"
echo '=== ROUND 11U 23/23 MOVEMENT + FULL ROLLBACK: PASS ==='
echo "Private movement report: $FRESH/replay.log"

# Reuse the previously pinned but not-yet-executed Round11U directory-fsync
# suite, which sets up a deed with the private fixture and switches to this
# exact hook-free release candidate before injecting any EIO.
test -s "$PREV/round11s_fsync_private.sh"
test -s "$PREV/round11s_fsync_replay.py"
test -s "$PREV/round11s_fsync_inject.c"
test -s "$PREV/round11p_populated_replay.py"
test -s "$PREV/round11p_crash_replay.py"
ACTUAL_PIN=$(sha256sum "$CAND/src/frp.new" | awk '{print $1}')
grep -Fq "$ACTUAL_PIN" "$PREV/round11p_populated_replay.py"
grep -Fq "$ACTUAL_PIN" "$PREV/round11p_crash_replay.py"
grep -Fq 'ROUND11U_CANDIDATE' "$PREV/round11s_fsync_replay.py"
echo '=== ROUND 11U PINNED 18-CHECK DIRECTORY-FSYNC EIO REPLAY ==='
set +e
ROUND11U_CANDIDATE="$CAND/src/frp.new" ROUND11U_PIN="$ACTUAL_PIN" \
 bash "$PREV/round11s_fsync_private.sh" >"$FRESH/18.log" 2>&1
fsync_status=$?
set -e
grep -E '^(PASS:|Passed:|Failed:|=== ROUND|Production source|Power-loss)' "$FRESH/18.log" | tail -n 32 || true
if test "$fsync_status" -ne 0 ||
   ! grep -Fxq 'Passed: 18' "$FRESH/18.log" ||
   ! grep -Fxq 'Failed: 0' "$FRESH/18.log"; then
 echo "STOP: private Round11U hook-free fsync replay failed, status $fsync_status" >&2
 tail -n 50 "$FRESH/18.log" >&2
 echo "Private fsync report: $FRESH/18.log" >&2
 exit 1
fi
echo '=== ROUND11U 18/18 EXACT-CANDIDATE FSYNC RECOVERY: PASS ==='
echo '=== ROUND11U EXACT-CANDIDATE REPLAY: 142/142 VERIFIED SUITE CHECKS ==='
echo 'Prior private 90/90 and 11/11 logs verified, fresh 23/23 and 18/18 checks passed.'
echo "Private reports: $PREV/90.log, $PREV/11.log, $FRESH/replay.log, $FRESH/18.log"
echo 'Remaining: actual Town Square exit integration + post-activation transaction-preserving rollback'
echo 'Production release: NO-GO'
