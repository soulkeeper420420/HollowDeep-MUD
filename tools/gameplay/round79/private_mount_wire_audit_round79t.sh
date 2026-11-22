#!/usr/bin/env bash
# Round79T: private ELF32 mount two-receipt serializer and read-only
# native player receipt capacity audit. NO mount storage is installed,
# no native executable rebuild or production/game mutation.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass NEW /root/hollowdeep-dev/round79t-* results directory}"
SOURCE="${2:?Pass accepted private Round79P ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79t-*) ;; *)
 echo "REFUSED: expected root-only Round79T results directory" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *)
 echo "REFUSED: accepted private Round79P ELF32 source only" >&2;exit 2;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" && -f "$SOURCE/frp.new" &&
   ! -L "$SOURCE/frp.new" ]] || {
 echo "REFUSED: missing or unsafe accepted source/repo" >&2;exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo "REFUSED: accepted candidate not native ELF32" >&2;exit 2;
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

verify() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$BASE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finish() {
 result=$?
 if ! verify; then
   echo "ROUND79T: SAFETY FAILURE — production/private executable changed" >&2
   result=1
 else
   echo "PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED"
 fi
 if ((result)) && [[ -f "$WORK/mount-wire-test.log" ]]; then
   echo "=== PRIVATE MOUNT WIRE FAILURE DETAILS ==="
   tail -n 75 "$WORK/mount-wire-test.log"
 fi
 echo "PRIVATE RESULTS: $WORK"
 echo "PRODUCTION DEPLOYMENT: NONE"
 exit "$result"
}
trap finish EXIT

echo "=== ROUND79T: MOUNT TWO-RECEIPT WIRE AND ATOMIC STORE AUDIT ==="
echo "=== 1. READ-ONLY SOURCE-AUDIT REGRESSIONS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
 test_audit_native_mount_receipt_capacity)

echo "=== 2. COMPILE STRICT PRIVATE ELF32 TWO-RECEIPT WIRE TESTS ==="
cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror -pedantic \
 -I "$HERE" \
 "$HERE/hd_wilderness_breath.c" \
 "$HERE/hd_mount_travel.c" \
 "$HERE/hd79_mount_roster.c" \
 "$HERE/hd79_mount_wire.c" \
 "$HERE/test_hd79_mount_wire.c" \
 -o "$WORK/test-mount-wire"
[[ "$(od -An -tx1 -N5 "$WORK/test-mount-wire" | tr -d ' \n')" == 7f454c4601 ]]

echo "=== 3. RUN CANONICAL ROUNDTRIP/CORRUPTION/REPLAY FIXTURES ==="
"$WORK/test-mount-wire" | tee "$WORK/mount-wire-test.log"
grep -Fq 'ROUND79T: PRIVATE MOUNT TWO-RECEIPT WIRE CONTRACT PASS' \
 "$WORK/mount-wire-test.log"

echo "=== 4. AUDIT PRIVATE NATIVE RECEIPT CAPACITY AND RESERVED IDs ==="
python3 "$HERE/audit_native_mount_receipt_capacity.py" "$SOURCE" \
 > "$WORK/private-native-receipt-audit.txt"
grep -Fq 'ROUND79T: PRIVATE NATIVE RECEIPT CAPACITY AUDIT PASS' \
 "$WORK/private-native-receipt-audit.txt"
tail -n 8 "$WORK/private-native-receipt-audit.txt"

echo "=== 5. VERIFY NO GAME OR PRODUCTION CHANGES ==="
verify
echo "ROUND79T: PRIVATE MOUNT WIRE AND NATIVE RECEIPT AUDIT PASS"
echo "REPORT: $WORK/private-native-receipt-audit.txt"
echo "NATIVE MOUNT SAVES, RESERVED IDS, COMMANDS: NOT YET INSTALLED"
echo "PRODUCTION DEPLOYMENT: NONE"
