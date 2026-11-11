#!/usr/bin/env bash
# Read-only original stage audit + isolated BOOT-ONLY private copies.
# Does not retry Round11F gameplay, alter old characters, or touch production.
set -Eeuo pipefail
umask 077

ROOT="/root/hollowdeep-dev/guild-social-batch1"
WORK="$ROOT/round11-load-UuprVvCZ"
BASE="/root/hollowdeep-dev/gm-v5/runtime-isolation/fasttrack-v19-stage-i6d5S65m/rootfs"
LIVE="/srv/hollowdeep/world/src_3.00"
LIVE_ROOMS="/srv/hollowdeep/world/rooms"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"

hash_source() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
hash_original_players() {
  ( cd "$WORK/rootfs/player"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
check_live_rooms() {
  local id p
  for id in $(seq 6000 6011); do
    p=$(printf '%s/r%05d' "$LIVE_ROOMS" "$id")
    if [ -e "$p" ] || [ -L "$p" ]; then
      echo "STOP: Live guild room exists: $p"; return 1
    fi
  done
}

echo "=== HOLLOWDEEP ROUND 11G ISOLATED BOOT DIAGNOSTICS ==="
echo "=== 1. PRESERVE ORIGINAL ROUND11F AND PRODUCTION ==="
test "$(id -u)" -eq 0
test "$(hash_source)" = "$EXPECTED"
test -d "$WORK/src"
test -s "$WORK/src/frp.new"
test -s "$WORK/src/files2.c"
test -s "$WORK/src/compress.c"
test -s "$WORK/src/command1.c"
test -s "$WORK/results.log"
test -s "$WORK/rootfs/bin/hollowdeep"
cmp -s "$WORK/src/frp.new" "$WORK/rootfs/bin/hollowdeep"
test -z "$(find "$WORK/rootfs" -type l -print -quit)"
test -z "$(find "$WORK/src" -type l -print -quit)"
test -s "$WORK/rootfs/player/Hdyajnroa"
test -s "$WORK/rootfs/player/Hdyajnrob"
test -s "$WORK/rootfs/player/Hdyajnroc"
test -d "$WORK/rootfs/hollowdeep-data"
test -s "$WORK/rootfs/hollowdeep-data/player-guilds.v1"
test -d "$BASE/player"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
test -z "$(find "$BASE" -type l -print -quit)"
check_live_rooms
grep -Fq 'Round 11F private workspace guard rejected' \
  "$WORK/round11f_bounded_runner.py"
grep -Fq 'Passed: 43' "$WORK/results.log"
grep -Fq 'Failed: 2' "$WORK/results.log"
grep -Fq 'Isolated game exited before opening port' "$WORK/results.log"
grep -Fq 'Existing character data cannot be loaded' "$WORK/src/command1.c"
grep -Fq 'hd11_raw_player_valid' "$WORK/src/files2.c"

PROD_HASH=$(hash_source)
ENGINE_HASH=$(sha256sum "$WORK/src/frp.new" | awk '{print $1}')
PLAYERS_HASH=$(hash_original_players)
BASE_HASH=$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')
echo "Live source: VERIFIED"
echo "Round 11F original binary/characters/ledger: VERIFIED"
echo "Original native game processes started: NO"
echo "Original private save files: WILL REMAIN UNCHANGED"

echo "=== 2. ORIGINAL PRIVATE FILE METADATA ONLY ==="
python3 - "$WORK/rootfs/player" "$WORK/rootfs/hollowdeep-data/player-guilds.v1" "$WORK/server.log" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]); guild=Path(sys.argv[2]); log=Path(sys.argv[3])
for name in ("Hdyajnroa","Hdyajnrob","Hdyajnroc"):
    p=root/name
    st=p.stat()
    print("Private test player:",name,"bytes=",st.st_size,
          "owner=",st.st_uid,"mode=",oct(st.st_mode & 0o777))
print("Guild ledger: present=",guild.is_file(),
      "size=",guild.stat().st_size if guild.is_file() else 0)
print("Private server log: present=",log.is_file(),
      "size=",log.stat().st_size if log.is_file() else 0)
# Never print contents of saved character files, guild token records, passwords,
# or unfiltered game logs.
PY

echo "=== 3. CREATE TWO BRAND-NEW, DISPOSABLE BOOT ENVIRONMENTS ==="
NEW=$(mktemp -d "$ROOT/round11-bootdiag-XXXXXXXX")
mkdir -m 700 "$NEW/with-saves" "$NEW/empty-saves"
mkdir -m 700 "$NEW/with-saves/rootfs" "$NEW/empty-saves/rootfs"

# Existing failed-run stage is COPIED, NEVER MODIFIED.
cp -a "$WORK/rootfs/." "$NEW/with-saves/rootfs/"
# Build the control from the known-empty disposable base.
cp -a "$BASE/." "$NEW/empty-saves/rootfs/"
for id in $(seq 6000 6011); do
    fn=$(printf 'r%05d' "$id")
    test -s "$WORK/rootfs/rooms/$fn"
    test ! -e "$NEW/empty-saves/rootfs/rooms/$fn"
    cp -p "$WORK/rootfs/rooms/$fn" "$NEW/empty-saves/rootfs/rooms/$fn"
