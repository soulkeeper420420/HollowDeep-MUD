#!/usr/bin/env bash
# Offline compile/test only. No native game process, player files or production.
set -Eeuo pipefail
cd "$(dirname "$0")"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -Wall -Wextra -Werror -fno-omit-frame-pointer)
if [[ ${HD_TEST_ELF32:-0} == 1 ]]; then FLAGS+=(-m32); fi
if [[ ${HD_SANITIZE:-0} == 1 ]]; then FLAGS+=(-fsanitize=address,undefined); fi
cc "${FLAGS[@]}" hd74_progression.c test_progression.c -o "$OUT/test"
"$OUT/test"

if [[ $# -eq 1 ]]; then
  [[ ${HD_TEST_ELF32:-0} == 1 ]] || { echo "Native ABI check requires HD_TEST_ELF32=1" >&2; exit 2; }
  SOURCE=$(realpath "$1")
  case "$SOURCE" in /srv/hollowdeep/*) echo "Refusing production source" >&2; exit 2 ;; esac
  [[ -f "$SOURCE/mstruct.h" && -f "$SOURCE/mtype.h" && ! -L "$SOURCE/mstruct.h" ]] || exit 2
  cc "${FLAGS[@]}" -I "$SOURCE" -I "$PWD" test_native_abi.c -o "$OUT/native-abi"
  "$OUT/native-abi"
elif [[ $# -ne 0 ]]; then
  echo 'Usage: run.sh [disposable_native_source_dir]' >&2
  exit 2
fi
