#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$(realpath "$0")")" && pwd)
TMP=$(mktemp -d /tmp/hd-radius-XXXXXXXX)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/rooms"
cc -std=gnu89 -O1 -Wall -Wextra -Werror -I "$ROOT" -DROOMPATH='"'"$TMP/rooms"'"' "$ROOT/harness.c" "$ROOT/../wilderness_radius.c" -o "$TMP/test"
"$TMP/test"
