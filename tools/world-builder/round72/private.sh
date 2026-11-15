#!/usr/bin/env bash
# Round 72: isolated browser and native gameplay regression suite.
set -Eeuo pipefail
umask 077

REPO=$(cd "$(dirname "$(realpath "$0")")/../../.." && pwd)
STAGE=/root/hollowdeep-dev/round71-work-UMEnU840
SOURCE=/root/hollowdeep-dev/world-forge/round59-bALCUYZ4
WORLD=/srv/hollowdeep/world
ENGINE_SOURCE="$STAGE/private/src_3.00"
RUNNER=/root/hollowdeep-dev/guild-social-batch1/playtest-83RaUqzk/runner.py
BASE=974f03be35ae9901c82b034ff5d0a2326a21718b
TOOLS=/root/hollowdeep-dev/round60-checkout-DGqPmo9H/replay-tools
export PATH="$TOOLS/node-v22.23.5-linux-x64/bin:$PATH"
export NODE_PATH="$TOOLS/node_modules${NODE_PATH:+:$NODE_PATH}"
export HD_CHROMIUM="$TOOLS/chromium-libs-2FRhrz7K/chromium"
export HD_CHROME_REAL="$TOOLS/browsers/chromium-1194/chrome-linux/chrome"
export HD_CHROME_LIBS="$TOOLS/chromium-libs-2FRhrz7K"
export LD_LIBRARY_PATH="$HD_CHROME_LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export HD_ROUND71_EXTENDED_ROOMS=1
export PYTHONDONTWRITEBYTECODE=1

[[ $(id -u) == 0 ]] || { echo 'Must run as root on the isolated Linode checkout'; exit 1; }
[[ "$REPO" == /root/hollowdeep-dev/round72-*/repo ]] || { echo "Unexpected checkout: $REPO"; exit 1; }
git -C "$REPO" merge-base --is-ancestor "$BASE" HEAD || { echo 'Unexpected Git ancestry'; exit 1; }
[[ $(systemctl is-active hollowdeep.service) == active ]] || { echo 'Production service not active'; exit 1; }
for f in "$SOURCE/populated/rootfs/bin/hollowdeep" "$SOURCE/populated/rootfs/rooms/r00014" \
         "$SOURCE/builder/app.py" "$SOURCE/builder/templates" "$RUNNER" \
         "$ENGINE_SOURCE/mtype.h" "$TOOLS/node-v22.23.5-linux-x64/bin/node" "$HD_CHROMIUM"; do
  [[ -e "$f" ]] || { echo "Missing prerequisite: $f"; exit 1; }
done
[[ -z $(find "$SOURCE/populated/rootfs" "$SOURCE/builder" -type l -print -quit) ]] || {
  echo 'Symlink in prior verified fixture'; exit 1;
}

tree_hash(){ (cd "$1"; find . -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1); }
service_identity(){ systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic; }
LIVE_SRC=$(tree_hash "$WORLD/src_3.00")
LIVE_ROOMS=$(tree_hash "$WORLD/rooms")
LIVE_OBJMON=$(tree_hash "$WORLD/objmon")
LIVE_SERVICE=$(service_identity)
LIVE_PID=$(systemctl show hollowdeep.service -p MainPID --value)
LIVE_EXE=$(sha256sum "/proc/$LIVE_PID/exe")
PRIOR_ENGINE=$(tree_hash "$ENGINE_SOURCE")
FIXTURE_SRC=$(tree_hash "$SOURCE")
check_production(){
  [[ $(tree_hash "$WORLD/src_3.00") == "$LIVE_SRC" &&
     $(tree_hash "$WORLD/rooms") == "$LIVE_ROOMS" &&
     $(tree_hash "$WORLD/objmon") == "$LIVE_OBJMON" &&
     $(service_identity) == "$LIVE_SERVICE" &&
     $(sha256sum "/proc/$LIVE_PID/exe") == "$LIVE_EXE" &&
     $(tree_hash "$ENGINE_SOURCE") == "$PRIOR_ENGINE" &&
     $(tree_hash "$SOURCE") == "$FIXTURE_SRC" ]]
}
finish(){
  rc=$?
  trap - EXIT
  if check_production; then
    echo 'PASS: Production and prior fixture unchanged'
  else
    echo 'FAIL: Protected production or prior fixture changed'
    exit 1
  fi
  exit "$rc"
}
trap finish EXIT

