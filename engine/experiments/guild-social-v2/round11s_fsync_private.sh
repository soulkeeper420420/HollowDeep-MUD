#!/usr/bin/env bash
# Run only on authorized private Linode, isolated PID/net/mount.
# One-shot EIO injection at ledger rename and guild parent-directory fsync.
# No deployment/restart, real accounts, or live saves.
set -Eeuo pipefail
umask 077
ROOT=/root/hollowdeep-dev/guild-social-batch1
FROM="$ROOT/round11s-durability-NXKx5FiI"
PROD=/srv/hollowdeep/world/src_3.00
PROD_ROOMS=/srv/hollowdeep/world/rooms
EXPECTED_PROD=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
EXPECTED_BINARY=8dbd6cd1d03b763ff0f454bba11861dd9470052716e2624838f5fec919c7f446
HERE=$(cd "$(dirname "$0")" && pwd -P)
STAGE=""
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
 xargs -0 -r sha256sum | sha256sum | awk '{print $1}')
}
guard() {
 test "$(hash_tree "$PROD")" = "$EXPECTED_PROD" &&
 test "$(hash_tree "$PROD_ROOMS")" = "$PROD_ROOMS_BEFORE" &&
 test "$(hash_tree "$FROM")" = "$FROM_BEFORE"
}
final_check() {
 status=$?
 trap - EXIT
 if ! guard; then
  echo "STOP: protected production or private baseline changed checksum" >&2
  status=1
 else
  echo "Production source, rooms, and previous Round11S stage: UNCHANGED"
 fi
 if [ -n "$STAGE" ]; then
  echo "Disposable fault stage: $STAGE"
  echo "Private result file: $STAGE/results.log"
 fi
 echo "Production deployment/restart: NONE"
 exit "$status"
}
echo "=== ROUND 11S REAL DIRECTORY FSYNC EIO TEST ==="
test "$(id -u)" -eq 0
test -f "$HERE/round11s_fsync_inject.c"
test -f "$HERE/round11s_fsync_replay.py"
test -s "$FROM/rootfs/bin/hollowdeep"
test -s "$FROM/runner.py"
test -s "$FROM/results.log"
grep -Fxq 'Passed: 73' "$FROM/results.log"
grep -Fxq 'Failed: 0' "$FROM/results.log"
test "$(sha256sum "$FROM/rootfs/bin/hollowdeep" | awk '{print $1}')" = "$EXPECTED_BINARY"
test -z "$(find "$FROM" -type l -print -quit)"
test -z "$(find "$HERE" -type l -print -quit)"
test "$(hash_tree "$PROD")" = "$EXPECTED_PROD"
PROD_ROOMS_BEFORE=$(hash_tree "$PROD_ROOMS")
FROM_BEFORE=$(hash_tree "$FROM")
guard
for n in $(seq 6000 6011); do
 f=$(printf '%s/r%05d' "$PROD_ROOMS" "$n")
 test ! -e "$f" && test ! -L "$f"
done
trap final_check EXIT

STAGE=$(mktemp -d "$ROOT/round11s-fsync-XXXXXXXX")
install -d -m 700 "$STAGE/rootfs"
for asset in "$FROM"/rootfs/*; do
 case "$(basename "$asset")" in
  player|hollowdeep-data) continue ;;
 esac
 cp -a "$asset" "$STAGE/rootfs/"
done
install -d -m 700 -o 65534 -g 65534 \
 "$STAGE/rootfs/player" "$STAGE/rootfs/hollowdeep-data"
cp -p "$FROM/runner.py" "$STAGE/runner.py"
test -z "$(find "$STAGE/rootfs" -type l -print -quit)"
test -z "$(find "$STAGE/rootfs/player" -mindepth 1 -print -quit)"
test -z "$(find "$STAGE/rootfs/hollowdeep-data" -mindepth 1 -print -quit)"

cc -m32 -Wall -Wextra -O1 -fPIC -shared \
 "$HERE/round11s_fsync_inject.c" -o "$STAGE/round11s-fsync-fault.so" -ldl
file "$STAGE/round11s-fsync-fault.so" | grep -Fq 'ELF 32-bit'
install -m 755 "$STAGE/round11s-fsync-fault.so" \
 "$STAGE/rootfs/bin/round11s-fsync-fault.so"
chown -R 65534:65534 "$STAGE/rootfs"
test "$(stat -c '%u' "$STAGE/rootfs")" = 65534
test "$(sha256sum "$STAGE/rootfs/bin/hollowdeep" | awk '{print $1}')" = "$EXPECTED_BINARY"
python3 -m py_compile "$HERE/round11s_fsync_replay.py"

echo "Round11S private candidate SHA-256: $EXPECTED_BINARY"
echo "Disposable accounts and ledger: EMPTY"
echo "Fault mechanism: 32-bit LD preload, one-shot rename EIO and directory fsync EIO"
echo "Mount, network and PID namespaces: REQUIRED"
set +e
timeout --kill-after=3s 360s unshare --mount --net --pid --fork \
 python3 "$HERE/round11s_fsync_replay.py" "$STAGE/runner.py" "$STAGE/rootfs" \
 >"$STAGE/results.log" 2>&1
status=$?
set -e
cat "$STAGE/results.log"
if [ "$status" -ne 0 ]; then
 echo "STOP: private fsync fault run failed (status $status)" >&2
 echo "Private server log tail follows; don't publish private server.log" >&2
 tail -n 30 "$STAGE/server.log" >&2 || true
 exit 1
fi
grep -Fxq 'Passed: 18' "$STAGE/results.log"
grep -Fxq 'Failed: 0' "$STAGE/results.log"
test -z "$(find "$STAGE/rootfs/player" -maxdepth 1 -name '.hd11-*' -print -quit)"
echo "=== ROUND 11S ACTUAL FSYNC EIO REPLAY: 18/18 PASS ==="
echo "Power-loss durability / exact hook-free release build: NOT YET CERTIFIED"
