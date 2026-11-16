#!/usr/bin/env bash
# Round 74B: 65-point new-character + XP60 + first-life + 5-bank.
# STAGES AND TESTS PRIVATE DISPOSABLE SOURCES ONLY. No game startup/restart.
set -Eeuo pipefail
[[ $# == 3 ]] || { echo 'Usage: run_combined_private.sh DISPOSABLE_SRC NATIVE_HOOK_DIR CORE_DIR' >&2; exit 2; }
SRC=$(realpath "$1")
P=$(realpath "$2")
CORE=$(realpath "$3")
case "$SRC" in /srv/*|/var/www/*|/root/hollowdeep/world/*) echo 'Production path refused' >&2; exit 2;; esac
[[ "$SRC" == *'/round74b-'*'/src' ]] || { echo 'Source must be in private round74b-*/src tree' >&2; exit 2; }
[[ ! -L "$SRC" && -f "$SRC/command1.c" && -f "$SRC/Makefile" ]] || exit 2
[[ -z $(find "$SRC" -type l -print -quit) ]] || { echo 'Symlinked private source refused' >&2; exit 2; }
[[ -f "$P/apply_private.py" && -f "$P/xp60/apply_xp_private.py" && \
   -f "$P/first-life/apply_first_life_private.py" && \
   -f "$P/bank5/apply_bank5_private.py" ]] || { echo 'Missing patch stage' >&2; exit 2; }
python3 "$P/apply_private.py" "$SRC" "$P" "$CORE"
python3 "$P/xp60/apply_xp_private.py" "$SRC" "$P/xp60"
python3 "$P/first-life/apply_first_life_private.py" "$SRC"
python3 "$P/bank5/apply_bank5_private.py" "$SRC"
HD_SANITIZE=${HD_SANITIZE:-0} HD_TEST_ELF32=${HD_TEST_ELF32:-0} bash "$P/first-life/run_first_life.sh" "$SRC"
HD_SANITIZE=${HD_SANITIZE:-0} HD_TEST_ELF32=${HD_TEST_ELF32:-0} bash "$P/bank5/run_bank5.sh" "$SRC"
echo 'ROUND 74B COMBINED PRIVATE TESTS: PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
