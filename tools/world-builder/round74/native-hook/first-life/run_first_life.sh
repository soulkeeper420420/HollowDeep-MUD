#!/usr/bin/env bash
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run_first_life.sh DISPOSABLE_SRC' >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in /srv/*|/var/www/*) echo 'Production source refused' >&2; exit 2;; esac
[[ "$SRC" == *'/round74b-'*'/src' ]] || { echo 'Disposable round74b source required' >&2; exit 2; }
for name in hd74_xp.c hd74_xp.h hd74_progression.c hd74_progression.h command7.c command4.c hollowdeep.c hd74_native.c; do
  [[ -f "$SRC/$name" && ! -L "$SRC/$name" ]] || { echo "Missing source: $name" >&2; exit 2; }
done
P=$(cd "$(dirname "$0")" && pwd -P)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -g -O1 -fcommon -Wall -Wextra -Werror)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && FLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" "$P/test_life_cost.c" -o "$OUT/test-costs"
"$OUT/test-costs"
cc "${FLAGS[@]}" -Wno-error -Wno-unused-parameter -Wno-implicit-function-declaration \
   -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
   -ffunction-sections -fdata-sections -DHD74_PRIVATE_NATIVE -DHD74_LIFE_TEST_BRIDGE \
   -I "$SRC" "$SRC/command7.c" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" \
   "$P/test_first_life_train.c" -Wl,--gc-sections -o "$OUT/test-first-train"
"$OUT/test-first-train"
for mode in legacy private; do
  EXTRA=()
  [[ "$mode" == private ]] && EXTRA=(-DHD74_PRIVATE_NATIVE)
  for name in command7.c command4.c hollowdeep.c hd74_native.c hd74_xp.c; do
    cc "${FLAGS[@]}" -Wno-error -Wno-implicit-function-declaration \
       -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
       "${EXTRA[@]}" -I "$SRC" -fsyntax-only "$SRC/$name" \
       >"$OUT/$mode-$name.log" 2>&1 || { cat "$OUT/$mode-$name.log"; exit 1; }
  done
done
[[ $(grep -c 'OBJECTS += hd74_native.o hd74_progression.o hd74_xp.o' "$SRC/Makefile") == 1 ]] || exit 2
echo 'ROUND 74B: firstlife private native compiler branches PASS'
echo 'ROUND 74B: trusted remort save bridge PENDING; live MUD unchanged'
