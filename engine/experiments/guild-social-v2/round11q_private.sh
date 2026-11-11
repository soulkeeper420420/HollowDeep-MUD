#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
base=/root/hollowdeep-dev/guild-social-batch1
prior=$base/round11-equip-aHkpdO8H
candidate=$base/round11p-candidate-IvW74AXW
live=/srv/hollowdeep/world
here=$(dirname "$(realpath "$0")")
test "$(id -u)" = 0
hash_tree() {
  (cd "$1"; find . -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
service() { systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic; }
source_before=$(hash_tree "$live/src_3.00")
rooms_before=$(hash_tree "$live/rooms")
service_before=$(service)
prior_before=$(hash_tree "$prior")
candidate_before=$(hash_tree "$candidate")
verify() {
  status=$?
  if [[ $(hash_tree "$live/src_3.00") != "$source_before" || $(hash_tree "$live/rooms") != "$rooms_before" ||
        $(service) != "$service_before" || $(hash_tree "$prior") != "$prior_before" ||
        $(hash_tree "$candidate") != "$candidate_before" ]]; then
    echo 'Protected tree or service identity changed' >&2
    exit 1
  fi
  echo 'Live source, rooms, service and earlier private stages verified'
  exit "$status"
}
trap verify EXIT
test "$source_before" = 0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
printf '%s  %s\n' \
  12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c "$candidate/src/frp.new" \
  b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5 "$live/src_3.00/frp.new" | sha256sum -c
test -z "$(find "$live/src_3.00" "$live/rooms" "$candidate/rootfs" -type l -print -quit)"
stage=$(mktemp -d "$base/round11q-XXXXXXXX")
echo "Private stage: $stage"
root="$stage/rootfs"
install -d -m 700 -o 65534 -g 65534 "$root"
for asset in "$candidate"/rootfs/*; do
  case ${asset##*/} in player|hollowdeep-data|rooms) continue ;; esac
  cp -a "$asset" "$root/"
done
install -d -m 700 -o 65534 -g 65534 "$root/player" "$root/hollowdeep-data"
mkdir "$stage/predecessor"
cp -a "$live/src_3.00" "$live/rooms" "$stage/predecessor/"
test "$(hash_tree "$stage/predecessor/src_3.00")" = "$source_before"
test "$(hash_tree "$stage/predecessor/rooms")" = "$rooms_before"
cp -a "$stage/predecessor/src_3.00" "$stage/src_3.00"
cp -a "$stage/predecessor/rooms" "$root/rooms"
for name in Makefile command1.c command10.c command6.c command7.c compress.c files2.c global.c \
    hollowdeep_social.c hollowdeep_social.h io.c room.c frp.new; do
  cp -p "$candidate/src/$name" "$stage/src_3.00/$name"
done
for name in r00001 r00002 r060{00..11}; do
  cp -p "$candidate/rootfs/rooms/$name" "$root/rooms/$name"
done
install -m 700 -o 65534 -g 65534 "$stage/src_3.00/frp.new" "$root/bin/hollowdeep"
objcopy --redefine-sym main=hd_native_main "$candidate/src/main.o" "$stage/native-main.o"
objects=()
for object in "$candidate"/src/*.o; do
  [[ ${object##*/} == main.o ]] || objects+=("$object")
done
cc -m32 -I"$candidate/src" "$here/round11q_fixture.c" "$stage/native-main.o" "${objects[@]}" -lm -o "$root/bin/fixture"
chmod 755 "$root/bin/fixture"
cc -m32 -Wall -Wextra -fPIC -shared "$here/round11q_rng.c" -ldl -o "$root/bin/fixture-rng.so"
chmod 755 "$root/bin/fixture-rng.so"
chown -R "$(stat -c '%u:%g' "$live/rooms")" "$root"
timeout --kill-after=3s 240s unshare --mount --net --pid --fork \
  python3 "$here/round11q_replay.py" "$prior/round11k_runner.py" "$root" | tee "$stage/results.log"
test "$(hash_tree "$stage/src_3.00")" = "$source_before"
test "$(hash_tree "$root/rooms")" = "$rooms_before"
cmp "$root/bin/hollowdeep" "$stage/predecessor/src_3.00/frp.new"
echo 'Complete isolated source, binary and room rollback verified'
