#!/usr/bin/env bash
# Round 74B: recover unpushed Codex C source from a private Linode workspace.
# Read-only on all existing source; creates one restricted archive for review.
set -Eeuo pipefail
umask 077
ROOT=${1:-/root/hollowdeep-dev}
ARCHIVE="$ROOT/round74b-native-source.tar.gz"
PIN=ac3a6f59e2126ddd344d068976fb89a3501c4c5446ecce49108190a3ca93ca50
[[ -d "$ROOT" && ! -L "$ROOT" && -f "$ARCHIVE" && ! -L "$ARCHIVE" ]] || {
  echo 'Missing private Round 74B source archive/workspace' >&2; exit 2;
}
[[ "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)" == "$PIN" ]] || {
  echo 'Source archive checksum mismatch: abort' >&2; exit 2;
}
# Reject alternate archive layouts before extracting to a new private folder.
while IFS= read -r entry; do
  case "$entry" in /*|../*|*/../*|*/..) echo 'Unsafe source archive entry' >&2; exit 2;; esac
done < <(tar -tzf "$ARCHIVE")
CANDIDATE=''
BEST=0
while IFS= read -r -d '' f; do
  p=${f%/*}
  [[ -d "$p" && ! -L "$p" && -f "$p/hd_player_store.c" &&
     -f "$p/treasure_receipt.c" && -f "$p/command7.c" ]] || continue
  # The original archive does NOT have life metadata in the player-store or
  # receipt codec. Require a changed native persistence layer, not merely a
  # stale copy of the pre-Codex level-60 XP helper.
  if ! grep -Eiq '(life.count|life_count|remort)' \
        "$p/hd_player_store.c" "$p/treasure_receipt.c"; then continue; fi
  t=$(stat -c %Y "$p/hd_player_store.c")
  other=$(stat -c %Y "$p/treasure_receipt.c")
  ((other > t)) && t=$other
  if ((t > BEST)); then CANDIDATE="$p"; BEST=$t; fi
done < <(find "$ROOT" -xdev -type f -name hd74_xp.c -print0)
if [[ -z "$CANDIDATE" ]]; then
  echo 'No modified private Round 74B source found on this Linode.' >&2
  echo 'Codex may have kept its source in an unpushed cloud workspace.' >&2
  exit 3
fi
STAGE=$(mktemp -d "$ROOT/round74b-handoff-stage-XXXXXXXX")
trap 'rm -rf -- "$STAGE"' EXIT
mkdir -m 700 "$STAGE/original" "$STAGE/changed"
tar -xzf "$ARCHIVE" -C "$STAGE/original" --no-same-owner --no-same-permissions
[[ ! -e "$STAGE/original/hd74_xp.c" ]] || {
  echo 'Unexpected source archive layout' >&2; exit 4;
}
printf 'Candidate source: %s\nBase SHA256: %s\n' "$CANDIDATE" "$PIN" > "$STAGE/manifest.txt"
count=0
for file in "$CANDIDATE"/*.c "$CANDIDATE"/*.h "$CANDIDATE"/Makefile; do
  [[ -f "$file" && ! -L "$file" ]] || continue
  name=${file##*/}
  if ! cmp -s -- "$file" "$STAGE/original/$name"; then
    cp -- "$file" "$STAGE/changed/$name"
    printf 'Changed: %s\n' "$name" >> "$STAGE/manifest.txt"
    ((count+=1))
  fi
done
((count > 0)) || { echo 'No changed or added source files found' >&2; exit 4; }
sha256sum "$STAGE"/changed/* >> "$STAGE/manifest.txt"
OUT="$ROOT/round74b-codex-handoff-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar -czf "$OUT" -C "$STAGE" changed manifest.txt
printf 'ROUND 74B CODEX SOURCE RECOVERED: %s\n' "$OUT"
printf 'Candidate: %s\nChanged C/H/Makefile files: %s\n' "$CANDIDATE" "$count"
sha256sum "$OUT"
echo 'No production files changed. Review archive for secrets before uploading to ChatGPT.'
