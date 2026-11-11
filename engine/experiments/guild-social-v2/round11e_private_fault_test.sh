#!/usr/bin/env bash
# Round 11E: fault-inject extracted private atomic player save function only.
# The native game is NEVER started. This does not touch player files.
set -Eeuo pipefail
umask 077
ROOT="/root/hollowdeep-dev/guild-social-batch1"
STAGE="$ROOT/round11-atomic-pGqKMYDt"
LIVE="/srv/hollowdeep/world/src_3.00"
ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="90217231ed28d51b96c9dad33d38036fea6728fc"
URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round11e_atomic_fault_harness.py"

hash_live() {
  (cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
hash_players() {
  (cd "$STAGE/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
echo "=== HOLLOWDEEP ROUND 11E ATOMIC SAVE FAULT INJECTION ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -s "$STAGE/src/frp.new"
test -s "$STAGE/src/files2.c"
test -s "$STAGE/src/compress.c"
test -s "$STAGE/results-resume.log"
grep -Fq 'Passed: 50' "$STAGE/results-resume.log"
grep -Fq 'Failed: 0' "$STAGE/results-resume.log"
grep -Fq 'hd11_atomic_player_write' "$STAGE/src/files2.c"
grep -Fq 'hd11_put_object' "$STAGE/src/files2.c"
grep -Fq 'hd11_compress_bounded' "$STAGE/src/compress.c"
test -z "$(find "$STAGE/src" -type l -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
for id in $(seq 6000 6011); do
  file=$(printf '%s/r%05d' "$ROOMS" "$id")
  if [ -e "$file" ] || [ -L "$file" ]; then
    echo "STOP: Unexpected live room $file"
    exit 1
  fi
done

SOURCE_BEFORE=$(hash_live)
ENGINE_BEFORE=$(sha256sum "$STAGE/src/frp.new" | awk '{print $1}')
PLAYER_BEFORE=$(hash_players)
BASE_BEFORE=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Round 11D 50/50 baseline: VERIFIED"
echo "Production live source: VERIFIED"
echo "Private tested character files: PROTECTED"

RUN=$(mktemp -d /root/hollowdeep-round11e-launch-XXXXXXXX)
HARNESS="$RUN/round11e_atomic_fault_harness.py"
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 "$URL" -o "$HARNESS"
test -s "$HARNESS"
grep -Fq 'hd11_atomic_player_write' "$HARNESS"
grep -Fq 'crash_after_rename' "$HARNESS"
grep -Fq 'Existing_symlink_refused' "$HARNESS" || \
  grep -Fq 'existing_symlink_refused' "$HARNESS"
python3 -m py_compile "$HARNESS"

echo "=== SYNTHETIC 32-BIT HELPER COMPILE AND FAULT TESTS ==="
set +e
timeout --signal=TERM --kill-after=3s 180s \
  python3 "$HARNESS" > "$RUN/results.log" 2>&1
STATUS=$?
set -e
cat "$RUN/results.log"

echo "=== VERIFY PRODUCTION AND ORIGINAL ROUND 11D FILES ==="
test "$(hash_live)" = "$SOURCE_BEFORE"
test "$(hash_live)" = "$EXPECTED"
test "$(sha256sum "$STAGE/src/frp.new" | awk '{print $1}')" = "$ENGINE_BEFORE"
test "$(hash_players)" = "$PLAYER_BEFORE"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_BEFORE"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
echo "Production source: UNCHANGED"
echo "Previously tested native engine/players: UNCHANGED"
echo "Production service: NOT RESTARTED"
echo "Website: NOT MODIFIED"
echo "=== ROUND 11E RESULT ==="
echo "Harness exit status: $STATUS"
echo "Results: $RUN/results.log"
echo "Production deployment: NONE"
echo "Native game restart and malformed-load checks: NOT PERFORMED"
echo "=== ROUND 11E COMPLETE ==="
exit "$STATUS"
