#!/usr/bin/env bash
# Round79AC3D: read-only native world monster-template audit.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="$1"
SOURCE="$2"
HERE="$(cd -- "$(dirname -- "$0")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac3d-*) ;; *) echo "REFUSED: work path"; exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79trustedspawn-*/src) ;; *) echo "REFUSED: private source"; exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" &&
   ! -L "$(dirname "$SOURCE")" && -f "$SOURCE/frp.new" &&
   ! -L "$SOURCE/frp.new" ]] || {
  echo "REFUSED: private workspace/source"; exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: accepted native source not ELF32"; exit 2;
}
grep -Fq 'num/MFILESIZE' "$SOURCE/files4.c"
grep -Fq 'sizeof(creature)' "$SOURCE/files4.c"
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local rc=$?
 if ! unchanged; then rc=1; echo "ROUND79AC3D: PRODUCTION/BASELINE SAFETY FAILED"; fi
 if ((rc)); then
   echo "ROUND79AC3D: PRIVATE AUDIT FAILED ($rc)"
   for log in "$WORK"/{unit,abi-build,abi,inventory}.log; do
     if [[ -f "$log" ]]; then echo "=== $(basename "$log") ==="; tail -n 55 "$log"; fi
   done
 else
   echo "ROUND79AC3D: PRIVATE NATIVE TEMPLATE ABI/READ-ONLY INVENTORY PASS"
   echo "PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED"
 fi
 echo "PRIVATE RESULTS: $WORK"
 echo "PRODUCTION DEPLOYMENT: NONE"
 exit "$rc"
}
trap finish EXIT
echo "=== ROUND79AC3D: NATIVE ELF32 MONSTER TEMPLATE AUDIT ==="
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 \
 python3 -m unittest -q test_native_template_inventory_round79ac3d) \
 > "$WORK/unit.log" 2>&1 || {
   cat "$WORK/unit.log"; exit 1;
 }
tail -n 5 "$WORK/unit.log"
cc -m32 -std=gnu99 -w -I "$SOURCE" \
 "$HERE/native_template_abi_round79ac3d.c" \
 -o "$WORK/native-template-abi" > "$WORK/abi-build.log" 2>&1 || {
   tail -n 75 "$WORK/abi-build.log"; exit 1;
 }
[[ "$(od -An -tx1 -N5 "$WORK/native-template-abi" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/native-template-abi" > "$WORK/abi.log"
python3 "$HERE/native_template_inventory_round79ac3d.py" \
 --world-root /srv/hollowdeep/world --abi "$WORK/abi.log" \
 > "$WORK/inventory.log" 2>&1 || {
   tail -n 90 "$WORK/inventory.log"; exit 1;
 }
cat "$WORK/inventory.log"
unchanged
echo "ROUND79AC3D: NAME-BASED CANDIDATES ONLY; TRUSTED CATALOG UNCONFIGURED"
echo "NO SPAWN/BOARD/STABLE/RETRIEVE/RESTORE/TRAVEL ENABLED"
