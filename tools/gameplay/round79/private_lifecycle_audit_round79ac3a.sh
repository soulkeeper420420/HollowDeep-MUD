#!/usr/bin/env bash
# Round79AC3A: READ-ONLY trusted native lifecycle inventory; no live edits.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="$1"
SOURCE="$2"
HERE="$(cd -- "$(dirname -- "$0")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac3a-*) ;; *) echo "REFUSED: private work path"; exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79worldproof-*/src) ;; *) echo "REFUSED: accepted source path"; exit 2;; esac
[[ -d "$WORK" && ! -L "$WORK" && "$(id -u)" -eq 0 &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE" ]] || {
  echo "REFUSED: private safety prerequisites"; exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
     "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
     "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
     systemctl is-active --quiet hollowdeep.service
}
finish() {
  local rc=$?
  if ! unchanged; then
    echo "ROUND79AC3A: PRODUCTION OR SOURCE BINARY SAFETY FAILED"
    rc=1
  fi
  if [[ "$rc" -eq 0 ]]; then
    echo "ROUND79AC3A: PRIVATE NATIVE LIFECYCLE AUDIT PASS"
  else
    echo "ROUND79AC3A: PRIVATE AUDIT FAILED ($rc)"
  fi
  echo "PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$rc"
}
trap finish EXIT
echo "=== ROUND79AC3A: PRIVATE LIFECYCLE PRE-FLIGHT ==="
(cd "$HERE" && python3 -m unittest -q test_lifecycle_audit_round79ac3a)
echo "=== STATIC NATIVE ADD/DELETE/FREE/QUIT HOOK MAP ==="
python3 "$HERE/lifecycle_audit_round79ac3a.py" "$SOURCE" > "$WORK/audit.log"
cat "$WORK/audit.log"
echo "ROUND79AC3A: EXACT SOURCE HOOK MAP READY FOR PRIVATE INTEGRATION"
