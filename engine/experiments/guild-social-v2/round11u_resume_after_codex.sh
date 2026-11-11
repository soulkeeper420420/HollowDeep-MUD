#!/usr/bin/env bash
# Continue current Round11U from last Codex result, without replaying 90/11:
# 23 private movement+rollback + 18 pinned fsync EIO + five Town Square checks.
# Fetch scripts from an immutable GitHub commit and do NOT deploy.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
REV=5cce7c62e6010ade6248ca6a1417ed0ad02bbbe5
URL="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$REV/engine/experiments/guild-social-v2"
echo '=== HOLLOWDEEP ROUND 11U CONTINUE FROM CODEX CHECKPOINT ==='
test "$(id -u)" -eq 0
test -d "$BASE"
WORK=$(mktemp -d "$BASE/round11u-continue-XXXXXXXX")
echo "Private reports: $WORK"

for name in round11u_movement_pipe_replay.sh round11v_town_square_layout_probe.sh; do
 curl -fsSL --retry 2 --max-time 30 "$URL/$name" -o "$WORK/$name"
 test -s "$WORK/$name"
 bash -n "$WORK/$name"
done
grep -Fq 'ROUND 11U PRIVATE MOVEMENT PIPE RECOVERY' "$WORK/round11u_movement_pipe_replay.sh"
grep -Fq 'ROUND 11V READ-ONLY TOWN SQUARE ROOM LAYOUT' "$WORK/round11v_town_square_layout_probe.sh"

echo '=== REPLAY ONLY PENDING 23 + 18 EXACT-CANDIDATE ASSERTIONS ==='
status=0
bash "$WORK/round11u_movement_pipe_replay.sh" > "$WORK/movement_and_fsync.log" 2>&1 || status=$?
grep -E '^(===|PASS:|Passed:|Failed:|STOP:|Production source|Production release|Live deployment|Private report:|Private reports:)' "$WORK/movement_and_fsync.log" | tail -n 60 || true
if test "$status" -ne 0; then
 echo "Private movement/fsync test stopped (status $status); diagnostic tail:" >&2
 tail -n 55 "$WORK/movement_and_fsync.log" >&2
fi

echo '=== FIND CORRECT TOWN SQUARE AMONG FIVE ROOM MATCHES ==='
roomstatus=0
bash "$WORK/round11v_town_square_layout_probe.sh" > "$WORK/town_square_layout.log" 2>&1 || roomstatus=$?
cat "$WORK/town_square_layout.log"
echo '=== PRIVATE REPORT FILES ==='
echo "$WORK/movement_and_fsync.log"
echo "$WORK/town_square_layout.log"
echo 'Production deployment or restart: NONE'
if test "$status" -ne 0 || test "$roomstatus" -ne 0; then
 echo '=== ROUND 11U / 11V: TESTS OR INSPECTION INCOMPLETE ==='
 exit 1
fi
echo '=== ROUND 11U EXACT-CANDIDATE CHECKS REPLAYED; TOWN ROOM NOT YET PATCHED ==='
echo 'Production release: NO-GO'
