#!/usr/bin/env bash
# Round 11I: no C rebuild, copy PASSED 11H binary into a fresh disposable world.
# 54 known native guild/persistence checks + 19 new guild-ledger fail-closed
# and same-port native restart checks, always inside mount/net/PID isolation.
set -Eeuo pipefail
umask 077

WORK="/root/hollowdeep-dev/guild-social-batch1"
PASSED="$WORK/round11-fixed-ZpafezVN"
FAILED="$WORK/round11-load-UuprVvCZ"
R10="$WORK/round10-PpNpn17k"
LIVE="/srv/hollowdeep/world/src_3.00"
ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="a0af5f138dfe6c408292d799c3e7dbc8f7b063bc"
URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round11i_append_ledger_sameport_tests.py"

hash_live() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
hash_saved() {
  ( cd "$PASSED/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
hash_failed() {
  ( cd "$FAILED/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local id room
  for id in $(seq 6000 6011); do
    room=$(printf '%s/r%05d' "$ROOMS" "$id")
    if [ -e "$room" ] || [ -L "$room" ]; then
      echo "STOP: Unexpected production guild room: $room"
      return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 11I FAST TRACK LEDGER + SAME-PORT RESTART ==="
echo "=== 1. CHECK PRODUCTION AND PASSED PRIVATE STAGES ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -s "$PASSED/results.log"
grep -Fq 'Passed: 54' "$PASSED/results.log"
grep -Fq 'Failed: 0' "$PASSED/results.log"
test -s "$PASSED/src/frp.new"
test -s "$PASSED/rootfs/bin/hollowdeep"
cmp -s "$PASSED/src/frp.new" "$PASSED/rootfs/bin/hollowdeep"
test -s "$PASSED/round11h_runner.py"
grep -Fq 'Round 11H private workspace guard rejected the path' "$PASSED/round11h_runner.py"
grep -Fq 'Private restart using fresh isolated test port: 4042' "$PASSED/round11h_runner.py"
test -s "$FAILED/results.log"
test -s "$R10/rooms.sha256"
test -s "$BASE/bin/hollowdeep"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$PASSED/rootfs/player" -type l -print -quit)"
test -z "$(find "$FAILED/rootfs/player" -type l -print -quit)"
test -z "$(find "$R10/test-world/rooms" -type l -print -quit)"
check_live_rooms
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )

LIVE_BEFORE=$(hash_live)
PASSED_ENGINE_BEFORE=$(sha256sum "$PASSED/src/frp.new" | awk '{print $1}')
PASSED_PLAYERS_BEFORE=$(hash_saved)
FAILED_PLAYERS_BEFORE=$(hash_failed)
BASE_ENGINE_BEFORE=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Production source/rooms: VERIFIED"
echo "Round11H 54/54 native baseline: VERIFIED"
echo "Previous passed and failed private player files: PROTECTED"
echo "Recompilation: NOT REQUIRED"
echo "Production deployment: DISABLED"

echo "=== 2. CREATE FRESH DISPOSABLE WORLD; REUSE COMPILED 32-BIT ENGINE ==="
NEW=$(mktemp -d "$WORK/round11-fixed-XXXXXXXX")
mkdir -m 700 "$NEW/rootfs"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
for id in $(seq 6000 6011); do
  filename=$(printf 'r%05d' "$id")
  test -s "$R10/test-world/rooms/$filename"
  test ! -e "$NEW/rootfs/rooms/$filename"
  cp -p "$R10/test-world/rooms/$filename" "$NEW/rootfs/rooms/$filename"
done
cp -p "$R10/test-world/rooms/r06000" "$NEW/rootfs/rooms/r00001"
cp -p "$R10/test-world/rooms/r06001" "$NEW/rootfs/rooms/r00002"
cp -p "$PASSED/src/frp.new" "$NEW/rootfs/bin/hollowdeep"
mkdir -p "$NEW/rootfs/hollowdeep-data"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
test ! -e "$NEW/rootfs/hollowdeep-data/player-guilds.v1"
file "$NEW/rootfs/bin/hollowdeep" | grep -Fq 'ELF 32-bit'
echo "Private test workspace: $NEW"
echo "Existing compiled Round11H engine: REUSED"
echo "New disposable player and guild state: EMPTY"

echo "=== 3. BUILD ONLY EXTENDED PRIVATE PYTHON GAMEPLAY RUNNER ==="
cp -p "$PASSED/round11h_runner.py" "$NEW/round11i_runner.py"
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 "$URL" -o "$NEW/round11i_append.py"
test -s "$NEW/round11i_append.py"
grep -Fq 'Expected checks: 54 original + 19 new = 73' "$NEW/round11i_append.py"
python3 -m py_compile "$NEW/round11i_append.py"
python3 "$NEW/round11i_append.py" "$NEW"
python3 -m py_compile "$NEW/round11i_runner.py"
grep -Fq 'ROUND 11I: BAD LEDGER MUST FAIL CLOSED' "$NEW/round11i_runner.py"
grep -Fq 'Starting native MUD again on SAME private port 4042' "$NEW/round11i_runner.py"
grep -Fq 'All three second disconnect saves fully committed' "$NEW/round11i_runner.py"
grep -Fq 'CORRUPT ACCOUNT LOAD MUST FAIL CLOSED' "$NEW/round11i_runner.py"
echo "Expected native checks: 73 (54 prior + 19 ledger/restart)"
echo "Network/PID/mount namespace: REQUIRED"

echo "=== 4. PLAYTEST PRIVATE LEDGER AND SAME-PORT RESTART ==="
set +e
timeout --signal=TERM --kill-after=3s 480s \
  unshare --mount --net --pid --fork \
  python3 "$NEW/round11i_runner.py" "$NEW/rootfs" \
  > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"

echo "=== 5. VERIFY EXISTING FILES REMAIN IDENTICAL ==="
test "$(hash_live)" = "$EXPECTED"
test "$(hash_live)" = "$LIVE_BEFORE"
test "$(sha256sum "$PASSED/src/frp.new" | awk '{print $1}')" = "$PASSED_ENGINE_BEFORE"
test "$(hash_saved)" = "$PASSED_PLAYERS_BEFORE"
test "$(hash_failed)" = "$FAILED_PLAYERS_BEFORE"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_ENGINE_BEFORE"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )
echo "Production source and rooms: UNCHANGED"
echo "Prior Round11H/11F character files and engine: UNCHANGED"
echo "Production MUD service: NOT RESTARTED"
echo "Website: NOT MODIFIED"
if [ "$STATUS" -eq 0 ]; then
  grep -Fq 'Passed: 73' "$NEW/results.log"
  grep -Fq 'Failed: 0' "$NEW/results.log"
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  echo "Ledger fail-closed and same-port reload assertions: ALL PASSED"
fi
echo "=== ROUND 11I FAST-TRACK SUMMARY ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "Private workspace: $NEW"
echo "Production deployment: NONE"
echo "Equipped-item and cross-file transaction crash tests: STILL PENDING"
echo "=== ROUND 11I COMPLETE ==="
exit "$STATUS"
