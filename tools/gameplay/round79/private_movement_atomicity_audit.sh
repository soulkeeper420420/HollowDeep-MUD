#!/usr/bin/env bash
# Round 79I: verify no production change; inspect verified private Breath
# storage build for atomic move/room checkpoints, terrain and recovery.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass private Round79I results directory}"
SOURCE="${2:?Pass verified private Breath storage native source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79i-*) ;; *)
    echo "DENIED: expected private Round79I directory" >&2; exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79store-*/src) ;; *)
    echo "DENIED: expected private tested Round79H storage source" >&2; exit 2;;
esac
test -d "$WORK/repo" &&
test -f "$SOURCE/frp.new" &&
test -f "$SOURCE/hd_breath_store.inc"

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
SERVICE=hollowdeep.service
PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
HASH_BEFORE="$(sha256sum "$LIVE" | cut -d' ' -f1)"
CANDIDATE_BEFORE="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

echo "=== ROUND 79I: PRIVATE MOVEMENT ATOMICITY AUDIT ==="
echo "=== 1. PRIVATE PATH AND SOURCE PARSER TESTS ==="
(
 cd "$HERE"
 python3 -m unittest -q test_native_movement_atomicity_audit
)

echo "=== 2. FIND RESOLVED NATIVE MOVE/GO AND ATOMIC SAVE ==="
python3 "$HERE/native_movement_atomicity_audit.py" "$SOURCE" \
  > "$WORK/movement-atomicity-report.txt"
tail -n 3 "$WORK/movement-atomicity-report.txt"

echo "=== 3. VERIFY PRODUCTION AND PRIVATE BASELINE UNCHANGED ==="
test "$PID_BEFORE" = "$(systemctl show "$SERVICE" -p MainPID --value)"
test "$HASH_BEFORE" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$CANDIDATE_BEFORE" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet "$SERVICE"

echo "ROUND 79I: PRIVATE MOVEMENT ATOMICITY AUDIT PASS"
echo "SOURCE REPORT: $WORK/movement-atomicity-report.txt"
echo "NATIVE BREATH MOVEMENT / MOUNTS: NOT YET ACTIVE"
echo "PRODUCTION SERVICE PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
