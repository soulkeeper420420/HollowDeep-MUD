#!/usr/bin/env bash
# Offline-only: never loads player saves from a running HollowDeep world.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: run_native_reward.sh PRIVATE_NATIVE_SOURCE_COPY' >&2; exit 2; }
P=$(cd "$(dirname "$0")" && pwd -P)
SRC=$(realpath "$1")
case "$SRC" in
  /root/hollowdeep-dev/*|/mnt/data/round73g_native_integration/stage-test) ;;
  *) echo 'Refusing source path outside disposable roots' >&2; exit 2;;
esac
[[ -f "$SRC/hd_player_store.c" && -f "$SRC/files2.c" ]] || exit 2
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FLAGS=(-std=gnu89 -O1 -g -fcommon -ffunction-sections -fdata-sections)
[[ ${HD_TEST_ELF32:-0} == 1 ]] && FLAGS+=(-m32)
[[ ${HD_SANITIZE:-1} == 1 ]] && FLAGS+=(-fsanitize=address,undefined)
compile() {
  cc "${FLAGS[@]}" -include stdlib.h -Wno-implicit-function-declaration \
    -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-type \
    -I "$SRC" -I "$P" -I "$OUT" -DCOMPRESS -DHD_ATOMIC_TESTING -DHD_TEST_FILES2_WRAPPER \
    "$@" "$SRC/files2.c" "$SRC/files3.c" "$SRC/compress.c" \
    "$SRC/hd_player_store.c" "$SRC/treasure_receipt.c" \
    "$SRC/atomic_player_snapshot.c" "$P/hd_native_reward.c" \
    "$P/test_native_reward.c" -Wl,--gc-sections -o "$OUT/test-reward"
}
compile
"$OUT/test-reward"
# The second replay uses an actual SQLite guardian/map-authorized claim and
# Python SHA-256 reward manifest from the previous Round 73G module.
python3 "$P/generate_manifest_fixture.py" "$OUT/hd_generated_manifest.h"
compile -DHD_LEDGER_FIXTURE
"$OUT/test-reward"
echo 'ROUND 73G: Python ledger -> actual native inventory + durable receipt PASS'
