#!/usr/bin/env bash
# Round 73J: combined new-code-only 32-bit/private gameplay and daemon replay.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run.sh DISPOSABLE_PATCHED_NATIVE_SOURCE' >&2; exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
SRC=$(realpath "$1")
case "$SRC" in
  /root/hollowdeep-dev/*|/mnt/data/round73g_native_integration/stage-test) ;;
  *) echo 'Refusing source outside disposable private build' >&2; exit 2;;
esac
[[ -f "$SRC/hd_player_store.c" && -f "$SRC/files2.c" && -f "$SRC/treasure_guard.c" ]] || exit 2
BASE="$P/.."
GUARD="$BASE/guard-proof"; BRIDGE="$BASE/bridge"; REWARD="$BASE/native-save-foundation"
for name in "$GUARD/build_guard_variant.py" "$BRIDGE/build_ledger_variant.py" \
 "$BRIDGE/hd_ledger_bridge.c" "$REWARD/hd_native_reward.c"; do
    [[ -f "$name" ]] || { echo "Missing source $name" >&2; exit 2; }
done
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
python3 "$GUARD/build_guard_variant.py" "$SRC/treasure_guard.c" "$OUT/h.c"
python3 "$BRIDGE/build_ledger_variant.py" "$OUT/h.c" "$OUT/i.c"
python3 "$P/build_reward_variant.py" "$OUT/i.c" "$OUT/treasure_guard.c"
FLAGS=(-D_GNU_SOURCE -std=gnu89 -O1 -g -fcommon -ffunction-sections -fdata-sections \
       -include stdlib.h -Wno-implicit-function-declaration -Wno-int-conversion \
       -Wno-incompatible-pointer-types -Wno-return-type)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && FLAGS+=(-fsanitize=address,undefined)
FLAGS+=( -I "$SRC" -I "$P" -I "$GUARD" -I "$BRIDGE" -I "$REWARD" -I "$OUT" \
         -DHD_GUARD_EVIDENCE_TEST -DHD_GPROOF_TESTING -DHD_LEDGER_BRIDGE_TEST \
         -DHD_J_REWARD_TEST -DHD_ATOMIC_TESTING -DCOMPRESS -DHD_TEST_FILES2_WRAPPER \
         "-DHD_LEDGER_TRUSTED_UID=$(id -u)")
COMMON=("$SRC/files2.c" "$SRC/files3.c" "$SRC/compress.c" \
        "$SRC/hd_player_store.c" "$SRC/treasure_receipt.c" \
        "$SRC/atomic_player_snapshot.c")
cc "${FLAGS[@]}" "${COMMON[@]}" "$P/test_receipt_probe.c" \
    -Wl,--gc-sections -o "$OUT/verifier"
cc "${FLAGS[@]}" "${COMMON[@]}" "$REWARD/hd_native_reward.c" \
   "$P/hd_reward_transport.c" "$BRIDGE/hd_ledger_bridge.c" \
   "$GUARD/hd_guard_proof.c" "$OUT/treasure_guard.c" \
   "$P/test_reward_native.c" -Wl,--gc-sections -o "$OUT/native"
export PYTHONPATH="$BASE:${PYTHONPATH:-}"
python3 "$P/test_reward_replay.py" "$OUT/native" "$OUT/verifier"
