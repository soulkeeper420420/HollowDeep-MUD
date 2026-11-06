#!/usr/bin/env python3
"""Template for a guarded repair of an unfinished Hollowdeep installation."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import pwd
import stat
import subprocess
import sys
import tempfile
import zlib

BASE = Path('/srv/hollowdeep')
STAGE = Path('/root/hollowdeep-recovery')
SYSTEMD = Path('/etc/systemd/system')
CONFIG_DIR = Path('/etc/hollowdeep')
TARGET_IP = '172.233.176.81'
UPSTREAM_SHA = '05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0'
GCC32 = '#!/bin/sh\nexec /usr/bin/gcc -m32 "$@"\n'

# EMBEDDED_REPAIR
PAYLOAD_SHA256 = None
PAYLOAD_BASE64 = ''
# END_EMBEDDED_REPAIR


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_payload(encoded, expected):
    packed = base64.b64decode(encoded)
    if digest(packed) != expected:
        raise ValueError('Repair file checksum differs; obtain a fresh copy.')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, 2 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Unexpected repair payload size or format.')
    data = json.loads(raw)
    if set(data) != {'expected_files', 'old_runtime', 'runtime', 'resume', 'enable_public'}:
        raise ValueError('Unexpected repair payload contents.')
    for name, checksum in data['expected_files'].items():
        path = PurePosixPath(name)
        if (path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts
                or not isinstance(checksum, str) or len(checksum) != 64):
            raise ValueError('Unexpected repair manifest path.')
    for name in ('old_runtime', 'runtime', 'resume', 'enable_public'):
        if not isinstance(data[name], str):
            raise ValueError('Unexpected repair source.')
    if digest(data['old_runtime'].encode()) != data['expected_files']['tests/test_runtime.py']:
        raise ValueError('Original test does not match its manifest.')
    return data


def run_readonly(*arguments):
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout.strip()


def require_directory(path):
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError(f'Expected a real directory: {path}. No repair performed.')


def verify_kit(data):
    kit = BASE / 'kit'
    require_directory(BASE)
    require_directory(kit)
    found = set()
    for path in kit.rglob('*'):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise RuntimeError(f'Unexpected linked or special kit file: {path}')
        if stat.S_ISDIR(mode):
            continue
        name = path.relative_to(kit).as_posix()
        if name not in data['expected_files']:
            raise RuntimeError(f'Unexpected kit file: {path}. Existing changes are preserved.')
        checksum = digest(path.read_bytes())
        allowed = {data['expected_files'][name]}
        if name == 'tests/test_runtime.py':
            allowed.add(digest(data['runtime'].encode()))
        if checksum not in allowed:
            raise RuntimeError(f'Kit file differs from this repair: {path}. Existing changes are preserved.')
        found.add(name)
    if found != set(data['expected_files']):
        raise RuntimeError('The installed kit is incomplete; no repair performed.')


def preflight(data):
    if os.geteuid() != 0:
        raise RuntimeError('Run this repair in the Linode root console.')
    release = platform.freedesktop_os_release()
    if platform.machine() != 'x86_64' or release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04':
        raise RuntimeError('This repair requires Ubuntu 24.04 on x86_64.')
    addresses = run_readonly('ip', '-4', '-o', 'addr', 'show').split()
    if not any(value.split('/')[0] == TARGET_IP for value in addresses):
        raise RuntimeError(f'This is not the expected server {TARGET_IP}.')
    for path in (CONFIG_DIR, SYSTEMD / 'hollowdeep.service', SYSTEMD / 'hollowdeep.service.d'):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f'{path} already exists. This repair only resumes an unfinished installation.')
    if run_readonly('systemctl', 'show', 'hollowdeep.service', '--property=LoadState', '--value') != 'not-found':
        raise RuntimeError('A Hollowdeep service is already registered; it will not be changed.')
    account = pwd.getpwnam('hollowdeep')
    if account.pw_uid == 0 or account.pw_dir != str(BASE) or account.pw_shell != '/usr/sbin/nologin':
        raise RuntimeError('The hollowdeep account differs from the dedicated installer account.')
    processes = subprocess.run(['pgrep', '-u', str(account.pw_uid)], capture_output=True, text=True)
    if processes.returncode == 0:
        raise RuntimeError('The hollowdeep account has running processes. No process will be stopped.')
    if processes.returncode != 1:
        raise RuntimeError('Could not verify that the hollowdeep account has no running processes.')
    if run_readonly('ss', '-Hlnt4', 'sport', '=', ':4040'):
        raise RuntimeError('TCP port 4040 is already in use; no repair performed.')
    verify_kit(data)
    world = BASE / 'world'
    require_directory(world)
    require_directory(world / 'src_3.00')
    if world.stat().st_uid != account.pw_uid:
        raise RuntimeError('The world owner differs from the installer-created account.')
    metadata_path = world / '.hollowdeep.json'
    if metadata_path.is_symlink() or not metadata_path.is_file():
        raise RuntimeError('Missing regular world metadata file.')
    metadata = json.loads(metadata_path.read_text())
    if any(metadata.get(key) != value for key, value in {
        'format': 1, 'archive_sha256': UPSTREAM_SHA, 'admin': 'Realmkeeper',
        'bits': 32, 'compatibility_revision': 2,
    }.items()):
        raise RuntimeError('World metadata does not match this recovery. Existing data is preserved.')
    compiler = BASE / 'gcc32'
    if compiler.is_symlink() or not compiler.is_file() or compiler.read_text() != GCC32:
        raise RuntimeError('The compiler wrapper differs from the reviewed installer.')
    executable = world / 'src_3.00/frp.new'
    if executable.is_symlink() or not executable.is_file() or executable.read_bytes()[:5] != b'\x7fELF\x01':
        raise RuntimeError('The existing world has no built 32-bit engine. This repair targets the later runtime-test failure.')


def stage_repair(data):
    """Retain a verified backup, then atomically replace only the runtime test."""
    contents = {
        'test_runtime.original.py': data['old_runtime'],
        'resume.sh': data['resume'],
        'enable-public.py': data['enable_public'],
        'repair.json': json.dumps({'payload_sha256': PAYLOAD_SHA256,
                                  'runtime_test_sha256': digest(data['runtime'].encode())}, indent=2) + '\n',
    }
    if STAGE.exists() or STAGE.is_symlink():
        require_directory(STAGE)
        if STAGE.stat().st_uid != os.geteuid():
            raise RuntimeError('Recovery staging directory is not root-owned.')
        if {path.name for path in STAGE.iterdir()} != set(contents):
            raise RuntimeError('Recovery directory contains unexpected files; they will be preserved.')
        for name, content in contents.items():
            path = STAGE / name
            if path.is_symlink() or not path.is_file() or path.read_text() != content:
                raise RuntimeError('A previous recovery file differs. Keep it for diagnosis.')
    else:
        STAGE.mkdir(mode=0o700)
        for name, content in contents.items():
            path = STAGE / name
            with path.open('x', encoding='utf-8') as stream:
                stream.write(content)
            path.chmod(0o600)
    target = BASE / 'kit/tests/test_runtime.py'
    current = target.read_bytes()
    if digest(current) not in {digest(data['old_runtime'].encode()), digest(data['runtime'].encode())}:
        raise RuntimeError('The runtime test changed after preflight; no replacement performed.')
    if current != data['runtime'].encode():
        fd, temporary = tempfile.mkstemp(prefix='.runtime-repair-', dir=target.parent)
        temporary = Path(temporary)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(data['runtime'])
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(0o644)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return STAGE / 'resume.sh'


def main():
    data = decode_payload(PAYLOAD_BASE64, PAYLOAD_SHA256)
    preflight(data)
    resume = stage_repair(data)
    print('Patched only the disposable runtime test. Existing world and saved characters retained.', flush=True)
    print('Rechecking the build and every required test before creating the localhost service…', flush=True)
    subprocess.run(['bash', str(resume)], cwd=BASE, check=True)
    print('\nAfter creating Realmkeeper locally and using save/quit, open native access with:', flush=True)
    print(f'python3 {STAGE}/enable-public.py', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Recovery stopped: {error}', file=sys.stderr)
        print('Keep the output and existing files. No public-access step was run.', file=sys.stderr)
        sys.exit(1)
