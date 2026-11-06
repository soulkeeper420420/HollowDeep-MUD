#!/usr/bin/env python3
"""Template for an isolated, authenticated WSS bridge on the existing Linode."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import pwd
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
import zlib

BASE = Path('/srv/hollowdeep-web')
SYSTEMD = Path('/etc/systemd/system')
TARGET_IP = '172.233.176.81'
NODE_VERSION = '22.23.4'
NODE_SHA = '1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce'
CADDY_VERSION = '2.11.8'
CADDY_SHA = 'f032f8805e4df2ce5e1a8a624495c91e9ff763d8ff3ceddadd4784a07c472f40'
UNITS = ('hollowdeep-web.service', 'hollowdeep-web-tls.service')

# EMBEDDED_BRIDGE
PAYLOAD_SHA256 = None
PAYLOAD_BASE64 = ''
# END_EMBEDDED_BRIDGE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_payload(encoded, checksum):
    compressed = base64.b64decode(''.join(encoded.split()), validate=True)
    if digest(compressed) != checksum:
        raise ValueError('Bridge installer checksum differs.')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Unexpected bridge payload size.')
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {'public_key_spki', 'origin', 'files', 'ws_url', 'ws_integrity'}:
        raise ValueError('Unexpected bridge payload.')
    if not all(isinstance(data[field], str) for field in ('public_key_spki', 'origin', 'ws_url', 'ws_integrity')):
        raise ValueError('Unexpected bridge configuration types.')
    key = base64.b64decode(data['public_key_spki'], validate=True)
    if (len(key) != 44 or key[:12].hex() != '302a300506032b6570032100'
            or base64.b64encode(key).decode() != data['public_key_spki']):
        raise ValueError('Expected an Ed25519 public verification key.')
    if data['origin'] != 'https://hollowdeep-dungeon.soulkeeper420.chatgpt.site':
        raise ValueError('Unexpected browser origin.')
    if not isinstance(data['files'], dict) or set(data['files']) != {'index.mjs', 'protocol.mjs', 'package.json', 'package-lock.json'}:
        raise ValueError('Unexpected bridge source files.')
    if not all(isinstance(content, str) for content in data['files'].values()):
        raise ValueError('Bridge sources must be text.')
    match = re.fullmatch(r'https://registry\.npmjs\.org/ws/-/ws-(\d+\.\d+\.\d+)\.tgz', data['ws_url'])
    if not match:
        raise ValueError('Unexpected dependency URL.')
    integrity = base64.b64decode(data['ws_integrity'][7:], validate=True)
    if (not data['ws_integrity'].startswith('sha512-') or len(integrity) != 64
            or 'sha512-' + base64.b64encode(integrity).decode() != data['ws_integrity']):
        raise ValueError('Unexpected dependency integrity value.')
    lock = json.loads(data['files']['package-lock.json'])
    try:
        dependency = lock['packages']['node_modules/ws']
        matches_lock = (dependency['resolved'] == data['ws_url']
                        and dependency['integrity'] == data['ws_integrity']
                        and dependency['version'] == match[1])
    except (KeyError, TypeError):
        matches_lock = False
    if not matches_lock:
        raise ValueError('WebSocket dependency differs from the included lockfile.')
    return data


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def preflight():
    if os.geteuid() != 0:
        raise RuntimeError('Run this installer in the Linode root console.')
    release = platform.freedesktop_os_release()
    if platform.machine() != 'x86_64' or release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04':
        raise RuntimeError('Ubuntu 24.04 x86_64 is required.')
    if not any(value.split('/')[0] == TARGET_IP for value in command('ip', '-4', '-o', 'addr', 'show').split()):
        raise RuntimeError('This is not the configured Linode.')
    if BASE.exists() or BASE.is_symlink():
        raise RuntimeError(f'{BASE} already exists; retain it and inspect the previous output.')
    for unit in UNITS:
        for suffix in ('', '.d'):
            path = SYSTEMD / (unit + suffix)
            if path.exists() or path.is_symlink():
                raise RuntimeError(f'{path} already exists; no replacement will be made.')
        if command('systemctl', 'show', unit, '--property=LoadState', '--value') != 'not-found':
            raise RuntimeError(f'{unit} is already registered.')
    for username in ('hollowdeep-web', 'hollowdeep-tls'):
        try:
            pwd.getpwnam(username)
        except KeyError:
            pass
        else:
            raise RuntimeError(f'The {username} account already exists.')
        if subprocess.run(['getent', 'group', username], capture_output=True).returncode == 0:
            raise RuntimeError(f'The {username} group already exists.')
    for port in (80, 443, 8788):
        if command('ss', '-Hlnut', 'sport', '=', f':{port}'):
            raise RuntimeError(f'Port {port} is already in use; existing services will be preserved.')
    with socket.create_connection(('127.0.0.1', 4040), timeout=3) as connection:
        connection.settimeout(3)
        received = b''
        while b'Please enter name:' not in received and len(received) < 16384:
            part = connection.recv(4096)
            if not part:
                break
            received += part
        if b'Mordor v3.00' not in received or b'Please enter name:' not in received:
            raise RuntimeError('The existing Mordor login was not verified.')


def download(url, maximum):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Hollowdeep-bridge-installer/1'}), timeout=40) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('Downloaded archive exceeds its size limit.')
    return data


def verified_download(url, checksum, maximum):
    data = download(url, maximum)
    if digest(data) != checksum:
        raise ValueError('Downloaded software checksum mismatch: ' + url)
    return data


def member_bytes(archive_bytes, name, *, optional=False, maximum=160 * 1024 * 1024):
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:*') as archive:
        members = [member for member in archive if member.name == name]
        if not members and optional:
            return None
        if len(members) != 1:
            raise ValueError('Expected exactly one binary archive member: ' + name)
        member = members[0]
        if not member.isfile() or member.size < 0 or member.size > maximum:
            raise ValueError('Unexpected binary archive member.')
        return archive.extractfile(member).read()


def dependency_files(data):
    output = {}
    total_size = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or '\\' in member.name or not path.parts or path.parts[0] != 'package':
                raise ValueError('Unexpected dependency archive path.')
            if member.isdir():
                continue
            if not member.isfile() or member.size < 0 or member.size > 2 * 1024 * 1024:
                raise ValueError('Unexpected dependency archive member.')
            relative = str(PurePosixPath(*path.parts[1:]))
            if relative in ('.', '') or relative in output:
                raise ValueError('Unexpected duplicate dependency file.')
            total_size += member.size
            if total_size > 8 * 1024 * 1024 or len(output) >= 128:
                raise ValueError('Dependency archive exceeds its total size limit.')
            output[relative] = archive.extractfile(member).read()
    if 'package.json' not in output or 'wrapper.mjs' not in output:
        raise ValueError('Incomplete WebSocket dependency.')
    return output


def write_file(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    with path.open('xb') as stream:
        stream.write(data.encode() if isinstance(data, str) else data)
    path.chmod(mode)


def tls_config():
    return f'''{{
    admin off
    default_sni {TARGET_IP}
}}
https://{TARGET_IP} {{
    tls {{
        issuer acme {{
            dir https://acme-v02.api.letsencrypt.org/directory
            profile shortlived
        }}
    }}
    reverse_proxy 127.0.0.1:8788
}}
'''


def service_files():
    common = '''Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
UMask=0077
'''
    bridge = f'''[Unit]
Description=Hollowdeep authenticated browser bridge
After=network-online.target hollowdeep.service
Wants=network-online.target
[Service]
User=hollowdeep-web
Group=hollowdeep-web
WorkingDirectory={BASE}/app
EnvironmentFile={BASE}/bridge.env
ExecStart={BASE}/bin/node {BASE}/app/index.mjs
{common}[Install]
WantedBy=multi-user.target
'''
    tls = f'''[Unit]
Description=Hollowdeep HTTPS and automatic IP certificate renewal
After=network-online.target hollowdeep-web.service
Wants=network-online.target
[Service]
User=hollowdeep-tls
Group=hollowdeep-tls
Environment=XDG_DATA_HOME={BASE}/tls-data
Environment=XDG_CONFIG_HOME={BASE}/tls-config
ExecStart={BASE}/bin/caddy run --config {BASE}/Caddyfile --adapter caddyfile
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
ReadWritePaths={BASE}/tls-data {BASE}/tls-config
{common}[Install]
WantedBy=multi-user.target
'''
    return {UNITS[0]: bridge, UNITS[1]: tls}


def main():
    data = decode_payload(PAYLOAD_BASE64, PAYLOAD_SHA256)
    preflight()
    print('Downloading checksum-pinned Node.js, Caddy and WebSocket dependency…', flush=True)
    node = verified_download(f'https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz', NODE_SHA, 64 * 1024 * 1024)
    caddy = verified_download(f'https://github.com/caddyserver/caddy/releases/download/v{CADDY_VERSION}/caddy_{CADDY_VERSION}_linux_amd64.tar.gz', CADDY_SHA, 40 * 1024 * 1024)
    dependency = download(data['ws_url'], 4 * 1024 * 1024)
    expected = base64.b64decode(data['ws_integrity'][7:])
    if hashlib.sha512(dependency).digest() != expected:
        raise ValueError('WebSocket dependency integrity mismatch.')
    ws_files = dependency_files(dependency)
    node_binary = member_bytes(node, f'node-v{NODE_VERSION}-linux-x64/bin/node')
    caddy_binary = member_bytes(caddy, 'caddy')
    caddy_license = member_bytes(caddy, 'LICENSE', optional=True, maximum=1024 * 1024)
    node_license = member_bytes(node, f'node-v{NODE_VERSION}-linux-x64/LICENSE', maximum=1024 * 1024)
    preflight()  # Downloads take time; recheck all host guards before writing.
    BASE.mkdir(mode=0o755)
    write_file(BASE / 'bin/node', node_binary, 0o755)
    write_file(BASE / 'bin/caddy', caddy_binary, 0o755)
    write_file(BASE / 'legal/node-LICENSE', node_license)
    if caddy_license is not None:
        write_file(BASE / 'legal/caddy-LICENSE', caddy_license)
    for name, source in data['files'].items():
        write_file(BASE / 'app' / name, source)
    for name, source in ws_files.items():
        write_file(BASE / 'app/node_modules/ws' / name, source)
    if command(str(BASE / 'bin/node'), '--version') != 'v' + NODE_VERSION:
        raise RuntimeError('Unexpected Node.js version.')
    for name in ('index.mjs', 'protocol.mjs'):
        command(str(BASE / 'bin/node'), '--check', str(BASE / 'app' / name))
    write_file(BASE / 'Caddyfile', tls_config())
    command(str(BASE / 'bin/caddy'), 'adapt', '--config', str(BASE / 'Caddyfile'), '--adapter', 'caddyfile')
    for username in ('hollowdeep-web', 'hollowdeep-tls'):
        command('useradd', '--system', '--user-group', '--no-create-home', '--home-dir', str(BASE), '--shell', '/usr/sbin/nologin', username)
    tls_user = pwd.getpwnam('hollowdeep-tls')
    for name in ('tls-data', 'tls-config'):
        target = BASE / name
        target.mkdir(mode=0o700)
        os.chown(target, tls_user.pw_uid, tls_user.pw_gid)
    write_file(BASE / 'bridge.env', '\n'.join((
        'HOST=127.0.0.1', 'PORT=8788', 'MORDOR_HOST=127.0.0.1', 'MORDOR_PORT=4040',
        'BRIDGE_PUBLIC_KEY_SPKI=' + data['public_key_spki'], 'ALLOWED_ORIGINS=' + data['origin'],
    )) + '\n', 0o600)
    write_file(BASE / 'install.json', json.dumps({'payload_sha256': PAYLOAD_SHA256, 'node': NODE_VERSION, 'caddy': CADDY_VERSION}, indent=2) + '\n', 0o600)
    for unit, source in service_files().items():
        write_file(SYSTEMD / unit, source)
    if shutil.which('ufw') and command('ufw', 'status').splitlines()[0:1] == ['Status: active']:
        for port in (80, 443):
            command('ufw', 'allow', f'{port}/tcp', 'comment', 'Hollowdeep browser access')
    command('systemctl', 'daemon-reload')
    command('systemctl', 'enable', '--now', *UNITS)
    print('Bridge services installed. Checking trusted HTTPS; certificate issuance may take a moment…', flush=True)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f'https://{TARGET_IP}/health', timeout=3) as response:
                health = json.loads(response.read(4096))
            if health.get('ok') is True and health.get('engine') is True:
                print('Trusted HTTPS and the game connection are verified.', flush=True)
                print('Open ' + data['origin'] + ' and sign in with ChatGPT.', flush=True)
                return
        except (OSError, ValueError):
            pass
        time.sleep(2)
    print('Bridge services are installed, but trusted HTTPS is not verified yet.', flush=True)
    print('If a Linode Cloud Firewall is attached, allow inbound TCP 80 and 443 for certificate issuance and browser access.', flush=True)
    print('Check: journalctl -u hollowdeep-web-tls.service -n 40 --no-pager', flush=True)
    print(f'Then retry: curl --fail https://{TARGET_IP}/health', flush=True)
    raise SystemExit(2)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f'Browser setup stopped: {error}', file=sys.stderr)
        print('Keep existing files and output for diagnosis. The native game service was not changed.', file=sys.stderr)
        sys.exit(1)
