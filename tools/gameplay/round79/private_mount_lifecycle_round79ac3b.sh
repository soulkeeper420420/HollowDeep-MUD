#!/usr/bin/env bash
# Round79AC3B: isolated central mount-binding revocation hooks.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Use new /root/hollowdeep-dev/round79ac3b-* directory}"
SOURCE="${2:?Use accepted AC2 private /tmp/.../src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac3b-*) ;; *) echo "REFUSED: private result path required";exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79worldproof-*/src) ;; *) echo "REFUSED: accepted private source required";exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
  echo "REFUSED: unsafe private directories or not root";exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: accepted source must be ELF32";exit 2;
}
[[ -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
  echo "REFUSED: symlinks in accepted native source";exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79lifecycle-XXXXXXXX)"
unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
     "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
     "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
     systemctl is-active --quiet hollowdeep.service
}
finish() {
  local result=$?
  if ! unchanged; then
    echo 'ROUND79AC3B: PRODUCTION/ACCEPTED ELF32 SAFETY FAILED' >&2
    result=1
  fi
  if ((result)); then
    echo "ROUND79AC3B: PRIVATE TEST FAILED ($result)"
    for f in "$WORK"/{stage,native-build,native-test,game-build,socket}.log; do
      if [[ -f "$f" ]]; then echo "=== $(basename "$f") ==="; tail -n 70 "$f";fi
    done
  else
    echo 'ROUND79AC3B: PRIVATE NATIVE LIFECYCLE REVOCATION PASS'
    echo 'PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED'
  fi
  echo "PRIVATE SOURCE: $STAGE/src"
  echo "PRIVATE RESULTS: $WORK"
  echo 'PRODUCTION DEPLOYMENT: NONE'
  exit "$result"
}
trap finish EXIT

echo '=== ROUND79AC3B: TRUSTED NATIVE MOUNT TOKEN REVOCATION ==='
echo '=== 1. STRICT PRIVATE SOURCE PATCH AND REGRESSION TESTS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_lifecycle_round79ac3b)

echo '=== 2. STAGE ACTUAL ACCEPTED PRIVATE ELF32 SOURCE ==='
python3 "$HERE/stage_mount_lifecycle_round79ac3b.py" \
  "$SOURCE" "$STAGE/src" >"$WORK/stage.log" 2>&1 || {
    tail -n 80 "$WORK/stage.log"; exit 1;
  }
cat "$WORK/stage.log"

echo '=== 3. REAL ELF32 IDENTITY TEST WITH CONSERVATIVE ALL-TOKEN CLEAR ==='
MOCK="$WORK/mock"
mkdir -p "$MOCK"
cp "$STAGE/src/hd79_mount_world_identity.c" "$MOCK/hd79_mount_world_identity.c"
cp "$STAGE/src/hd79_mount_world_identity.h" "$MOCK/hd79_mount_world_identity.h"
python3 - "$HERE/test_world_identity_round79ac2.c" "$MOCK/test_identity.c" <<'PY'
from pathlib import Path
import sys
src,dst=map(Path,sys.argv[1:])
code=src.read_text()
needle='    printf("ROUND79AC2: PRIVATE NATIVE MOUNT WORLD IDENTITY PASS\\n");'
if code.count(needle)!=1:
    raise ValueError('Accepted Round79AC2 test source anchor changed')
addition=(
 '    hd79_world_mount_unbind_all();\n'
 '    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);\n'
 '    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==1);\n'
 '    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);\n'
 '    hd79_world_mount_unbind_all();\n'
 '    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);\n'
 '    puts("PASS: native room unload all-clear revokes every ephemeral mount token");\n'
)
dst.write_text(code.replace(needle,addition+needle))
PY
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$MOCK" -I "$HERE/ac2-mock" -I "$HERE" \
 "$MOCK/test_identity.c" \
 "$MOCK/hd79_mount_world_identity.c" \
 "$HERE/hd79_mount_presence.c" \
 "$HERE/hd79_mount_roster.c" \
 "$HERE/hd_mount_travel.c" \
 -o "$WORK/test-native-revoke" >"$WORK/native-build.log" 2>&1 || {
   tail -n 95 "$WORK/native-build.log";exit 1;
 }
[[ "$(od -An -tx1 -N5 "$WORK/test-native-revoke" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-native-revoke" > "$WORK/native-test.log" 2>&1 || {
 tail -n 75 "$WORK/native-test.log";exit 1;
}
grep -Fq 'PASS: native room unload all-clear revokes every ephemeral mount token' "$WORK/native-test.log"
grep -Fq 'ROUND79AC2: PRIVATE NATIVE MOUNT WORLD IDENTITY PASS' "$WORK/native-test.log"
tail -n 8 "$WORK/native-test.log"

echo '=== 4. REBUILD COMPLETE DISPOSABLE ELF32 GAME WITH CENTRAL HOOKS ==='
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
 frp.new > "$WORK/game-build.log" 2>&1 || {
   tail -n 95 "$WORK/game-build.log";exit 1;
 }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: full private ELF32 game builds native room/free lifecycle hooks'

echo '=== 5. ISOLATED NATIVE SOCKET BASELINE REGRESSION ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
 echo 'REFUSED: accepted socket harness missing';exit 2;
}
python3 - "$BASE_SOCKET" "$WORK/check_socket.py" <<'PY'
from pathlib import Path
import sys
src,dst=map(Path,sys.argv[1:])
body=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79lifecycle-")'
if body.count(old)!=1:
    raise RuntimeError('Accepted socket replay anchor drift')
dst.write_text(body.replace(old,new))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_socket.py" "$STAGE/src" \
  > "$WORK/socket.log" 2>&1 || { tail -n 80 "$WORK/socket.log"; exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -n 12 "$WORK/socket.log"

echo '=== 6. PRODUCTION AND ACCEPTED BASELINE SAFETY ==='
unchanged
echo 'ROUND79AC3B: PRIVATE ELF32 DISPOSAL/LOGOUT REVOCATION AND SOCKET PASS'
echo 'NO MOUNT SPAWN/BIND AT GAMEPLAY; NO BOARD/STABLE/RETRIEVE/TRAVEL'
echo 'PRODUCTION DEPLOYMENT: NONE'
