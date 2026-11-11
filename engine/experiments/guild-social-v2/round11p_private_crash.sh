#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
base=/root/hollowdeep-dev/guild-social-batch1
prior=$base/round11-equip-aHkpdO8H
here=$(dirname "$(realpath "$0")")
candidate=$(realpath "$1")
test "$(id -u)" = 0
test -z "$(find "$prior/rootfs" -type l -print -quit)"
stage=$(mktemp -d "$base/round11p-crash-XXXXXXXX")
echo "Private crash stage: $stage"
root="$stage/rootfs"
install -d -m 700 -o 65534 -g 65534 "$root"
for asset in "$prior"/rootfs/*; do
  case ${asset##*/} in player|hollowdeep-data) continue ;; esac
  cp -a "$asset" "$root/"
done
install -d -m 700 -o 65534 -g 65534 "$root/player" "$root/hollowdeep-data"
cc -m32 -Wall -Wextra -shared -fPIC "$here/round11p_crash_rename.c" -o "$stage/crash-rename.so" -ldl
install -m 755 "$stage/crash-rename.so" "$root/bin/crash-rename.so"
timeout --kill-after=3s 160s unshare --mount --net --pid --fork \
  python3 "$here/round11p_crash_replay.py" "$prior/round11k_runner.py" "$root" "$candidate" \
  | tee "$stage/results.log"
