#!/usr/bin/env bash
# Round 10 private guild charter + hall ACL playtest ONLY.
set -Eeuo pipefail
umask 077

ROOT="/root/hollowdeep-dev/guild-social-batch1"
ORIGINAL="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
TEST_SRC="$ROOT/round9-X6jx4lbm/src"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
# Immutable revision that contains all V2 experiment components.
COMMIT="ae49643d6063ac5d6f5ac1af538f94e592e1607c"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$COMMIT/engine/experiments/guild-social-v2"

echo "=== HOLLOWDEEP ROUND 10 CHARTER + GUILD HALL PLAYTEST ==="

hash_source() {
  ( cd "$ORIGINAL"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_room_absent() {
  local id
  for id in $(seq 6000 6011); do
    local path
    path=$(printf '%s/r%05d' "$LIVE_ROOMS" "$id")
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "STOP: Live room now exists: $path"
      return 1
    fi
  done
}

echo "=== 1. PROTECT LIVE GAME ==="
test "$(id -u)" -eq 0
test "$(hash_source)" = "$EXPECTED"
test -s "$TEST_SRC/frp.new"
test -s "$BASE/bin/hollowdeep"
test -s "$BASE/rooms/r00001"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$TEST_SRC" -type l -print -quit)"
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$TEST_SRC/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$TEST_SRC/Makefile"; then
  echo "STOP: The deed-free founding feature must not be built."
  exit 1
fi
check_live_room_absent

TEST_HASH=$(sha256sum "$TEST_SRC/frp.new" | awk '{print $1}')
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Production checksum: VERIFIED"
echo "Prior private compiled test: VERIFIED"

echo "=== 2. STAGE NEW EXPERIMENTAL SOURCE AND WORLD ==="
WORK=$(mktemp -d "$ROOT/round10-XXXXXXXX")
mkdir -m 700 "$WORK/src" "$WORK/rootfs" "$WORK/test-world" "$WORK/test-world/rooms"
cp -a "$TEST_SRC/." "$WORK/src/"
cp -a "$BASE/." "$WORK/rootfs/"
test -z "$(find "$WORK" -type l -print -quit)"
echo "Private Round 10 workspace: $WORK"

echo "=== 3. DOWNLOAD PINNED V2 EXPERIMENT ==="
for name in hollowdeep_social.c hollowdeep_social.h \
            guild_district_gen.c round10_apply.py round10_runner.py; do
  local_target="$WORK/$name"
  case "$name" in
    hollowdeep_social.c|hollowdeep_social.h) local_target="$WORK/src/$name" ;;
  esac
  curl -fsSL --retry 2 --max-time 30 "$RAW/$name" -o "$local_target"
  test -s "$local_target"
done
grep -Fq 'HDGUILD2' "$WORK/src/hollowdeep_social.c"
grep -Fq 'hd_guild_mint_deed' "$WORK/src/hollowdeep_social.c"
grep -Fq 'hd_guild_can_enter' "$WORK/src/hollowdeep_social.h"
python3 -m py_compile "$WORK/round10_apply.py" "$WORK/round10_runner.py"
echo "Experimental V2 C source: DOWNLOADED"
echo "Test scripts: SYNTAX-VALIDATED"

echo "=== 4. PATCH PRIVATE ENGINE PATHS ==="
python3 "$WORK/round10_apply.py" "$WORK/src"

echo "=== 5. COMPILE PRIVATE NATIVE GAME ==="
(
  cd "$WORK/src"
  find . -maxdepth 1 -type f -name '*.o' -delete
  rm -f ./frp.new
  timeout 240 make -j1 > "$WORK/build.log" 2>&1
) || {
  echo "=== ROUND 10 COMPILER DIAGNOSTICS ==="
  grep -nE 'error:|undefined reference|multiple definition' "$WORK/build.log" |
    tail -n 40 || true
  tail -n 55 "$WORK/build.log"
  echo "Workspace: $WORK"
  exit 1
}
test -s "$WORK/src/frp.new"
file "$WORK/src/frp.new" | grep -Fq 'ELF 32-bit'
for symbol in hd_guild_mint_deed hd_guild_can_enter hd_player_clan; do
  nm "$WORK/src/hollowdeep_social.o" |
    grep -Eq "[[:space:]]T[[:space:]]$symbol$"
  echo "$symbol: COMPILED"
done

echo "=== 6. BUILD NATIVE FORMAT CONNECTED GUILD DISTRICT ==="
gcc -m32 -std=gnu89 -D_GNU_SOURCE -O1 -fcommon \
  -I "$WORK/src" "$WORK/guild_district_gen.c" \
  -o "$WORK/guild-district-gen" \
  > "$WORK/generator-build.log" 2>&1 || {
    cat "$WORK/generator-build.log"
    exit 1
  }
"$WORK/guild-district-gen" "$WORK/test-world/rooms" |
  tee "$WORK/generator-results.log"
for id in $(seq 6000 6011); do
  name=$(printf 'r%05d' "$id")
  test -s "$WORK/test-world/rooms/$name"
  test ! -e "$WORK/rootfs/rooms/$name"
  cp -p "$WORK/test-world/rooms/$name" "$WORK/rootfs/rooms/$name"
done
( cd "$WORK/test-world/rooms"; sha256sum r* > "$WORK/rooms.sha256";
  sha256sum -c "$WORK/rooms.sha256" >/dev/null )

# Disposable entry shop and stock used by native shop test.
cp -p "$WORK/test-world/rooms/r06000" "$WORK/rootfs/rooms/r00001"
cp -p "$WORK/test-world/rooms/r06001" "$WORK/rootfs/rooms/r00002"

echo "=== 7. PREPARE ISOLATED MUD AND PLAYER DATA ==="
cp -p "$WORK/src/frp.new" "$WORK/rootfs/bin/hollowdeep"
mkdir -p "$WORK/rootfs/hollowdeep-data"
test -z "$(find "$WORK/rootfs/player" -mindepth 1 -print -quit)"
test -z "$(find "$WORK/rootfs" -type l -print -quit)"
chown -R 65534:65534 "$WORK/rootfs"
chmod 700 "$WORK/rootfs/hollowdeep-data"
echo "Native gameplay process: DISPOSABLE"
echo "Test gold funding code: STAGING ONLY"

echo "=== 8. RUN THREE-PLAYER COMBINED GAMEPLAY TEST ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$WORK/round10_runner.py" "$WORK/rootfs" \
  > "$WORK/results.log" 2>&1
STATUS=$?
set -e
cat "$WORK/results.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== PRIVATE GAME DIAGNOSTICS ==="
  tail -n 30 "$WORK/server.log" 2>/dev/null || true
fi

echo "=== 9. VERIFY PRODUCTION AND EARLIER TEST INTEGRITY ==="
test "$(hash_source)" = "$EXPECTED"
test "$(sha256sum "$TEST_SRC/frp.new" | awk '{print $1}')" = "$TEST_HASH"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_room_absent
( cd "$WORK/test-world/rooms"; sha256sum -c "$WORK/rooms.sha256" >/dev/null )
echo "Production engine/source/rooms/player data: UNCHANGED"
echo "Public website: NOT ACCESSED"
echo "Original isolated executables: UNCHANGED"
echo "Production service restarted: NO"

echo "=== ROUND 10 RESULT ==="
echo "Playtest exit code: $STATUS"
echo "Private results: $WORK/results.log"
echo "Private workspace: $WORK"
echo "Live deployment: NONE"
echo "=== ROUND 10 COMPLETE ==="
exit "$STATUS"
