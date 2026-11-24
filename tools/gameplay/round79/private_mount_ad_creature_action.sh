#!/usr/bin/env bash
# R6C: unexposed physical mount/receipt lifecycle; real isolated native ELF32.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Fresh private /root/hollowdeep-dev/round79ad-* results}"
SOURCE="${2:?Prior verified private R6B /tmp/hd-army-game-round79adcas-*/src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: unsafe private work path';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79adcas-*/src) ;; *) echo 'REFUSED: unsafe R6B source';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   ! -e "$WORK/r6c-stage.log" && -d "$SOURCE" &&
   ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: symlink, missing source, reused work root'; exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: previous real ELF32 required';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adcreature-XXXXXXXX)"
unchanged(){
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish(){
 local code=$?
 trap - EXIT
 if ! unchanged;then echo 'FAIL: production or R6B ELF32 changed';code=1;fi
 if ((code));then
   echo "ROUND79AD R6C: PRIVATE NATIVE PHYSICAL RECONCILER FAILED ($code)"
   for file in "$WORK"/{r6c-py,r6c-stage,r6c-policy-build,r6c-policy,r6c-game-build,r6c-test-build,r6c-socket}.log;do
     if [[ -f "$file" ]];then echo "=== $(basename "$file") ===";tail -n 75 "$file";fi
   done
 else
   echo 'ROUND79AD R6C: PRIVATE NATIVE PHYSICAL BOARD/DISMOUNT ELF32/SOCKET PASS'
   echo 'PRODUCTION PID/BINARY AND R6B PRIVATE ELF32: UNCHANGED'
 fi
 echo 'NORMAL PLAYER COMMANDS, LOGIN RESTORE, MOUNTED TRAVEL: DISABLED'
 echo 'PRIVATE SOURCE:' "$STAGE/src"
 echo 'PRIVATE RESULTS:' "$WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79AD R6C: NATIVE PHYSICAL MOUNT RECONCILIATION ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_ad_creature_action test_build_ad_r6c_socket) \
 >"$WORK/r6c-py.log" 2>&1 || { tail -90 "$WORK/r6c-py.log";exit 1; }
tail -5 "$WORK/r6c-py.log"
python3 "$HERE/stage_mount_ad_creature_action.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/r6c-stage.log" 2>&1 || { tail -100 "$WORK/r6c-stage.log";exit 1; }
cat "$WORK/r6c-stage.log"
STAGED="$STAGE/src"

# Mock test checks four lifecycle transitions and uncertainty BEFORE native
# gameplay; native candidate verifies exact ELF32 ABI and command isolation.
cat > "$WORK/compat.h" <<'EOF'
#include "hd_player_store.h"
void del_crt_rom(creature *,room *);
void free_crt(creature *);
EOF
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$HERE/ad2-mock" -I "$HERE" -I "$STAGED" \
 -include "$WORK/compat.h" \
 "$HERE/hd79_ad_creature_action.c" "$HERE/test_hd79_ad_creature_action.c" \
 -o "$WORK/r6c-policy" >"$WORK/r6c-policy-build.log" 2>&1 || {
 tail -105 "$WORK/r6c-policy-build.log";exit 1; }
"$WORK/r6c-policy" >"$WORK/r6c-policy.log" 2>&1 || {
 tail -95 "$WORK/r6c-policy.log";exit 1; }
grep -Fq 'ROUND79AD R6C: PRIVATE NATIVE MOUNT CREATURE RECONCILIATION POLICY PASS' "$WORK/r6c-policy.log"
tail -8 "$WORK/r6c-policy.log"

build_native(){
 make -s -B -j2 -C "$1" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 CORPSE_PLAYTEST=1 \
 PET_STORE_PLAYTEST=1 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 BREATH_STORE_PLAYTEST=1 \
 BREATH_MOVE_CHECKPOINT_TEST=1 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 MOUNT_COMMAND_PLAYTEST=1 \
 MOUNT_STABLECHECK_PLAYTEST=1 MOUNT_PRESENCE_STORE_PLAYTEST=1 \
 MOUNT_TRIPLE_COMMAND_PLAYTEST=1 MOUNT_WORLD_IDENTITY_PLAYTEST=1 \
 MOUNT_LIFECYCLE_PLAYTEST=1 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 \
 MOUNT_AD_PRIVATE_FLEET=1 MOUNT_AD_DEATH_GATE=1 MOUNT_AD_FOUR_STORE=1 \
 MOUNT_AD_COMBAT_DEATH=1 MOUNT_AD_AUTH_ACTION=1 MOUNT_AD_ACTION_CAS=1 \
 MOUNT_AD_CREATURE_ACTION=1 frp.new
}
build_native "$STAGED" >"$WORK/r6c-game-build.log" 2>&1 || {
 tail -115 "$WORK/r6c-game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGED/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
nm "$STAGED/frp.new" >"$WORK/r6c-normal-symbols.log"
grep -Fq 'hd79_ad_creature_action' "$WORK/r6c-normal-symbols.log"
grep -Fq 'hd79_ad_native_bound_creature' "$WORK/r6c-normal-symbols.log"
if grep -Eq 'hd79_ad_socket_fixture|hd79_ad_r6c_socket_fixture|hd79_ad_four_store_test_award' \
 "$WORK/r6c-normal-symbols.log";then
 echo 'FAIL: test grant/fixture linked into normal candidate';exit 1
fi
echo 'PASS: genuine ELF32 links physical reconciler; normal native command table/test grants unchanged'

# Separate disposable native game with explicit test-only fixture. No real
# character, production path or stable registry is ever modified.
TEST_ROOT="$(mktemp -d /tmp/hd-army-game-round79adcreature-socket-XXXXXXXX)"
cp -a "$STAGED" "$TEST_ROOT/src"
TEST_SOURCE="$TEST_ROOT/src"
python3 "$HERE/build_ad_r6c_socket_fixture.py" \
 "$HERE/test_ad_native_socket_fixture.c" \
 "$TEST_SOURCE/hd79_ad_r6c_socket_fixture.c"
python3 - "$TEST_SOURCE" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]); p=src/'Makefile'
text=p.read_text(encoding='latin-1')
anchor='frp.new: $(OBJECTS)'
if text.count(anchor)!=1 or 'HD79_AD_SOCKET_TESTING' in text:
    raise ValueError('Test-only native Makefile anchor drift')
