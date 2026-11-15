#!/usr/bin/env bash
set -Eeuo pipefail
HERE=$(cd "$(dirname "$(realpath "$0")")" && pwd)
TMP=$(mktemp -d /tmp/hd-showmap-XXXXXXXX)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/rooms"
cc -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE" -DROOMPATH='"'"$TMP/rooms"'"' \
  "$HERE/harness.c" "$HERE/../wilderness_showmap.c" -o "$TMP/test"
"$TMP/test"
