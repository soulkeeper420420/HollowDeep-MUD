#!/usr/bin/env bash
# Resume only HollowDeep's private Round 10 workspace after the patcher stopped.
set -Eeuo pipefail
umask 077

WORK="/root/hollowdeep-dev/guild-social-batch1/round10-PpNpn17k"
SRC="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
TEST_SRC="/root/hollowdeep-dev/guild-social-batch1/round9-X6jx4lbm/src"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
COMMIT="18c9bd0a9fdb8fa0a3fdd114b0825e75156bccde"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$COMMIT/engine/experiments/guild-social-v2"

echo "=== HOLLOWDEEP ROUND 10 NATIVE SAVE COMPILER FIX ==="

source_hash() {
  ( cd "$SRC"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
live_rooms_clear() {
  local id path
  for id in $(seq 6000 6011); do
    path=$(printf '%s/r%05d' "$LIVE_ROOMS" "$id")
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "STOP: Real room exists: $path"
      return 1
    fi
  done
}

echo "=== 1. VERIFY PRIVATE STAGE AND PRODUCTION ==="
test "$(id -u)" -eq 0
test "$(source_hash)" = "$EXPECTED"
test -s "$TEST_SRC/frp.new"
test -s "$BASE/bin/hollowdeep"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -d "$WORK/src"
test -d "$WORK/rootfs"
test -d "$WORK/test-world/rooms"
test -z "$(find "$WORK" -type l -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
live_rooms_clear
for item in room.c command7.c command6.c command10.c hollowdeep_social.c hollowdeep_social.h Makefile; do
  test -s "$WORK/src/$item"
done
test -s "$WORK/guild_district_gen.c"
test -s "$WORK/round10_runner.py"
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$WORK/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$WORK/src/Makefile"; then
  echo "STOP: Unsafe deed-free founding flag detected"
  exit 1
fi
grep -Fq 'hd_guild_mint_deed(obj_ptr2)' "$WORK/src/command7.c"
for f in command6.c command10.c; do
  grep -Fq 'if (!hd_guild_can_enter(ply_ptr, rom_ptr->rom_num)) return 0;' "$WORK/src/$f"
done
grep -Fq 'hd_guild_can_enter' "$WORK/src/room.c"
grep -Fq 'PSAVES' "$WORK/src/hollowdeep_social.c"
test ! -e "$WORK/test-world/rooms/r06000"
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
TEST_HASH=$(sha256sum "$TEST_SRC/frp.new" | awk '{print $1}')
echo "Previous staged shop/go/sneak/central room ACL patches: VERIFIED"
echo "Original source: VERIFIED UNCHANGED"

echo "=== 2. REPAIR UNDEFINED NATIVE SAVE FLAG IN PRIVATE STAGE ==="
curl -fsSL --retry 2 --max-time 30 \
  "$RAW/round10_fix_native_save.py" -o "$WORK/round10_fix_native_save.py"
python3 -m py_compile "$WORK/round10_fix_native_save.py"
python3 "$WORK/round10_fix_native_save.py" "$WORK/src"

echo "=== 3. COMPILE PRIVATE NATIVE ENGINE ==="
(
  cd "$WORK/src"
  find . -maxdepth 1 -type f -name '*.o' -delete
  rm -f frp.new
  timeout 240 make -j1 > "$WORK/build-resume.log" 2>&1
) || {
  echo "=== PRIVATE COMPILER DIAGNOSTICS ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
    "$WORK/build-resume.log" | tail -n 45 || true
  tail -n 55 "$WORK/build-resume.log"
  echo "Production engine: UNTOUCHED"
  echo "Staging workspace: $WORK"
  exit 1
}
test -s "$WORK/src/frp.new"
file "$WORK/src/frp.new" | grep -Fq 'ELF 32-bit'
for sym in hd_guild_mint_deed hd_guild_can_enter hd_player_clan; do
  nm "$WORK/src/hollowdeep_social.o" |
    grep -Eq "[[:space:]]T[[:space:]]$sym$"
  echo "$sym: COMPILED"
done

echo "=== 4. GENERATE LINKED DISTRICT IN DISPOSABLE WORLD ==="
gcc -m32 -std=gnu89 -D_GNU_SOURCE -O1 -fcommon \
  -I "$WORK/src" "$WORK/guild_district_gen.c" \
  -o "$WORK/guild-district-gen" > "$WORK/generator-resume.log" 2>&1 || {
    cat "$WORK/generator-resume.log"
    exit 1
  }
"$WORK/guild-district-gen" "$WORK/test-world/rooms" |
  tee "$WORK/generation-resume.log"
for id in $(seq 6000 6011); do
  name=$(printf 'r%05d' "$id")
  test -s "$WORK/test-world/rooms/$name"
  test ! -e "$WORK/rootfs/rooms/$name"
  cp -p "$WORK/test-world/rooms/$name" "$WORK/rootfs/rooms/$name"
done
( cd "$WORK/test-world/rooms"; sha256sum r* > "$WORK/rooms.sha256";
  sha256sum -c "$WORK/rooms.sha256" >/dev/null )
cp -p "$WORK/test-world/rooms/r06000" "$WORK/rootfs/rooms/r00001"
cp -p "$WORK/test-world/rooms/r06001" "$WORK/rootfs/rooms/r00002"
echo "Connected Guild District: PRIVATE ROOM FILES GENERATED"

echo "=== 5. INSTALL INTO DISPOSABLE GAME ONLY ==="
cp -p "$WORK/src/frp.new" "$WORK/rootfs/bin/hollowdeep"
mkdir -p "$WORK/rootfs/hollowdeep-data"
test -z "$(find "$WORK/rootfs/player" -mindepth 1 -print -quit)"
test -z "$(find "$WORK/rootfs" -type l -print -quit)"
chown -R 65534:65534 "$WORK/rootfs"
chmod 700 "$WORK/rootfs/hollowdeep-data"
python3 -m py_compile "$WORK/round10_runner.py"
echo "Private network namespace: REQUIRED"
echo "Real players/world: NOT COPIED"

echo "=== 6. RUN THREE-PLAYER GUILD / HOUSING PLAYTEST ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$WORK/round10_runner.py" "$WORK/rootfs" \
  > "$WORK/results-resume.log" 2>&1
STATUS=$?
set -e
cat "$WORK/results-resume.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== PRIVATE GAME DIAGNOSTICS ==="
  tail -n 35 "$WORK/server.log" 2>/dev/null || true
fi

echo "=== 7. FINAL INTEGRITY ==="
test "$(source_hash)" = "$EXPECTED"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test "$(sha256sum "$TEST_SRC/frp.new" | awk '{print $1}')" = "$TEST_HASH"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
live_rooms_clear
( cd "$WORK/test-world/rooms"; sha256sum -c "$WORK/rooms.sha256" >/dev/null )
echo "Production engine/rooms/characters: UNCHANGED"
echo "Public website: NOT MODIFIED"
echo "Running production MUD: NOT RESTARTED"
echo "=== ROUND 10 SAVE FIX RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Results: $WORK/results-resume.log"
echo "Production deployment: NONE"
echo "=== ROUND 10 SAVE FIX COMPLETE ==="
exit "$STATUS"
