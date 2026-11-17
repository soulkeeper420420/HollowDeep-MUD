#!/usr/bin/env bash
# Validate the revised Necromancer skill in a disposable native source copy.
set -Eeuo pipefail
umask 077
[[ $# == 1 ]] || { echo 'Usage: run_permanent_private.sh /root/hollowdeep-dev/necromancer-playtest-*/src' >&2; exit 2; }
SRC=$(realpath "$1")
case "$SRC" in */necromancer-playtest-*/src) ;; *) echo 'Private source directory required' >&2; exit 2;; esac
case "$SRC" in /srv/*|/var/www/*|/usr/*|/etc/*|/opt/*) echo 'Production path refused' >&2; exit 2;; esac
[[ -z $(find "$SRC" -maxdepth 1 -type l -print -quit) ]] || { echo 'Symlinks refused' >&2;exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
python3 "$P/apply_permanent_private.py" "$SRC" "$P"
OUT=$(mktemp -d "$SRC/../permanent-tests-XXXXXXXX")
FLAGS=(-std=gnu89 -O1 -g -fcommon -DHD_NECROMANCER_PLAYTEST -ffunction-sections -fdata-sections -Wl,--gc-sections)
FLAGS+=(-Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-type)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
if [[ ${HD_SANITIZE:-0} == 1 ]];then
 [[ ${HD_TEST_ELF32:-0} != 1 ]] || { echo 'ASan requires 64-bit test run';exit 2; }
 FLAGS+=(-fsanitize=address,undefined -fno-omit-frame-pointer)
fi
cc "${FLAGS[@]}" -Wall -Wextra -Werror -I "$SRC" \
  "$SRC/hd_necro_skeleton.c" "$P/test_permanent_skeleton.c" \
  -o "$OUT/test-lifecycle"
"$OUT/test-lifecycle"
cc "${FLAGS[@]}" -I "$SRC" \
  "$SRC/hd_necro_skeleton.c" "$SRC/magic1.c" "$SRC/magic2.c" "$SRC/magic3.c" \
  "$P/test_healing_native.c" -o "$OUT/test-healing"
"$OUT/test-healing"
for mode in legacy private;do
  EXTRA=()
  [[ $mode == private ]] && EXTRA=(-DHD_NECROMANCER_PLAYTEST)
  for file in command1.c creature.c magic1.c magic2.c magic3.c;do
    cc -std=gnu89 -fcommon "${EXTRA[@]}" \
      -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-type \
      -fsyntax-only -I "$SRC" "$SRC/$file" \
      >"$OUT/syntax-$mode-$file.log" 2>&1 || {
        tail -60 "$OUT/syntax-$mode-$file.log";exit 1;
      }
  done
  echo "NECROMANCER: $mode branch syntax PASS"
done
if [[ ${HD_TEST_ELF32:-0} == 1 ]];then
 make -s -C "$SRC" -j2 NECROMANCER_PLAYTEST=1 >"$OUT/build.log" 2>&1 || {
  tail -70 "$OUT/build.log";exit 1;
 }
 file "$SRC/frp.new" | grep -q 'ELF 32-bit'
 echo 'NECROMANCER: corpse-derived no-timer healing ELF32 build PASS'
fi
printf 'NECROMANCER: PRIVATE CORPSE SKELETON AND HEALING PASS\nPRODUCTION DEPLOYMENT: NONE\nTEST LOGS: %s\n' "$OUT"
