#!/usr/bin/env bash
# Round 10G: isolate test-runner disconnect/SIGTERM race. No C source edits.
set -Eeuo pipefail
umask 077
ROOT="/root/hollowdeep-dev/guild-social-batch1"
R10="$ROOT/round10-PpNpn17k"
R10E="$ROOT/round10-persist-PE4PRFyX"
LIVE="/srv/hollowdeep/world/src_3.00"
ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="cc2b7d219211fc103fadc50122824235ed7188ff"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round10g_graceful_runner.py"

source_hash() {
  (cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
player_hash() {
  (cd "$R10E/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
check_live_rooms() {
  local id path
  for id in $(seq 6000 6011); do
    path=$(printf '%s/r%05d' "$ROOMS" "$id")
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "STOP: Production guild room now exists: $path"
      return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 10G GRACEFUL DISCONNECT RETEST ==="
echo "=== 1. VERIFY PRODUCTION AND ISOLATED EXECUTABLE ==="
test "$(id -u)" -eq 0
test "$(source_hash)" = "$EXPECTED"
test -s "$R10E/src/frp.new"
test -s "$R10E/rootfs/bin/hollowdeep"
cmp -s "$R10E/src/frp.new" "$R10E/rootfs/bin/hollowdeep"
test -s "$R10/rooms.sha256"
test -d "$BASE/player"
test -s "$BASE/bin/hollowdeep"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$R10/test-world/rooms" -type l -print -quit)"
test -z "$(find "$R10E/rootfs/player" -type l -print -quit)"
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$R10E/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$R10E/src/Makefile"; then
  echo "STOP: Deed-free founding flag enabled"
  exit 1
fi
grep -Fq 'save_ply(player->name, player)' "$R10E/src/hollowdeep_social.c"
if grep -Fq 'save_ply(player);' "$R10E/src/hollowdeep_social.c"; then
  echo "STOP: Invalid one-argument save found"
  exit 1
fi
test -z "$(find "$R10E/src" -type l -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
LIVE_BEFORE=$(source_hash)
OLD_BINARY_HASH=$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')
OLD_PLAYER_HASH=$(player_hash)
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Production C source: VERIFIED"
echo "Round 10E corrected engine: VERIFIED"
echo "Previous failed-run characters: PRESERVED"
echo "Game execution before namespace: DISABLED"

echo "=== 2. CREATE CLEAN PRIVATE GAME, REUSE COMPILED ENGINE ==="
NEW=$(mktemp -d "$ROOT/round10-graceful-XXXXXXXX")
mkdir -m 700 "$NEW/rootfs"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
for id in $(seq 6000 6011); do
  f=$(printf 'r%05d' "$id")
  test -s "$R10/test-world/rooms/$f"
  test ! -e "$NEW/rootfs/rooms/$f"
  cp -p "$R10/test-world/rooms/$f" "$NEW/rootfs/rooms/$f"
done
cp -p "$R10/test-world/rooms/r06000" "$NEW/rootfs/rooms/r00001"
cp -p "$R10/test-world/rooms/r06001" "$NEW/rootfs/rooms/r00002"
cp -p "$R10E/src/frp.new" "$NEW/rootfs/bin/hollowdeep"
mkdir -p "$NEW/rootfs/hollowdeep-data"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
echo "Private gameplay root: $NEW/rootfs"
echo "C recompilation: NOT REQUIRED"

echo "=== 3. VERIFY GRACEFUL-DISCONNECT TEST RUNNER ==="
curl -fsSL --retry 2 --max-time 30 "$RAW" -o "$NEW/round10g_graceful_runner.py"
test -s "$NEW/round10g_graceful_runner.py"
python3 -m py_compile "$NEW/round10g_graceful_runner.py"
grep -Fq 'Native player disconnect acknowledgments: COMPLETE' "$NEW/round10g_graceful_runner.py"
grep -Fq 'All three disconnect saves completed and stable:' "$NEW/round10g_graceful_runner.py"
grep -Fq 'verify_native_saves("after stop")' "$NEW/round10g_graceful_runner.py"
echo "Disconnect-save barrier: VERIFIED"
echo "Private network namespace: REQUIRED"

echo "=== 4. PLAYTEST GUILD AND THREE CHARACTER RESTART PERSISTENCE ==="
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

echo "=== 5. VERIFY PRODUCTION AND OLD FAILED-RUN FILES ==="
test "$(source_hash)" = "$LIVE_BEFORE"
test "$(source_hash)" = "$EXPECTED"
test "$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')" = "$OLD_BINARY_HASH"
test "$(player_hash)" = "$OLD_PLAYER_HASH"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
echo "Production C source and guild rooms: UNCHANGED"
echo "Previous test players and compiled engine: UNCHANGED"
echo "Production MUD restarted: NO"
echo "Website: NOT MODIFIED"
echo "=== ROUND 10G RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "Workspace: $NEW"
echo "Live deployment: NONE"
echo "=== ROUND 10G COMPLETE ==="
exit "$STATUS"
