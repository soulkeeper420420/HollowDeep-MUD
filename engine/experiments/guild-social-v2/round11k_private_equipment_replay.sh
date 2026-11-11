#!/usr/bin/env bash
# One-shot Round11K private source fix + 73 native guild/ledger/restart checks.
# Fresh private world. No live changes. Equipped items are preserved by
# code path matching native savegame, but worn-item injection is a later test.
set -Eeuo pipefail
umask 077
HOMEDEV="/root/hollowdeep-dev/guild-social-batch1"
STABLE="$HOMEDEV/round11-fixed-ZpafezVN"
STABLE73="$HOMEDEV/round11-fixed-nyIRgHx6"
FAILED="$HOMEDEV/round11-load-UuprVvCZ"
R10="$HOMEDEV/round10-PpNpn17k"
LIVE="/srv/hollowdeep/world/src_3.00"
ROOMS="/srv/hollowdeep/world/rooms"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
PIN="92583863c08d5ac277f16393941aa43acef5ea7b"
URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round11k_patch_equipped_guild_save.py"

hash_live() {
  (cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
hash_test_players() {
  (cd "$STABLE73/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
check_live_rooms() {
 local n p
 for n in $(seq 6000 6011); do
   p=$(printf '%s/r%05d' "$ROOMS" "$n")
   if [ -e "$p" ] || [ -L "$p" ]; then
     echo "STOP: Live guild room exists: $p"; return 1
   fi
 done
}

echo "=== HOLLOWDEEP ROUND 11K PRIVATE EQUIPPED SAVE REPLAY ==="
echo "=== 1. VERIFY PASSED PRIVATE BASELINE AND PRODUCTION ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -s "$STABLE/results.log"
test -s "$STABLE73/results.log"
grep -Fq 'Passed: 54' "$STABLE/results.log"
grep -Fq 'Failed: 0' "$STABLE/results.log"
grep -Fq 'Passed: 73' "$STABLE73/results.log"
grep -Fq 'Failed: 0' "$STABLE73/results.log"
test -s "$STABLE/src/frp.new"
test -s "$STABLE/src/hollowdeep_social.c"
test -s "$STABLE/src/command8.c"
test -s "$STABLE73/round11i_runner.py"
test -s "$R10/rooms.sha256"
test -s "$BASE/bin/hollowdeep"
test -z "$(find "$STABLE/src" -type l -print -quit)"
test -z "$(find "$STABLE73/rootfs/player" -type l -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
grep -Fq 'HD_ROUND9_ISOLATED_FUNDS=1' "$STABLE/src/Makefile"
if grep -Fq 'HD_GUILD_STAGING_FREE_CREATE=1' "$STABLE/src/Makefile"; then
  echo "STOP: Unsafe test bypass flag enabled"; exit 1
fi
grep -Fq 'save_ply(player->name, player)' "$STABLE/src/hollowdeep_social.c"
grep -Fq 'hd11_atomic_player_write' "$STABLE/src/files2.c"
grep -Fq 'hd11_uncompress_bounded' "$STABLE/src/compress.c"
LIVE_BEFORE=$(hash_live)
STABLE_BINARY_BEFORE=$(sha256sum "$STABLE/src/frp.new" | awk '{print $1}')
STABLE73_BINARY_BEFORE=$(sha256sum "$STABLE73/rootfs/bin/hollowdeep" | awk '{print $1}')
OLD_PLAYERS_BEFORE=$(hash_test_players)
BASE_BINARY_BEFORE=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Original production and rooms: VERIFIED"
echo "Round11H/11I baselines: 54/54 and 73/73 PASS"
echo "Previous source and test players: PROTECTED"

echo "=== 2. COPY EXISTING BOUNDED NATIVE ENGINE TO NEW PRIVATE STAGE ==="
NEW=$(mktemp -d "$HOMEDEV/round11-equip-XXXXXXXX")
mkdir -m 700 "$NEW/src" "$NEW/rootfs"
cp -a "$STABLE/src/." "$NEW/src/"
cp -a "$BASE/." "$NEW/rootfs/"
test -z "$(find "$NEW" -type l -print -quit)"
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "Private workspace: $NEW"

echo "=== 3. PATCH ONLY PRIVATE GUILD SAVE CALLS ==="
PATCH="$NEW/round11k_patch_equipped_guild_save.py"
curl --fail --silent --show-error --location \
  --retry 2 --max-time 30 "$URL" -o "$PATCH"
test -s "$PATCH"
grep -Fq 'Native files2.c loader and atomic saver: UNCHANGED' "$PATCH"
python3 -m py_compile "$PATCH"
python3 "$PATCH" "$NEW"
grep -Fq 'hd_guild_save_equipped(player)' "$NEW/src/hollowdeep_social.c"
test -s "$NEW/src/hollowdeep_social.c.before-round11k"

echo "=== 4. REBUILD ONLY MODIFIED PRIVATE GUILD C AND RELINK ==="
(
  cd "$NEW/src"
  rm -f hollowdeep_social.o frp.new
  timeout 240 make -j1 > "$NEW/build.log" 2>&1
) || {
  echo "=== PRIVATE BUILD FAILURES ==="
  grep -nE 'error:|undefined reference|multiple definition|No rule to make target' \
       "$NEW/build.log" | tail -n 40 || true
  tail -n 40 "$NEW/build.log"
  echo "Private workspace: $NEW"
  exit 1
}
test -s "$NEW/src/frp.new"
file "$NEW/src/frp.new" | grep -Fq 'ELF 32-bit'
nm "$NEW/src/hollowdeep_social.o" | grep -Eq '[[:space:]]T[[:space:]]hd_player_clan$'
echo "Equipped-aware guild save candidate: 32-BIT COMPILED"

echo "=== 5. LOAD EMPTY DISPOSABLE WORLD WITH VERIFIED GUILD ROOMS ==="
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
test -z "$(find "$NEW/rootfs/player" -mindepth 1 -print -quit)"
echo "Fresh disposable players and ledger: EMPTY"

echo "=== 6. RETEST 73 NATIVE GUILD, LEDGER AND RESTART ASSERTIONS ==="
RUNNER="$NEW/round11k_runner.py"
cp -p "$STABLE73/round11i_runner.py" "$RUNNER"
python3 - "$RUNNER" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
old='not ROOT.parent.name.startswith("round11-fixed-")'
new='not ROOT.parent.name.startswith("round11-equip-")'
if s.count(old)!=1:
    raise SystemExit("STOP: Private runner workspace guard changed")
s=s.replace(old,new,1)
s=s.replace("Round 11H private workspace guard rejected the path",
            "Round 11K private workspace guard rejected the path",1)
s=s.replace("=== ROUND 11I FAST-TRACK GUILD SAFETY SUMMARY ===",
            "=== ROUND 11K EQUIPMENT-AWARE GUILD SAVE SUMMARY ===",1)
if "ROUND 11I: BAD LEDGER MUST FAIL CLOSED" not in s:
    raise SystemExit("STOP: 73-check ledger runner not preserved")
if "Starting native MUD again on SAME private port 4042" not in s:
    raise SystemExit("STOP: Same-port checks missing")
p.write_text(s)
PY
python3 -m py_compile "$RUNNER"
echo "Single-batch native 73-test replay: READY"
echo "Private PID/net/mount namespace: REQUIRED"

set +e
timeout --signal=TERM --kill-after=3s 480s \
  unshare --mount --net --pid --fork \
  python3 "$RUNNER" "$NEW/rootfs" > "$NEW/results.log" 2>&1
STATUS=$?
set -e
cat "$NEW/results.log"

echo "=== 7. VERIFY ORIGINAL TEST AND PRODUCTION INTEGRITY ==="
test "$(hash_live)" = "$LIVE_BEFORE"
test "$(hash_live)" = "$EXPECTED"
test "$(sha256sum "$STABLE/src/frp.new" | awk '{print $1}')" = "$STABLE_BINARY_BEFORE"
test "$(sha256sum "$STABLE73/rootfs/bin/hollowdeep" | awk '{print $1}')" = "$STABLE73_BINARY_BEFORE"
test "$(hash_test_players)" = "$OLD_PLAYERS_BEFORE"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_BINARY_BEFORE"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
(cd "$R10/test-world/rooms"; sha256sum -c "$R10/rooms.sha256" >/dev/null)
echo "Production source and rooms: UNCHANGED"
echo "Earlier tested player files and engine: UNCHANGED"
echo "Production MUD restarted: NO"
echo "Website: NOT MODIFIED"
if [ "$STATUS" -eq 0 ]; then
  grep -Fq 'Passed: 73' "$NEW/results.log"
  grep -Fq 'Failed: 0' "$NEW/results.log"
  test -z "$(find "$NEW/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
  echo "73-check native gameplay regression: PASS"
fi
echo "=== ROUND 11K RESULT ==="
echo "Gameplay exit status: $STATUS"
echo "Report: $NEW/results.log"
echo "Private workspace: $NEW"
echo "Live deployment: NONE"
echo "Actual worn-item grant/reload and cross-file failure injection: NOT YET TESTED"
echo "=== ROUND 11K COMPLETE ==="
exit "$STATUS"
