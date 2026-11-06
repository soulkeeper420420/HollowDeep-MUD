#!/usr/bin/env bash
# Fresh installation only. Run on the target Linode, not in the source workspace.
# The game starts on loopback; public access is a separate, explicit step.
set -Eeuo pipefail
umask 027

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
usage() {
  printf 'Usage: sudo bash %s /path/to/hollowdeep-server-kit.tar.gz [AdminName] [port]\n' "$0"
}
install_phase='prerequisite checks'
trap 'printf "Installation stopped during %s (line %s). Any newly created installation is retained for diagnosis; no existing world was replaced.\n" "$install_phase" "$LINENO" >&2' ERR

[[ $# -ge 1 && $# -le 3 ]] || { usage; exit 2; }
[[ ${EUID} -eq 0 ]] || die 'Run this installer with sudo or from a root console.'
kit_input=$1
admin_name=${2:-Realmkeeper}
game_port=${3:-4040}
kit_sha256=946d69e0afb2be03964a4b76eb51dc5b0945aa26e57e3c7304b46e2347e89cb3
base=/srv/hollowdeep
[[ $admin_name =~ ^[A-Z][a-z]{2,13}$ ]] || die 'AdminName must be 3–14 letters: an initial capital, then lowercase.'
[[ $game_port =~ ^[0-9]{4,5}$ ]] || die 'Choose a TCP port from 1024 to 65535.'
game_port=$((10#$game_port))
(( game_port >= 1024 && game_port <= 65535 )) || die 'Choose a TCP port from 1024 to 65535.'
[[ -f $kit_input && -r $kit_input ]] || die 'The server-kit archive is missing or unreadable.'
[[ $(uname -m) == x86_64 ]] || die 'This installer requires x86_64 Linux.'
[[ -r /etc/os-release ]] || die 'Cannot identify this Linux distribution.'
# /etc/os-release is root-managed operating-system metadata.
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04 ]] || die 'This installer is for Ubuntu 24.04 LTS.'
[[ -d /run/systemd/system ]] || die 'A running systemd installation is required.'
command -v systemctl >/dev/null || die 'systemctl is unavailable.'
[[ ! -e $base && ! -L $base ]] || die "$base already exists; this fresh installer will not replace it."
[[ ! -e /etc/hollowdeep && ! -L /etc/hollowdeep ]] || die '/etc/hollowdeep already exists; inspect that installation first.'
if getent passwd hollowdeep >/dev/null || getent group hollowdeep >/dev/null; then
  die 'A hollowdeep account or group already exists; inspect it before installing.'
fi
[[ ! -e /etc/systemd/system/hollowdeep.service && ! -L /etc/systemd/system/hollowdeep.service ]] || die 'hollowdeep.service already exists.'
[[ ! -e /etc/systemd/system/hollowdeep.service.d && ! -L /etc/systemd/system/hollowdeep.service.d ]] || die 'A Hollowdeep service override already exists.'
[[ $(systemctl show hollowdeep.service --property=LoadState --value) == not-found ]] || die 'A Hollowdeep service is already registered.'

# Verify a private copy before extracting or running any archive contents.
[[ -d /srv ]] || install -d -m 0755 /srv
stage=$(mktemp -d /srv/.hollowdeep-install.XXXXXXXX)
cleanup() { rm -rf -- "$stage"; }
trap cleanup EXIT
cp -- "$kit_input" "$stage/kit.tar.gz"
printf '%s  %s\n' "$kit_sha256" "$stage/kit.tar.gz" | sha256sum --check --status || die 'Archive checksum mismatch. Use the corrected kit supplied with this installer.'

install_phase='Ubuntu package installation'
printf 'Installing the Ubuntu 32-bit compiler and runtime prerequisites…\n'
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  python3 build-essential gcc-multilib libc6-dev-i386 ca-certificates \
  util-linux iproute2 telnet

# Bind-check the intended IPv4 endpoint without changing any firewall rules.
install_phase='TCP port and archive checks'
python3 - "$game_port" <<'PY'
import socket, sys
port = int(sys.argv[1])
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('0.0.0.0', port))
except OSError as exc:
    raise SystemExit(f'TCP port {port} is unavailable: {exc}. Choose another port; no game installation was created.')
PY

# The pinned archive is trusted, but also require its expected plain-file layout.
python3 - "$stage/kit.tar.gz" <<'PY'
from pathlib import PurePosixPath
import sys, tarfile
with tarfile.open(sys.argv[1], 'r:gz') as archive:
    for member in archive:
        name = PurePosixPath(member.name)
        if (name.is_absolute() or '..' in name.parts or not name.parts
                or name.parts[0] != 'hollowdeep-server-kit'
                or not (member.isfile() or member.isdir())):
            raise SystemExit('Unexpected path or special file in the server-kit archive.')
PY
tar -xzf "$stage/kit.tar.gz" -C "$stage" --no-same-owner --no-same-permissions
install -d -m 0755 "$base"
mv -- "$stage/hollowdeep-server-kit" "$base/kit"
chown -R root:root "$base/kit"
find "$base/kit" -type d -exec chmod 0755 {} +
find "$base/kit" -type f -exec chmod 0644 {} +
useradd --system --user-group --home-dir "$base" --no-create-home --shell /usr/sbin/nologin hollowdeep
install -d -m 0700 -o hollowdeep -g hollowdeep "$base/.prepare"

cat > "$base/gcc32" <<'SH'
#!/bin/sh
exec /usr/bin/gcc -m32 "$@"
SH
chmod 0755 "$base/gcc32"

as_game() {
  runuser -u hollowdeep -- env --chdir="$base" PYTHONDONTWRITEBYTECODE=1 "$@"
}
install_phase='world preparation'
as_game /usr/bin/python3 "$base/kit/manage.py" prepare \
  --archive "$base/kit/Mordor_3.00.tar.gz" \
  --destination "$base/.prepare/world" --admin "$admin_name"
mv -- "$base/.prepare/world" "$base/world"
rmdir "$base/.prepare"
install_phase='32-bit engine compilation'
as_game /usr/bin/python3 "$base/kit/manage.py" build --work "$base/world" --cc "$base/gcc32"

printf 'Running preparation, 32-bit command/input tests, and the two-player runtime smoke test…\n'
install_phase='preparation tests'
as_game /usr/bin/python3 "$base/kit/tests/test_prepare.py" --archive "$base/kit/Mordor_3.00.tar.gz"
install_phase='command extension tests'
as_game env CC="$base/gcc32" /usr/bin/python3 "$base/kit/tests/test_extensions.py" --source "$base/world/src_3.00"
install_phase='Telnet normalization tests'
as_game /usr/bin/python3 "$base/kit/tests/test_network.py" --source "$base/world/src_3.00" --cc "$base/gcc32"
install_phase='engine input tests'
as_game /usr/bin/python3 "$base/kit/tests/test_input.py" --source "$base/world/src_3.00" --cc "$base/gcc32"
install_phase='two-player runtime test'
as_game /usr/bin/python3 "$base/kit/tests/test_runtime.py" --archive "$base/kit/Mordor_3.00.tar.gz" --cc "$base/gcc32"

# Record installation settings only after all tests pass. This file has no passwords.
install_phase='localhost service installation'
install -d -m 0700 /etc/hollowdeep
python3 - "$game_port" "$admin_name" "$kit_sha256" <<'PY'
import json, os, sys
path = '/etc/hollowdeep/install.json'
with open(path, 'x') as out:
    json.dump({'port': int(sys.argv[1]), 'admin': sys.argv[2], 'kit_sha256': sys.argv[3]}, out, indent=2)
    out.write('\n')
os.chmod(path, 0o600)
PY
cat > /etc/systemd/system/hollowdeep.service <<UNIT
[Unit]
Description=Hollowdeep original Mordor 3.00 game server
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=hollowdeep
Group=hollowdeep
WorkingDirectory=/srv/hollowdeep/world
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/usr/bin/python3 /srv/hollowdeep/kit/manage.py run --work /srv/hollowdeep/world --port $game_port
Restart=on-failure
RestartSec=5
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/srv/hollowdeep/world
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
UNIT
chmod 0644 /etc/systemd/system/hollowdeep.service
systemctl daemon-reload
systemctl enable --now hollowdeep.service
python3 - "$game_port" <<'PY'
import socket, sys, time
deadline = time.monotonic() + 20
last_error = 'no greeting'
while time.monotonic() < deadline:
    try:
        with socket.create_connection(('127.0.0.1', int(sys.argv[1])), timeout=2) as client:
            received = b''
            while len(received) < 8192 and b'Please enter name:' not in received:
                chunk = client.recv(2048)
                if not chunk:
                    break
                received += chunk
            if b'Mordor v3.00' in received and b'Please enter name:' in received:
                print('Verified original Mordor greeting on localhost.')
                break
            last_error = 'listener did not return the expected original Mordor login prompt'
    except OSError as exc:
        last_error = str(exc)
    time.sleep(0.25)
else:
    raise SystemExit('Server startup was not verified: ' + last_error)
PY
systemctl is-active --quiet hollowdeep.service

cat <<INSTRUCTIONS

Hollowdeep is installed and listening on localhost only, TCP $game_port.
All required build and runtime tests passed on this host.

Create the administrator locally now:
  telnet 127.0.0.1 $game_port

Enter the character name $admin_name and follow the original creation prompts.
Choose the game password privately in that terminal. Once in game, type:
  save
  quit

After every test client has quit, use the separately supplied enable-public.py
script to enable public native-client access. No firewall rules were changed.
Do not restart or stop a populated game until its players have saved and quit.

Logs: journalctl -u hollowdeep.service -n 60 --no-pager
Source: /srv/hollowdeep/world/src_3.00
Player saves: /srv/hollowdeep/world/player
Chronicle saves: /srv/hollowdeep/world/hollowdeep-data
INSTRUCTIONS