echo '=== ROUND 72: DISPOSABLE WILDERNESS REGRESSION ==='
BUILD_PARENT=$(mktemp -d /root/hollowdeep-dev/round72-build-XXXXXXXX)
BUILD="$BUILD_PARENT/round72-native-build"
python3 "$REPO/tools/world-builder/round72/patch_native.py" "$ENGINE_SOURCE" "$BUILD"
python3 "$REPO/tools/world-builder/round73/patch_native_locate.py" "$BUILD"
python3 "$REPO/tools/world-builder/round73/patch_native_guard.py" "$BUILD"
python3 "$REPO/tools/world-builder/round73/patch_native_radius.py" "$BUILD"
make -C "$BUILD" clean >"$BUILD_PARENT/build.log" 2>&1
make -C "$BUILD" -j2 >>"$BUILD_PARENT/build.log" 2>&1 || { tail -60 "$BUILD_PARENT/build.log"; exit 1; }
ENGINE="$BUILD/frp.new"
[[ $(file -b "$ENGINE") == *'ELF 32-bit'* ]] || { echo 'Private engine is not 32-bit'; exit 1; }
echo 'PASS: Isolated 32-bit native build'
TEST=$(mktemp -d /root/hollowdeep-dev/world-forge/round59-XXXXXXXX)
mkdir -p "$TEST/builder" "$TEST/exports"
echo "Private regression directory: $TEST"
cp -a "$SOURCE/builder/." "$TEST/builder/"
cp "$REPO/tools/world-builder/round57/"{area_export.py,app.py,round55_http.py,round57_http.py,round69_custom.py,test_exit_validation.py,wilderness_map.py,treasure_sites.py} "$TEST/builder/"
cp "$REPO/tools/world-builder/round71/"{round71_http.py,round71_wilderness.py,round71_private.py} "$TEST/builder/"
cp "$REPO/tools/world-builder/round72/round72_native.py" "$TEST/builder/"
cp "$REPO/tools/world-builder/round73/round73c_native.py" "$TEST/builder/"
cp "$REPO/tools/world-builder/round73/round73d_native.py" "$TEST/builder/"
cp "$REPO/tools/world-builder/round73/round73e_native.py" "$TEST/builder/"
for label in populated cleared browser custom quick wilderness mapped; do
  root="$TEST/$label/rootfs"
  mkdir -p "$root"
  for asset in "$SOURCE"/populated/rootfs/*; do
    case ${asset##*/} in player|hollowdeep-data) continue;; esac
    cp -a "$asset" "$root/"
  done
  install -d -m 700 -o 65534 -g 65534 "$root/player" "$root/hollowdeep-data"
  chown 65534:65534 "$root"
  install -m 755 "$ENGINE" "$root/bin/hollowdeep"
  [[ -f "$root/bin/replay-rng.so" ]] || { echo 'Required private replay RNG library missing'; exit 1; }
done
[[ -z $(find "$TEST" -type l -print -quit) ]] || { echo 'Symlink in isolated test stage'; exit 1; }

(
  cd "$TEST/builder"
  python3 -m py_compile app.py area_export.py round55_http.py round57_http.py round69_custom.py round71_http.py round71_wilderness.py round71_private.py
  python3 app.py --test
  python3 test_exit_validation.py
  python3 round69_custom.py --test
  python3 round55_http.py --test
  python3 round71_private.py --test
  PYTHONPATH=. python3 "$REPO/tools/world-builder/round72/test_region.py"
  PYTHONPATH=. python3 "$REPO/tools/world-builder/round73/test_treasure.py"
  echo 'ROUND 73: treasure blueprint and claim unit tests PASS'
) | tee "$TEST/regression.log"
node --check "$REPO/tools/world-builder/round71/round71_browser.cjs"

timeout --kill-after=5s 650s unshare --mount --net --pid --fork \
  env PYTHONDONTWRITEBYTECODE=1 HD_ROUND71_EXTENDED_ROOMS=1 \
  python3 "$REPO/tools/world-builder/round59/replay.py" "$TEST" "$RUNNER" \
  | tee "$TEST/results.log"
for marker in \
 'ROUND 59: PASS' \
 'ROUND 60: PASS' \
 'ROUND 61: PASS' \
 'ROUND 62: PASS' \
 'ROUND 69: native draft room, custom templates and named exit gameplay PASS' \
 'ROUND 70: browser-exported new room navigable in isolated native gameplay PASS' \
 'ROUND 71: browser grid created reciprocal 4x4 region PASS' \
 'ROUND 71: browser duplicate room rejected without draft mutation PASS' \
 'ROUND 71: browser dirty-state protection PASS' \
 'ROUND 71: browser native ZIP export and existing validation PASS' \
 'ROUND 71: browser-generated 4x4 wilderness ZIP navigable in isolated native gameplay PASS' \
 'ROUND 72: seeded terrain, map preview, landmark and browser ZIP PASS' \
 'ROUND 72: browser-exported terrain and native map navigation PASS' \
 'ROUND 73C: native held-map locate, lost-map denial and owner isolation PASS' \
 'ROUND 73D: native guardian-bound virtual chest, dropped-map denial, no rewards PASS' \
 'ROUND 73E: native mapradius 0-10 and map navigation PASS'; do
  grep -Fxq "$marker" "$TEST/results.log" || { echo "Missing regression marker: $marker"; exit 1; }
done
grep -Fxq 'ROUND 71: validated connected 100-room wilderness batch PASS' "$TEST/regression.log"
grep -Fxq 'ROUND 71: collision, unsafe input and atomic rejection PASS' "$TEST/regression.log"
grep -Fxq 'ROUND 72: deterministic terrain, connected restrictions and metadata validation PASS' "$TEST/regression.log"
grep -Fxq 'ROUND 73: treasure blueprint and claim unit tests PASS' "$TEST/regression.log"
check_production || { echo 'Protected production changed; publication blocked'; exit 1; }

echo 'ROUND 72: private regression suite PASS'
