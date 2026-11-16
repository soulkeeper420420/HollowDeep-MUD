#!/usr/bin/env bash
# Compile and execute a disposable native player save/reload test fixture.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: test_private.sh /root/hollowdeep-dev/DISPOSABLE-NATIVE-COPY' >&2; exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
SRC=$(realpath "$1")
case "$SRC" in
  /root/hollowdeep-dev/*|/mnt/data/round73g_native_integration/stage-test) ;;
  *) echo 'Refusing non-private native tree' >&2; exit 2;;
esac
[[ -f "$SRC/hd_player_store.c" && -f "$SRC/files2.c" && -f "$SRC/Makefile" ]] || exit 2
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -fcommon -ffunction-sections -fdata-sections)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && FLAGS+=(-fsanitize=address,undefined)
cc "${FLAGS[@]}" -include stdlib.h -Wno-implicit-function-declaration \
  -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-type \
  -I "$SRC" -I "$P" -DCOMPRESS -DHD_ATOMIC_TESTING -DHD_TEST_FILES2_WRAPPER \
  "$SRC/files2.c" "$SRC/files3.c" "$SRC/compress.c" \
  "$SRC/hd_player_store.c" "$SRC/treasure_receipt.c" \
  "$SRC/atomic_player_snapshot.c" "$P/test_player_store.c" \
  -Wl,--gc-sections -o "$OUT/test-player"
"$OUT/test-player"
