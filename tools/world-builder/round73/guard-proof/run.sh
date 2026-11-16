#!/usr/bin/env bash
# Isolated, no server startup, no production/world file writes.
set -Eeuo pipefail
P=$(cd "$(dirname "$0")" && pwd -P)
[[ $# == 2 ]] || { echo 'Usage: run.sh AUDITED_GUARD.c AUDITED_NATIVE_HEADER_DIR' >&2; exit 2; }
GUARD=$(realpath "$1"); SRC=$(realpath "$2")
[[ -f "$GUARD" && -f "$SRC/mstruct.h" && -f "$SRC/mtype.h" && -f "$SRC/mextern.h" ]] || exit 2
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -Wall -Wextra -Werror)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-1} == 1 ]] && FLAGS+=(-fsanitize=address,undefined)
cc "${FLAGS[@]}" -DHD_GPROOF_TESTING "$P/hd_guard_proof.c" \
  "$P/test_guard_proof.c" -o "$OUT/test-proof"
"$OUT/test-proof"
python3 "$P/build_guard_variant.py" "$GUARD" "$OUT/treasure_guard.c"
cc "${FLAGS[@]}" -Wno-unused-parameter -DHD_GUARD_EVIDENCE_TEST \
  -DHD_GPROOF_TESTING -I "$SRC" -I "$P" \
  "$P/hd_guard_proof.c" "$OUT/treasure_guard.c" "$P/test_guard_native.c" \
  -o "$OUT/test-native"
"$OUT/test-native"
echo 'ROUND 73H: private evidence gate PASS; chest rewards remain disabled'
