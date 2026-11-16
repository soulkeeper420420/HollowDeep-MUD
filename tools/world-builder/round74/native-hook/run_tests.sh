#!/usr/bin/env bash
# Run only on verified disposable/isolated source. Does not start MUD.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo "Usage: bash run_tests.sh ROUND74B_PRIVATE_SOURCE" >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in /srv/*|/var/www/*) echo 'Production source denied' >&2; exit 2;; esac
[[ "$SRC" == *'/round74b-'*'/src' ]] || { echo 'Refusing non-round74b test source' >&2; exit 2; }
for f in command1.c global.c mstruct.h mextern.h mtype.h hd74_native.c hd74_native.h hd74_progression.c hd74_progression.h; do
  [[ -f "$SRC/$f" && ! -L "$SRC/$f" ]] || { echo "Invalid native test source: $f" >&2; exit 2; }
done
P=$(cd "$(dirname "$0")" && pwd -P)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -Wall -Wextra -Werror -fcommon)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-0} == 1 ]] && FLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_native.c" "$SRC/hd74_progression.c" "$P/test_hd74_native.c" -o "$OUT/test-native"
"$OUT/test-native"
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd74_progression.c" "$P/test_progression.c" -o "$OUT/test-core"
"$OUT/test-core"
# Old engine warnings intentionally permitted here; compile-time syntax and
# compatibility of new command hooks are the test, not a legacy warning audit.
for name in command1.c global.c; do
  cc "${FLAGS[@]}" -Wno-error -Wno-implicit-function-declaration \
    -Wno-incompatible-pointer-types -Wno-int-conversion -Wno-return-type \
    -DHD74_PRIVATE_NATIVE -fsyntax-only "$SRC/$name" \
    >"$OUT/${name}.log" 2>&1 || { cat "$OUT/${name}.log"; exit 1; }
done
rg -q '"hprogress", 201, hd74_progress' "$SRC/global.c" 2>/dev/null || \
  grep -q '"hprogress", 201, hd74_progress' "$SRC/global.c"
grep -q 'hd74_parse_starting_stats(str,num)' "$SRC/command1.c"
echo 'ROUND 74B: private command/creation syntax and source hooks PASS'
