#!/usr/bin/env bash
# Round79AC1: native three-receipt dismount/list commands, isolated only.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Pass fresh private work directory}"
SOURCE="${2:?Pass accepted Round79AB private ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac-*) ;; *) echo 'REFUSED private work root';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79presence-*/src) ;; *) echo 'REFUSED private AB baseline';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || { echo 'REFUSED: unsafe source or uid';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || { echo 'REFUSED: no ELF32 base';exit 2; }
[[ -z "$(find "$SOURCE" -type l -print -quit)" ]] || { echo 'REFUSED: symlink source';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79triplecmd-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-ac-fixture-XXXXXXXX)"
check_unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finish() {
 code=$?
 if ! check_unchanged; then echo 'PRODUCTION/BASELINE SAFETY CHECK FAILED' >&2;code=1;fi
 if ((code)); then
  echo "ROUND79AC1: PRIVATE FAILURE ($code)"
  for f in "$WORK"/{stage,mock-build,native-build,native-test,game-build,socket}.log;do
   if [[ -f "$f" ]];then echo "=== $(basename "$f") ===";tail -n 40 "$f";fi
  done
 else
  echo 'ROUND79AC1: PRIVATE NATIVE TRIPLE-COMMAND/DISMOUNT PASS'
  echo 'PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED'
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79AC1: TRIPLE-RECEIPT NATIVE DISMOUNT AND STATUS ==='
echo '=== 1. PRIVATE STAGING REGRESSIONS ==='
(cd "$HERE" && python3 -m unittest -q test_stage_mount_triple_commands_round79ac1)
echo '=== 2. PURE MOCK SAVE-FAILURE REPLAY ==='
cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror \
 -I "$HERE/ac1-mock" -I "$HERE" \
 "$HERE/hd79_presence_dismount_store.c" "$HERE/ac1-mock/test_ac_dismount.c" \
 -o "$WORK/mock-dismount" >"$WORK/mock-build.log" 2>&1 || { tail -n 70 "$WORK/mock-build.log"; exit 1; }
"$WORK/mock-dismount" | tee "$WORK/mock-test.log"
cc -m32 -std=gnu99 -O1 -g -Wall -Wextra -Werror \
 -DHD79_MOUNT_TRIPLE_COMMAND_PLAYTEST \
 -I "$HERE/ac1-mock" -I "$HERE" \
 "$HERE/hd79_mount_command_ac.c" "$HERE/ac1-mock/test_ac_command.c" \
 -o "$WORK/mock-command" >"$WORK/mock-command-build.log" 2>&1 || {
 tail -n 70 "$WORK/mock-command-build.log";exit 1; }
"$WORK/mock-command" | tee "$WORK/mock-command-test.log"

echo '=== 3. STAGE STRICTLY PRIVATE ELF32 SOURCE ==='
python3 "$HERE/stage_mount_triple_commands_round79ac1.py" \
 "$SOURCE" "$STAGE/src" >"$WORK/stage.log" 2>&1 || { tail -n 80 "$WORK/stage.log"; exit 1; }
cat "$WORK/stage.log"

echo '=== 4. BUILD DISPOSABLE NATIVE PLAYER DISMOUNT TEST ==='
if [[ ! -f "$HERE/test_native_mount_presence_store_round79ab.c" ]]; then
 echo 'REFUSED: missing accepted Round79AB test fixture';exit 2
fi
python3 - "$HERE" "$FIX" <<'PY'
from pathlib import Path
import ast,sys
here,fix=map(Path,sys.argv[1:])
p=here.parents[1]/'necromancer/petstore/onepass_linode.py'
if not p.is_file():raise RuntimeError('Missing public synthetic source')
t=ast.parse(p.read_text())
ns=[x.value for x in t.body if isinstance(x,ast.Assign) and any(isinstance(k,ast.Name) and k.id=='PAYLOAD' for k in x.targets)]
if len(ns)!=1:raise RuntimeError('Private fixture source drift')
body=ast.literal_eval(ns[0])['test_pet_store.c']
if not isinstance(body,str) or 'int main' not in body:raise RuntimeError('Fixture invalid')
(fix/'test_pet_store.c').write_text(body)
test=here/'test_native_mount_presence_store_round79ab.c'
s=test.read_text()
if s.count('int main(void)')!=1:
    raise RuntimeError('Accepted AB native fixture entrypoint drift')
(fix/'round79ab_native_test_embed.c').write_text(
    s.replace('int main(void)','int round79ab_fixture_main(void)',1))
PY
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
 -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
 -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
 -DHD79_BREATH_STORE_PLAYTEST -DHD79_MOUNT_STORE_PLAYTEST \
 -DHD79_MOUNT_PRESENCE_STORE_PLAYTEST \
 -Wno-implicit-function-declaration -Wno-int-conversion \
 -Wno-incompatible-pointer-types \
 -ffunction-sections -fdata-sections -Wl,--gc-sections \
 -I "$STAGE/src" -I "$FIX" -I "$HERE" \
 "$HERE/test_native_dismount_round79ac1.c" \
 "$STAGE/src/hd_mount_travel.c" \
 "$STAGE/src/hd79_mount_roster.c" \
 "$STAGE/src/hd79_mount_wire.c" \
 "$STAGE/src/hd79_mount_presence.c" \
 "$STAGE/src/hd79_presence_dismount_store.c" \
 "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
 "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
 "$STAGE/src/treasure_receipt.c" \
 "$STAGE/src/atomic_player_snapshot.c" \
 "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
 -o "$FIX/test-ac-native" >"$WORK/native-build.log" 2>&1 || { tail -n 85 "$WORK/native-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$FIX/test-ac-native" | tr -d ' \n')" == 7f454c4601 ]]
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-ac-native") > "$WORK/native-test.log" 2>&1 || { tail -n 85 "$WORK/native-test.log"; exit 1; }
grep -Fq 'ROUND79AC1: REAL ELF32 ATOMIC DISMOUNT ADAPTER PASS' "$WORK/native-test.log"
tail -n 18 "$WORK/native-test.log"

echo '=== 5. BUILD COMPLETE PRIVATE ELF32 MUD WITH COMMAND TABLE ==='
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
 frp.new >"$WORK/game-build.log" 2>&1 || { tail -n 85 "$WORK/game-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: full game ELF32 build and triple-store native commands linked'

echo '=== 6. REAL NATIVE SOCKET: READ-ONLY AND STABLECHECK REGRESSIONS ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || { echo 'REFUSED: accepted Round79Z socket replay missing'; exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ac_socket.py" <<'PY'
from pathlib import Path
import sys
src,dest=map(Path,sys.argv[1:])
s=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79triplecmd-")'
if s.count(old)!=1:raise RuntimeError('Accepted native socket source drift')
dest.write_text(s.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ac_socket.py" "$STAGE/src" > "$WORK/socket.log" 2>&1 || { tail -n 75 "$WORK/socket.log"; exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: read-only stablecheck never creates a mount roster' "$WORK/socket.log"
tail -n 15 "$WORK/socket.log"

echo '=== 7. VERIFY UNCHANGED PRODUCTION ==='
check_unchanged
echo 'ROUND79AC1: PRIVATE TRIPLE-COMMAND LIVE STATUS/DISMOUNT PASS'
echo 'BOARD, STABLE, RETRIEVE, MOUNTED TRAVEL: STILL DISABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
