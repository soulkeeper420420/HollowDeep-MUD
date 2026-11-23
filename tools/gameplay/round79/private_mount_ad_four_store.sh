#!/usr/bin/env bash
# Round79AD R3: one private native 80/81/82/83 atomic save + socket replay.
# Neither the live world nor a real player file is opened for writing.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Pass new /root/hollowdeep-dev/round79ad-* private work directory}"
SOURCE="${2:?Pass R2 accepted private /tmp/hd-army-game-round79adgate-*/src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: unsafe work path';exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79adgate-*/src) ;; *) echo 'REFUSED: expected private R2 source';exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: unsafe nonprivate source, symlink or uid';exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: expected verified private ELF32 engine';exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adfour-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-army-79adfour-fixture-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local code=$?
 if ! unchanged;then code=1;echo 'ROUND79AD R3: PRODUCTION/BASELINE SAFETY FAILED';fi
 if ((code));then
  echo "ROUND79AD R3: PRIVATE FOUR-RECEIPT INTEGRATION FAILED ($code)"
  for file in "$WORK"/{stage-tests,stage,native-build,native-test,game-build,socket}.log;do
   if [[ -f "$file" ]];then echo "=== $(basename "$file") ===";tail -n 85 "$file";fi
  done
 else
  echo 'ROUND79AD R3: PRIVATE NATIVE FOUR-RECEIPT ATOMIC SAVE ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND PREVIOUS R2 ELF32: UNCHANGED'
 fi
 echo 'COMBAT DEATH HOOK/PLAYER MOUNT COMMANDS/RESTORE/MOUNTED MOVE: NOT YET CONNECTED'
 echo 'LEGACY TWO/THREE MOUNT WRITERS: REFUSED BY R3 PRIVATE FEATURE GATE'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79AD R3: PRIVATE NATIVE 80/81/82/83 ATOMIC DEATH STORE ==='
echo '=== 1. PRIVATE NATIVE STAGING AND SECURITY REGRESSIONS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 \
 python3 -m unittest -q test_stage_mount_ad_four_store) \
 >"$WORK/stage-tests.log" 2>&1 || { tail -n 90 "$WORK/stage-tests.log"; exit 1; }
tail -n 5 "$WORK/stage-tests.log"

echo '=== 2. STRICT PRIVATE ELF32 R2->R3 SOURCE STAGING ==='
python3 "$HERE/stage_mount_ad_four_store.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/stage.log" 2>&1 || { tail -n 90 "$WORK/stage.log"; exit 1; }
cat "$WORK/stage.log"

echo '=== 3. PRIVATE SYNTHETIC REAL NATIVE PLAYER FIXTURE ==='
python3 - "$HERE" "$FIX" <<'PY'
from pathlib import Path
import ast,sys
here,fix=map(Path,sys.argv[1:])
p=here.parents[1]/'necromancer/petstore/onepass_linode.py'
if not p.is_file():raise RuntimeError('Missing accepted native pet fixture generator')
tree=ast.parse(p.read_text())
values=[node.value for node in tree.body if isinstance(node,ast.Assign) and
        any(isinstance(target,ast.Name) and target.id=='PAYLOAD' for target in node.targets)]
if len(values)!=1:raise RuntimeError('Native fixture generator drift')
fixture=ast.literal_eval(values[0])['test_pet_store.c']
if not isinstance(fixture,str) or 'int main' not in fixture:
    raise RuntimeError('Synthetic native fixture absent')
(fix/'test_pet_store.c').write_text(fixture)
PY

echo '=== 4. ELF32 REAL PLAYER COMPRESSED SNAPSHOT + FAILURE/REPLAY TEST ==='
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
 -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
 -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
 -DHD79_BREATH_STORE_PLAYTEST -DHD79_MOUNT_STORE_PLAYTEST \
 -DHD79_MOUNT_PRESENCE_STORE_PLAYTEST \
 -DHD79_AD_FOUR_STORE_PLAYTEST -DHD79_AD_FOUR_STORE_TESTING \
 -Wno-implicit-function-declaration -Wno-int-conversion \
 -Wno-incompatible-pointer-types \
 -ffunction-sections -fdata-sections -Wl,--gc-sections \
 -I "$STAGE/src" -I "$FIX" -I "$HERE" \
 "$HERE/test_native_four_store_round79ad.c" \
 "$STAGE/src/hd_mount_travel.c" \
 "$STAGE/src/hd79_mount_roster.c" \
 "$STAGE/src/hd79_mount_wire.c" \
 "$STAGE/src/hd79_mount_presence.c" \
 "$STAGE/src/hd79_ad_death_receipt.c" \
 "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
 "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
 "$STAGE/src/treasure_receipt.c" \
 "$STAGE/src/atomic_player_snapshot.c" \
 "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
 -o "$FIX/test-ad-four-native" >"$WORK/native-build.log" 2>&1 || {
  tail -n 120 "$WORK/native-build.log";exit 1;
}
[[ "$(od -An -tx1 -N5 "$FIX/test-ad-four-native" | tr -d ' \n')" == 7f454c4601 ]]
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-ad-four-native") \
 >"$WORK/native-test.log" 2>&1 || { tail -n 100 "$WORK/native-test.log"; exit 1; }
grep -Fq 'ROUND79AD R3: PRIVATE NATIVE FOUR-RECEIPT PLAYER STORE PASS' \
 "$WORK/native-test.log"
tail -n 20 "$WORK/native-test.log"

echo '=== 5. FULL PRIVATE ELF32 NATIVE GAME LINK, NO NEW GAME COMMANDS ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 MOUNT_COMMAND_PLAYTEST=1 MOUNT_STABLECHECK_PLAYTEST=1 \
 MOUNT_PRESENCE_STORE_PLAYTEST=1 MOUNT_TRIPLE_COMMAND_PLAYTEST=1 \
 MOUNT_WORLD_IDENTITY_PLAYTEST=1 MOUNT_LIFECYCLE_PLAYTEST=1 \
 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 MOUNT_AD_PRIVATE_FLEET=1 \
 MOUNT_AD_DEATH_GATE=1 MOUNT_AD_FOUR_STORE=1 \
 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -n 105 "$WORK/game-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: complete private native ELF32 engine compiles four-receipt writer'

echo '=== 6. ISOLATED GAME SOCKET: BREATH/STABLECHECK/LOGOUT REPLAY ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
 echo 'REFUSED: accepted stablecheck/Breath socket script missing'; exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ad3_socket.py" <<'PY'
from pathlib import Path
import sys
src,dst=map(Path,sys.argv[1:])
script=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79adfour-")'
if script.count(old)!=1:raise RuntimeError('Accepted socket source anchor changed')
dst.write_text(script.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ad3_socket.py" "$STAGE/src" \
 >"$WORK/socket.log" 2>&1 || { tail -n 95 "$WORK/socket.log"; exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo '=== 7. PRODUCTION AND PRIOR ELF32 UNCHANGED ==='
unchanged
echo 'ROUND79AD R3: PRIVATE FOUR-RECEIPT COMPRESSION/ATOMICITY/REPLAY PASS'
echo 'DEATH SAVE ADAPTER EXISTS; COMBAT DEATH HOOK AND RECONNECT RESTORE STILL DISABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
