#!/usr/bin/env bash
# One-shot Necromancer prototype -> Raise Skeleton private ELF32 validation.
# No live executable replacement, player/world mutation or service restart.
set -Eeuo pipefail
umask 077
R=${1:-/root/hollowdeep-dev/round72-73g-5RBvsQC2/repo}
PIN_BASE=3324e24c7ab2fa8fb60dae9965385fa4a41f9533
BRANCH=necromancer-raise-skeleton-playtest
[[ -d "$R/.git" || -f "$R/.git" ]] || { echo 'Missing verified private Git checkout' >&2;exit 2; }
BEFORE=$(systemctl show hollowdeep.service -p MainPID --value)
[[ "$BEFORE" =~ ^[0-9]+$ && "$BEFORE" -gt 0 ]] || { echo 'Live service not active: refusing build' >&2;exit 2; }
# This fetch changes ONLY the private repository's Git objects/refs.
git -C "$R" fetch -q --no-tags origin "$BRANCH"
COMMIT=$(git -C "$R" rev-parse FETCH_HEAD)
if [[ -n ${EXPECTED_COMMIT:-} && "$COMMIT" != "$EXPECTED_COMMIT" ]]; then
  echo "Unexpected branch revision: $COMMIT" >&2
  exit 2
fi
W=$(mktemp -d /root/hollowdeep-dev/necromancer-skeleton-onepass-XXXXXXXX)
mkdir -m 700 "$W/pkg"
git -C "$R" show "$PIN_BASE:tools/necromancer/build-and-check.sh" > "$W/prototype.sh"
printf '%s  %s\n' \
  94d1ea2f729b012dc97a670c7dddd38624984454cb49a0f527c7eec3f5c45f9b \
  "$W/prototype.sh" | sha256sum -c -
git -C "$R" archive "$COMMIT" tools/necromancer/raise_skeleton | tar -x -C "$W/pkg"
# The pinned script checks both private native-source archives and builds
# the verified Necromancer identity prototype in a fresh disposable workspace.
bash "$W/prototype.sh" >"$W/prototype.log" 2>&1 || {
  tail -65 "$W/prototype.log" >&2
  exit 1
}
SRC=$(sed -n 's|^HOLLOWDEEP NECROMANCER PRIVATE ELF32 BUILD PASS: \(.*\)/frp.new$|\1|p' "$W/prototype.log" | tail -1)
[[ "$SRC" == /root/hollowdeep-dev/necromancer-playtest-*/src ]] || {
  echo 'No verified private source path in prototype output' >&2
  tail -20 "$W/prototype.log"
  exit 1
}
[[ -f "$SRC/Makefile" && -f "$SRC/hd_player_store.c" ]] || exit 1
HD_TEST_ELF32=1 HD_SANITIZE=0 \
  bash "$W/pkg/tools/necromancer/raise_skeleton/run_private.sh" "$SRC" \
  >"$W/raise-skeleton.log" 2>&1 || {
    tail -80 "$W/raise-skeleton.log"
    exit 1
  }
grep '^NECROMANCER:' "$W/raise-skeleton.log" | tail -8
AFTER=$(systemctl show hollowdeep.service -p MainPID --value)
[[ "$BEFORE" = "$AFTER" ]] || { echo 'Protected production service changed' >&2; exit 1; }
echo "NECROMANCER RAISE SKELETON PRIVATE ELF32: PASS"
echo "Production deployment: NONE"
echo "Private source: $SRC"
echo "Private logs: $W"
echo "Published source commit: $COMMIT"
