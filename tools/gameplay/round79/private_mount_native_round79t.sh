#!/usr/bin/env bash
# Disposable ELF32 native mount acceptance. Raw logs stay private.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ $# == 2 ]] || { echo 'Usage: private_mount_native_round79t.sh NEW_OUTPUT ACCEPTED_NATIVE_SOURCE'; exit 2; }
WORK=$1
SOURCE=$2
HERE=$(cd "$(dirname "$0")" && pwd -P)
case "$WORK" in /root/hollowdeep-dev/round79t-*) ;; *) exit 2;; esac
[[ ! -e "$WORK" && ! -L "$WORK" ]] || { echo 'Use a new private output directory'; exit 2; }
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *) exit 2;; esac
[[ -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || exit 2
[[ $(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1) == e8aa9e09f325460f2ad8a463d0324f86ef7f2bab8a972f6a534d506eec8d1f5b ]] || {
    echo 'Accepted Round 79P native binary differs'; exit 1;
}
mkdir -m 700 "$WORK"
tree_hash() {
    (cd "$1"; find . -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
LIVE=/srv/hollowdeep/world
before_source=$(tree_hash "$SOURCE")
before_live=$(tree_hash "$LIVE/src_3.00")
before_rooms=$(tree_hash "$LIVE/rooms")
before_entities=$(tree_hash "$LIVE/objmon")
identity=$(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic)
pid=$(systemctl show hollowdeep.service -p MainPID --value)
live_binary=$(sha256sum "/proc/$pid/exe")
finish() {
    rc=$?
    trap - EXIT
    if [[ $(tree_hash "$SOURCE") != "$before_source" ||
          $(tree_hash "$LIVE/src_3.00") != "$before_live" ||
          $(tree_hash "$LIVE/rooms") != "$before_rooms" ||
          $(tree_hash "$LIVE/objmon") != "$before_entities" ||
          $(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic) != "$identity" ||
          $(sha256sum "/proc/$pid/exe") != "$live_binary" ]] ||
          ! systemctl is-active --quiet hollowdeep.service; then
        echo 'FAIL: Protected production or accepted private source changed'
        rc=1
    else
        echo 'PASS: Protected production, service identity and accepted source unchanged'
    fi
    exit "$rc"
}
trap finish EXIT
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -W error::ResourceWarning -m unittest discover -q) > "$WORK/python-tests.log" 2>&1
for kind in roster wire; do
    cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror -pedantic -I "$HERE" \
        "$HERE/hd_wilderness_breath.c" "$HERE/hd_mount_travel.c" "$HERE/hd79_mount_roster.c" \
        "$HERE/hd79_mount_wire.c" "$HERE/test_hd79_mount_$kind.c" -o "$WORK/test-$kind"
    "$WORK/test-$kind" > "$WORK/$kind.log"
done
python3 "$HERE/audit_native_mount_receipt_capacity.py" "$SOURCE" > "$WORK/source-audit.log"
stage=$(mktemp -d /tmp/hd-army-game-round79mount-XXXXXXXX)
python3 "$HERE/stage_mount_native.py" "$SOURCE" "$stage/src"
make -s -B -j2 -C "$stage/src" \
    NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
    PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
    BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 BREATH_TRAVEL_PLAYTEST=1 \
    REST_BREATH_PLAYTEST=1 frp.new > "$WORK/build.log" 2>&1
[[ $(od -An -tx1 -N5 "$stage/src/frp.new" | tr -d ' \n') == 7f454c4601 ]]
fixture="$WORK/fixture"
mkdir -p "$fixture/world/player"
python3 - "$HERE" "$fixture" <<'PY'
import ast,sys
from pathlib import Path
here,out=map(Path,sys.argv[1:])
repo=here.parents[2]
tree=ast.parse((repo/"tools/necromancer/petstore/onepass_linode.py").read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=="PAYLOAD" for t in n.targets)]
if len(nodes)!=1: raise SystemExit("Native fixture anchor mismatch")
(out/"test_pet_store.c").write_text(ast.literal_eval(nodes[0])["test_pet_store.c"])
text=(here/"test_native_breath_travel.c").read_text()
if text.count("int main(void)")!=1: raise SystemExit("Native travel fixture mismatch")
(out/"travel_base.c").write_text(text.replace("int main(void)","int previous_travel_main(void)"))
PY
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
    -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST -DHD_WARLOCK_PLAYTEST \
    -DHD_ATOMIC_TESTING -DHD79_BREATH_STORE_PLAYTEST -DHD79_BREATH_MOVE_CHECKPOINT_TEST \
    -DHD79_BREATH_TRAVEL_PLAYTEST -DHD79_REST_PLAYTEST -DHD79_REST_TESTING \
    -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types \
    -ffunction-sections -fdata-sections -Wl,--gc-sections \
    -I "$stage/src" -I "$fixture" -I "$HERE" \
    "$HERE/test_native_mount_store.c" "$stage/src/hd79_breath_travel_runtime.c" \
    "$stage/src/hd79_rest_game.c" "$stage/src/hd79_rest_session.c" \
    "$stage/src/hd79_mount_game.c" "$stage/src/files1.c" "$stage/src/files3.c" \
    "$stage/src/compress.c" "$stage/src/hd_player_store.c" "$stage/src/treasure_receipt.c" \
    "$stage/src/atomic_player_snapshot.c" "$stage/src/hd74_xp.c" "$stage/src/hd74_progression.c" \
    -o "$fixture/test-mount" > "$WORK/fixture-build.log" 2>&1
(cd "$fixture/world" && "$fixture/test-mount") > "$WORK/fixture.log" 2>&1
timeout --kill-after=5s 400s unshare --net --mount --fork bash -c \
    'set -e; ip link set lo up; exec python3 "$1" "$2"' _ \
    "$HERE/check_mount_socket.py" "$stage/src" > "$WORK/socket.log" 2>&1
grep -Fxq 'ROUND79T: ISOLATED NATIVE MOUNT GAMEPLAY PASS' "$WORK/socket.log"
timeout --kill-after=5s 400s unshare --net --mount --fork bash -c \
    'set -e; ip link set lo up; export HD79Q_TIMED_REST=1; exec python3 "$1" "$2"' _ \
    "$HERE/check_mount_regressions.py" "$stage/src" > "$WORK/regressions.log" 2>&1
grep -Fxq 'ROUND 79P: PRIVATE SOCKET REST COMMAND + TRAVEL + HUD PASS' "$WORK/regressions.log"
grep -Fxq 'REST +15: REAL CONNECTED 45-SECOND SOCKET TIMER VERIFIED' "$WORK/regressions.log"
sha256sum "$stage/src/frp.new" > "$WORK/candidate.sha256"
echo "ROUND79T: ELF32 MOUNT OWNERSHIP/STABLE/PERSISTENCE/ENDURANCE PASS"
echo "Private results: $WORK"
