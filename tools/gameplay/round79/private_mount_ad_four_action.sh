#!/usr/bin/env bash
# Round79AD R6B: native four-record CAS, test-only socket actions and R5 deaths.
# Never changes the live world, accepted branch, systemd service or player DB.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Fresh /root/hollowdeep-dev/round79ad-* results directory}"
SOURCE="${2:?Clean R6A private /tmp/hd-army-game-round79adauth-*/src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: private result root';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79adauth-*/src) ;; *) echo 'REFUSED: private R6A source only';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   ! -e "$WORK/r6b-stage.log" && -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" && -f "$SOURCE/frp.new" &&
   ! -L "$SOURCE/frp.new" && -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: unsafe source or stale work root';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: source must be existing private ELF32';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adcas-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local rc=$?
 trap - EXIT
 if ! unchanged;then rc=1;echo 'FAIL: production or R6A source ELF32 changed';fi
 if ((rc));then
  echo "ROUND79AD R6B: PRIVATE NATIVE ACTION CAS TEST FAILED ($rc)"
  for file in "$WORK"/{r6b-stage-tests,r6b-stage,r6b-game-build,r6b-test-build,r6b-socket}.log;do
   if [[ -f "$file" ]];then echo "=== $(basename "$file") ===";tail -n 95 "$file";fi
  done
 else
  echo 'ROUND79AD R6B: PRIVATE ATOMIC FOUR-RECEIPT BOARD/DISMOUNT ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND R6A PRIVATE ELF32: UNCHANGED'
 fi
 echo 'NATIVE PLAYER COMMANDS, CREATURE SIDE EFFECTS, RESTART RESTORE, MOUNTED TRAVEL: DISABLED'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$rc"
}
trap finish EXIT

echo '=== ROUND79AD R6B: ATOMIC PRIVATE FOUR-RECEIPT ACTION SAVE ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_ad_four_action test_build_ad_r6b_socket) \
 >"$WORK/r6b-stage-tests.log" 2>&1 || {
 tail -90 "$WORK/r6b-stage-tests.log";exit 1; }
tail -5 "$WORK/r6b-stage-tests.log"
python3 "$HERE/stage_mount_ad_four_action.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/r6b-stage.log" 2>&1 || {
 tail -100 "$WORK/r6b-stage.log";exit 1; }
cat "$WORK/r6b-stage.log"
STAGED="$STAGE/src"

# R5 source-tested dedicated species definitions; never touch existing
# world monster template banks or persisted room/player files.
cp "$HERE/hd79_ad_species.c" "$HERE/hd79_ad_species.h" "$STAGED/"
python3 - "$STAGED" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/'Makefile'
s=p.read_text(encoding='latin-1')
anchor='frp.new: $(OBJECTS)'
if s.count(anchor)!=1 or 'HD79_AD_SPECIES_PLAYTEST' in s:
    raise ValueError('Native R6B species link anchor drift')
s=s.replace(anchor,'CFLAGS += -DHD79_AD_SPECIES_PLAYTEST\n'
    'OBJECTS += hd79_ad_species.o\n\n'+anchor,1)
p.write_text(s,encoding='latin-1')
PY

build_game() {
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
 MOUNT_AD_COMBAT_DEATH=1 MOUNT_AD_AUTH_ACTION=1 MOUNT_AD_ACTION_CAS=1 frp.new
}

build_game "$STAGED" >"$WORK/r6b-game-build.log" 2>&1 || {
 tail -110 "$WORK/r6b-game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGED/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGED/hd79_ad_authenticated_action.o" ]]
nm "$STAGED/frp.new" >"$WORK/r6b-normal-symbols.log"
if grep -Eq 'hd79_ad_socket_fixture|hd79_ad_r6b_socket_fixture|hd79_ad_four_store_test_award' \
 "$WORK/r6b-normal-symbols.log";then
 echo 'FAIL: test-only socket grant leaked into normal candidate';exit 1
fi
grep -q 'hd79_ad_four_action_commit_native' "$WORK/r6b-normal-symbols.log" || {
 echo 'FAIL: native R6B action CAS not linked';exit 1; }
echo 'PASS: genuine native ELF32 links private CAS, no test grants or socket fixture'

# A separate copied test ELF32 is the ONLY build with the synthetic socket
# grant/action command. Ordinary mount commands stay fail-closed.
TEST_ROOT="$(mktemp -d /tmp/hd-army-game-round79adcas-socket-XXXXXXXX)"
cp -a "$STAGED" "$TEST_ROOT/src"
TEST_SOURCE="$TEST_ROOT/src"
python3 "$HERE/build_ad_r6b_socket_fixture.py" \
 "$HERE/test_ad_native_socket_fixture.c" \
 "$TEST_SOURCE/hd79_ad_r6b_socket_fixture.c"
python3 - "$TEST_SOURCE" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1])
make=(src/'Makefile').read_text(encoding='latin-1')
anchor='frp.new: $(OBJECTS)'
if make.count(anchor)!=1 or 'HD79_AD_SOCKET_TESTING' in make:
    raise ValueError('Native socket test-only build anchor drift')
make=make.replace(anchor,
  'CFLAGS += -DHD79_AD_SOCKET_TESTING -DHD_ATOMIC_TESTING '
  '-DHD79_AD_FOUR_STORE_TESTING\n'
  'OBJECTS += hd79_ad_r6b_socket_fixture.o\n\n'+anchor,1)
(src/'Makefile').write_text(make,encoding='latin-1')
p=src/'global.c'
g=p.read_text(encoding='latin-1')
anchor='{ "mount", 100, hd79_mount_command },'
if g.count(anchor)!=1 or 'adfixture' in g:
    raise ValueError('Native test-only command dispatch anchor drift')
g='extern int hd79_ad_socket_fixture();\n'+g.replace(anchor,
    '        { "adfixture", 100, hd79_ad_socket_fixture },\n'+anchor,1)
p.write_text(g,encoding='latin-1')
PY
build_game "$TEST_SOURCE" >"$WORK/r6b-test-build.log" 2>&1 || {
 tail -110 "$WORK/r6b-test-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$TEST_SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
python3 "$HERE/build_ad_combat_socket_replay.py" \
 /root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py \
 "$WORK/r5-base-socket.py"
python3 "$HERE/build_ad_r6b_socket_replay.py" \
 "$WORK/r5-base-socket.py" "$WORK/check_r6b_socket.py"
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_r6b_socket.py" "$TEST_SOURCE" \
 >"$WORK/r6b-socket.log" 2>&1 || {
 tail -120 "$WORK/r6b-socket.log";exit 1; }
grep -Fq 'ROUND79AD R6B: PRIVATE NATIVE ATOMIC BOARD/DISMOUNT CAS SOCKET PASS' \
 "$WORK/r6b-socket.log"
grep -Fq 'ROUND79AD: SIX REAL NATIVE COMBAT DEATHS PASS' \
 "$WORK/r6b-socket.log"
grep -Fq 'PASS: failed native action rename leaves all four receipts intact' \
 "$WORK/r6b-socket.log"
grep -Fq 'PASS: native R6B action CAS board/dismount, uncertain rename' \
 "$WORK/r6b-socket.log"
tail -35 "$WORK/r6b-socket.log"
unchanged
printf '%s\n' 'ROUND79AD R6B PRIVATE ACTION CAS AND SIX NATIVE COMBAT DEATHS VERIFIED' \
 'PRODUCTION DEPLOYMENT: NONE'
