#!/usr/bin/env bash
# Round11S private-only tri-state durability patch + 73 native regression.
# This checks gameplay compatibility, NOT directory-fsync fault injection.
set -Eeuo pipefail
umask 077
ROOT=/root/hollowdeep-dev/guild-social-batch1
FROM="$ROOT/round11-equip-aHkpdO8H"
PROD=/srv/hollowdeep/world/src_3.00
ROOMS=/srv/hollowdeep/world/rooms
EXPECT=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
PIN=d4dde1d0eb14a4370bf79f9043662462fd883073
URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$PIN/engine/experiments/guild-social-v2/round11s_patch_ledger_durability.py"
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
  xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
guard() {
 test "$(hash_tree "$PROD")" = "$EXPECT"
 test "$(hash_tree "$FROM")" = "$BASELINE"
 for id in $(seq 6000 6011); do
  file=$(printf '%s/r%05d' "$ROOMS" "$id")
  test ! -e "$file" && test ! -L "$file"
 done
}
echo "=== ROUND 11S PRIVATE DIRECTORY DURABILITY CANDIDATE ==="
test "$(id -u)" -eq 0
test -s "$FROM/results.log"
grep -Fxq "Passed: 73" "$FROM/results.log"
grep -Fxq "Failed: 0" "$FROM/results.log"
test -s "$FROM/round11k_runner.py"
test -s "$FROM/src/hollowdeep_social.c"
test -z "$(find "$FROM" -type l -print -quit)"
BASELINE=$(hash_tree "$FROM")
guard
stage=$(mktemp -d "$ROOT/round11s-durability-XXXXXXXX")
echo "Disposable candidate stage: $stage"
mkdir -m 700 "$stage/src" "$stage/rootfs"
cp -a "$FROM/src/." "$stage/src/"
for entry in "$FROM"/rootfs/*; do
 case "$(basename "$entry")" in
  player|hollowdeep-data) continue ;;
 esac
 cp -a "$entry" "$stage/rootfs/"
done
install -d -m 700 -o 65534 -g 65534 "$stage/rootfs/player" "$stage/rootfs/hollowdeep-data"
cp -p "$FROM/round11k_runner.py" "$stage/runner.py"
python3 - "$stage/runner.py" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
old='round11-equip-'
new='round11s-durability-'
if s.count(old)!=1:
 raise SystemExit("STOP: private runner stage-path check changed")
p.write_text(s.replace(old,new,1))
PY
curl -fsSL --retry 2 --max-time 30 "$URL" -o "$stage/patch.py"
grep -Fq 'Round11S private tri-state ledger commit patch' "$stage/patch.py"
python3 -m py_compile "$stage/patch.py" "$stage/runner.py"
python3 "$stage/patch.py" "$stage"
(
 cd "$stage/src"
 rm -f hollowdeep_social.o frp.new
 timeout 240 make -j1
) >"$stage/build.log" 2>&1 || {
 tail -n 55 "$stage/build.log"
 echo "Private build failed in: $stage"
 exit 1
}
test -s "$stage/src/frp.new"
file "$stage/src/frp.new" | grep -Fq "ELF 32-bit"
install -o 65534 -g 65534 -m 755 "$stage/src/frp.new" "$stage/rootfs/bin/hollowdeep"
test -z "$(find "$stage/rootfs/player" -mindepth 1 -print -quit)"
echo "Isolated native 73-check regression starting"
set +e
timeout --kill-after=3s 480s unshare --mount --net --pid --fork \
 python3 "$stage/runner.py" "$stage/rootfs" > "$stage/results.log" 2>&1
status=$?
set -e
grep -E '^(Passed|Failed):|^=== ROUND' "$stage/results.log" || tail -n 50 "$stage/results.log"
guard
echo "Production and Round11K baseline checksum: UNCHANGED"
echo "Private report: $stage/results.log"
echo "Private binary SHA-256: $(sha256sum "$stage/src/frp.new" | cut -d' ' -f1)"
if [ "$status" -ne 0 ]; then exit "$status"; fi
grep -Fxq 'Passed: 73' "$stage/results.log"
grep -Fxq 'Failed: 0' "$stage/results.log"
echo "=== ROUND 11S PRIVATE REPLAY: 73/73 PASS ==="
echo "WARNING: directory fsync injection, new release candidate, and Round11R entrance/rollback not yet certified."
echo "LIVE DEPLOYMENT: NONE"
