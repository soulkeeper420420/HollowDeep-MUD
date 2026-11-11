#!/usr/bin/env bash
# Round11F: fresh private source copy, bounded player loader & corrupt-account
# rejection, then known guild gameplay + native graceful restart smoke.
# No source, character, room, process, or website production edits.
set -Eeuo pipefail
umask 077

ROOT="/root/hollowdeep-dev/guild-social-batch1"
R10="$ROOT/round10-PpNpn17k"
R11D="$ROOT/round11-atomic-pGqKMYDt"
LIVE="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="5c0d42ba7e6e447798f0e883f997d386104621d7"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2"

source_hash() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
old_players_hash() {
  ( cd "$R11D/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local id path
  for id in $(seq 6000 6011); do
    path=$(printf '%s/r%05d' "$LIVE_ROOMS" "$id")
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "STOP: Real guild room exists: $path"; return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 11F BOUNDED NATIVE PLAYER LOAD ==="
echo "=== 1. VERIFY LIVE AND PREVIOUS PRIVATE TEST INTEGRITY ==="
test "$(id -u)" -eq 0
test "$(source_hash)" = "$EXPECTED"
test -s "$R11D/src/frp.new"
test -s "$R11D/src/files2.c"
test -s "$R11D/src/compress.c"
test -s "$R11D/src/command1.c"
test -s "$R11D/src/hollowdeep_social.c"
test -s "$R11D/results-resume.log"
grep -Fq 'Passed: 50' "$R11D/results-resume.log"
grep -Fq 'Failed: 0' "$R11D/results-resume.log"
test -s "$BASE/bin/hollowdeep"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$R11D/src" -type l -print -quit)"
test -z "$(find "$R10/test-world/rooms" -type l -print -quit)"
test -s "$R10/rooms.sha256"
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )
check_live_rooms
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$R11D/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$R11D/src/Makefile"; then
  echo "STOP: Test bypass flag must remain disabled"; exit 1
fi
grep -Fq 'hd11_atomic_player_write' "$R11D/src/files2.c"
grep -Fq 'hd11_put_object' "$R11D/src/files2.c"
grep -Fq 'hd11_compress_bounded' "$R11D/src/compress.c"
grep -Fq 'save_ply(player->name, player)' "$R11D/src/hollowdeep_social.c"

LIVE_BEFORE=$(source_hash)
ENGINE_BEFORE=$(sha256sum "$R11D/src/frp.new" | awk '{print $1}')
PLAYER_BEFORE=$(old_players_hash)
BASE_BEFORE=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Production engine source: VERIFIED"
echo "Round 11D 50/50 native persistence: VERIFIED"
echo "Round 11E 14/14 synthetic fault baseline: REPORTED"
echo "Previous private player files/binary: PROTECTED"

echo "=== 2. CREATE FRESH DISPOSABLE 32-BIT SOURCE / ROOTFS ==="
NEW=$(mktemp -d "$ROOT/round11-load-XXXXXXXX")
mkdir -m 700 "$NEW/src" "$NEW/rootfs"
cp -a "$R11D/src/." "$NEW/src/"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "Private workspace: $NEW"

echo "=== 3. PATCH PRIVATE BOUNDED LOAD AND ACCOUNT SAFETY ==="
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 \
  "$RAW/round11f_stage_bounded_loader.py" \
  -o "$NEW/round11f_stage_bounded_loader.py"
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 \
  "$RAW/round11f_bounded_runner.py" -o "$NEW/round11f_bounded_runner.py"
test -s "$NEW/round11f_stage_bounded_loader.py"
test -s "$NEW/round11f_bounded_runner.py"
python3 -m py_compile "$NEW/round11f_stage_bounded_loader.py" \
  "$NEW/round11f_bounded_runner.py"
grep -Fq 'Round 11F private workspace guard rejected' \
  "$NEW/round11f_bounded_runner.py"
grep -Fq '=== CORRUPT ACCOUNT LOAD MUST FAIL CLOSED ===' \
  "$NEW/round11f_bounded_runner.py"
grep -Fq 'All three disconnect saves completed and stable:' \
  "$NEW/round11f_bounded_runner.py"
python3 "$NEW/round11f_stage_bounded_loader.py" "$NEW/src"
grep -Fq 'hd11_raw_player_valid' "$NEW/src/files2.c"
grep -Fq 'hd11_uncompress_bounded' "$NEW/src/compress.c"
grep -Fq 'hd11_existing_character_unreadable' "$NEW/src/command1.c"

echo "=== 4. COMPILE CLEAN PRIVATE 32-BIT NATIVE ENGINE ==="
(
  cd "$NEW/src"
  find . -maxdepth 1 -type f -name '*.o' -delete
  rm -f frp.new
  timeout 240 make -j1 > "$NEW/build.log" 2>&1
) || {
  echo "=== PRIVATE COMPILER ERRORS ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
    "$NEW/build.log" | tail -n 50 || true
  tail -n 50 "$NEW/build.log"
  echo "New private workspace: $NEW"
  echo "Production deployment: NONE"
  exit 1
}
test -s "$NEW/src/frp.new"
file "$NEW/src/frp.new" | grep -Fq 'ELF 32-bit'
nm "$NEW/src/compress.o" | grep -Eq '[[:space:]]T[[:space:]]hd11_uncompress_bounded$'
nm "$NEW/src/files2.o" | grep -Eq '[[:space:]]T[[:space:]]load_ply$'
echo "Bounded native load candidate: COMPILED"

echo "=== 5. INSTALL ONLY VERIFIED PRIVATE GUILD ROOMS ==="
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
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
echo "Empty private player/ledger data: VERIFIED"
echo "Network/PID/mount isolation: REQUIRED"

echo "=== 6. TEST CORRUPT LOAD DENIAL + 50 GUILD RESTART CHECKS ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$NEW/round11f_bounded_runner.py" "$NEW/rootfs" \
  > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== PRIVATE GAME DIAGNOSTICS ==="
  tail -n 45 "$NEW/server.log" 2>/dev/null || true
fi

echo "=== 7. RECHECK ORIGINAL AND LIVE INTEGRITY ==="
test "$(source_hash)" = "$LIVE_BEFORE"
test "$(source_hash)" = "$EXPECTED"
test "$(sha256sum "$R11D/src/frp.new" | awk '{print $1}')" = "$ENGINE_BEFORE"
test "$(old_players_hash)" = "$PLAYER_BEFORE"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_BEFORE"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
( cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null )
echo "Production C source and guild rooms: UNCHANGED"
echo "Previous Round11D character saves and binary: UNCHANGED"
echo "Production service: NOT RESTARTED"
echo "Website: NOT MODIFIED"
if [ "$STATUS" -eq 0 ]; then
  grep -Fq 'Passed: 54' "$NEW/results.log"
  grep -Fq 'Failed: 0' "$NEW/results.log"
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  echo "Round 11F 54/54 native + corrupt-save checks: PASSED"
fi
echo "=== ROUND 11F PRIVATE RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Test report: $NEW/results.log"
echo "Private workspace: $NEW"
echo "Production deployment: NONE"
echo "Full malformed-input fuzz/ledger/equipment fault testing: PENDING"
echo "=== ROUND 11F COMPLETE ==="
exit "$STATUS"
