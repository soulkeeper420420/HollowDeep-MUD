#!/usr/bin/env bash
# Genuine native combat replay. Every runtime file stays in private test roots.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Fresh private /root/hollowdeep-dev/round79ad-* results}"
SOURCE="${2:?Accepted private R3 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) exit 2;; esac
[[ -d "$WORK" && ! -L "$WORK" && ! -e "$WORK/baseline.log" ]] || exit 2
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
finish() {
 local rc=$?
 if [[ "$PID" != "$(systemctl show hollowdeep.service -p MainPID --value)" ||
       "$LIVE_SHA" != "$(sha256sum "$LIVE" | cut -d' ' -f1)" ||
       "$SOURCE_SHA" != "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] ||
       ! systemctl is-active --quiet hollowdeep.service; then
   echo 'FAIL: production/R3 identity changed'; rc=1
 fi
 echo "ROUND79AD COMBAT GAMEPLAY EXIT: $rc"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$rc"
}
trap finish EXIT
bash "$HERE/private_mount_ad_combat_death.sh" "$WORK" "$SOURCE" \
 >"$WORK/baseline.log" 2>&1 || { tail -80 "$WORK/baseline.log"; exit 1; }
STAGED="$(sed -n 's/^PRIVATE SOURCE: //p' "$WORK/baseline.log" | tail -1)"
case "$STAGED" in /tmp/hd-army-game-round79addeath-*/src) ;; *) exit 2;; esac
mkdir "$WORK/identity"
cp "$STAGED/hd79_mount_world_identity.c" "$WORK/identity/"
cp "$HERE/ad-mock/hd_player_store.h" "$HERE/ad-mock/mextern.h" "$WORK/identity/"
for name in hd79_mount_world_identity.h hd79_mount_presence.h \
 hd79_mount_roster.h hd_mount_travel.h hd_wilderness_breath.h \
 hd79_ad_death_identity.inc; do cp "$HERE/$name" "$WORK/identity/"; done
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -DHD79_AD_COMBAT_DEATH_PLAYTEST -I "$WORK/identity" -I "$HERE" \
 "$WORK/identity/hd79_mount_world_identity.c" \
 "$HERE/test_hd79_ad_death_identity.c" "$HERE/hd79_mount_roster.c" \
 "$HERE/hd79_mount_presence.c" "$HERE/hd_mount_travel.c" \
 -o "$WORK/test-death-identity" >"$WORK/identity-build.log" 2>&1 || {
 tail -80 "$WORK/identity-build.log"; exit 1; }
"$WORK/test-death-identity" >"$WORK/identity-test.log" 2>&1
TEST_ROOT="$(mktemp -d /tmp/hd-army-game-round79addeath-socket-XXXXXXXX)"
cp -a "$STAGED" "$TEST_ROOT/src"
TEST_SOURCE="$TEST_ROOT/src"
cp "$HERE/hd79_ad_species.c" "$HERE/hd79_ad_species.h" "$TEST_SOURCE/"
build_native() {
make -s -B -j2 -C "$TEST_SOURCE" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 CORPSE_PLAYTEST=1 \
 PET_STORE_PLAYTEST=1 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 BREATH_STORE_PLAYTEST=1 \
 BREATH_MOVE_CHECKPOINT_TEST=1 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 MOUNT_COMMAND_PLAYTEST=1 \
 MOUNT_STABLECHECK_PLAYTEST=1 MOUNT_PRESENCE_STORE_PLAYTEST=1 \
 MOUNT_TRIPLE_COMMAND_PLAYTEST=1 MOUNT_WORLD_IDENTITY_PLAYTEST=1 \
 MOUNT_LIFECYCLE_PLAYTEST=1 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 \
 MOUNT_AD_PRIVATE_FLEET=1 MOUNT_AD_DEATH_GATE=1 MOUNT_AD_FOUR_STORE=1 \
 MOUNT_AD_COMBAT_DEATH=1 frp.new
}
python3 - "$TEST_SOURCE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/'Makefile'
s=p.read_text(encoding='latin-1');anchor='frp.new: $(OBJECTS)'
if s.count(anchor)!=1:raise ValueError('Native target anchor drift')
p.write_text(s.replace(anchor,'CFLAGS += -DHD79_AD_SPECIES_PLAYTEST\n'
 'OBJECTS += hd79_ad_species.o\n\n'+anchor,1),encoding='latin-1')
PY
build_native >"$WORK/species-build.log" 2>&1 || {
 tail -90 "$WORK/species-build.log"; exit 1; }
cp "$TEST_SOURCE/frp.new" "$WORK/species-candidate.elf32"
nm "$WORK/species-candidate.elf32" >"$WORK/species-symbols.log"
if grep -Eq 'hd79_ad_socket_fixture|hd79_ad_four_store_test_award' \
 "$WORK/species-symbols.log"; then
 echo 'FAIL: test grant hook in normal species build'; exit 1
fi
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror -I "$HERE" \
 "$HERE/hd79_ad_species.c" "$HERE/hd_mount_travel.c" \
 "$HERE/test_hd79_ad_species.c" -o "$WORK/test-species" \
 >"$WORK/species-policy-build.log" 2>&1
"$WORK/test-species" >"$WORK/species-policy.log" 2>&1
cp "$HERE/test_ad_native_socket_fixture.c" "$TEST_SOURCE/hd79_ad_socket_fixture.c"
python3 - "$TEST_SOURCE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
make=(p/'Makefile').read_text(encoding='latin-1')
anchor='frp.new: $(OBJECTS)'
if make.count(anchor)!=1:raise ValueError('Native target anchor drift')
make=make.replace(anchor,
 'CFLAGS += -DHD79_AD_SOCKET_TESTING -DHD_ATOMIC_TESTING -DHD79_AD_FOUR_STORE_TESTING\n'
 'OBJECTS += hd79_ad_socket_fixture.o\n\n'+anchor,1)
(p/'Makefile').write_text(make,encoding='latin-1')
g=(p/'global.c').read_text(encoding='latin-1')
anchor='{ "mount", 100, hd79_mount_command },'
if g.count(anchor)!=1:raise ValueError('Native command anchor drift')
g='extern int hd79_ad_socket_fixture();\n'+g.replace(anchor,
 '        { "adfixture", 100, hd79_ad_socket_fixture },\n'+anchor,1)
(p/'global.c').write_text(g,encoding='latin-1')
PY
build_native >"$WORK/combat-build.log" 2>&1 || {
 tail -90 "$WORK/combat-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$TEST_SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
python3 "$HERE/build_ad_combat_socket_replay.py" \
 /root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py \
 "$WORK/check_combat_socket.py"
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_combat_socket.py" "$TEST_SOURCE" >"$WORK/combat-socket.log" 2>&1 || {
 tail -110 "$WORK/combat-socket.log"; exit 1; }
grep -Fq 'ROUND79AD: SIX REAL NATIVE COMBAT DEATHS PASS' "$WORK/combat-socket.log"
tail -24 "$WORK/combat-socket.log"
echo "PRIVATE COMBAT TEST SOURCE: $TEST_SOURCE"
echo 'PASS: normal candidate and test-only combat ELF32 builds; real socket deaths'
echo 'PLAYER RIDING/STABLE/RETRIEVE/RESTART RESTORE: NOT ACCEPTED'
