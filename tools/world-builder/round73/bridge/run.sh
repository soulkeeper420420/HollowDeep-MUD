#!/usr/bin/env bash
# Round 73I standalone native pointer/death -> PID-checked SQLite ledger.
# No production access, server startup, world modification, or loot grants.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run.sh DISPOSABLE_NATIVE_SOURCE' >&2; exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
SRC=$(realpath "$1")
case "$SRC" in
  /root/hollowdeep-dev/*|/mnt/data/round73g_native_integration/stage-test|/mnt/data/round73i-fixture) ;;
  *) echo 'Refusing non-disposable source directory' >&2; exit 2;;
esac
[[ -f "$SRC/treasure_guard.c" && -f "$SRC/mstruct.h" && -f "$SRC/mextern.h" ]] || exit 2
GUARD_P="$P/../guard-proof"
[[ -f "$GUARD_P/build_guard_variant.py" && -f "$GUARD_P/hd_guard_proof.c" ]] || {
  echo 'Missing sibling Round 73H sources' >&2; exit 2;
}
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
python3 "$GUARD_P/build_guard_variant.py" "$SRC/treasure_guard.c" "$OUT/round73h_guard.c"
python3 "$P/build_ledger_variant.py" "$OUT/round73h_guard.c" "$OUT/treasure_guard.c"
FLAGS=(-std=gnu89 -O1 -g -fcommon -Wall -Wextra -Werror -Wno-unused-parameter)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-1} == 1 ]] && FLAGS+=(-fsanitize=address,undefined)
FLAGS+=(-DHD_GUARD_EVIDENCE_TEST -DHD_LEDGER_BRIDGE_TEST -DHD_GPROOF_TESTING \
        "-DHD_LEDGER_TRUSTED_UID=$(id -u)" -I "$SRC" -I "$GUARD_P" -I "$P")
cc "${FLAGS[@]}" "$P/hd_ledger_bridge.c" "$GUARD_P/hd_guard_proof.c" \
 "$OUT/treasure_guard.c" "$P/test_bridge_native.c" -o "$OUT/test-native"
cc "${FLAGS[@]}" "$P/hd_ledger_bridge.c" "$GUARD_P/hd_guard_proof.c" \
 "$P/test_bridge_replay.c" -o "$OUT/test-replay"
export PYTHONPATH="$P/..:${PYTHONPATH:-}"
python3 "$P/test_bridge_replay.py" "$OUT/test-native" "$OUT/test-replay"
