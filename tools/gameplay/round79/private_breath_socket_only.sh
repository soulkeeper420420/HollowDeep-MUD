#!/usr/bin/env bash
# Round79K socket-only continuation after a verified ELF32 compile and
# private atomic Breath transaction fixture PASS.
# Read-only toward the prior ELF32 source and live production.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || {
  echo "REFUSED: run as root for isolated namespace/chroot" >&2; exit 2;
}
WORK="${1:?Provide NEW private Round79K socket results directory}"
SOURCE="${2:?Provide compiled and tested Round79K private travel source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79ks-*) ;; *)
  echo "REFUSED: isolated results directory required" >&2; exit 2 ;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: prior private Round79K ELF32 candidate required" >&2; exit 2 ;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" ]] || {
  echo "REFUSED: pinned repo or private source missing" >&2; exit 2;
}
for name in frp.new command2.c command6.c hd79_breath_travel_runtime.c \
            hd_breath_move_checkpoint.inc; do
  [[ -f "$SOURCE/$name" && ! -L "$SOURCE/$name" ]] || {
    echo "REFUSED: private source file missing or symlinked: $name" >&2; exit 2;
  }
done
[[ ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: private candidate symlink" >&2; exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: expected previously compiled ELF32 game" >&2; exit 2;
}
grep -Fq 'HD79_BREATH_TRAVEL_PLAYTEST' "$SOURCE/command2.c"
grep -Fq 'HD79_BREATH_TRAVEL_PLAYTEST' "$SOURCE/command6.c"
grep -Fq 'hd79_breath_precommit' "$SOURCE/hd79_breath_travel_runtime.c"

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

verify_unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$SOURCEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]]
}
finish() {
  local status=$?
  if ! verify_unchanged; then
    echo "ROUND 79K: WARNING — baseline/service verification failed"
    status=1
  else
    echo "PRODUCTION PID/BINARY AND PRIVATE ELF32 BASELINE: UNCHANGED"
  fi
  if ((status)); then
    echo "ROUND 79K: PRIVATE SOCKET TEST FAILED (exit $status)"
    [[ ! -f "$WORK/socket.log" ]] || tail -n 70 "$WORK/socket.log"
  fi
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$status"
}
trap finish EXIT

echo "=== ROUND 79K: SOCKET-ONLY CONTINUATION ==="
echo "=== 1. VERIFY CORRECT PRIVATE SOCKET SUPPORT PATHS ==="
(cd "$HERE" && python3 -m unittest -q \
 test_stage_breath_travel.TravelStageTests.test_socket_harness_helpers_resolve_from_tools_tree \
 test_breath_socket_reconnect)

echo "=== 2. REUSE PASSED PRIVATE ELF32 GAME FOR REAL SOCKET REPLAY ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$HERE/check_breath_travel_socket.py" "$SOURCE" \
    > "$WORK/socket.log" 2>&1 || {
  tail -n 75 "$WORK/socket.log"
  exit 1
}

grep -Fq 'ROUND 79K: PRIVATE SOCKET BREATH TRAVEL + HUD PASS' \
    "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo "ROUND 79K: SOCKET BREATH TRAVEL AND HUD PASS"
echo "RESTING +15, MOUNTS/ENDURANCE/STABLES: PENDING"
echo "PRODUCTION DEPLOYMENT: NONE"
