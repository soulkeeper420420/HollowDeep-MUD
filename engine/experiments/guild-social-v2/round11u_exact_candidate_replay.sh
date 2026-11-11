#!/usr/bin/env bash
# Run known 90/11/23/18 suites against private SHA-256-verified Round11T binary.
# No production deployment, restart, player-save access or mutations.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
LIVE=/srv/hollowdeep/world
OLD_SOURCE=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
OLD_BIN=b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5
HERE=$(cd "$(dirname "$0")" && pwd -P)
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
  xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
service_id() {
 systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic
}
echo "=== HOLLOWDEEP ROUND 11U EXACT-CANDIDATE REGRESSIONS ==="
test "$(id -u)" -eq 0
test "$(hash_tree "$LIVE/src_3.00")" = "$OLD_SOURCE"
test "$(sha256sum "$LIVE/src_3.00/frp.new" | awk '{print $1}')" = "$OLD_BIN"
test -s "$BASE/round11s-durability-NXKx5FiI/results.log"
grep -Fxq "Passed: 73" "$BASE/round11s-durability-NXKx5FiI/results.log"
test -z "$(find "$LIVE/src_3.00" "$LIVE/rooms" -type l -print -quit)"
for id in $(seq 6000 6011); do
 file=$(printf '%s/rooms/r%05d' "$LIVE" "$id")
 test ! -e "$file" && test ! -L "$file"
done

mapfile -t choices < <(find "$BASE" -mindepth 1 -maxdepth 1 -type d -name 'round11t-hookfree-*' -print |
 while IFS= read -r dir; do
  if test -s "$dir/candidate.sha256" &&
     grep -Fq "PASS: Hook-free candidate reached native login prompt" "$dir/smoke.log"; then
   printf '%s\n' "$dir"
  fi
 done)
if test -n "${ROUND11U_STAGE:-}"; then
 CANDIDATE=$(realpath -e "$ROUND11U_STAGE")
else
 if test "${#choices[@]}" -ne 1; then
  printf 'STOP: found %s eligible private candidates. Set ROUND11U_STAGE explicitly.\n' "${#choices[@]}" >&2
  printf '%s\n' "${choices[@]}" >&2
  exit 1
 fi
 CANDIDATE="${choices[0]}"
fi
[[ "$CANDIDATE" == "$BASE"/round11t-hookfree-* ]]
test -s "$CANDIDATE/candidate.sha256"
test -s "$CANDIDATE/src/frp.new"
test -z "$(find "$CANDIDATE/src" "$CANDIDATE/rootfs" -type l -print -quit)"
test -z "$(find "$CANDIDATE/rootfs/player" "$CANDIDATE/rootfs/hollowdeep-data" -mindepth 1 -print -quit)"
PIN=$(python3 - "$CANDIDATE" <<'PY'
import hashlib,re,sys
from pathlib import Path
stage=Path(sys.argv[1]).resolve(strict=True)
lines=(stage/"candidate.sha256").read_text().splitlines()
if len(lines)!=1:
 raise SystemExit("STOP: expected exactly one candidate manifest entry")
m=re.fullmatch(r"([a-f0-9]{64})  (/.+)",lines[0])
if not m or Path(m.group(2)).resolve(strict=True)!=stage/"src/frp.new":
 raise SystemExit("STOP: manifest path not the candidate")
h=hashlib.sha256((stage/"src/frp.new").read_bytes()).hexdigest()
if h!=m.group(1): raise SystemExit("STOP: candidate does not match manifest SHA")
print(h)
PY
)
file "$CANDIDATE/src/frp.new" | grep -Fq 'ELF 32-bit'
test "$(sha256sum "$CANDIDATE/rootfs/bin/hollowdeep" | awk '{print $1}')" = "$PIN"
if strings "$CANDIDATE/src/frp.new" | grep -Eiq \
 'Round 11 fixture granted|gold granted: 3000|round11n-ledger-fail|inject-dir-fsync-eio'; then
 echo 'STOP: test-only string present in release executable' >&2; exit 1
fi
test -z "$(grep -E 'HD_ROUND9_ISOLATED_FUNDS|round9_test_funds[.]o|HD_ROUND11_TEST' \
 "$CANDIDATE/src/Makefile" || true)"
