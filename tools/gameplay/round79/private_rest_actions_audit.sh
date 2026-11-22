#!/usr/bin/env bash
# Round79M: read-only private native social-action command semantics.
# Uses accepted Round79K ELF32 source; never invokes the MUD executable
# or modifies private/native source, world, player data or production.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass new private /root/hollowdeep-dev/round79m-* directory}"
SOURCE="${2:?Pass accepted private Round79K ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79m-*) ;; *)
  echo "REFUSED: Round79M results directory must be private" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: previously tested Round79K private source required" >&2;exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"
test -f "$SOURCE/global.c"
test -f "$SOURCE/io.c"
test -f "$SOURCE/command2.c"
test "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" = 7f454c4601

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d ' ' -f1)"
BASEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d ' ' -f1)"

echo "=== ROUND 79M: PRIVATE NATIVE REST ACTION AUDIT ==="
echo "=== 1. PRIVATE-ONLY COMMAND SCANNER REGRESSION ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
    test_audit_native_rest_actions)

echo "=== 2. EXACT NATIVE ACTION HANDLER AND SOCIAL COMMAND TABLE ==="
python3 "$HERE/audit_native_rest_actions.py" "$SOURCE" \
  > "$WORK/private-action-handler-report.txt"
tail -n 4 "$WORK/private-action-handler-report.txt"

echo "=== 3. VERIFY ACCEPTED ELF32 GAME AND PRODUCTION UNCHANGED ==="
test "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVEHASH" = "$(sha256sum "$LIVE" | cut -d ' ' -f1)"
test "$BASEHASH" = "$(sha256sum "$SOURCE/frp.new" | cut -d ' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79M: PRIVATE ACTION COMMAND AUDIT PASS"
echo "ACTION REPORT: $WORK/private-action-handler-report.txt"
echo "RESTING +15: WAITING FOR VERIFIED NATIVE HANDLER CONTRACT"
echo "PRODUCTION PID AND ELF32 BASELINE: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
