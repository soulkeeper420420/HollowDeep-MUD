#!/usr/bin/env bash
# Round 79H: isolated private ELF32 Breath receipt integration validation.
# No gameplay hooks, production deployment, world edits, or live player writes.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || { echo "Run as root for private ELF32 build" >&2; exit 2; }
WORK="${1:?Pass private Round79H work directory}"
SOURCE="${2:?Pass verified private Round79E HUD source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$HERE/../../.." && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79h-*) ;; *)
  echo "DENIED: work must be in private Round79H directory" >&2; exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79hud-*/src) ;; *)
  echo "DENIED: expected verified disposable HUD build" >&2; exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79store-XXXXXXXX)"
FIXTURES="$(mktemp -d /tmp/hd-breath79h-fixture-XXXXXXXX)"
echo "ROUND 79H: PRIVATE STAGE: $STAGE"
echo "ROUND 79H: PRIVATE FIXTURES: $FIXTURES"

finish() {
  local status=$?
  if ((status)); then
    echo "ROUND 79H: FAIL (exit $status)"
    for log in "$WORK"/native-test.log "$WORK"/native-build.log; do
      if [[ -f "$log" ]]; then
        echo "=== $(basename "$log") (tail) ==="
        tail -n 35 "$log"
      fi
    done
  fi
  echo "PRIVATE SOURCE: $STAGE/src"
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
}
trap finish EXIT

echo "=== 1. BREATH STORAGE SOURCE AND GUARD TESTS ==="
(cd "$HERE" && python3 -m unittest -q test_stage_breath_store)

echo "=== 2. STAGE NATIVE ATOMIC BREATH RECEIPT ==="
python3 "$HERE/stage_breath_store.py" "$SOURCE" "$STAGE/src"

echo "=== 3. PREPARE SYNTHETIC PRIVATE PLAYER FIXTURE ==="
python3 - "$REPO" "$FIXTURES" <<'PY'
import ast
from pathlib import Path
import sys
repo, target = map(Path,sys.argv[1:])
fixture=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(fixture.read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=="PAYLOAD" for t in n.targets)]
if len(nodes)!=1:
    raise RuntimeError("Verified synthetic pet fixture not found")
value=ast.literal_eval(nodes[0])
text=value["test_pet_store.c"]
if not isinstance(text,str) or "int main" not in text:
    raise RuntimeError("Not a verified native test fixture")
(target/"test_pet_store.c").write_text(text)
PY

echo "=== 4. BUILD ELF32 NATIVE ATOMIC-PLAYER TEST ==="
CC="${CC:-cc}"
"$CC" -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIXTURES" \
  "$HERE/test_native_breath_store.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIXTURES/test-breath" > "$WORK/native-build.log" 2>&1 || {
    tail -n 70 "$WORK/native-build.log"; exit 1
  }
test "$(od -An -tx1 -N5 "$FIXTURES/test-breath" | tr -d ' \n')" = 7f454c4601

echo "=== 5. TEST DURABLE RECEIPTS / SAVE / FAILURES ==="
mkdir -p "$FIXTURES/world/player"
(
 cd "$FIXTURES/world"
 "$FIXTURES/test-breath"
) > "$WORK/native-test.log" 2>&1 || {
   tail -n 70 "$WORK/native-test.log"; exit 1
}
grep -Fq 'ROUND 79H: NATIVE ATOMIC BREATH PLAYER-RECEIPT TEST PASS' \
  "$WORK/native-test.log"
tail -n 9 "$WORK/native-test.log"

echo "=== 6. REBUILD PRIVATE ELF32 GAME WITH DISABLED MOVEMENT HOOKS ==="
make -s -B -j2 -C "$STAGE/src" \
  NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
  CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
  PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
  STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
  BREATH_STORE_PLAYTEST=1 frp.new >"$WORK/native-build-game.log" 2>&1 || {
    tail -n 70 "$WORK/native-build-game.log"; exit 1
}
test "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" = 7f454c4601

echo "=== 7. VERIFY PRODUCTION AND BASELINE UNCHANGED ==="
test "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVEHASH" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$SOURCEHASH" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79H: PRIVATE NATIVE BREATH ATOMIC STORAGE PASS"
echo "BREATH MOVEMENT / MOUNTS: NOT YET CONNECTED"
echo "PRODUCTION SERVICE PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
