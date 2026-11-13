#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
base=/root/hollowdeep-dev/world-forge
builder=$base/round57-gameplay-builder
prior=$base/round58-native-gameplay/round58y-62BlAm6v
runner=/root/hollowdeep-dev/guild-social-batch1/playtest-83RaUqzk/runner.py
live=/srv/hollowdeep/world
hash_tree() {
  (cd "$1"; find . -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum)
}
identity() { systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic; }
source_before=$(hash_tree "$live/src_3.00")
rooms_before=$(hash_tree "$live/rooms")
objects_before=$(hash_tree "$live/objmon")
service_before=$(identity)
prior_before=$(hash_tree "$prior")
builder_before=$(hash_tree "$builder")
verify() {
  status=$?
  [[ $(hash_tree "$live/src_3.00") == "$source_before" &&
     $(hash_tree "$live/rooms") == "$rooms_before" &&
     $(hash_tree "$live/objmon") == "$objects_before" &&
     $(identity) == "$service_before" &&
     $(hash_tree "$prior") == "$prior_before" &&
     $(hash_tree "$builder") == "$builder_before" ]] || exit 1
  echo 'Production source, rooms, templates, service and earlier stages verified'
  exit "$status"
}
trap verify EXIT
test "$(id -u)" = 0
grep -Fxq '=== ROUND 58Y RESULT: PASS ===' "$prior/results.log"
printf '%s  %s\n' 86dd59d6d91127b9ec6c636898463b12171ecb10c3dee2de9764da5e1d3a9d77 \
  "$prior/rootfs/bin/hollowdeep" | sha256sum -c
test -z "$(find "$prior/rootfs" "$builder/templates" -type l -print -quit)"
stage=$(mktemp -d "$base/round59-XXXXXXXX")
echo "Private stage: $stage"
mkdir "$stage/builder"
cp -a "$builder"/*.py "$builder"/*.json "$builder/templates" "$stage/builder/"
repo_builder="$(dirname "$(realpath "$0")")/../round57"
cp "$repo_builder/"{area_export.py,test_exit_validation.py} "$stage/builder/"
cc -m32 -Wall -Wextra -shared -fPIC \
  "$(dirname "$(realpath "$0")")/../../../engine/experiments/guild-social-v2/round11q_rng.c" \
  -ldl -o "$stage/replay-rng.so"
cp -p "$prior/rootfs/objmon/"{m00,o00} "$stage/builder/templates/"
for label in populated cleared; do
  root="$stage/$label/rootfs"
  mkdir -p "$root"
  for asset in "$prior"/rootfs/*; do
    case ${asset##*/} in player|hollowdeep-data) continue ;; esac
    cp -a "$asset" "$root/"
  done
  install -d -m 700 -o 65534 -g 65534 "$root/player" "$root/hollowdeep-data"
  chown 65534:65534 "$root"
  install -m 755 "$stage/replay-rng.so" "$root/bin/replay-rng.so"
done
(
  cd "$stage/builder"
  export PYTHONDONTWRITEBYTECODE=1
  python3 app.py --test
  python3 test_exit_validation.py
  python3 round55_http.py --test
) | tee "$stage/regression.log"
timeout --kill-after=3s 340s unshare --mount --net --pid --fork \
  env PYTHONDONTWRITEBYTECODE=1 python3 "$(dirname "$(realpath "$0")")/replay.py" "$stage" "$runner" \
  | tee "$stage/results.log"
grep -Fxq 'ROUND 59: PASS' "$stage/results.log"
