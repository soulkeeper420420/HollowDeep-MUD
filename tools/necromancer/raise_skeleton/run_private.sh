#!/usr/bin/env bash
# Complete source-only, disposable Raise Skeleton build and focused C replay.
set -Eeuo pipefail
umask 077
[[ $# == 1 ]] || { echo 'Usage: run_private.sh /root/hollowdeep-dev/necromancer-playtest-.../src' >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in */necromancer-playtest-*/src) ;; *) echo 'Refusing non-disposable source path' >&2; exit 2 ;; esac
case "$SRC" in /srv/*|/var/www/*|/usr/*|/etc/*|/opt/*) echo 'Production source refused' >&2; exit 2 ;; esac
P=$(cd -- "$(dirname -- "$0")" && pwd -P)
[[ -f "$SRC/hd_player_store.c" && -f "$SRC/command1.c" ]] || { echo 'Missing native source'; exit 2; }
[[ -z $(find "$SRC" -maxdepth 1 -type l -print -quit) ]] || { echo 'Symlink detected'; exit 2; }
python3 "$P/apply_private.py" "$SRC" "$P"
OUT=$(mktemp -d "$SRC/../test-skeleton-XXXXXXXX")
FLAGS=(-std=gnu89 -O1 -g -fcommon -Wall -Wextra -Werror -DHD_NECROMANCER_PLAYTEST)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
if [[ ${HD_SANITIZE:-0} == 1 ]]; then
  [[ ${HD_TEST_ELF32:-0} != 1 ]] || { echo 'Sanitizer test requires 64-bit host build' >&2; exit 2; }
  FLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
fi
cc "${FLAGS[@]}" -I "$SRC" "$SRC/hd_necro_skeleton.c" "$P/test_skeleton.c" -o "$OUT/test-skeleton"
"$OUT/test-skeleton"
for mode in legacy private; do
  EXTRA=()
  [[ $mode == private ]] && EXTRA=(-DHD_NECROMANCER_PLAYTEST)
  for f in global.c command5.c command2.c player.c creature.c update.c files1.c; do
    cc -std=gnu89 -fcommon -Wno-implicit-function-declaration \
       -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-type \
       "${EXTRA[@]}" -fsyntax-only -I "$SRC" "$SRC/$f" \
       >"$OUT/$mode-$f.log" 2>&1 || {
           echo "Native syntax failure: $mode $f"
           tail -45 "$OUT/$mode-$f.log"
           exit 1
       }
  done
  echo "NECROMANCER: private and legacy $mode C syntax PASS"
done
if [[ ${HD_TEST_ELF32:-0} == 1 ]]; then
  make -s -C "$SRC" -j2 NECROMANCER_PLAYTEST=1 >"$OUT/build.log" 2>&1 || {
    tail -70 "$OUT/build.log"
    exit 1
  }
  file "$SRC/frp.new" | grep -q 'ELF 32-bit'
  echo 'NECROMANCER: private Raise Skeleton ELF32 native build PASS'
fi
printf 'NECROMANCER: TEST-ONLY SKELETON CHECK PASS\nNO PRODUCTION DEPLOYMENT\nPrivate test logs: %s\n' "$OUT"
