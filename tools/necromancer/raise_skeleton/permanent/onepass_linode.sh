#!/usr/bin/env bash
# One private pinned build: identity -> base skeleton -> untimed corpse/HP/MP/healing.
# No production writes, no service restart, no player-save/world changes.
set -Eeuo pipefail
umask 077
R=${1:-/root/hollowdeep-dev/round72-73g-5RBvsQC2/repo}
BRANCH=necromancer-untimed-healing-playtest
BASE_SHA=db175187b1f56cff10a7394cb083e0538ca99d35
[[ -d "$R/.git" || -f "$R/.git" ]] || { echo 'Missing private Git checkout' >&2; exit 2; }
BEFORE=$(systemctl show hollowdeep.service -p MainPID --value)
[[ "$BEFORE" =~ ^[0-9]+$ && "$BEFORE" -gt 0 ]] || { echo 'Production service not active: refusing' >&2; exit 2; }
git -C "$R" fetch -q --no-tags origin "$BRANCH"
COMMIT=$(git -C "$R" rev-parse FETCH_HEAD)
[[ -n ${EXPECTED_COMMIT:-} && "$COMMIT" == "$EXPECTED_COMMIT" ]] || {
  echo "Commit differs from pinned request: $COMMIT" >&2; exit 2;
}
W=$(mktemp -d /root/hollowdeep-dev/necromancer-untimed-XXXXXXXX)
mkdir -m 700 "$W/pkg"
git -C "$R" archive "$COMMIT" tools/necromancer/raise_skeleton | tar -x -C "$W/pkg"
# Older script fetches its own, specifically pinned, approved first-skill stage.
EXPECTED_COMMIT="$BASE_SHA" \
  bash "$W/pkg/tools/necromancer/raise_skeleton/onepass_linode.sh" "$R" \
  >"$W/baseline.log" 2>&1 || { tail -70 "$W/baseline.log"; exit 1; }
SRC=$(sed -n 's/^Private source: //p' "$W/baseline.log" | tail -1)
[[ "$SRC" == /root/hollowdeep-dev/necromancer-playtest-*/src ]] || {
  echo 'No valid source from base stage' >&2;tail -30 "$W/baseline.log";exit 1;
}
HD_TEST_ELF32=1 HD_SANITIZE=0 \
  bash "$W/pkg/tools/necromancer/raise_skeleton/permanent/run_permanent_private.sh" "$SRC" \
  >"$W/untimed.log" 2>&1 || { tail -80 "$W/untimed.log"; exit 1; }
[[ $(systemctl show hollowdeep.service -p MainPID --value) == "$BEFORE" ]] || {
  echo 'Production PID changed; release blocked' >&2;exit 1;
}
grep -E '^NECROMANCER:' "$W/untimed.log"
echo 'NECROMANCER: UNTIMED CORPSE HP/MP + NATIVE HEALING ELF32 PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
echo "PRIVATE SOURCE: $SRC"
echo "PRIVATE LOGS: $W"
echo "PINNED COMMIT: $COMMIT"
