#!/usr/bin/env bash
# Round79AC3E: read-only native monster candidate inspection.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="$1"
SOURCE="$2"
HERE="$(cd -- "$(dirname -- "$0")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac3e-*) ;; *) echo "REFUSED: work path";exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79trustedspawn-*/src) ;; *) echo "REFUSED: source path";exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
 echo "REFUSED: private prerequisites";exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo "REFUSED: accepted ELF32 source";exit 2;
}
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
 local code=$?
 if ! unchanged;then code=1;echo "ROUND79AC3E: PRODUCTION SAFETY FAILED";fi
 if ((code));then
  echo "ROUND79AC3E: PRIVATE TEMPLATE RISK REVIEW FAILED ($code)"
  for file in "$WORK"/{unit,abi-build,trait-build,review}.log;do
   if [[ -f "$file" ]];then echo "=== $(basename "$file") ===";tail -n 60 "$file";fi
  done
 else
  echo "ROUND79AC3E: PRIVATE NATIVE ELF32 TEMPLATE RISK REVIEW PASS"
  echo "PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED"
 fi
 echo "PRIVATE RESULTS: $WORK"
 echo "PRODUCTION DEPLOYMENT: NONE"
 exit "$code"
}
trap finish EXIT
echo "=== ROUND79AC3E: NATIVE MOUNT TEMPLATE CANDIDATE REVIEW ==="
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 \
 python3 -m unittest -q test_native_mount_candidate_review_round79ac3e) \
 > "$WORK/unit.log" 2>&1 || { tail -n 80 "$WORK/unit.log";exit 1; }
tail -n 5 "$WORK/unit.log"
cc -m32 -std=gnu99 -w -I "$SOURCE" \
 "$HERE/native_template_abi_round79ac3d.c" \
 -o "$WORK/native-abi" > "$WORK/abi-build.log" 2>&1 || {
 tail -n 70 "$WORK/abi-build.log";exit 1; }
cc -m32 -std=gnu99 -w -I "$SOURCE" \
 "$HERE/native_mount_trait_abi_round79ac3e.c" \
 -o "$WORK/native-traits" > "$WORK/trait-build.log" 2>&1 || {
 tail -n 70 "$WORK/trait-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/native-traits" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/native-abi" > "$WORK/abi.log"
"$WORK/native-traits" > "$WORK/traits.log"
# Numeric C sizeof/offsetof probe output only; no private monster data.
# This makes future ABI mismatches diagnosable in a single safe run.
echo "=== NATIVE ELF32 TRAIT METADATA (NO MONSTER DATA) ==="
cat "$WORK/traits.log"
python3 "$HERE/native_mount_candidate_review_round79ac3e.py" \
 --world-root /srv/hollowdeep/world --abi "$WORK/abi.log" \
 --traits "$WORK/traits.log" > "$WORK/review.log" 2>&1 || {
 tail -n 90 "$WORK/review.log";exit 1; }
cat "$WORK/review.log"
unchanged
echo "ROUND79AC3E: NO MOUNT CATALOG OR PLAYER MOUNTING ENABLED"
