#!/usr/bin/env bash
# Round 79F: deterministic Breath receipt wire tests and read-only native audit.
# This script never modifies the live service, native world or player saves.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass new private Round79F results directory}"
SOURCE="${2:?Pass verified private HUD ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79f-*) ;; *)
  echo "REFUSED: expected private Round79F results directory" >&2
  exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79hud-*/src) ;; *)
  echo "REFUSED: expected tested disposable Round79E HUD source" >&2
  exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"

PID_BEFORE="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
LIVE_BEFORE="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_BEFORE="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
trap '
  code=$?
  echo "PRIVATE RUN: '"$WORK"'"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$code"
' EXIT

echo "=== ROUND 79F: DURABLE BREATH CONTRACT ==="
echo "=== 1. COMPILE AND TEST PRIVATE RECORD FORMAT ==="
cc -m32 -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE" \
  "$HERE/hd_breath_record.c" \
  "$HERE/hd_wilderness_breath.c" \
  "$HERE/hd_status_hud.c" \
  "$HERE/test_breath_record.c" \
  -o "$WORK/breath-record-test"
"$WORK/breath-record-test"

echo "=== 2. RECHECK ACTUAL MOVEMENT / STAMINA RULES ==="
cc -m32 -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE" \
  "$HERE/hd_wilderness_breath.c" \
  "$HERE/hd_status_hud.c" \
  "$HERE/test_wilderness_breath.c" \
  -o "$WORK/breath-movement-test"
"$WORK/breath-movement-test"

echo "=== 3. INSPECT ATOMIC NATIVE PLAYER SAVE / TIMER CONTRACT ==="
python3 "$HERE/native_breath_store_audit.py" "$SOURCE" \
  > "$WORK/breath-storage-report.txt"
tail -n 4 "$WORK/breath-storage-report.txt"

echo "=== 4. VERIFY NO PRODUCTION OR HUD SOURCE CHANGES ==="
test "$PID_BEFORE" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVE_BEFORE" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$SOURCE_BEFORE" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79F: PRIVATE BREATH RECORD/RULES PASS"
echo "NATIVE SAVE AND MOVEMENT DEBIT: PENDING INTEGRATION"
echo "REPORT: $WORK/breath-storage-report.txt"
echo "PRODUCTION SERVICE PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
