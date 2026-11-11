#!/usr/bin/env bash
# Round11T private rebuild from the exact SHA-pinned Round11P hook-free source.
# Apply the verified equipment + Round11S durability changes only to a copy.
# Smoke-run the binary in private net/PID/mount namespaces. NO DEPLOYMENT.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
OLD="$BASE/round11p-candidate-IvW74AXW"
LIVE=/srv/hollowdeep/world
OLD_SHA=12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c
SOURCE_SHA=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
SOCIAL_SHA=4093b0fe93d4d915ca13e55ec56aa11fd3e84ed4c73fe110702647e0fb9f8ce9
PATCH_SHA_REF=f2c84c0d43312bba072f529b290228aaf6c04758
PATCH_URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PATCH_SHA_REF/engine/experiments/guild-social-v2/round11t_hookfree_candidate_patch.py"
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
 xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
service_id() {
 systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic
}
echo "=== ROUND 11T PINNED HOOK-FREE GUILD RELEASE REBUILD ==="
test "$(id -u)" -eq 0
test -s "$OLD/src/frp.new"
test -s "$OLD/src/hollowdeep_social.c"
test -s "$OLD/rootfs/bin/hollowdeep"
test -s "$BASE/round11-equip-aHkpdO8H/round11k_runner.py"
test "$(sha256sum "$OLD/src/frp.new" | awk '{print $1}')" = "$OLD_SHA"
test "$(sha256sum "$OLD/src/hollowdeep_social.c" | awk '{print $1}')" = "$SOCIAL_SHA"
test "$(hash_tree "$LIVE/src_3.00")" = "$SOURCE_SHA"
test -z "$(find "$OLD/src" "$OLD/rootfs" -type l -print -quit)"
test -z "$(find "$LIVE/src_3.00" "$LIVE/rooms" -type l -print -quit)"
SOURCE_BEFORE=$(hash_tree "$LIVE/src_3.00")
ROOMS_BEFORE=$(hash_tree "$LIVE/rooms")
OLD_BEFORE=$(hash_tree "$OLD")
SERVICE_BEFORE=$(service_id)
verify() {
 result=$?
 trap - EXIT
 if test "$(hash_tree "$LIVE/src_3.00")" != "$SOURCE_BEFORE" ||
    test "$(hash_tree "$LIVE/rooms")" != "$ROOMS_BEFORE" ||
    test "$(hash_tree "$OLD")" != "$OLD_BEFORE" ||
    test "$(service_id)" != "$SERVICE_BEFORE"; then
  echo "STOP: Protected source, rooms, prior candidate or live service changed" >&2
  exit 1
 fi
 echo "Production source, rooms, live service and old candidate: UNCHANGED"
 echo "Live deployment: NONE"
 exit "$result"
}
trap verify EXIT
for n in $(seq 6000 6011); do
 r=$(printf '%s/rooms/r%05d' "$LIVE" "$n")
 test ! -e "$r" && test ! -L "$r"
