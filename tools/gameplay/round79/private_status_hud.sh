#!/usr/bin/env bash
# Round 79E: verify private ANSI HUD, not production.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ "$(id -u)" == 0 ]] || { echo "Root required for isolated socket chroot" >&2; exit 2; }

WORK="${1:?Provide private results directory}"
SRC="${2:?Provide previously verified Round 79 ANSI source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$HERE/../../.." && pwd -P)"
GAMEPLAY="$REPO/tools/necromancer/petruntime/gameplay"
WARLOCK="$REPO/tools/character-content"

case "$WORK" in /root/hollowdeep-dev/round79e-*) ;; *)
    echo "REFUSED: results must be a private Round 79E directory" >&2; exit 2;;
esac
case "$SRC" in /tmp/hd-army-game-round79-*/src) ;; *)
    echo "REFUSED: verified private Round 79 ANSI build required" >&2; exit 2;;
esac
test -d "$WORK/repo"
test -f "$SRC/frp.new"

BEFORE="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEBIN=/srv/hollowdeep/world/src_3.00/frp.new
LIVE_SHA="$(sha256sum "$LIVEBIN" | cut -d' ' -f1)"
PRIVATE="$(mktemp -d /tmp/hd-army-game-round79hud-XXXXXXXX)"

finish() {
    local rc=$?
    if ((rc)); then
        echo "ROUND 79E: PRIVATE FAILURE (exit $rc)"
        for log in "$WORK"/make.log "$WORK"/characters.log "$WORK"/warlock.log "$WORK"/help.log; do
            if [[ -f "$log" ]]; then
                echo "=== $(basename "$log") (last 30 lines) ==="
                tail -n 30 "$log"
            fi
        done
    fi
    echo "ROUND 79E RESULTS: $WORK"
    echo "PRIVATE BUILD: $PRIVATE/src"
    echo "PRODUCTION DEPLOYMENT: NONE"
}
trap finish EXIT

echo "=== 1. PRIVATE STATUS/ANSI STAGING TESTS ==="
(cd "$HERE" &&
 python3 -m unittest -v test_stage_status_hud test_stage_ansi_creation &&
 cc -m32 -std=gnu89 -Wall -Wextra -Werror -I. \
   hd_status_hud.c test_status_hud.c -o "$WORK/status-unit" &&
 "$WORK/status-unit"
) 2>&1 | tee "$WORK/units.log"

echo "=== 2. STAGE STATUS HUD FROM ANSI PLAYTEST ==="
python3 "$HERE/stage_status_hud.py" "$SRC" "$PRIVATE/src"

echo "=== 3. COMPILE PRIVATE ELF32 ENGINE ==="
if ! make -s -B -j2 -C "$PRIVATE/src" \
    NECROMANCER_PLAYTEST=1 \
    DEITY_PLAYTEST=1 \
    CORPSE_PLAYTEST=1 \
    PET_STORE_PLAYTEST=1 \
    PET_RUNTIME_PLAYTEST=1 \
    WARLOCK_PLAYTEST=1 \
    STATUS_ANSI_PLAYTEST=1 \
    STATUS_HUD_PLAYTEST=1 \
    frp.new > "$WORK/make.log" 2>&1; then
    tail -n 70 "$WORK/make.log"; exit 1
fi
test "$(od -An -tx1 -N5 "$PRIVATE/src/frp.new" | tr -d ' \n')" = 7f454c4601

echo "=== 4. SOCKET CREATION: COLORED AND PLAIN ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$GAMEPLAY/check_new_character.py" "$PRIVATE/src" \
    >"$WORK/characters.log" 2>&1 || {
        tail -n 65 "$WORK/characters.log"; exit 1
    }
grep -Fq 'PASS: ANSI colorized HP/MP/unknown Breath HUD' "$WORK/characters.log"
grep -Fq 'PASS: plain HP/MP/unknown Breath HUD without ANSI' "$WORK/characters.log"
grep -Fq 'ROUND 75F: NATIVE CHARACTER CREATION PASS' "$WORK/characters.log"
tail -n 10 "$WORK/characters.log"

echo "=== 5. WARLOCK AND HELP REGRESSIONS ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WARLOCK/check_warlock_socket.py" "$PRIVATE/src" \
    >"$WORK/warlock.log" 2>&1 || {
        tail -n 65 "$WORK/warlock.log"; exit 1
    }
grep -Fq 'ROUND 78E: NATIVE WARLOCK CREATION AND RECONNECT PASS' \
    "$WORK/warlock.log"
tail -n 3 "$WORK/warlock.log"

unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$GAMEPLAY/check_creation_help.py" "$PRIVATE/src" \
    >"$WORK/help.log" 2>&1 || {
        tail -n 65 "$WORK/help.log"; exit 1
    }
grep -Fq 'ROUND 75E: NATIVE HELP AND SKILL CATALOG PASS' "$WORK/help.log"
tail -n 3 "$WORK/help.log"

echo "=== 6. TARGET EXACT WILDERNESS MOVE HANDLER ==="
python3 "$HERE/native_wilderness_move_exact.py" "$PRIVATE/src" \
    >"$WORK/native-wilderness-move.txt"
tail -n 3 "$WORK/native-wilderness-move.txt"

echo "=== 7. VERIFY PRODUCTION UNCHANGED ==="
test "$BEFORE" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVE_SHA" = "$(sha256sum "$LIVEBIN" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79E: PRIVATE COLORED HP/MP STATUS HUD PASS"
echo "BREATH MOVEMENT/STATE: NOT YET ACTIVE"
echo "REPORT: $WORK/native-wilderness-move.txt"
echo "PRODUCTION PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