text=text.replace(anchor,
  'CFLAGS += -DHD79_AD_SOCKET_TESTING -DHD_ATOMIC_TESTING '
  '-DHD79_AD_FOUR_STORE_TESTING\n'
  'OBJECTS += hd79_ad_r6c_socket_fixture.o\n\n'+anchor,1)
p.write_text(text,encoding='latin-1')
p=src/'global.c';text=p.read_text(encoding='latin-1')
anchor='{ "mount", 100, hd79_mount_command },'
if text.count(anchor)!=1 or 'adfixture' in text:
    raise ValueError('Test-only global command anchor drift')
p.write_text('extern int hd79_ad_socket_fixture();\n'+text.replace(anchor,
  '        { "adfixture", 100, hd79_ad_socket_fixture },\n'+anchor,1),
  encoding='latin-1')
PY
build_native "$TEST_SOURCE" >"$WORK/r6c-test-build.log" 2>&1 || {
 tail -115 "$WORK/r6c-test-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$TEST_SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
python3 "$HERE/build_ad_combat_socket_replay.py" \
 /root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py \
 "$WORK/r5-base-socket.py"
python3 "$HERE/build_ad_r6c_socket_replay.py" \
 "$WORK/r5-base-socket.py" "$WORK/check_r6c_socket.py"
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_r6c_socket.py" "$TEST_SOURCE" \
 >"$WORK/r6c-socket.log" 2>&1 || {
 tail -130 "$WORK/r6c-socket.log";exit 1; }
grep -Fq 'ROUND79AD R6C: PRIVATE NATIVE PHYSICAL BOARD/DISMOUNT SOCKET PASS' "$WORK/r6c-socket.log"
grep -Fq 'ROUND79AD: SIX REAL NATIVE COMBAT DEATHS PASS' "$WORK/r6c-socket.log"
grep -Fq 'PASS: native R6C creature removed on atomic board;' "$WORK/r6c-socket.log"
tail -30 "$WORK/r6c-socket.log"
unchanged
echo 'ROUND79AD R6C REAL NATIVE CREATURE AND SIX DEATH REPLAYS PASS'
