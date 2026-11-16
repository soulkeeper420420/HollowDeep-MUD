#!/usr/bin/env bash
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run_bank5.sh DISPOSABLE_ROUND74B_SRC' >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in /srv/*|/var/www/*) echo 'Production path rejected' >&2;exit 2;;esac
[[ "$SRC" == *'/round74b-'*'/src' ]] || { echo 'Disposable source folder required' >&2;exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
CFLAGS=(-std=gnu89 -O1 -g -fcommon -Wall -Wextra -Werror)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && CFLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && CFLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
cc "${CFLAGS[@]}" -I "$SRC" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" \
   "$P/test_bank5.c" -o "$OUT/bank"
"$OUT/bank"
cc "${CFLAGS[@]}" -Wno-error -Wno-unused-parameter -Wno-implicit-function-declaration \
   -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
   -ffunction-sections -fdata-sections -DHD74_PRIVATE_NATIVE -DHD74_LIFE_TEST_BRIDGE \
   -I "$SRC" "$SRC/command7.c" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" \
   "$P/test_train_one_level.c" -Wl,--gc-sections -o "$OUT/one"
"$OUT/one"
# Verify all modified award locations, and exact one-level native train semantics.
[[ $(grep -c 'up_level(ply_ptr);' "$SRC/command7.c") == 1 ]]
[[ $(grep -l 'hd74_xp_add_banked' "$SRC"/{creature,command2,command8,command10}.c | wc -l) == 4 ]]
for mode in legacy private; do
  DEFS=()
  [[ "$mode" == private ]] && DEFS=(-DHD74_PRIVATE_NATIVE)
  for file in creature.c command2.c command8.c command10.c command7.c hd74_xp.c; do
    cc "${CFLAGS[@]}" -Wno-error -Wno-unused-parameter \
       -Wno-implicit-function-declaration -Wno-incompatible-pointer-types \
       -Wno-int-conversion -Wno-return-type "${DEFS[@]}" \
       -I "$SRC" -fsyntax-only "$SRC/$file" >"$OUT/$mode-$file.log" 2>&1 || {
         cat "$OUT/$mode-$file.log";exit 1;}
  done
done
echo 'ROUND 74B: native train remains exactly one level per invocation PASS'
echo 'ROUND 74B: 5-level banked XP award paths and private/legacy syntax PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
