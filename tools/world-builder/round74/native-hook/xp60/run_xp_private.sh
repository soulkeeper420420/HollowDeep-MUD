#!/usr/bin/env bash
# Round 74B: private source-only training/XP tests; no game/network/startup.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run_xp_private.sh DISPOSABLE_ROUND74B_SRC' >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in /srv/*|/var/www/*) echo 'Production source refused' >&2; exit 2;; esac
[[ "$SRC" == *'/round74b-'*'/src' ]] || { echo 'Private round74b source path required' >&2; exit 2; }
for file in command1.c command7.c command4.c misc.c player.c creature.c \
    global.c hollowdeep.c command2.c command8.c command10.c \
    hd74_native.c hd74_xp.c hd74_xp.h hd74_progression.c hd74_progression.h; do
    [[ -f "$SRC/$file" && ! -L "$SRC/$file" ]] || { echo "Missing or symlinked source: $file" >&2;exit 2; }
done
P=$(cd "$(dirname "$0")" && pwd -P)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -fcommon -Wall -Wextra -Werror)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && FLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" \
  "$P/test_xp_native.c" -o "$OUT/test-xp"
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_native.c" "$SRC/hd74_progression.c" \
  "$P/test_hd74_native.c" -o "$OUT/test-progress"
"$OUT/test-progress"
"$OUT/test-xp"
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_native.c" "$SRC/hd74_progression.c" \
  "$P/test_hd74_native.c" -o "$OUT/test-progress"
"$OUT/test-progress"
# Actual command7.c compiled with unrelated old sections garbage-collected;
# all train() calls exercise the native function with fake disposable actors.
cc "${FLAGS[@]}" -Wno-error -Wno-unused-parameter -Wno-implicit-function-declaration \
  -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
  -ffunction-sections -fdata-sections -DHD74_PRIVATE_NATIVE -I "$SRC" \
  "$SRC/command7.c" "$SRC/hd74_xp.c" "$SRC/hd74_progression.c" \
  "$P/test_train_native.c" -Wl,--gc-sections -o "$OUT/test-train"
"$OUT/test-train"
# Both legacy branch and new test-only branch must remain valid C.
for mode in legacy test; do
  EXTRA=()
  [[ "$mode" == test ]] && EXTRA=(-DHD74_PRIVATE_NATIVE)
  for file in command1.c command7.c command4.c misc.c player.c creature.c \
      hollowdeep.c command2.c command8.c command10.c global.c; do
      cc "${FLAGS[@]}" -Wno-error -Wno-implicit-function-declaration \
         -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
         "${EXTRA[@]}" -fsyntax-only "$SRC/$file" \
         >"$OUT/$mode-$file.log" 2>&1 || {
            cat "$OUT/$mode-$file.log"; exit 1;
         }
  done
done
[[ $(grep -c 'OBJECTS += hd74_native.o hd74_progression.o hd74_xp.o' "$SRC/Makefile") == 1 ]] || {
  echo 'Makefile lacks all XP objects' >&2;exit 1;
}
echo 'ROUND 74B: private native train, score, death-penalty, and XP-source syntax PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
