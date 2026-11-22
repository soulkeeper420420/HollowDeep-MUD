#!/usr/bin/env bash
# Round79L: reuse accepted Round79K private ELF32 source to identify
# the native REST/SLEEP/WAKE flags and update_ply timing.
# Strictly read-only on game source; private report never added to GitHub.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass NEW private /root/hollowdeep-dev/round79l-* results dir}"
SOURCE="${2:?Pass passed private Round79K ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79l-*) ;; *)
  echo "REFUSED: expected Round79L private results directory" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: expected accepted Round79K private ELF32 source" >&2;exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"
test -f "$SOURCE/hd79_breath_travel_runtime.c"
test -f "$SOURCE/player.c"
test "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" = 7f454c4601

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
HASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASE="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

echo "=== ROUND79L: NATIVE REST/SLEEP STATE AUDIT ==="
echo "=== 1. PRIVATE SOURCE SAFETY AND NATIVE REST STATE TESTS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q test_audit_native_rest_state)

echo "=== 2. INSPECT EXACT REST, STAND, SLEEP, WAKE AND UPDATE_PLY STATE ==="
python3 "$HERE/audit_native_rest_state.py" "$SOURCE" \
  >"$WORK/private-rest-state-report.txt"
tail -n 4 "$WORK/private-rest-state-report.txt"

echo "=== 3. VERIFY PRODUCTION AND ACCEPTED PRIVATE GAME UNCHANGED ==="
test "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$HASH" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$BASE" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79L: PRIVATE NATIVE REST/UPDATE SOURCE AUDIT PASS"
echo "REST STATE REPORT: $WORK/private-rest-state-report.txt"
echo "RESTING +15 PLAYABILITY: NOT YET INTEGRATED"
echo "PRODUCTION PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
