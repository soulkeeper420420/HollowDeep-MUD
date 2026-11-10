#!/usr/bin/env bash
# Round 11D: compile private bounded native-format atomic-save candidate and
# replay 50 native guild + graceful persistence checks. No production edits.
set -Eeuo pipefail
umask 077

ROOT="/root/hollowdeep-dev/guild-social-batch1"
R10="$ROOT/round10-PpNpn17k"
R10E="$ROOT/round10-persist-PE4PRFyX"
R10G="$ROOT/round10-graceful-NylI8Od3"
LIVE="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="213eb1a107ef7db25d27554c2904ccd3958583cf"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2"

hash_live() {
  ( cd "$LIVE"; find . -type f -print0 | sort -z |
    xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
player_hash() {
  ( cd "$R10G/rootfs/player"; find . -type f -print0 | sort -z |
    xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local i path
  for i in $(seq 6000 6011); do
    path=$(printf '%s/r%05d' "$LIVE_ROOMS" "$i")
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "STOP: Production guild room present: $path"
      return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 11D PRIVATE ATOMIC SAVE CANDIDATE ==="
echo "=== 1. VERIFY PRODUCTION PROTECTION / BASELINE ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -s "$R10E/src/frp.new"
test -s "$R10E/src/files2.c"
test -s "$R10E/src/compress.c"
test -s "$R10E/src/hollowdeep_social.c"
test -s "$R10/rooms.sha256"
test -s "$R10G/results.log"
grep -Fq 'Passed: 50' "$R10G/results.log"
grep -Fq 'Failed: 0' "$R10G/results.log"
test -d "$R10G/rootfs/player"
test -s "$BASE/bin/hollowdeep"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$R10E/src" -type l -print -quit)"
test -z "$(find "$R10/test-world/rooms" -type l -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$R10E/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$R10E/src/Makefile"; then
  echo "STOP: Test guild founding bypass detected"; exit 1
fi
grep -Fq 'save_ply(player->name, player)' "$R10E/src/hollowdeep_social.c"
LIVE_HASH=$(hash_live)
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
R10E_HASH=$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')
R10G_PLAYERS=$(player_hash)
echo "Production source and private world: VERIFIED"
echo "Round 10G 50/50 PASS baseline: VERIFIED"
echo "Original private players and executables: PROTECTED"

echo "=== 2. COPY TO NEW, EMPTY PRIVATE BUILD AND WORLD ==="
NEW=$(mktemp -d "$ROOT/round11-atomic-XXXXXXXX")
mkdir -m 700 "$NEW/src" "$NEW/rootfs"
cp -a "$R10E/src/." "$NEW/src/"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "Isolated Round 11D workspace: $NEW"

echo "=== 3. APPLY PRIVATE-ONLY BOUNDED SAVE PATCH ==="
curl -fsSL --retry 2 --max-time 30 \
  "$RAW/round11d_stage_atomic_save.py" -o "$NEW/round11d_stage_atomic_save.py"
curl -fsSL --retry 2 --max-time 30 \
  "$RAW/round10g_graceful_runner.py" -o "$NEW/round10g_graceful_runner.py"
test -s "$NEW/round11d_stage_atomic_save.py"
test -s "$NEW/round10g_graceful_runner.py"
python3 -m py_compile "$NEW/round11d_stage_atomic_save.py" "$NEW/round10g_graceful_runner.py"
grep -Fq 'All three disconnect saves completed and stable:' "$NEW/round10g_graceful_runner.py"
python3 "$NEW/round11d_stage_atomic_save.py" "$NEW/src"
grep -Fq 'hd11_put_object' "$NEW/src/files2.c"
grep -Fq 'hd11_atomic_player_write' "$NEW/src/files2.c"
grep -Fq 'hd11_compress_bounded' "$NEW/src/compress.c"

echo "=== 4. COMPILE EXPERIMENTAL 32-BIT NATIVE ENGINE ==="
(
  cd "$NEW/src"
  find . -maxdepth 1 -type f -name '*.o' -delete
  rm -f frp.new
  timeout 240 make -j1 > "$NEW/build.log" 2>&1
) || {
  echo "=== PRIVATE COMPILER DIAGNOSTICS ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
    "$NEW/build.log" | tail -n 45 || true
  tail -n 60 "$NEW/build.log"
  echo "New private workspace: $NEW"
  echo "Production changes: NONE"
  exit 1
}
test -s "$NEW/src/frp.new"
file "$NEW/src/frp.new" | grep -Fq 'ELF 32-bit'
nm "$NEW/src/compress.o" | grep -Eq '[[:space:]]T[[:space:]]hd11_compress_bounded$'
nm "$NEW/src/files2.o" | grep -Eq '[[:space:]]T[[:space:]]save_ply$'
echo "Bounded-save native engine: COMPILED"

echo "=== 5. INSTALL VERIFIED ROOMS INTO DISPOSABLE GAME ==="
for i in $(seq 6000 6011); do
  file=$(printf 'r%05d' "$i")
  test -s "$R10/test-world/rooms/$file"
  test ! -e "$NEW/rootfs/rooms/$file"
  cp -p "$R10/test-world/rooms/$file" "$NEW/rootfs/rooms/$file"
done
cp -p "$R10/test-world/rooms/r06000" "$NEW/rootfs/rooms/r00001"
cp -p "$R10/test-world/rooms/r06001" "$NEW/rootfs/rooms/r00002"
cp -p "$NEW/src/frp.new" "$NEW/rootfs/bin/hollowdeep"
mkdir -p "$NEW/rootfs/hollowdeep-data"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
echo "Fresh native-format private world: READY"
echo "Private network namespace: REQUIRED"

echo "=== 6. RUN 50 GUILD AND GRACEFUL RESTART ASSERTIONS ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$NEW/round10g_graceful_runner.py" "$NEW/rootfs" \
  > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== PRIVATE GAME DIAGNOSTICS ==="
  tail -n 35 "$NEW/server.log" 2>/dev/null || true
fi

echo "=== 7. ASSERT NO UNFINISHED PRIVATE TEMP SAVES ==="
if [ "$STATUS" -eq 0 ]; then
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '*~' -print -quit)"
  grep -Fq 'Failed: 0' "$NEW/results.log"
  echo "Atomic save temporary/backup litter: NONE"
fi

echo "=== 8. VERIFY LIVE AND EXISTING TESTS REMAIN UNCHANGED ==="
test "$(hash_live)" = "$LIVE_HASH"
test "$(hash_live)" = "$EXPECTED"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test "$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')" = "$R10E_HASH"
test "$(player_hash)" = "$R10G_PLAYERS"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
echo "Production source and rooms: UNCHANGED"
echo "Previous Round 10G characters and executable: UNCHANGED"
echo "Production server restarted: NO"
echo "Website: NOT MODIFIED"
echo "=== ROUND 11D EXPERIMENTAL RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "Private workspace: $NEW"
echo "Production deployment: NONE"
echo "Crash/fault-injection certification: NOT YET PERFORMED"
echo "=== ROUND 11D COMPLETE ==="
exit "$STATUS"
