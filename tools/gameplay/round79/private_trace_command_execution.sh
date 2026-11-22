#!/usr/bin/env bash
# Round79O: read-only actual command-function-pointer dispatch and
# disconnect/combat lifecycle trace for a future explicit rest hook.
# Zero production changes, zero native build, no socket or player access.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Provide NEW private Round79O results directory}"
SOURCE="${2:?Provide verified private Round79K ELF32 native source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79o-*) ;; *)
  echo "REFUSED: private Round79O result directory expected" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: private Round79K ELF32 source only" >&2;exit 2;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: missing or unsafe private source/repo" >&2; exit 2;
}
[[ -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
  echo "REFUSED: native ELF32 executable missing" >&2;exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: native ELF32 executable has changed" >&2;exit 2;
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$BASEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finish() {
  status=$?
  if ! unchanged; then
    echo "ROUND79O: SAFETY FAILURE — production or private ELF32 changed" >&2
    status=1
  fi
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$status"
}
trap finish EXIT

echo "=== ROUND79O: NATIVE COMMAND-EXECUTION BOUNDARY ==="
echo "=== 1. PRIVATE ELF32 DISPATCH-TRACE REGRESSION TESTS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
  test_trace_native_command_execution)

echo "=== 2. READ ONLY: ACTUAL COMMAND CALLBACK AND CHARACTER LIFECYCLE ==="
python3 "$HERE/trace_native_command_execution.py" "$SOURCE" \
  > "$WORK/private-command-execution-report.txt"
tail -n 6 "$WORK/private-command-execution-report.txt"

echo "=== 3. VERIFY ACCEPTED PRIVATE BUILD AND PRODUCTION UNCHANGED ==="
unchanged
echo "ROUND79O: PRIVATE NATIVE COMMAND DISPATCH TRACE PASS"
echo "PRIVATE REPORT: $WORK/private-command-execution-report.txt"
echo "EXPLICIT REST/+15 NATIVE GAMEPLAY: NOT YET CONNECTED"
echo "MOUNTS/ENDURANCE/STABLES: NOT YET CONNECTED"
echo "PRODUCTION PID AND ELF32 BASELINE: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
