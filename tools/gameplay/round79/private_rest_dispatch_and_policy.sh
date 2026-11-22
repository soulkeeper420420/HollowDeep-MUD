#!/usr/bin/env bash
# Round79N: isolated rest-policy tests + read-only native dispatcher audit.
# The native MUD is NOT restarted or patched. No production reads except
# PID/executable checksum; no world/player/server settings are accessed.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass NEW /root/hollowdeep-dev/round79n-* results directory}"
SOURCE="${2:?Pass accepted Round79K private ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79n-*) ;; *)
  echo "REFUSED: private Round79N result directory expected" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: accepted disposable Round79K source required" >&2;exit 2;;
esac
[[ -d "$WORK/repo" && -f "$SOURCE/frp.new" ]] || {
  echo "REFUSED: pinned repo or native ELF32 source missing" >&2;exit 2;
}
[[ ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: private native directory symlink" >&2;exit 2;
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID=$(systemctl show hollowdeep.service -p MainPID --value)
LIVEHASH=$(sha256sum "$LIVE" | cut -d' ' -f1)
BASEHASH=$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)

verify() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$BASEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finish() {
  status=$?
  if ! verify; then
    echo "ROUND79N: SAFETY FAILURE — production or baseline changed" >&2
    status=1
  fi
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$status"
}
trap finish EXIT

echo "=== ROUND79N: EXPLICIT REST POLICY + PRIVATE DISPATCH AUDIT ==="
echo "=== 1. NATIVE DISPATCH INSPECTOR SOURCE-SAFETY TESTS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
    test_audit_native_rest_dispatch)

echo "=== 2. COMPILE AND VERIFY PURE REST SESSION RULES ==="
cc -std=c99 -O2 -Wall -Wextra -Werror -pedantic \
  -I "$HERE" \
  "$HERE/hd79_rest_session.c" \
  "$HERE/test_hd79_rest_session.c" \
  -o "$WORK/test-rest-session"
"$WORK/test-rest-session"

echo "=== 3. READ NATIVE COMMAND DISPATCH, ACTION AND DISCONNECT EDGES ==="
python3 "$HERE/audit_native_rest_dispatch.py" "$SOURCE" \
  > "$WORK/private-rest-dispatch-report.txt"
tail -n 10 "$WORK/private-rest-dispatch-report.txt"

echo "=== 4. ASSERT ACCEPTED PRIVATE ELF32 AND LIVE SERVICE UNCHANGED ==="
verify

echo "ROUND79N: REST SESSION POLICY AND PRIVATE DISPATCH AUDIT PASS"
echo "PRIVATE REPORT: $WORK/private-rest-dispatch-report.txt"
echo "NATIVE +15 RESTING BONUS: NOT YET INSTALLED"
echo "MOUNTS, ENDURANCE AND STABLES: NOT YET INSTALLED"
echo "PRODUCTION PID AND ELF32 BASELINE: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
