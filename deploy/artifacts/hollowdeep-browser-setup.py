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
PAYLOAD_SHA256 = "df8dc3aa53d5fd3b4d4a98fbe7f983fee3cda83cc47cc42649fed0f829203fb2"
PAYLOAD_BASE64 = """
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
30ipKcG4mox40D3a4/n/A7lWpeU=
"""
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