done
cp -p "$WORK/rootfs/rooms/r00001" "$NEW/empty-saves/rootfs/rooms/r00001"
cp -p "$WORK/rootfs/rooms/r00002" "$NEW/empty-saves/rootfs/rooms/r00002"
cp -p "$WORK/src/frp.new" "$NEW/empty-saves/rootfs/bin/hollowdeep"
mkdir -p "$NEW/empty-saves/rootfs/hollowdeep-data"
chown -R 65534:65534 "$NEW/empty-saves/rootfs"
chmod 700 "$NEW/empty-saves/rootfs/hollowdeep-data"
for mode in with-saves empty-saves; do
   test -z "$(find "$NEW/$mode/rootfs" -type l -print -quit)"
   cmp -s "$NEW/$mode/rootfs/bin/hollowdeep" "$WORK/src/frp.new"
done
test -z "$(find "$NEW/empty-saves/rootfs/player" -mindepth 1 -print -quit)"
test -s "$NEW/with-saves/rootfs/player/Hdyajnroa"
echo "Isolated probe workspace: $NEW"
echo "Both probes use identical Round11F binary"
echo "Probe A: fresh control without players/ledger"
echo "Probe B: COPY of failed-run private test players/ledger"
echo "Existing Round 11F stage: UNCHANGED"

cat > "$NEW/boot_probe.py" <<'PY'
#!/usr/bin/env python3
"""Boot-only chroot in an already unshared private PID/net/mount namespace."""
import fcntl
import os
from pathlib import Path
import resource
import signal
import socket
import struct
import subprocess
import sys
import time

label, rootarg, logarg = sys.argv[1:]
root=Path(rootarg)
log=Path(logarg)
ctl=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
try:
    request=struct.pack("16sH14s",b"lo",0,b"\0"*14)
    received=fcntl.ioctl(ctl,0x8913,request)
    iface,flags,pad=struct.unpack("16sH14s",received)
    fcntl.ioctl(ctl,0x8914,
        struct.pack("16sH14s",iface,flags|1,pad))
finally:
    ctl.close()

def limits():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(35,35))
    resource.setrlimit(resource.RLIMIT_AS,
        (512*1024*1024,512*1024*1024))

print("=== BOOT PROBE:",label,"===",flush=True)
print("Private network: ENABLED; production service: NOT ACCESSED",flush=True)
p=None
ready=False
reason=""
with log.open("ab") as output:
    p=subprocess.Popen(
      ["chroot","--userspec=65534:65534",str(root),
       "/bin/hollowdeep","4041"],
      cwd=str(root),stdin=subprocess.DEVNULL,
      stdout=output,stderr=subprocess.STDOUT,preexec_fn=limits)
    try:
        deadline=time.monotonic()+18
        while time.monotonic()<deadline:
            result=p.poll()
            if result is not None:
                reason="early-exit="+str(result)
                break
            try:
                sock=socket.create_connection(("127.0.0.1",4041),timeout=.25)
                sock.close()
                ready=True
                reason="listener-ready"
                break
            except OSError:
                time.sleep(.15)
        if not reason:
            reason="port-not-ready"
    finally:
        if p.poll() is None:
            try: os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            try: p.wait(timeout=4)
            except subprocess.TimeoutExpired:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait(timeout=4)
print("Startup result:",reason,flush=True)
print("Listener ready:",ready,flush=True)
print("Private server stdout bytes:",log.stat().st_size,flush=True)
print("Private server output retained locally; contents NOT printed.",flush=True)
PY

python3 -m py_compile "$NEW/boot_probe.py"
echo "=== 4. BOOT ONLY; NEW PRIVATE PID + NETWORK NAMESPACE FOR EACH ==="
for mode in empty-saves with-saves; do
  echo "--- Case: $mode ---"
  set +e
  timeout --signal=TERM --kill-after=3s 45s \
    unshare --mount --net --pid --fork \
    python3 "$NEW/boot_probe.py" "$mode" \
      "$NEW/$mode/rootfs" "$NEW/$mode/server.log"
  status=$?
  set -e
  echo "Isolated probe process status: $status"
done

echo "=== 5. VERIFY ORIGINAL AND PRODUCTION INTEGRITY ==="
test "$(hash_source)" = "$EXPECTED"
test "$(hash_source)" = "$PROD_HASH"
test "$(sha256sum "$WORK/src/frp.new" | awk '{print $1}')" = "$ENGINE_HASH"
test "$(hash_original_players)" = "$PLAYERS_HASH"
test "$(sha256sum "$BASE/bin/hollowdeep" | awk '{print $1}')" = "$BASE_HASH"
test -z "$(find "$BASE/player" -mindepth 1 -print -quit)"
check_live_rooms
echo "Original Round11F binary and character files: UNCHANGED"
echo "Original production C source/rooms: UNCHANGED"
echo "Production service: NOT RESTARTED"
echo "Website: NOT MODIFIED"
echo "=== ROUND 11G DIAGNOSTICS COMPLETE ==="
echo "Disposable probe workspace: $NEW"
echo "Private diagnostic output: $NEW/{empty-saves,with-saves}/server.log"
echo "This audit does not certify Round11F or alter the original test results."
