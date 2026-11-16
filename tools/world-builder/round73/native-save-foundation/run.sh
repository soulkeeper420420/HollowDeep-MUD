#!/usr/bin/env bash
# Round 73G source-only test runner. Never contacts or modifies the live MUD.
set -Eeuo pipefail
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -fno-omit-frame-pointer)
if [[ ${HD_TEST_ELF32:-0} == 1 ]]; then FLAGS+=(-m32); fi
if [[ ${HD_SANITIZE:-1} == 1 ]]; then FLAGS+=(-fsanitize=address,undefined); fi
cc "${FLAGS[@]}" -Wall -Wextra -Werror \
  treasure_receipt.c test_receipt.c -o "$OUT/test-receipt"
"$OUT/test-receipt"
cc "${FLAGS[@]}" -Wall -Wextra -Werror -DHD_ATOMIC_TESTING \
  atomic_player_snapshot.c test_atomic_snapshot.c -o "$OUT/test-atomic"
"$OUT/test-atomic"
if [[ $# -gt 1 ]]; then echo 'Usage: run.sh [private-native-src-dir]' >&2; exit 2; fi
if [[ $# -eq 1 ]]; then
  SOURCE=$(realpath "$1")
  case "$SOURCE" in /srv/hollowdeep/*) echo 'Refusing production source directory' >&2; exit 2;; esac
  for name in files3.c mstruct.h mtype.h mextern.h; do
    [[ -f "$SOURCE/$name" && ! -L "$SOURCE/$name" ]] || {
      echo "Missing/symlinked private native fixture: $SOURCE/$name" >&2; exit 2;
    }
  done
  EXTRA=()
  if [[ -f "$SOURCE/compress.c" && ! -L "$SOURCE/compress.c" ]]; then
    EXTRA=(-DHD_WITH_ORIGINAL_COMPRESS -DCOMPRESS "$SOURCE/compress.c")
  fi
  cc "${FLAGS[@]}" -include stdlib.h -Wno-implicit-function-declaration \
    -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
    -ffunction-sections -fdata-sections -I "$SOURCE" \
    treasure_receipt.c "$SOURCE/files3.c" test_native_serializer.c "${EXTRA[@]}" \
    -Wl,--gc-sections -o "$OUT/test-native"
  "$OUT/test-native"
fi