done
STAGE=$(mktemp -d "$BASE/round11t-hookfree-XXXXXXXX")
echo "Private candidate stage: $STAGE"
mkdir -m 700 "$STAGE/src" "$STAGE/rootfs"
cp -a "$OLD/src/." "$STAGE/src/"
for asset in "$OLD"/rootfs/*; do
 case "$(basename "$asset")" in
  player|hollowdeep-data) continue ;;
 esac
 cp -a "$asset" "$STAGE/rootfs/"
done
install -d -m 700 -o 65534 -g 65534 \
 "$STAGE/rootfs/player" "$STAGE/rootfs/hollowdeep-data"
test -z "$(find "$STAGE" -type l -print -quit)"
test -z "$(find "$STAGE/rootfs/player" "$STAGE/rootfs/hollowdeep-data" -mindepth 1 -print -quit)"
test "$(sha256sum "$STAGE/src/Makefile" | awk '{print $1}')" = \
 ee3d0c9c3f0d77bebc15d01b7e1a5c9892660632ca9d1c5be89db0af1b4c83d5
if grep -Eq 'HD_ROUND9_ISOLATED_FUNDS|round9_test_funds[.]o|HD_ROUND11_TEST' "$STAGE/src/Makefile"; then
 echo "STOP: isolated gameplay hook present in release Makefile" >&2
 exit 1
fi
curl -fsSL --retry 2 --max-time 30 "$PATCH_URL" -o "$STAGE/round11t_patch.py"
test -s "$STAGE/round11t_patch.py"
python3 -m py_compile "$STAGE/round11t_patch.py"
python3 "$STAGE/round11t_patch.py" "$STAGE"

echo "=== FULL PRIVATE 32-BIT REBUILD, NO STALE OBJECTS ==="
(
 cd "$STAGE/src"
 find . -maxdepth 1 -name '*.o' -type f -delete
 rm -f frp.new
 timeout 360 make -j1
) >"$STAGE/build.log" 2>&1 || {
 tail -n 65 "$STAGE/build.log"
 echo "Private build failed at $STAGE"
 exit 1
}
file "$STAGE/src/frp.new" | grep -Fq "ELF 32-bit"
test -s "$STAGE/src/frp.new"
if strings "$STAGE/src/frp.new" | grep -Eiq \
 'Round 11 fixture granted|gold granted: 3000|round11n-ledger-fail|inject-dir-fsync-eio'; then
 echo "STOP: test-only runtime marker detected inside release executable" >&2
 exit 1
fi
install -o 65534 -g 65534 -m 755 \
 "$STAGE/src/frp.new" "$STAGE/rootfs/bin/hollowdeep"
chown -R 65534:65534 "$STAGE/rootfs"
NEW_SHA=$(sha256sum "$STAGE/src/frp.new" | awk '{print $1}')
echo "Candidate SHA-256: $NEW_SHA"

echo "=== ISOLATED CLEAN-ACCOUNT NATIVE LOGIN SMOKE ==="
set +e
timeout --kill-after=3s 95s unshare --mount --net --pid --fork \
 python3 - "$STAGE/rootfs" "$BASE/round11-equip-aHkpdO8H/round11k_runner.py" \
 >"$STAGE/smoke.log" 2>&1 <<'PY'
import runpy, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(strict=True)
runner = Path(sys.argv[2]).resolve(strict=True)
if root.name != "rootfs" or not root.parent.name.startswith("round11t-hookfree-"):
    raise SystemExit("STOP: invalid private smoke rootfs")
sys.argv=[str(runner),str(root)]
m=runpy.run_path(str(runner))
m["loopback"]()
try:
    m["server_start"]()
    with m["connect"]() as conn:
        text=m["receive"](conn,8)
        if "please enter name" not in text.lower():
            raise RuntimeError("Native login prompt unavailable")
    print("PASS: Hook-free candidate reached native login prompt", flush=True)
finally:
    m["server_stop"]()
PY
status=$?
set -e
cat "$STAGE/smoke.log"
if [ "$status" -ne 0 ]; then
 echo "STOP: candidate isolated smoke failed"
 echo "Stage: $STAGE"
 exit 1
fi
test "$(hash_tree "$LIVE/src_3.00")" = "$SOURCE_BEFORE"
test "$(hash_tree "$LIVE/rooms")" = "$ROOMS_BEFORE"
echo "=== ROUND 11T CANDIDATE BUILD + LOGIN SMOKE: PASS ==="
echo "Candidate binary: $STAGE/src/frp.new"
echo "Private manifest: $STAGE/candidate.sha256"
printf '%s  %s\n' "$NEW_SHA" "$STAGE/src/frp.new" >"$STAGE/candidate.sha256"
echo "Not yet cleared: 90/90 populated replay, 11/11 kill tests, 23/23 movement, Town Square, transaction-preserving rollback."
echo "Production decision: NO-GO"
