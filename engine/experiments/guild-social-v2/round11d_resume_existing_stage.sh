#!/usr/bin/env bash
# Round 11D: resume *only* the previously compiled disposable private stage.
# Do NOT reapply native save patches or rebuild; do NOT touch production.
set -Eeuo pipefail
umask 077

BASE="/root/hollowdeep-dev/guild-social-batch1"
WORK="$BASE/round11-atomic-pGqKMYDt"
LIVE="/srv/hollowdeep/world/src_3.00"
ROOMS="/srv/hollowdeep/world/rooms"
R10="$BASE/round10-PpNpn17k"
R10E="$BASE/round10-persist-PE4PRFyX"
R10G="$BASE/round10-graceful-NylI8Od3"
ROOTFS="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="82f044922b5378fdd201dd200d28fd1c16418ffc"
RAW="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round11d_resume_runner.py"

hash_live() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
hash_previous_players() {
  ( cd "$R10G/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local id file
  for id in $(seq 6000 6011); do
    file=$(printf '%s/r%05d' "$ROOMS" "$id")
    if [ -e "$file" ] || [ -L "$file" ]; then
      echo "STOP: Live guild room exists: $file"
      return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 11D FIXED TEST GUARD RESUME ==="
echo "=== 1. ASSERT PRODUCTION AND PRIVATE STAGE INTEGRITY ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -d "$WORK/rootfs"
test -d "$WORK/src"
test -s "$WORK/src/frp.new"
test -s "$WORK/src/files2.c"
test -s "$WORK/src/compress.c"
test -s "$WORK/build.log"
test -s "$WORK/results.log"
test -s "$WORK/rootfs/bin/hollowdeep"
cmp -s "$WORK/src/frp.new" "$WORK/rootfs/bin/hollowdeep"
test -s "$R10E/src/frp.new"
test -s "$R10/rooms.sha256"
test -s "$R10G/results.log"
grep -Fq 'Passed: 50' "$R10G/results.log"
grep -Fq 'Failed: 0' "$R10G/results.log"
grep -Fq 'Passed: 0' "$WORK/results.log"
grep -Fq 'Failed: 0' "$WORK/results.log"
grep -Fq 'Round 10 private workspace guard rejected the path' "$WORK/results.log"
grep -Fq 'hd11_put_object' "$WORK/src/files2.c"
grep -Fq 'hd11_atomic_player_write' "$WORK/src/files2.c"
grep -Fq 'hd11_compress_bounded' "$WORK/src/compress.c"
grep -Fq 'save_ply(player->name, player)' "$WORK/src/hollowdeep_social.c"
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$WORK/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$WORK/src/Makefile"; then
  echo "STOP: Unsafe free-guild test flag is enabled"; exit 1
fi
test -z "$(find "$WORK" -type l -print -quit)"
test -z "$(find "$ROOTFS" -type l -print -quit)"
test -z "$(find "$ROOTFS/player" -mindepth 1 -print -quit)"
test -z "$(find "$WORK/rootfs/player" -mindepth 1 -print -quit)"
test ! -e "$WORK/rootfs/hollowdeep-data/player-guilds.v1"
test -z "$(find "$WORK/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
for id in $(seq 6000 6011); do
  file=$(printf 'r%05d' "$id")
  cmp -s "$R10/test-world/rooms/$file" "$WORK/rootfs/rooms/$file"
done
file "$WORK/src/frp.new" | grep -Fq 'ELF 32-bit'
nm "$WORK/src/compress.o" | grep -Eq '[[:space:]]T[[:space:]]hd11_compress_bounded$'
nm "$WORK/src/files2.o" | grep -Eq '[[:space:]]T[[:space:]]save_ply$'

BEFORE_LIVE=$(hash_live)
BEFORE_ENGINE=$(sha256sum "$WORK/src/frp.new" | awk '{print $1}')
BEFORE_R10E=$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')
BEFORE_R10G_PLAYERS=$(hash_previous_players)
BEFORE_BASE=$(sha256sum "$ROOTFS/bin/hollowdeep" | awk '{print $1}')
echo "Original production source: VERIFIED"
echo "Existing Round11D 32-bit save candidate: VERIFIED COMPILED"
echo "Original Round11D players/ledger: EMPTY"
echo "Previous private guild tests: PRESERVED"
echo "Production deployment: DISABLED"

echo "=== 2. FETCH ONLY CORRECTED PRIVATE TEST RUNNER ==="
RUNNER="$WORK/round11d_resume_runner.py"
test ! -e "$RUNNER"
test ! -L "$RUNNER"
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 "$RAW" -o "$RUNNER"
test -s "$RUNNER"
grep -Fq 'round11-atomic-pGqKMYDt/rootfs' "$RUNNER"
grep -Fq 'Round 11D resume permits only its existing private rootfs' "$RUNNER"
grep -Fq 'All three disconnect saves completed and stable:' "$RUNNER"
grep -Fq 'verify_native_saves("after stop")' "$RUNNER"
python3 -m py_compile "$RUNNER"
echo "Workspace-specific runner: VERIFIED"
echo "Source repatching: DISABLED"
echo "Recompilation: DISABLED"

echo "=== 3. RUN 50 NATIVE GAMEPLAY AND RESTART CHECKS ==="
set +e
timeout --signal=TERM --kill-after=3s 420s \
  unshare --mount --net --pid --fork \
  python3 "$RUNNER" "$WORK/rootfs" \
  > "$WORK/results-resume.log" 2>&1
STATUS=$?
set -e
cat "$WORK/results-resume.log"
if [ "$STATUS" -ne 0 ]; then
  echo "=== DISPOSABLE GAME DIAGNOSTICS ==="
  tail -n 45 "$WORK/server.log" 2>/dev/null || true
fi

echo "=== 4. VERIFY NO LOSS OF PRODUCTION OR OLD TEST DATA ==="
test "$(hash_live)" = "$BEFORE_LIVE"
test "$(hash_live)" = "$EXPECTED"
test "$(sha256sum "$WORK/src/frp.new" | awk '{print $1}')" = "$BEFORE_ENGINE"
test "$(sha256sum "$R10E/src/frp.new" | awk '{print $1}')" = "$BEFORE_R10E"
test "$(hash_previous_players)" = "$BEFORE_R10G_PLAYERS"
test "$(sha256sum "$ROOTFS/bin/hollowdeep" | awk '{print $1}')" = "$BEFORE_BASE"
test -z "$(find "$ROOTFS/player" -mindepth 1 -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
echo "Production source and rooms: UNCHANGED"
echo "Prior private test players/binaries: UNCHANGED"
echo "Production server restarted: NO"
echo "Website: NOT MODIFIED"
if [ "$STATUS" -eq 0 ]; then
  test -z "$(find "$WORK/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  test -z "$(find "$WORK/rootfs/player" -maxdepth 1 -name '*~' -print -quit)"
  grep -Fq 'Failed: 0' "$WORK/results-resume.log"
  echo "Private temporary saves: CLEAN"
fi
echo "=== ROUND 11D RESUME RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $WORK/results-resume.log"
echo "Private workspace: $WORK"
echo "Live deployment: NONE"
echo "Crash/fault injection: NOT TESTED"
echo "=== ROUND 11D RESUME COMPLETE ==="
exit "$STATUS"
