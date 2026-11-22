#!/usr/bin/env bash
# Round79S: deterministic NEW mount-roster + stable/Endurance policy.
# Compile in root-only private directory, never in native MUD source.
# Does not start a MUD listener or change player/world/service files.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass NEW /root/hollowdeep-dev/round79s-* results directory}"
SOURCE="${2:?Pass accepted private Round79P ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79s-*) ;; *)
 echo "REFUSED: private Round79S result directory required" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *)
 echo "REFUSED: accepted private ELF32 rest source required" >&2;exit 2;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
 echo "REFUSED: missing or unsafe pinned/private native input" >&2;exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo "REFUSED: expected ELF32 accepted private native game" >&2;exit 2;
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$BASE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
on_exit() {
 status=$?
 if ! unchanged; then
   echo "ROUND79S: SAFETY FAIL — production/private executable changed" >&2
   status=1
 else
   echo "PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED"
 fi
 if ((status)) && [[ -f "$WORK/mount-roster-test.log" ]]; then
   tail -n 80 "$WORK/mount-roster-test.log"
 fi
 echo "PRIVATE RESULTS: $WORK"
 echo "PRODUCTION DEPLOYMENT: NONE"
 exit "$status"
}
trap on_exit EXIT

echo "=== ROUND79S: MOUNT OWNERSHIP/STABLE/ENDURANCE POLICY ==="
echo "=== 1. COMPILE PRIVATE ELF32 PURE ROSTER + TERRAIN RULES ==="
cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror -pedantic \
  -I "$HERE" \
  "$HERE/hd_wilderness_breath.c" \
  "$HERE/hd_mount_travel.c" \
  "$HERE/hd79_mount_roster.c" \
  "$HERE/test_hd79_mount_roster.c" \
  -o "$WORK/test-mount-roster"
[[ "$(od -An -tx1 -N5 "$WORK/test-mount-roster" | tr -d ' \n')" == 7f454c4601 ]]

echo "=== 2. RUN FULL EPOCH/OWNERSHIP/STABLE/TRAVEL TEST REPLAY ==="
"$WORK/test-mount-roster" | tee "$WORK/mount-roster-test.log"
grep -Fq 'ROUND79S: PRIVATE EPOCH-BOUND MOUNT ROSTER POLICY PASS' \
  "$WORK/mount-roster-test.log"

echo "=== 3. VERIFY ACCEPTED PRIVATE ELF32/PRODUCTION UNCHANGED ==="
unchanged
echo "ROUND79S: PRIVATE MOUNT ROSTER/ENDURANCE/STABLE POLICY PASS"
echo "NATIVE PLAYER SAVE/OWNERSHIP COMMANDS: NOT YET CONNECTED"
echo "NO LIVE WORLD/PLAYER/SERVICE MODIFICATIONS"
echo "PRODUCTION DEPLOYMENT: NONE"
