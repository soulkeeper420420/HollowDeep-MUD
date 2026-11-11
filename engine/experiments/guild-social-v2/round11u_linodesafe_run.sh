#!/usr/bin/env bash
# Round11U one-paste launcher: test EXACT private 11T binary and inspect native
# Town Square contract. GitHub inputs SHA-pinned at the prior source commit.
# Neither action modifies live source, rooms, services, players or guild ledger.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
REV=8388cee7cfe4ea5758d3899d1fae27b07ac3c8a6
ROOT="https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/$REV/engine/experiments/guild-social-v2"
echo "=== HOLLOWDEEP ROUND 11U PRIVATE RUN LAUNCHER ==="
test "$(id -u)" -eq 0
test -d "$BASE" && test -d /srv/hollowdeep/world/src_3.00
PACK=$(mktemp -d "$BASE/round11u-toolpack-XXXXXXXX")
echo "Private toolpack and reports: $PACK"

names=(
 round11u_prepare_replay.py
 round11u_exact_candidate_replay.sh
 round11u_town_square_probe.sh
 round11n_patch.py
 round11n_private_replay.sh
 round11p_populated_replay.py
 round11p_private_crash.sh
 round11p_crash_replay.py
 round11p_crash_rename.c
 round11q_private.sh
 round11q_replay.py
 round11q_fixture.c
 round11q_rng.c
 round11s_fsync_private.sh
 round11s_fsync_replay.py
 round11s_fsync_inject.c
)
for file in "${names[@]}"; do
 curl -fsSL --retry 2 --max-time 30 "$ROOT/$file" -o "$PACK/$file"
 test -s "$PACK/$file"
done
for file in "$PACK"/*.sh; do bash -n "$file"; done
for file in "$PACK"/*.py; do python3 -m py_compile "$file"; done

echo "=== RUNNING 142 PINNED-CANDIDATE ASSERTIONS (PRIVATE ONLY) ==="
tests=0
bash "$PACK/round11u_exact_candidate_replay.sh" >"$PACK/exact_candidate_replay.log" 2>&1 || tests=$?
grep -E '^(===|PASS:|Passed:|Failed:|Candidate stage:|Pinned candidate SHA-256:|Total exact candidate suites:|Private report:|Production decision:)' "$PACK/exact_candidate_replay.log" | tail -n 85 || true
if test "$tests" -ne 0; then
 echo "Round11U candidate suite: FAILED OR INCOMPLETE (status $tests)" >&2
 echo "Candidate suite diagnostic tail (private):" >&2
 tail -n 70 "$PACK/exact_candidate_replay.log" >&2
else
 echo "Round11U candidate suite: PASS"
fi

echo "=== READ-ONLY TOWN SQUARE NATIVE ROOM SOURCE CONTRACT ==="
world=0
bash "$PACK/round11u_town_square_probe.sh" >"$PACK/town_square_probe.log" 2>&1 || world=$?
grep -E '^(===|Possible Town Square file:|Matched native room files:|NO EXACT|Room and source bytes|Live service identity|Characters and guild ledger|---)' "$PACK/town_square_probe.log" | head -n 45 || true
if test "$world" -ne 0; then
 echo "Town Square read-only inspection: FAILED (status $world)" >&2
 tail -n 50 "$PACK/town_square_probe.log" >&2
else
 echo "Town Square read-only inspection: COMPLETE"
fi

echo "Full private reports:"
echo "  $PACK/exact_candidate_replay.log"
echo "  $PACK/town_square_probe.log"
echo "Production deployment: NONE"
if test "$tests" -ne 0 || test "$world" -ne 0; then
 echo "=== ROUND 11U: NOT YET READY FOR RELEASE ==="
 exit 1
fi
echo "=== ROUND 11U EXACT-CANDIDATE VALIDATION COMPLETE; WORLD PATCH STILL PENDING ==="
echo "Release decision: NO-GO until room patch and post-activation rollback rehearsal pass"
