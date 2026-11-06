#!/usr/bin/env python3
"""Open an installer-created Hollowdeep world after local admin creation."""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time

BASE = Path('/srv/hollowdeep')
UNIT = 'hollowdeep.service'
UNIT_FILE = Path('/etc/systemd/system') / UNIT
DROPIN_DIR = Path('/etc/systemd/system/hollowdeep.service.d')
DROPIN = DROPIN_DIR / '20-public.conf'
INSTALL_CONFIG = Path('/etc/hollowdeep/install.json')
KIT_SHA256 = '946d69e0afb2be03964a4b76eb51dc5b0945aa26e57e3c7304b46e2347e89cb3'


def command(*arguments):
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout.strip()


def is_public_listener(port):
    lines = command('ss', '-Hlnt4', 'sport', '=', f':{port}').splitlines()
    return any(re.search(rf'(?:0\.0\.0\.0|\*):{port}\s', line) for line in lines)


def check_greeting(port):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=2) as client:
                client.settimeout(3)
                data = b''
                while b'Please enter name:' not in data and len(data) < 16384:
                    part = client.recv(4096)
                    if not part:
                        break
                    data += part
                if b'Mordor v3.00' in data and b'Please enter name:' in data:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.25)
    raise RuntimeError('The original Mordor login greeting was not received. Inspect journalctl -u hollowdeep.service.')


def main():
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo or as root on the Linode.')
    config = json.loads(INSTALL_CONFIG.read_text())
    port, admin = config.get('port'), config.get('admin')
    if (type(port) is not int or not 1024 <= port <= 65535 or
            not isinstance(admin, str) or not re.fullmatch(r'[A-Z][a-z]{2,13}', admin) or
            config.get('kit_sha256') != KIT_SHA256):
        raise RuntimeError('Unrecognized installation metadata; no changes made.')
    world = BASE / 'world'
    metadata = json.loads((world / '.hollowdeep.json').read_text())
    if metadata.get('admin') != admin or metadata.get('compatibility_revision') != 2:
        raise RuntimeError('World metadata does not match this installer; no changes made.')
    player = world / 'player' / admin
    if player.is_symlink() or not player.is_file() or player.stat().st_size == 0:
        raise RuntimeError(f'First create {admin} with telnet 127.0.0.1 {port}, then use save and quit.')
    fragment = command('systemctl', 'show', UNIT, '--property=FragmentPath', '--value')
    if fragment != str(UNIT_FILE) or UNIT_FILE.is_symlink():
        raise RuntimeError('Unexpected service definition; no changes made.')
    dropins = command('systemctl', 'show', UNIT, '--property=DropInPaths', '--value').split()
    if any(path != str(DROPIN) for path in dropins):
        raise RuntimeError('Additional service overrides exist. Review them before opening the game.')
    if DROPIN_DIR.is_symlink() or DROPIN.is_symlink():
        raise RuntimeError('Unexpected service symlink; no changes made.')
    desired = ('[Service]\nExecStart=\nExecStart=/usr/bin/python3 '
               f'{BASE}/kit/manage.py run --work {world} --port {port} --public\n')
    previous = DROPIN.read_text() if DROPIN.exists() else None
    if previous is not None and previous != desired:
        raise RuntimeError('An edited public override already exists; refusing to replace it.')
    already_public = previous == desired and is_public_listener(port)
    if not already_public:
        connected = command('ss', '-Htn', 'state', 'established', 'sport', '=', f':{port}')
        if connected:
            raise RuntimeError('Clients are still connected. Have them save and quit, then retry; no restart performed.')
        DROPIN_DIR.mkdir(mode=0o755, exist_ok=True)
        DROPIN.write_text(desired)
        DROPIN.chmod(0o644)
        try:
            command('systemctl', 'daemon-reload')
            command('systemctl', 'restart', UNIT)
            check_greeting(port)
            if not is_public_listener(port):
                raise RuntimeError('The listener did not bind to all IPv4 interfaces.')
        except (RuntimeError, subprocess.CalledProcessError, OSError):
            if previous is None:
                DROPIN.unlink(missing_ok=True)
            else:
                DROPIN.write_text(previous)
            subprocess.run(['systemctl', 'daemon-reload'], check=False)
            subprocess.run(['systemctl', 'restart', UNIT], check=False)
            raise
    else:
        check_greeting(port)
    if shutil.which('ufw'):
        status = command('ufw', 'status')
        if re.search(r'^Status: active$', status, re.M):
            print(command('ufw', 'allow', f'{port}/tcp', 'comment', 'Hollowdeep MUD'))
    print(f'Original Mordor login verified on all IPv4 interfaces, TCP port {port}.')
    print('In Linode Cloud Firewall, allow inbound TCP on this port if a firewall is attached.')
    print(f'Test from your MUD client: host 172.233.176.81, port {port}, Telnet (SSL off).')
    print('This verifies the local listener; an external client must confirm firewall reachability.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
