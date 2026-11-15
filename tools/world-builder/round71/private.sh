#!/usr/bin/env bash
# Round 71: isolated browser/native regression suite and guarded publication.
set -Eeuo pipefail
umask 077

REPO=$(cd "$(dirname "$(realpath "$0")")/../../.." && pwd)
STAGE=/root/hollowdeep-dev/round71-work-UMEnU840
SOURCE=/root/hollowdeep-dev/world-forge/round59-bALCUYZ4
WORLD=/srv/hollowdeep/world
ENGINE="$STAGE/private/src_3.00/frp.new"
RUNNER=/root/hollowdeep-dev/guild-social-batch1/playtest-83RaUqzk/runner.py
BASE=603662df71982280fc78a97adb64a36aa4f45db1
BRANCH=guild-production-readiness
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
[[ "$REPO" == "$STAGE/repo" ]] || { echo "Unexpected checkout: $REPO"; exit 1; }
[[ $(git -C "$REPO" rev-parse HEAD) == "$BASE" ]] || { echo 'Unexpected Git HEAD'; exit 1; }
[[ $(systemctl is-active hollowdeep.service) == active ]] || { echo 'Production service not active'; exit 1; }
for f in "$SOURCE/populated/rootfs/bin/hollowdeep" "$SOURCE/populated/rootfs/rooms/r00014" \
         "$SOURCE/builder/app.py" "$SOURCE/builder/templates" "$RUNNER" \
         "$ENGINE" "$TOOLS/node-v22.23.5-linux-x64/bin/node" "$HD_CHROMIUM"; do
  [[ -e "$f" ]] || { echo "Missing prerequisite: $f"; exit 1; }
done
[[ $(file -b "$ENGINE") == *'ELF 32-bit'* ]] || { echo 'Private engine is not 32-bit'; exit 1; }
[[ -z $(find "$SOURCE/populated/rootfs" "$SOURCE/builder" -type l -print -quit) ]] || {
  echo 'Symlink in prior verified fixture'; exit 1;
}

tree_hash(){ (cd "$1"; find . -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1); }
service_identity(){ systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic; }
LIVE_SRC=$(tree_hash "$WORLD/src_3.00")
LIVE_ROOMS=$(tree_hash "$WORLD/rooms")
LIVE_OBJMON=$(tree_hash "$WORLD/objmon")
LIVE_SERVICE=$(service_identity)
FIXTURE_SRC=$(tree_hash "$SOURCE")
check_production(){
  [[ $(tree_hash "$WORLD/src_3.00") == "$LIVE_SRC" &&
     $(tree_hash "$WORLD/rooms") == "$LIVE_ROOMS" &&
     $(tree_hash "$WORLD/objmon") == "$LIVE_OBJMON" &&
     $(service_identity) == "$LIVE_SERVICE" &&
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

echo '=== ROUND 71: DISPOSABLE WILDERNESS REGRESSION ==='
TEST=$(mktemp -d /root/hollowdeep-dev/world-forge/round59-XXXXXXXX)
mkdir -p "$TEST/builder" "$TEST/exports"
echo "Private regression directory: $TEST"
cp -a "$SOURCE/builder/." "$TEST/builder/"
cp "$REPO/tools/world-builder/round57/"{area_export.py,app.py,round55_http.py,round57_http.py,round69_custom.py,test_exit_validation.py} "$TEST/builder/"
cp "$REPO/tools/world-builder/round71/"{round71_http.py,round71_wilderness.py,round71_private.py} "$TEST/builder/"
for label in populated cleared browser custom quick wilderness; do
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
 'ROUND 71: browser-generated 4x4 wilderness ZIP navigable in isolated native gameplay PASS'; do
  grep -Fxq "$marker" "$TEST/results.log" || { echo "Missing regression marker: $marker"; exit 1; }
done
grep -Fxq 'ROUND 71: validated connected 100-room wilderness batch PASS' "$TEST/regression.log"
grep -Fxq 'ROUND 71: collision, unsafe input and atomic rejection PASS' "$TEST/regression.log"
check_production || { echo 'Protected production changed; publication blocked'; exit 1; }

echo '=== ROUND 71: REGRESSIONS PASSED — PUBLISH SOURCE ONLY ==='
if [[ $(git -C "$REPO" ls-remote origin "refs/heads/$BRANCH" | cut -f1) != "$BASE" ]]; then
  echo 'Remote branch changed: publication blocked'; exit 1
fi
unset GIT_ASKPASS SSH_ASKPASS VSCODE_GIT_ASKPASS_NODE VSCODE_GIT_ASKPASS_MAIN VSCODE_GIT_IPC_HANDLE || true

git -C "$REPO" add -- \
  tools/world-builder/round57/area_export.py \
  tools/world-builder/round57/round55_http.py \
  tools/world-builder/round57/visual.html \
  tools/world-builder/round59/replay.py \
  tools/world-builder/round71/README.md \
  tools/world-builder/round71/GAMEPLAY_VISION.md \
  tools/world-builder/round71/round71_browser.cjs \
  tools/world-builder/round71/round71_http.py \
  tools/world-builder/round71/round71_private.py \
  tools/world-builder/round71/round71_wilderness.py \
  tools/world-builder/round71/private.sh

git -C "$REPO" diff --cached --check
[[ $(git -C "$REPO" diff --cached --name-only | wc -l) -eq 11 ]] || {
  echo 'Unexpected approved staged file count; aborting publication'; exit 1;
}
check_production || { echo 'Protected production changed before commit'; exit 1; }
git -C "$REPO" commit -m 'Round 71: private wilderness grid generator and 16000-ID validation'
NEW=$(git -C "$REPO" rev-parse HEAD)
[[ $(git -C "$REPO" ls-remote origin "refs/heads/$BRANCH" | cut -f1) == "$BASE" ]] || {
  echo 'Remote branch moved before push'; exit 1;
}
check_production || { echo 'Protected production changed before push'; exit 1; }
git -C "$REPO" push origin "HEAD:refs/heads/$BRANCH"
[[ $(git -C "$REPO" ls-remote origin "refs/heads/$BRANCH" | cut -f1) == "$NEW" ]]
check_production

echo "ROUND 71: PUBLISHED $NEW"
echo 'Browser, native gameplay, old regression suite and 100-room builder validation: PASS'
echo 'Production restart: NONE'
echo "Private regression log: $TEST/results.log"
echo 'ROUND 71 COMPLETE'