SOURCE_BEFORE=$(hash_tree "$LIVE/src_3.00")
ROOMS_BEFORE=$(hash_tree "$LIVE/rooms")
SERVICE_BEFORE=$(service_id)
CANDIDATE_BEFORE=$(hash_tree "$CANDIDATE")
FROM="$BASE/round11s-durability-NXKx5FiI"
FROM_BEFORE=$(hash_tree "$FROM")
TOOLS=$(mktemp -d "$BASE/round11u-tools-XXXXXXXX")
RESULT="$TOOLS/summary.txt"
verify() {
 status=$?
 trap - EXIT
 if test "$(hash_tree "$LIVE/src_3.00")" != "$SOURCE_BEFORE" ||
    test "$(hash_tree "$LIVE/rooms")" != "$ROOMS_BEFORE" ||
    test "$(service_id)" != "$SERVICE_BEFORE" ||
    test "$(hash_tree "$CANDIDATE")" != "$CANDIDATE_BEFORE" ||
    test "$(hash_tree "$FROM")" != "$FROM_BEFORE"; then
   echo "STOP: protected production, source baseline or binary changed" >&2
   status=1
 else
   echo "Production source, rooms, service, candidate and prior fixture: UNCHANGED"
 fi
 echo "Private report: $RESULT"
 echo "Production deployment or restart: NONE"
 exit "$status"
}
trap verify EXIT
echo "Candidate stage: $CANDIDATE"
echo "Pinned candidate SHA-256: $PIN"
printf 'Round11T candidate SHA-256: %s\n' "$PIN" > "$RESULT"

names=(
 round11u_prepare_replay.py
 round11n_patch.py
 round11n_private_replay.sh
 round11p_populated_replay.py
 round11p_private_crash.sh
 round11p_crash_replay.py
 round11p_crash_rename.c
 round11q_private.sh
 round11q_replay.py
 round11q_fixture.c
 round11q_rng.c
 round11s_fsync_private.sh
 round11s_fsync_replay.py
 round11s_fsync_inject.c
)
for name in "${names[@]}"; do
 test -s "$HERE/$name" && test ! -L "$HERE/$name"
 cp -p "$HERE/$name" "$TOOLS/$name"
done
python3 "$TOOLS/round11u_prepare_replay.py" "$TOOLS" "$CANDIDATE" "$PIN"
for file in "$TOOLS"/*.sh; do bash -n "$file"; done
for file in "$TOOLS"/*.py; do python3 -m py_compile "$file"; done

echo "=== ROUND11U 90 POPULATED NATIVE REPLAY ==="
HD_EXACT_CANDIDATE="$CANDIDATE/src/frp.new" \
HD_ROLLBACK_BINARY="$LIVE/src_3.00/frp.new" \
 bash "$TOOLS/round11n_private_replay.sh" --exact-candidate | tee "$TOOLS/90.log"
grep -Fxq 'Passed: 90' "$TOOLS/90.log"
grep -Fxq 'Failed: 0' "$TOOLS/90.log"
echo 'Populated: 90/90 PASS' | tee -a "$RESULT"

echo "=== ROUND11U 11 ABRUPT CRASH RECOVERY ==="
bash "$TOOLS/round11p_private_crash.sh" "$CANDIDATE/src/frp.new" | tee "$TOOLS/11.log"
test "$(grep -c '^PASS:' "$TOOLS/11.log")" -eq 11
echo 'Crash recovery: 11/11 PASS' | tee -a "$RESULT"

echo "=== ROUND11U 23 ALTERNATE ENTRY AND FULL ROLLBACK ==="
bash "$TOOLS/round11q_private.sh" | tee "$TOOLS/23.log"
test "$(grep -c '^PASS:' "$TOOLS/23.log")" -eq 23
echo 'Security and full rollback: 23/23 PASS' | tee -a "$RESULT"

echo "=== ROUND11U 18 HOOK-FREE DIRECTORY-FSYNC EIO ==="
ROUND11U_CANDIDATE="$CANDIDATE/src/frp.new" ROUND11U_PIN="$PIN" \
 bash "$TOOLS/round11s_fsync_private.sh" | tee "$TOOLS/18.log"
grep -Fxq 'Passed: 18' "$TOOLS/18.log"
grep -Fxq 'Failed: 0' "$TOOLS/18.log"
echo 'Directory fsync fault: 18/18 PASS' | tee -a "$RESULT"

echo 'Total exact candidate suites: 142/142 PASS' | tee -a "$RESULT"
echo "=== ROUND11U EXACT CANDIDATE: 142/142 PASS ==="
echo "NOT CERTIFIED: real Town Square integration; post-activation ledger transaction rollback; power-loss durability."
echo "Production decision: NO-GO"
