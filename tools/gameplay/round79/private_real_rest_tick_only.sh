#!/usr/bin/env bash
# Round79Q: re-use COMPLETED Round79P native ELF32 private build.
# Real socket waits for the game's own timed Breath recovery; no test
# clock shortcuts, process restart, production world/player file access,
# or modification to previously tested native source.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || {
  echo "REFUSED: only root may start the private chroot socket" >&2
  exit 2
}
WORK="${1:?Pass new private /root/hollowdeep-dev/round79q-* results directory}"
SOURCE="${2:?Pass verified Round79P private ELF32 rest source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79q-*) ;; *)
  echo "REFUSED: expected private Round79Q results directory" >&2
  exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *)
  echo "REFUSED: expected previously accepted private Round79P rest source" >&2
  exit 2;;
esac
[[ -d "$WORK/repo" && -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: unsafe or missing private source" >&2
  exit 2
}
for part in frp.new command1.c global.c \
            hd79_breath_travel_runtime.c hd79_rest_game.c \
            hd79_rest_session.c; do
  [[ -f "$SOURCE/$part" && ! -L "$SOURCE/$part" ]] || {
    echo "REFUSED: missing or symlinked private ELF32 component $part" >&2
    exit 2
  }
done
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" = 7f454c4601 ]] || {
  echo "REFUSED: private candidate is not ELF32" >&2;exit 2;
}
grep -Fq "HD79_REST_PLAYTEST" "$SOURCE/command1.c"
grep -Fq 'hd79_rest_bonus_eligible(' "$SOURCE/hd79_breath_travel_runtime.c"
grep -Fq '"rest", 100, hd79_rest_command' "$SOURCE/global.c"

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
PRIVATE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
verify_unchanged() {
  [[ "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVE_SHA" = "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$PRIVATE_SHA" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finish() {
  status=$?
  if ! verify_unchanged; then
    echo "ROUND79Q: SAFETY CHECK FAILED; PID/binary/baseline changed" >&2
    status=1
  else
    echo "PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED"
  fi
  if ((status)); then
    echo "ROUND79Q: PRIVATE REAL-TIME SOCKET TEST FAILED (exit $status)"
    if [[ -f "$WORK/timed-rest-socket.log" ]]; then
      tail -n 80 "$WORK/timed-rest-socket.log"
    fi
  fi
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$status"
}
trap finish EXIT

echo "=== ROUND79Q: REAL CONNECTED REST +15 TIMER VERIFICATION ==="
echo "=== 1. SYNTAX PREFLIGHT AND 11 NATURAL-TICK REGRESSIONS ==="
python3 - "$HERE" <<'PY'
from pathlib import Path
import ast,sys
h=Path(sys.argv[1])
for name in ("round79q_real_rest_tick.py",
             "test_round79q_real_rest_tick.py",
             "check_breath_rest_socket.py"):
    path=h/name
    ast.parse(path.read_text(),filename=str(path))
    print("PASS: private Python syntax",name)
PY
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
  test_round79q_real_rest_tick test_breath_socket_reconnect)

echo "=== 1B. READ-ONLY NATIVE UPDATE_PLY CALLSITE TRACE ==="
python3 - "$SOURCE" <<'PY'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
pattern=re.compile(r"\bupdate_ply[ \t]*\(")
matches=[]
for file in sorted(root.glob("*.c")):
    if file.is_symlink():
        raise RuntimeError("Native source symlink refused: "+file.name)
    for number,line in enumerate(file.read_text(encoding="latin-1").splitlines(),1):
        if pattern.search(line):
            matches.append((file.name,number,line.strip()[:125]))
if not matches:
    raise RuntimeError("No real native update_ply references discovered")
for name,number,line in matches:
    print("PRIVATE NATIVE CALLSITE %s:%d %s"%(name,number,line))
print("Native update_ply callsite count:",len(matches))
PY

echo "=== 2. REUSE VERIFIED PRIVATE ELF32 GAME IN ISOLATED NETWORK/CHROOT ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
export HD79Q_TIMED_REST=1
exec python3 "$1" "$2"
' _ "$HERE/check_breath_rest_socket.py" "$SOURCE" \
  > "$WORK/timed-rest-socket.log" 2>&1 || {
  tail -n 85 "$WORK/timed-rest-socket.log"
  exit 1
}

grep -Fq 'ROUND79Q: REAL SOCKET REST +15 TIMER PASS' \
  "$WORK/timed-rest-socket.log"
grep -Fq 'ROUND 79P: PRIVATE SOCKET REST COMMAND + TRAVEL + HUD PASS' \
  "$WORK/timed-rest-socket.log"
tail -n 18 "$WORK/timed-rest-socket.log"

echo "=== 3. VERIFY NO PRODUCTION OR PRIVATE ELF32 CHANGES ==="
verify_unchanged

echo "ROUND79Q: PRIVATE REAL WALL-CLOCK REST +15 SOCKET PASS"
echo "MOUNTS, ENDURANCE AND STABLES: NOT YET ACTIVE"
echo "PRODUCTION DEPLOYMENT: NONE"
