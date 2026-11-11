#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
base=/root/hollowdeep-dev/guild-social-batch1
prior=$base/round11-equip-aHkpdO8H
live=/srv/hollowdeep/world/src_3.00
rollback=$(realpath "$1")
case "$rollback" in
  /root/hollowdeep-dev/round11o-restore-*/isolated/world/src_3.00/frp.new) ;;
  *) exit 2 ;;
esac
test "$(id -u)" = 0
hash_tree() {
  (cd "$1"; find . -type f -print0 | sort -z |
    xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
production=$(hash_tree "$live")
test "$production" = 0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
before=$(hash_tree "$prior")
service() { systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic; }
service_before=$(service)
verify() {
  status=$?
  if [[ $(hash_tree "$live") != "$production" || $(hash_tree "$prior") != "$before" ||
        $(service) != "$service_before" ]]; then
    echo 'Protected source, prior stage, or service identity changed' >&2
    exit 1
  fi
  echo 'Production source, service identity and Round 11K stage verified'
  exit "$status"
}
trap verify EXIT
grep -Fxq 'Passed: 73' "$prior/results.log"
grep -Fxq 'Failed: 0' "$prior/results.log"
test -z "$(find "$prior/src" "$prior/rootfs" -type l -print -quit)"
stage=$(mktemp -d "$base/round11p-candidate-XXXXXXXX")
echo "Private candidate stage: $stage"
cp -a "$prior/src" "$stage/"
python3 - "$stage/src" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1])
for name, snippets in {
    "global.c": (
        "extern int hd_round9_testfund(creature *, cmd *);\n",
        '        { "r9fund", 153, hd_round9_testfund },\n',
    ),
    "Makefile": (" round9_test_funds.o", "CFLAGS += -DHD_ROUND9_ISOLATED_FUNDS=1\n"),
}.items():
    path = src / name
    text = path.read_text()
    for snippet in snippets:
        if text.count(snippet) != 1:
            raise SystemExit(f"Missing unique build anchor in {name}")
        text = text.replace(snippet, "")
    path.write_text(text)
PY
(
  cd "$stage/src"
  rm -f round9_test_funds.c ./*.o frp.new
  timeout 240 make -j1
) >"$stage/build.log" 2>&1
candidate="$stage/src/frp.new"
file "$candidate" | grep -q 'ELF 32-bit'
nm "$candidate" >"$stage/symbols.txt"
strings "$candidate" >"$stage/strings.txt"
grep -q ' T hd_player_clan$' "$stage/symbols.txt"
if grep -Ei 'hd_round9_testfund|r9fund|Round Eleven Blade|round11[nop]-.*fail|HD_GUILD_STAGING_FREE_CREATE|HD_ROUND9_ISOLATED_FUNDS' \
    "$stage/symbols.txt" "$stage/strings.txt" "$stage/build.log"; then
  exit 1
fi
sha256sum "$candidate" "$rollback" >"$stage/binary.sha256"
cat "$stage/binary.sha256"
root="$stage/rootfs"
install -d -m 700 -o 65534 -g 65534 "$root"
for asset in "$prior"/rootfs/*; do
  case ${asset##*/} in player|hollowdeep-data) continue ;; esac
  cp -a "$asset" "$root/"
done
install -d -m 700 -o 65534 -g 65534 "$root/player" "$root/hollowdeep-data"
install -m 700 -o 65534 -g 65534 "$candidate" "$root/bin/hollowdeep"
timeout --kill-after=3s 150s unshare --mount --net --pid --fork \
  python3 "$(dirname "$(realpath "$0")")/round11p_candidate_smoke.py" \
  "$prior/round11k_runner.py" "$root" "$rollback" | tee "$stage/results.log"
sha256sum --check "$stage/binary.sha256"
