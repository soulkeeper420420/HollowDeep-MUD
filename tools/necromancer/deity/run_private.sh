#!/usr/bin/env bash
# Guarded private build/test of DM deity assignment. Never touches production.
set -Eeuo pipefail
umask 077
[[ $# -eq 1 ]] || { echo 'Usage: run_private.sh necromancer-playtest-*/src' >&2; exit 2; }
SRC=$(realpath -- "$1")
case "$SRC" in /root/hollowdeep-dev/necromancer-playtest-*/src|/mnt/data/necromancer-playtest-*/src) ;; *) echo 'Not a disposable Necromancer source' >&2;exit 2;; esac
P=$(cd -- "$(dirname -- "$0")" && pwd -P)
[[ -z $(find "$SRC" -maxdepth 1 -type l -print -quit) ]] || { echo 'Symlinked source refused' >&2; exit 2; }
python3 "$P/test_source_profiles.py"
python3 "$P/apply_deity_private.py" "$SRC" "$P"
TEST=$(mktemp -d "$(dirname "$SRC")/deity-qa-XXXXXXXX")
mkdir -p "$TEST/fixture"
FLAGS=(-std=gnu89 -O1 -g -fcommon -DHD_DEITY_PLAYTEST -Wall -Wextra -Werror)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
cc "${FLAGS[@]}" -I"$SRC" "$SRC/hd_deity.c" "$P/test_deity.c" -o "$TEST/test-deity"
(cd "$TEST/fixture" && "$TEST/test-deity")
python3 "$P/stage_help.py" "$TEST/fixture"
cc "${FLAGS[@]}" -DHD_NECROMANCER_PLAYTEST -I"$SRC" "$SRC/hollowdeep_help.c" "$P/test_help.c" -Wno-format-truncation -o "$TEST/test-help"
(cd "$TEST/fixture" && "$TEST/test-help")
for variant in legacy private; do
  opt=()
  if [[ "$variant" == private ]]; then opt=(-DHD_DEITY_PLAYTEST -DHD_NECROMANCER_PLAYTEST); fi
  for file in global.c hollowdeep_staff.c hollowdeep_help.c; do
    cc -std=gnu89 -fcommon -Wno-implicit-function-declaration -Wno-int-conversion \
       -Wno-incompatible-pointer-types "${opt[@]}" -fsyntax-only \
       -I"$SRC" "$SRC/$file" >"$TEST/$variant-$file.log" 2>&1 || {
         tail -40 "$TEST/$variant-$file.log";exit 1; }
  done
  echo "DEITY: $variant dispatch, native permission and audited database syntax PASS"
done
if [[ ${HD_TEST_ELF32:-0} == 1 ]]; then
  make -B -s -j2 -C "$SRC" NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 >"$TEST/build.log" 2>&1 || {
    tail -60 "$TEST/build.log";exit 1; }
  file "$SRC/frp.new" | grep -q 'ELF 32-bit'
  echo 'DEITY: native private ELF32 build PASS'
fi
echo 'DEITY: PRIVATE DM ASSIGNMENT AND PERSISTENCE PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
echo "PRIVATE TESTS: $TEST"
