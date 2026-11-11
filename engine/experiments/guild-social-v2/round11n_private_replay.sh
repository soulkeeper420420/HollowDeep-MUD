#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
base=/root/hollowdeep-dev/guild-social-batch1
prior=$base/round11-equip-aHkpdO8H
live=/srv/hollowdeep/world/src_3.00
here=$(dirname "$(realpath "$0")")
patch=round11n_patch.py
if [[ ${1:-} == --native-writer-faults ]]; then
  patch=round11o_writer_faults.py
elif [[ $# != 0 ]]; then
  exit 2
fi
hash_tree() {
  (cd "$1"; find . -type f -print0 | sort -z |
    xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
test "$(id -u)" = 0
grep -Fxq 'Passed: 73' "$prior/results.log"
grep -Fxq 'Failed: 0' "$prior/results.log"
test -z "$(find "$prior/src" "$prior/rootfs" -type l -print -quit)"
before=$(hash_tree "$prior")
production=$(hash_tree "$live")
test "$production" = 0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
verify() {
  status=$?
  if [[ $(hash_tree "$live") != "$production" || $(hash_tree "$prior") != "$before" ]]; then
    echo 'Protected tree checksum changed' >&2
    exit 1
  fi
  echo 'Production source and previous private stage checksums verified'
  exit "$status"
}
trap verify EXIT
stage=$(mktemp -d "$base/round11-equip-11n-XXXXXXXX")
echo "Private stage $stage"
install -d -o 65534 -g 65534 -m 700 "$stage/rootfs"
cp -a "$prior/src" "$stage/"
cp -a "$prior/round11k_runner.py" "$stage/runner.py"
for asset in "$prior"/rootfs/*; do
  case ${asset##*/} in player|hollowdeep-data) continue ;; esac
  cp -a "$asset" "$stage/rootfs/"
done
install -d -o 65534 -g 65534 -m 700 "$stage/rootfs/player" "$stage/rootfs/hollowdeep-data"
python3 "$here/$patch" "$stage"
(
  cd "$stage/src"
  rm -f round9_test_funds.o hollowdeep_social.o frp.new
  if [[ $patch == round11o_writer_faults.py ]]; then rm -f files2.o; fi
  timeout 240 make -j1
) >"$stage/build.log" 2>&1
install -o 65534 -g 65534 -m 755 "$stage/src/frp.new" "$stage/rootfs/bin/hollowdeep"
timeout --kill-after=3s 480s unshare --mount --net --pid --fork \
  python3 "$stage/runner.py" "$stage/rootfs" >"$stage/results.log" 2>&1
grep -E '^(Passed|Failed):' "$stage/results.log"
grep -Fxq 'Passed: 84' "$stage/results.log"
grep -Fxq 'Failed: 0' "$stage/results.log"
