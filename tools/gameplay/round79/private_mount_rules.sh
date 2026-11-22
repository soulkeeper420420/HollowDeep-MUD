#!/usr/bin/env bash
# Round 79G: test mount and foot travel rules without modifying native game.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Provide private Round79G working directory}"
SOURCE="${2:?Provide existing private HUD ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79g-*) ;; *)
  echo "REFUSED: results must be a private Round79G directory" >&2; exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79hud-*/src) ;; *)
  echo "REFUSED: expected previously verified private HUD candidate" >&2; exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"

BEFORE="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
LIVE_BEFORE="$(sha256sum "$LIVE" | cut -d' ' -f1)"
HUD_BEFORE="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"

echo "=== ROUND 79G: MOUNT + BREATH DESIGN PROTOTYPE ==="
echo "=== 1. COMPILE FOOT/MOUNT/TERRAIN RULES AS ELF32 ==="
cc -m32 -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE" \
  "$HERE/hd_mount_travel.c" \
  "$HERE/hd_wilderness_breath.c" \
  "$HERE/test_mount_travel.c" \
  -o "$WORK/mount-travel-test"
"$WORK/mount-travel-test"

echo "=== 2. AUDIT NATIVE COMMAND COLLISIONS AND TERRAIN ==="
python3 "$HERE/native_mount_command_audit.py" "$SOURCE" \
  > "$WORK/mount-command-report.txt"
tail -n 3 "$WORK/mount-command-report.txt"

echo "=== 3. VERIFY NO LIVE OR PRIVATE GAME MUTATIONS ==="
test "$BEFORE" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVE_BEFORE" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$HUD_BEFORE" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79G: PRIVATE MOUNT TRAVEL RULES PASS"
echo "MOUNT COMMAND AUDIT: $WORK/mount-command-report.txt"
echo "NATIVE MOUNTS / SAVE PERSISTENCE: NOT YET IMPLEMENTED"
echo "PRODUCTION PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
