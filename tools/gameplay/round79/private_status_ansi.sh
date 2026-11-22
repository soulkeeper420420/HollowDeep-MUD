#!/usr/bin/env bash
# Round 79B: isolated ANSI creation acceptance, status source audit.
set -Eeuo pipefail
umask 077
ulimit -c 0

if [[ "$(id -u)" != 0 ]]; then
    echo "ROUND 79B: root required for isolated chroot/socket tests" >&2
    exit 2
fi

RUN="${1:?Usage: private_status_ansi.sh PRIVATE_RUN_DIRECTORY}"
SRC="${2:-/tmp/hd-army-game-round78-VibwvrvC/src}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$SCRIPT_DIR/../../.." && pwd -P)"
EXAMPLE="$REPO/tools/necromancer/petruntime/gameplay"
WARLOCK="$REPO/tools/character-content"

case "$RUN" in /root/hollowdeep-dev/round79b-*) ;; *)
    echo "ROUND 79B: run directory must be private" >&2; exit 2;; esac
test -d "$RUN/repo" && test -d "$SCRIPT_DIR"
test -f "$SRC/frp.new"

BEFORE="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE="/srv/hollowdeep/world/src_3.00/frp.new"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79-XXXXXXXX)"

finish() {
    local rc=$?
    if (( rc )); then
        echo "ROUND 79B: PRIVATE TEST FAILED (exit $rc)"
        for log in "$RUN"/make.log "$RUN"/create.log "$RUN"/warlock.log "$RUN"/help.log; do
            if [[ -f "$log" ]]; then
                echo "=== $(basename "$log") (last 25 lines) ==="
                tail -n 25 "$log"
            fi
        done
    fi
    echo "PRIVATE RESULTS: $RUN"
    echo "PRIVATE NATIVE BUILD: $STAGE/src"
    echo "PRODUCTION PID: $(systemctl show hollowdeep.service -p MainPID --value)"
    echo "PRODUCTION DEPLOYMENT: NONE"
}
trap finish EXIT

echo "=== ROUND 79B: STATUS + ANSI FOUNDATIONS ==="
echo "=== 1. STATUS DISPLAY / ANSI CHOICE UNIT TESTS ==="
(
    cd "$SCRIPT_DIR"
    python3 -m unittest -v test_stage_ansi_creation
    cc -m32 -std=gnu89 -Wall -Wextra -Werror -I. \
        hd_status_hud.c test_status_hud.c -o "$RUN/status-unit"
    "$RUN/status-unit"
    cc -m32 -std=gnu89 -Wall -Wextra -Werror -I. \
        hd_ansi_choice.c test_ansi_choice.c -o "$RUN/ansi-unit"
    "$RUN/ansi-unit"
) 2>&1 | tee "$RUN/unit.log"

echo "=== 2. AUDIT NATIVE PROMPT AND BREATH CODE ==="
python3 "$SCRIPT_DIR/native_status_ansi_probe.py" "$SRC" \
    > "$RUN/native-status-report.txt"
tail -n 3 "$RUN/native-status-report.txt"

echo "=== 3. STAGE PRIVATE ANSI CREATION ==="
python3 "$SCRIPT_DIR/stage_ansi_creation.py" "$SRC" "$STAGE/src"

echo "=== 4. COMPILE PRIVATE ELF32 GAME ==="
if ! make -s -B -j2 -C "$STAGE/src" \
    NECROMANCER_PLAYTEST=1 \
    DEITY_PLAYTEST=1 \
    CORPSE_PLAYTEST=1 \
    PET_STORE_PLAYTEST=1 \
    PET_RUNTIME_PLAYTEST=1 \
    WARLOCK_PLAYTEST=1 \
    STATUS_ANSI_PLAYTEST=1 \
    frp.new >"$RUN/make.log" 2>&1; then
    tail -n 65 "$RUN/make.log"
    exit 1
fi
test "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" = 7f454c4601

echo "=== 5. SAVE ANSI-YES NECROMANCER / ANSI-NO MAGE ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$EXAMPLE/check_new_character.py" "$STAGE/src" \
    > "$RUN/create.log" 2>&1 || {
        tail -n 60 "$RUN/create.log"
        exit 1
    }
grep -Fq 'ROUND 75F: NATIVE CHARACTER CREATION PASS' "$RUN/create.log"
grep -Fq 'PASS: Character ANSI choice saved for Necromancer' "$RUN/create.log"
grep -Fq 'PASS: Character ANSI choice saved for Mage' "$RUN/create.log"
tail -n 8 "$RUN/create.log"

echo "=== 6. WARLOCK + HELP REGRESSION ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WARLOCK/check_warlock_socket.py" "$STAGE/src" \
    > "$RUN/warlock.log" 2>&1 || {
        tail -n 60 "$RUN/warlock.log"
        exit 1
    }
grep -Fq 'ROUND 78E: NATIVE WARLOCK CREATION AND RECONNECT PASS' \
    "$RUN/warlock.log"
tail -n 3 "$RUN/warlock.log"

unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$EXAMPLE/check_creation_help.py" "$STAGE/src" \
    > "$RUN/help.log" 2>&1 || {
        tail -n 60 "$RUN/help.log"
        exit 1
    }
grep -Fq 'ROUND 75E: NATIVE HELP AND SKILL CATALOG PASS' "$RUN/help.log"
tail -n 3 "$RUN/help.log"

echo "=== 7. PRODUCTION SAFETY ==="
test "$BEFORE" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVE_SHA" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79B: PRIVATE ANSI CREATION AND SAVE REGRESSION PASS"
echo "STATUS HUD FORMAT: UNIT-TESTED; NATIVE PROMPT HOOK PENDING"
echo "PRODUCTION SERVICE PID: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
