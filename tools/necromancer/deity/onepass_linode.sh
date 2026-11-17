#!/usr/bin/env bash
# Run private deity command checks against a *copy* of an existing Necromancer
# source, never the original or production. Requires already verified ELF32 src.
set -Eeuo pipefail
umask 077
SRC=${1:?Pass the verified private necromancer-playtest-*/src directory}
R=${2:-/root/hollowdeep-dev/round72-73g-5RBvsQC2/repo}
COMMIT=${3:?Pass pinned GitHub commit}
case "$SRC" in /root/hollowdeep-dev/necromancer-playtest-*/src) ;; *) echo 'Refusing source path' >&2; exit 2;; esac
[[ -d "$SRC" && ! -L "$SRC" && -f "$SRC/hd_player_store.c" ]] || exit 2
BEFORE=$(systemctl show hollowdeep.service -p MainPID --value)
[[ "$BEFORE" =~ ^[0-9]+$ && "$BEFORE" -gt 0 ]] || exit 2
W=$(mktemp -d /root/hollowdeep-dev/necromancer-playtest-deity-XXXXXXXX)
mkdir -m 700 "$W/src" "$W/pkg"
cp -a "$SRC/." "$W/src/"
# No symlinked files allowed anywhere in the copied build.
[[ -z $(find "$W/src" -type l -print -quit) ]] || { echo 'Symlinked source rejected';exit 2; }
git -C "$R" archive "$COMMIT" tools/necromancer/deity | tar -x -C "$W/pkg"
HD_TEST_ELF32=1 bash "$W/pkg/tools/necromancer/deity/run_private.sh" "$W/src" \
  >"$W/deity-build.log" 2>&1 || { tail -90 "$W/deity-build.log";exit 1; }
grep -E '^(DEITY:|PRODUCTION)' "$W/deity-build.log"
AFTER=$(systemctl show hollowdeep.service -p MainPID --value)
[[ "$BEFORE" = "$AFTER" ]] || { echo 'Production service PID changed: check service';exit 1; }
echo 'DEITY: PRIVATE ELF32 DEITY COMMAND PASS'
echo 'PRODUCTION DEPLOYMENT: NONE'
echo "PRIVATE BUILD: $W"
