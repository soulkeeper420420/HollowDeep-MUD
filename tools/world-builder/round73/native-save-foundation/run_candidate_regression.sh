#!/usr/bin/env bash
# Launch ONE candidate-specific native/browser regression in disposable roots.
# Must run as root from the existing verified private 73G checkout on Linode.
set -Eeuo pipefail
umask 077
[[ $# == 3 ]] || { echo 'Usage: run_candidate_regression.sh REPO PKG OUT' >&2; exit 2; }
[[ $(id -u) == 0 ]] || { echo 'Must run as root' >&2; exit 2; }
REPO=$(realpath "$1")
PKG=$(realpath "$2")
OUT=$(realpath "$3")
case "$REPO" in /root/hollowdeep-dev/round72-*/repo) ;; *) echo 'Private checkout required'; exit 2;; esac
case "$PKG" in /root/hollowdeep-dev/round73g-*/pkg) ;; *) echo 'Private package required'; exit 2;; esac
case "$OUT" in /root/hollowdeep-dev/round73g-*) ;; *) echo 'Private log root required'; exit 2;; esac
[[ $(systemctl is-active hollowdeep.service) == active ]] || exit 2
SOURCE="$REPO/tools/world-builder/round72/private.sh"
TARGET="$REPO/tools/world-builder/round72/private_73g_candidate.sh"
[[ -f "$SOURCE" && ! -e "$TARGET" && -f "$PKG/apply_private.py" && -f "$PKG/test_private.sh" ]] || {
  echo 'Missing original regression or candidate already present; no changes'; exit 2;
}
python3 - "$SOURCE" "$TARGET" "$PKG" <<'PY'
import pathlib, shlex, sys
source, target, pkg = map(pathlib.Path, sys.argv[1:])
old=source.read_text()
needle='python3 "$REPO/tools/world-builder/round73/patch_native_showmap.py" "$BUILD"\n'
assert old.count(needle)==1, 'Original private regression changed'
insert=(f'python3 {shlex.quote(str(pkg / "apply_private.py"))} "$BUILD" '
        f'{shlex.quote(str(pkg))}\n'
        f'HD_TEST_ELF32=1 HD_SANITIZE=0 bash '
        f'{shlex.quote(str(pkg / "test_private.sh"))} "$BUILD"\n')
target.write_text(old.replace(needle, needle+insert,1))
target.chmod(0o700)
PY
LOG="$OUT/candidate.log"
STATUS="$OUT/candidate.status"
[[ ! -e "$LOG" && ! -e "$STATUS" ]] || { echo 'Status/log already exists'; exit 2; }
nohup setsid bash -c '
  bash "$1"
  rc=$?
  printf "%s\n" "$rc" > "$2"
  exit "$rc"
' _ "$TARGET" "$STATUS" > "$LOG" 2>&1 </dev/null &
echo "ROUND 73G candidate regression launched: PID $!"
echo "Log: $LOG"
echo "Status: $STATUS"
echo 'Production deployment: NONE'
