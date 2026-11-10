#!/usr/bin/env bash
# Round 10E: clean disposable guild persistence replay. Do NOT deploy.
set -Eeuo pipefail
umask 077
ROOT="/root/hollowdeep-dev/guild-social-batch1"
OLD="$ROOT/round10-PpNpn17k"
LIVE="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="a22027f3a922cbb02bd00c0567c3598a2660dc3b"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2"
source_hash() { ( cd "$LIVE"; find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' ); }
old_player_hash() { ( cd "$OLD/rootfs/player"; find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' ); }
check_live_rooms() {
  local i f
  for i in $(seq 6000 6011); do
    f=$(printf '%s/r%05d' "$LIVE_ROOMS" "$i")
    if [ -e "$f" ] || [ -L "$f" ]; then echo "STOP: Live room exists: $f"; return 1; fi
  done
}

echo "=== HOLLOWDEEP ROUND 10E CHARACTER PERSISTENCE RETEST ==="
echo "=== 1. PROTECT PRODUCTION AND PRIOR TEST DATA ==="
test "$(id -u)" -eq 0
test "$(source_hash)" = "$EXPECTED"
test -s "$OLD/src/frp.new"
test -s "$OLD/src/files2.c"
test -s "$OLD/src/hollowdeep_social.c"
test -s "$OLD/rooms.sha256"
test -s "$BASE/bin/hollowdeep"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$OLD/src" -type l -print -quit)"
test -z "$(find "$OLD/test-world/rooms" -type l -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -f "$OLD/rootfs/player/Hdnlbxiba"
test ! -s "$OLD/rootfs/player/Hdnlbxiba"
test -s "$OLD/rootfs/player/Hdnlbxiba~"
test -s "$OLD/rootfs/player/Hdnlbxibb"
test -s "$OLD/rootfs/player/Hdnlbxibc"
check_live_rooms
( cd "$OLD/test-world/rooms"; sha256sum -c "$OLD/rooms.sha256" >/dev/null )
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$OLD/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$OLD/src/Makefile"; then
  echo "STOP: Deed-free founding flag must be disabled"; exit 1
fi
grep -Fq 'hd_guild_can_enter' "$OLD/src/room.c"
grep -Fq 'hd_guild_mint_deed' "$OLD/src/command7.c"
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
OLD_HASH=$(sha256sum "$OLD/src/frp.new" | awk '{print $1}')
OLD_PLAYERS=$(old_player_hash)
echo "Live source: VERIFIED"
echo "Failed-run player files: PRESERVED"
echo "12 original test rooms: VERIFIED"

echo "=== 2. COPY TO FRESH PRIVATE WORKSPACE ==="
NEW=$(mktemp -d "$ROOT/round10-persist-XXXXXXXX")
mkdir -m 700 "$NEW/src" "$NEW/rootfs"
cp -a "$OLD/src/." "$NEW/src/"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "New private workspace: $NEW"

echo "=== 3. APPLY PROTOTYPED TWO-ARGUMENT SAVE FIX ==="
curl -fsSL --retry 2 --max-time 30 \
  "$RAW/round10e_apply_twoarg.py" -o "$NEW/round10e_apply_twoarg.py"
curl -fsSL --retry 2 --max-time 30 \
  "$RAW/round10_runner.py" -o "$NEW/round10_runner.py"
python3 -m py_compile "$NEW/round10e_apply_twoarg.py" "$NEW/round10_runner.py"
grep -Fq 'verify_native_saves("before restart")' "$NEW/round10_runner.py"
grep -Fq 'verify_native_saves("after stop")' "$NEW/round10_runner.py"
python3 "$NEW/round10e_apply_twoarg.py" "$NEW/src"

echo "=== 4. COMPILE CLEAN 32-BIT PRIVATE GAME ==="
(
  cd "$NEW/src"
  find . -maxdepth 1 -type f -name '*.o' -delete
  rm -f frp.new
  timeout 240 make -j1 > "$NEW/build.log" 2>&1
) || {
  echo "=== COMPILER DIAGNOSTICS ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
    "$NEW/build.log" | tail -n 45 || true
  tail -n 50 "$NEW/build.log"
  echo "Private workspace: $NEW"
  exit 1
}
test -s "$NEW/src/frp.new"
file "$NEW/src/frp.new" | grep -Fq 'ELF 32-bit'
for sym in hd_guild_mint_deed hd_guild_can_enter hd_player_clan; do
  nm "$NEW/src/hollowdeep_social.o" |
    grep -Eq "[[:space:]]T[[:space:]]$sym$"
done
echo "Native two-argument save build: COMPILED"

echo "=== 5. INSTALL GUILD ROOMS INTO DISPOSABLE WORLD ==="
for i in $(seq 6000 6011); do
  file=$(printf 'r%05d' "$i")
  test -s "$OLD/test-world/rooms/$file"
  test ! -e "$NEW/rootfs/rooms/$file"
  cp -p "$OLD/test-world/rooms/$file" "$NEW/rootfs/rooms/$file"
done
cp -p "$OLD/test-world/rooms/r06000" "$NEW/rootfs/rooms/r00001"
cp -p "$OLD/test-world/rooms/r06001" "$NEW/rootfs/rooms/r00002"
cp -p "$NEW/src/frp.new" "$NEW/rootfs/bin/hollowdeep"
mkdir -p "$NEW/rootfs/hollowdeep-data"
test -z "$(find "$NEW/rootfs" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
chown -R 65534:65534 "$NEW/rootfs"
chmod 700 "$NEW/rootfs/hollowdeep-data"
echo "Fresh player data: EMPTY"
echo "Private network isolation: REQUIRED"

echo "=== 6. REPLAY GUILD AND RESTART PERSISTENCE TESTS ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$NEW/round10_runner.py" "$NEW/rootfs" \
  > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== PRIVATE GAME LOG ==="
  tail -n 35 "$NEW/server.log" 2>/dev/null || true
fi

echo "=== 7. VERIFY LIVE AND FAILED TEST WERE NOT MODIFIED ==="
test "$(source_hash)" = "$EXPECTED"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test "$(sha256sum "$OLD/src/frp.new" | awk '{print $1}')" = "$OLD_HASH"
test "$(old_player_hash)" = "$OLD_PLAYERS"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
( cd "$OLD/test-world/rooms"; sha256sum -c "$OLD/rooms.sha256" >/dev/null )
echo "Production source/rooms: UNCHANGED"
echo "Prior test characters: UNCHANGED"
echo "Prior test executable and rooms: UNCHANGED"
echo "Production MUD restart: NO"
echo "Website: NOT MODIFIED"

echo "=== ROUND 10E RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "New private workspace: $NEW"
echo "Production deployment: NONE"
echo "=== ROUND 10E COMPLETE ==="
exit "$STATUS"
