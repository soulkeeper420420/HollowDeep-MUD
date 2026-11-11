#!/usr/bin/env bash
# HollowDeep Round11H: a single guarded private build + 54-check native replay.
# Source copied from failed Round11F (no mutation); reuse bounded save/load,
# fix rejection reply and switch port on restart to test rebinding separately.
set -Eeuo pipefail
umask 077

BASE_DIR="/root/hollowdeep-dev/guild-social-batch1"
FAILED="$BASE_DIR/round11-load-UuprVvCZ"
PASSED="$BASE_DIR/round11-atomic-pGqKMYDt"
R10="$BASE_DIR/round10-PpNpn17k"
LIVE="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
ROOTFS="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="96612d138d3550ad5527a45233df3334550ef49b"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2"

hash_live() {
    ( cd "$LIVE"; find . -type f -print0 |
      sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
hash_previous_players() {
    ( cd "$FAILED/rootfs/player"; find . -type f -print0 |
      sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local id file
  for id in $(seq 6000 6011); do
    file=$(printf '%s/r%05d' "$LIVE_ROOMS" "$id")
    if [ -e "$file" ] || [ -L "$file" ]; then
      echo "STOP: Unexpected live guild room: $file"
      return 1
    fi
  done
}
echo "=== HOLLOWDEEP ROUND 11H FAST TRACK: ONE-BATCH BOUNDED LOAD RETEST ==="
echo "=== 1. VERIFY PRODUCTION, COMPILATION BASELINE AND FAILED-RUN DATA ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -d "$FAILED/src"
test -s "$FAILED/src/frp.new"
test -s "$FAILED/src/command1.c"
test -s "$FAILED/src/command1.o"
test -s "$FAILED/src/files2.c"
test -s "$FAILED/src/compress.c"
test -s "$FAILED/src/Makefile"
test -s "$FAILED/results.log"
grep -Fq 'Passed: 43' "$FAILED/results.log"
grep -Fq 'Failed: 2' "$FAILED/results.log"
grep -Fq 'Isolated game exited before opening port' "$FAILED/results.log"
test -s "$PASSED/results-resume.log"
grep -Fq 'Passed: 50' "$PASSED/results-resume.log"
grep -Fq 'Failed: 0' "$PASSED/results-resume.log"
test -s "$R10/rooms.sha256"
test -z "$(find "$FAILED/src" -type l -print -quit)"
test -z "$(find "$FAILED/rootfs/player" -type l -print -quit)"
test -z "$(find "$R10/test-world/rooms" -type l -print -quit)"
test -d "$ROOTFS/player"
test -z "$(find "$ROOTFS" -type l -print -quit)"
test -z "$(find "$ROOTFS/player" -mindepth 1 -print -quit)"
for name in Hdyajnroa Hdyajnrob Hdyajnroc; do
  test -s "$FAILED/rootfs/player/$name"
done
test -s "$FAILED/rootfs/hollowdeep-data/player-guilds.v1"
test -s "$FAILED/rootfs/bin/hollowdeep"
cmp -s "$FAILED/rootfs/bin/hollowdeep" "$FAILED/src/frp.new"
test -s "$ROOTFS/bin/hollowdeep"
check_live_rooms
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )
grep -Fq 'hd11_uncompress_bounded' "$FAILED/src/compress.c"
grep -Fq 'hd11_raw_player_valid' "$FAILED/src/files2.c"
grep -Fq 'hd11_atomic_player_write' "$FAILED/src/files2.c"
grep -Fq 'hd11_existing_character_unreadable' "$FAILED/src/command1.c"
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$FAILED/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$FAILED/src/Makefile"; then
  echo "STOP: Deed-free test flag must remain disabled"
  exit 1
fi
BEFORE_PROD=$(hash_live)
BEFORE_FAILED_BINARY=$(sha256sum "$FAILED/src/frp.new" | awk '{print $1}')
BEFORE_PLAYERS=$(hash_previous_players)
BEFORE_BASE=$(sha256sum "$ROOTFS/bin/hollowdeep" | awk '{print $1}')
BEFORE_PASS=$(sha256sum "$PASSED/src/frp.new" | awk '{print $1}')
echo "Production source/rooms: PROTECTED"
echo "Failed-run private Round11F characters/ledger: PROTECTED"
echo "Prior Round11D 50/50 and Round11E 14/14: PRESERVED"

echo "=== 2. CREATE FRESH PRIVATE SOURCE AND EMPTY DISPOSABLE WORLD ==="
NEW=$(mktemp -d "$BASE_DIR/round11-fixed-XXXXXXXX")
mkdir -m 700 "$NEW/src" "$NEW/rootfs"
cp -a "$FAILED/src/." "$NEW/src/"
cp -a "$ROOTFS/." "$NEW/rootfs/"
test -z "$(find "$NEW" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "Fresh private workspace: $NEW"

echo "=== 3. APPLY EXACT GUARD FIXES; KEEP BOUNDED LOAD FORMAT UNCHANGED ==="
PATCH="$NEW/round11h_fix_private_runner.py"
RUNNER="$NEW/round11h_runner.py"
curl --fail --silent --show-error --location --retry 2 --max-time 30 \
  "$RAW/round11h_fix_private_runner.py" -o "$PATCH"
curl --fail --silent --show-error --location --retry 2 --max-time 30 \
  "$RAW/round11f_bounded_runner.py" -o "$RUNNER"
test -s "$PATCH"
test -s "$RUNNER"
python3 -m py_compile "$PATCH" "$RUNNER"
python3 "$PATCH" "$NEW"
python3 -m py_compile "$RUNNER"
grep -Fq 'scwrite(fd, "Existing character data cannot be loaded.' "$NEW/src/command1.c"
grep -Fq 'PORT = 4042' "$RUNNER"
grep -Fq 'Round 11H private workspace guard' "$RUNNER"
grep -Fq 'verify_native_saves("after stop")' "$RUNNER"
grep -Fq '=== CORRUPT ACCOUNT LOAD MUST FAIL CLOSED ===' "$RUNNER"
echo "Direct corrupt-account response: PATCHED IN PRIVATE COPY"
echo "Private restart test port: 4042"
echo "Native bounded loader and atomic saver: SOURCE UNCHANGED"

echo "=== 4. REBUILD ONLY PRIVATE COMMAND1 AND RELINK 32-BIT ENGINE ==="
(
  cd "$NEW/src"
  rm -f command1.o frp.new
  timeout 240 make -j1 > "$NEW/build.log" 2>&1
) || {
  echo "=== PRIVATE BUILD ERRORS ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
      "$NEW/build.log" | tail -n 45 || true
  tail -n 35 "$NEW/build.log"
  echo "Private workspace: $NEW"
  exit 1
}
test -s "$NEW/src/frp.new"
file "$NEW/src/frp.new" | grep -Fq 'ELF 32-bit'
nm "$NEW/src/files2.o" | grep -Eq '[[:space:]]T[[:space:]]load_ply$'
nm "$NEW/src/compress.o" | grep -Eq '[[:space:]]T[[:space:]]hd11_uncompress_bounded$'
echo "Round11H updated 32-bit MUD: COMPILED"

echo "=== 5. INSTALL 12 VERIFIED ROOMS INTO NEW PRIVATE ROOTFS ==="
for id in $(seq 6000 6011); do
  file=$(printf 'r%05d' "$id")
  test -s "$R10/test-world/rooms/$file"
  test ! -e "$NEW/rootfs/rooms/$file"
  cp -p "$R10/test-world/rooms/$file" "$NEW/rootfs/rooms/$file"
done
cp -p "$R10/test-world/rooms/r06000" "$NEW/rootfs/rooms/r00001"
cp -p "$R10/test-world/rooms/r06001" "$NEW/rootfs/rooms/r00002"
cp -p "$NEW/src/frp.new" "$NEW/rootfs/bin/hollowdeep"
mkdir -p "$NEW/rootfs/hollowdeep-data"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
test ! -e "$NEW/rootfs/hollowdeep-data/player-guilds.v1"
echo "New test characters and guild registry: EMPTY"
echo "Private network/mount/PID namespace: REQUIRED"

echo "=== 6. RUN FOUR CORRUPT LOAD + FIFTY GUILD/RESTART CHECKS ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$RUNNER" "$NEW/rootfs" > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"
if [ "$STATUS" -ne 0 ]; then
  echo "Private native server log bytes:"
  stat -c '%s' "$NEW/server.log" 2>/dev/null || true
  echo "No private credentials or saved player data printed."
fi

echo "=== 7. PRODUCTION AND PREVIOUS PRIVATE FILE INTEGRITY ==="
test "$(hash_live)" = "$EXPECTED"
test "$(hash_live)" = "$BEFORE_PROD"
test "$(sha256sum "$FAILED/src/frp.new" | awk '{print $1}')" = "$BEFORE_FAILED_BINARY"
test "$(hash_previous_players)" = "$BEFORE_PLAYERS"
test "$(sha256sum "$ROOTFS/bin/hollowdeep" | awk '{print $1}')" = "$BEFORE_BASE"
test "$(sha256sum "$PASSED/src/frp.new" | awk '{print $1}')" = "$BEFORE_PASS"
test -z "$(find "$ROOTFS/player" -mindepth 1 -print -quit)"
check_live_rooms
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )
echo "Production source and guild rooms: UNCHANGED"
echo "Previous Round11F character saves and engine: UNCHANGED"
echo "Previous Round11D 50/50 engine: UNCHANGED"
echo "Production MUD service: NOT RESTARTED"
echo "Website: NOT MODIFIED"
if [ "$STATUS" -eq 0 ]; then
  grep -Fq 'Passed: 54' "$NEW/results.log"
  grep -Fq 'Failed: 0' "$NEW/results.log"
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  echo "Normal private gameplay and bounded-load checks: 54/54 PASS"
fi
echo "=== HOLLOWDEEP ROUND 11H RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "Private workspace: $NEW"
echo "Production deployment: NONE"
echo "Full loader fuzz, equipped items and guild ledger fault tests: PENDING"
echo "=== ROUND 11H COMPLETE ==="
exit "$STATUS"
