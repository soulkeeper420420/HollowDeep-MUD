#!/usr/bin/env bash
# Round79R: reused accepted Round79P private game; NO source patch.
# Tests pure mount terrain rules and audits native command/flags.
# No world, player save, production source or service changes.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass NEW private /root/hollowdeep-dev/round79r-* directory}"
SOURCE="${2:?Pass verified Round79P private ELF32 rest source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79r-*) ;; *)
  echo "REFUSED: new root-only Round79R results directory required" >&2
  exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *)
  echo "REFUSED: accepted private Round79P ELF32 source required" >&2
  exit 2;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" &&
   ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: source or pinned checkout missing/unsafe" >&2
  exit 2
}
for file in frp.new global.c wilderness.c mstruct.h mtype.h; do
  [[ -f "$SOURCE/$file" && ! -L "$SOURCE/$file" ]] || {
    echo "REFUSED: accepted private native source missing $file" >&2
    exit 2
  }
done
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: private source executable is not ELF32" >&2;exit 2
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d ' ' -f1)"
BASE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d ' ' -f1)"
unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d ' ' -f1)" ]] &&
  [[ "$BASE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d ' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finish() {
  code=$?
  if ! unchanged; then
    echo "ROUND79R: SAFETY ERROR — production/private source changed" >&2
    code=1
  fi
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$code"
}
trap finish EXIT

echo "=== ROUND79R: PRIVATE MOUNT FLAG AND COMMAND FOUNDATION ==="
echo "=== 1. RUN SIX PRIVATE ELF32 AUDIT SAFETY TESTS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
  test_native_mount_command_audit)

echo "=== 2. RECHECK FOOT VS MOUNT ENDURANCE/TERRAIN RULES AS ELF32 ==="
cc -m32 -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE" \
  "$HERE/hd_mount_travel.c" \
  "$HERE/hd_wilderness_breath.c" \
  "$HERE/test_mount_travel.c" \
  -o "$WORK/test-mount-terrain"
[[ "$(od -An -tx1 -N5 "$WORK/test-mount-terrain" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-mount-terrain" > "$WORK/mount-terrain-test.log"
grep -Fq 'ROUND 79G: FOOT BREATH / MOUNT ENDURANCE / TERRAIN RULES PASS' \
  "$WORK/mount-terrain-test.log"
tail -n 3 "$WORK/mount-terrain-test.log"

echo "=== 3. READ-ONLY NATIVE MOUNT/CLASS/FLAG/COMMAND COLLISION AUDIT ==="
python3 "$HERE/native_mount_command_audit.py" "$SOURCE" \
  > "$WORK/private-mount-flag-report.txt"
grep -Fq 'ROUND 79G: MOUNT COMMAND/TERRAIN AUDIT COMPLETE' \
  "$WORK/private-mount-flag-report.txt"
tail -n 4 "$WORK/private-mount-flag-report.txt"

echo "=== 4. VERIFY LIVE SERVICE AND ACCEPTED ELF32 GAME UNCHANGED ==="
unchanged
echo "ROUND79R: PRIVATE MOUNT RULES AND NATIVE FLAG AUDIT PASS"
echo "AUDIT REPORT: $WORK/private-mount-flag-report.txt"
echo "MOUNT OWNERSHIP, STABLES AND NATIVE ENDURANCE: NOT YET INSTALLED"
echo "PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
