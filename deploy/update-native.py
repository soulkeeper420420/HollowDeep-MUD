#!/usr/bin/env python3
"""Template: test a native update separately, then switch an empty game safely."""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import pwd
import re
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zlib

BASE = Path('/srv/hollowdeep')
CONFIG = Path('/etc/hollowdeep')
SYSTEMD = Path('/etc/systemd/system')
UNIT = 'hollowdeep.service'
UNIT_FILE = SYSTEMD / UNIT
DROPINS = SYSTEMD / (UNIT + '.d')
PUBLIC = DROPINS / '20-public.conf'
MAINTENANCE = DROPINS / '90-native-update.conf'
TARGET_IP = '172.233.176.81'
LEGACY_SHA = 'c50a99730f83a16e994f941006f2b64b7943b12f6fd60f0d3c087481208d3537'
UPSTREAM_SHA = '05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0'
RECORD = CONFIG / 'native-update.json'

# EMBEDDED_UPDATE
PAYLOAD_SHA256 = None
PAYLOAD_BASE64 = ''
# END_EMBEDDED_UPDATE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_name(name):
    path = PurePosixPath(name)
    if (not path.parts or path.is_absolute() or '..' in path.parts or '\\' in name
            or str(path) != name):
        raise ValueError('Unexpected update path.')
    return path


def decode_payload(encoded, checksum):
    packed = base64.b64decode(encoded)
    if digest(packed) != checksum:
        raise ValueError('Update checksum differs. Obtain a fresh copy.')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, 8 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Unexpected update payload size or format.')
    data = json.loads(raw)
    if set(data) - {'predecessor_sha256'} != {'engine', 'kit_baseline', 'world_baseline', 'world_updates',
                     'runtime_fix_sha', 'unit_text', 'tests'}:
        raise ValueError('Unexpected update payload contents.')
    if 'predecessor_sha256' in data and not re.fullmatch(r'[0-9a-f]{64}', str(data['predecessor_sha256'])):
        raise ValueError('Unexpected predecessor update checksum.')
    for section in ('engine', 'kit_baseline', 'world_baseline', 'world_updates'):
        for name in data[section]:
            path = relative_name(name)
            if section.startswith('world_') and path.parts[0] not in ('src_3.00', 'help'):
                raise ValueError('An update tried to change persistent game data.')
    for section in ('engine', 'world_updates'):
        for name, value in data[section].items():
            data[section][name] = base64.b64decode(value, validate=True)
    if 'manage.py' not in data['engine'] or 'tests/test_runtime.py' not in data['engine']:
        raise ValueError('Required engine files are missing.')
    if any(name in data['world_updates'] for name in ('src_3.00/mstruct.h', 'src_3.00/frp.new')):
        raise ValueError('A source update must not replace serialized types or embed a binary.')
    return data


def read_command(*arguments):
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout.strip()


def service(action):
    read_command('systemctl', action, UNIT)


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f'Expected a regular file: {path}. Existing data retained.')
    return path.read_bytes()


def directory(path):
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError(f'Expected a real directory: {path}. Existing data retained.')


def public_override():
    return ('[Service]\nExecStart=\nExecStart=/usr/bin/python3 '
            f'{BASE}/kit/manage.py run --work {BASE}/world --port 4040 --public\n')


def maintenance_override():
    return ('[Service]\nExecStart=\nExecStart=/usr/bin/python3 '
            f'{BASE}/kit/manage.py run --work {BASE}/world --port 4040\n')


def connected_clients():
    # Include half-closed sessions: Mordor may still be finishing their saves.
    rows = read_command('ss', '-Htan', 'sport', '=', ':4040').splitlines()
    return [row for row in rows if row.split() and row.split()[0] not in ('LISTEN', 'TIME-WAIT', 'CLOSED')]


def wait_for_empty(timeout=2.5):
    """Let a just-closed health probe finish without ignoring real sessions."""
    deadline = time.monotonic() + timeout
    while connected_clients():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(0.1, remaining))
    return True


def require_empty():
    if not wait_for_empty():
        raise RuntimeError('Players or login sessions are connected. Save and quit, then retry; no restart is allowed.')


def check_greeting(*, public):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', 4040), timeout=2) as connection:
                connection.settimeout(2)
                data = b''
                while b'Please enter name:' not in data and len(data) < 16384:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                if b'Mordor v3.00' in data and b'Please enter name:' in data:
                    bindings = read_command('ss', '-Hlnt4', 'sport', '=', ':4040')
                    expected = '0.0.0.0:4040' if public else '127.0.0.1:4040'
                    if expected in bindings or (public and '*:4040' in bindings):
                        return
        except OSError:
            pass
        time.sleep(0.2)
    raise RuntimeError('The expected Mordor login and listener were not verified.')


def verify_manifest(root, expected, *, allowed=None, skip_objects=False):
    directory(root)
    found = set()
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise RuntimeError(f'Linked or special file found: {path}')
        if stat.S_ISDIR(mode):
            continue
        name = path.relative_to(root).as_posix()
        if skip_objects and (name.endswith('.o') or name == 'frp.new'):
            continue
        hashes = {expected[name]} if name in expected else set()
        hashes.update((allowed or {}).get(name, []))
        if not hashes or digest(path.read_bytes()) not in hashes:
            raise RuntimeError(f'Local source changes or unexpected files found: {path}. Nothing will be overwritten.')
        found.add(name)
    if found != set(expected):
        raise RuntimeError(f'Required source files are missing from {root}.')


def expected_after(data):
    kit = dict(data['kit_baseline'])
    kit.update({name: digest(content) for name, content in data['engine'].items()})
    world = dict(data['world_baseline'])
    world.update({name: digest(content) for name, content in data['world_updates'].items()})
    return kit, world


def verify_world(expected):
    source = {name.removeprefix('src_3.00/'): sha for name, sha in expected.items() if name.startswith('src_3.00/')}
    verify_manifest(BASE / 'world/src_3.00', source, skip_objects=True)
    directory(BASE / 'world/help')
    for name, sha in expected.items():
        if name.startswith('help/') and digest(regular(BASE / 'world' / name)) != sha:
            raise RuntimeError(f'Local help edits found: {name}. Nothing will be overwritten.')


def inspect_update_record(data):
    """Accept only the exact completed predecessor, this update or its rollback."""
    predecessor = data.get('predecessor_sha256')
    if not RECORD.exists() and not RECORD.is_symlink():
        if predecessor:
            raise RuntimeError('This package requires the previously completed native update; its record is missing.')
        return False
    record = json.loads(regular(RECORD))
    own = record.get('payload_sha256') == PAYLOAD_SHA256
    prior = predecessor and record.get('payload_sha256') == predecessor and record.get('status') == 'complete'
    if not prior and not (own and record.get('status') in ('complete', 'rolled-back')):
        raise RuntimeError('A different or unfinished update exists. Preserve its backup and inspect it first.')
    if prior or record.get('status') == 'complete' or predecessor:
        if digest(regular(BASE / 'world/src_3.00/frp.new')) != record.get('binary_sha256'):
            raise RuntimeError('The installed binary differs from its update record; no update will be applied.')
    return bool(own and record['status'] == 'complete')


def preflight(data):
    if os.geteuid() != 0:
        raise RuntimeError('Run this updater in the Linode root console.')
    release = platform.freedesktop_os_release()
    if platform.machine() != 'x86_64' or release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04':
        raise RuntimeError('This updater requires Ubuntu 24.04 x86_64.')
    addresses = read_command('ip', '-4', '-o', 'addr', 'show').split()
    if not any(value.split('/')[0] == TARGET_IP for value in addresses):
        raise RuntimeError(f'This is not the expected Linode {TARGET_IP}.')
    for path in (BASE, BASE / 'world', BASE / 'kit', CONFIG, SYSTEMD):
        directory(path)
    config = json.loads(regular(CONFIG / 'install.json'))
    if config != {'port': 4040, 'admin': 'Realmkeeper', 'kit_sha256': LEGACY_SHA}:
        raise RuntimeError('This updater targets the original recovered installation; its metadata differs.')
    metadata = json.loads(regular(BASE / 'world/.hollowdeep.json'))
    for key, value in {'format': 1, 'admin': 'Realmkeeper', 'archive_sha256': UPSTREAM_SHA,
                       'bits': 32, 'compatibility_revision': 2}.items():
        if metadata.get(key) != value:
            raise RuntimeError('The world metadata differs from the supported installation.')
    if regular(UNIT_FILE).decode() != data['unit_text']:
        raise RuntimeError('The service has local edits. Keep it intact and review the update manually.')
    if read_command('systemctl', 'show', UNIT, '--property=FragmentPath', '--value') != str(UNIT_FILE):
        raise RuntimeError('Unexpected service definition.')
    overrides = read_command('systemctl', 'show', UNIT, '--property=DropInPaths', '--value').split()
    public = PUBLIC.exists()
    if DROPINS.is_symlink() or MAINTENANCE.exists() or MAINTENANCE.is_symlink():
        raise RuntimeError('An existing maintenance override needs review; no service changes made.')
    if overrides != ([str(PUBLIC)] if public else []):
        raise RuntimeError('Unexpected service overrides; no service changes made.')
    if public and regular(PUBLIC).decode() != public_override():
        raise RuntimeError('The public service override has local edits.')
    if DROPINS.exists() and any(path != PUBLIC for path in DROPINS.iterdir()):
        raise RuntimeError('Unexpected files in the service override directory.')
    if read_command('systemctl', 'is-active', UNIT) != 'active':
        raise RuntimeError('The game service must be healthy before an update.')
    account = pwd.getpwnam('hollowdeep')
    if account.pw_uid == 0 or account.pw_dir != str(BASE) or account.pw_shell != '/usr/sbin/nologin':
        raise RuntimeError('The dedicated game account differs from the installer.')
    if (BASE / 'world').stat().st_uid != account.pw_uid:
        raise RuntimeError('The world has an unexpected owner.')
    if regular(BASE / 'gcc32') != b'#!/bin/sh\nexec /usr/bin/gcc -m32 "$@"\n':
        raise RuntimeError('Unexpected compiler wrapper.')
    if regular(BASE / 'world/src_3.00/frp.new')[:5] != b'\x7fELF\x01':
        raise RuntimeError('The running world has no regular ELF32 game binary.')
    pid = int(read_command('systemctl', 'show', UNIT, '--property=MainPID', '--value'))
    if pid < 1 or not os.path.samefile(f'/proc/{pid}/exe', BASE / 'world/src_3.00/frp.new'):
        raise RuntimeError('The service is not running the expected game binary.')
    if inspect_update_record(data):
        kit, world = expected_after(data)
        verify_manifest(BASE / 'kit', kit)
        verify_world(world)
        check_greeting(public=public)
        return account, public, True
    verify_manifest(BASE / 'kit', data['kit_baseline'], allowed={} if data.get('predecessor_sha256') else {
        'tests/test_runtime.py': [data['runtime_fix_sha']]})
    verify_world(data['world_baseline'])
    for name in set(data['world_updates']) - set(data['world_baseline']):
        path = BASE / 'world' / name
        if path.exists() or path.is_symlink():
            raise RuntimeError(f'A new update file already exists locally: {path}')
    check_greeting(public=public)
    return account, public, False


def atomic_write(path, content, *, mode, uid, gid):
    directory(path.parent)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise RuntimeError(f'Refusing to replace a linked or special file: {path}')
    fd, temporary = tempfile.mkstemp(prefix='.native-update-', dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.chown(temporary, uid, gid)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_stage(data, account):
    parent = BASE / '.updates'
    if not parent.exists():
        parent.mkdir(mode=0o710)
        os.chown(parent, 0, account.pw_gid)
    directory(parent)
    if parent.stat().st_uid != 0 or parent.stat().st_mode & 0o022:
        raise RuntimeError('Unsafe update staging directory permissions.')
    stage = Path(tempfile.mkdtemp(prefix='native-', dir=parent))
    stage.chmod(0o750)
    os.chown(stage, 0, account.pw_gid)
    kit = stage / 'kit'
    for name, content in data['engine'].items():
        target = kit / name
        target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        target.write_bytes(content)
    for path in [kit, *kit.rglob('*')]:
        os.chown(path, 0, account.pw_gid)
        path.chmod(0o750 if path.is_dir() else 0o640)
    original = regular(BASE / 'kit/Mordor_3.00.tar.gz')
    if digest(original) != UPSTREAM_SHA:
        raise RuntimeError('The original archive checksum differs.')
    (kit / 'Mordor_3.00.tar.gz').write_bytes(original)
    os.chown(kit / 'Mordor_3.00.tar.gz', 0, account.pw_gid)
    (kit / 'Mordor_3.00.tar.gz').chmod(0o640)
    build = stage / 'build'
    build.mkdir(mode=0o700)
    os.chown(build, account.pw_uid, account.pw_gid)
    return stage


def test_candidate(data, stage):
    kit, world = stage / 'kit', stage / 'build/world'
    mapping = {'{kit}': str(kit), '{world}': str(world), '{source}': str(world / 'src_3.00'),
               '{cc}': str(BASE / 'gcc32'), '{archive}': str(kit / 'Mordor_3.00.tar.gz')}
    def execute(arguments):
        args = []
        for argument in arguments:
            for marker, value in mapping.items():
                argument = argument.replace(marker, value)
            args.append(argument)
        subprocess.run(['runuser', '-u', 'hollowdeep', '--', 'env', '--chdir=' + str(stage / 'build'),
                        'PYTHONDONTWRITEBYTECODE=1', 'CC=' + str(BASE / 'gcc32'), *args], check=True)
    execute(['/usr/bin/python3', '{kit}/manage.py', 'prepare', '--archive', '{archive}',
             '--destination', '{world}', '--admin', 'Realmkeeper'])
    execute(['/usr/bin/python3', '{kit}/manage.py', 'build', '--work', '{world}', '--cc', '{cc}'])
    for arguments in data['tests']:
        execute(arguments)
    candidate = regular(world / 'src_3.00/frp.new')
    if candidate[:5] != b'\x7fELF\x01':
        raise RuntimeError('The tested candidate is not an ELF32 executable.')
    expected = dict(data['world_baseline'])
    expected.update({name: digest(content) for name, content in data['world_updates'].items()})
    for name, sha in expected.items():
        if digest(regular(world / name)) != sha:
            raise RuntimeError(f'Tested source differs from the reviewed update: {name}')
    # Hold the verified binary in a root-only file before the activation phase.
    frozen = stage / 'candidate'
    frozen.write_bytes(candidate)
    frozen.chmod(0o600)
    return candidate


def write_record(stage, status, binary=None):
    record = {'payload_sha256': PAYLOAD_SHA256, 'status': status, 'backup_directory': str(stage / 'backup')}
    if binary is not None:
        record['binary_sha256'] = digest(binary)
    atomic_write(RECORD, (json.dumps(record, indent=2) + '\n').encode(), mode=0o600, uid=0, gid=0)


def changed_targets(data, candidate):
    result = {BASE / 'kit' / name: content for name, content in data['engine'].items()}
    result.update({BASE / 'world' / name: content for name, content in data['world_updates'].items()})
    result[BASE / 'world/src_3.00/frp.new'] = candidate
    return {path: content for path, content in result.items() if not path.exists() or regular(path) != content}


def back_up(stage, targets):
    backup = stage / 'backup'
    backup.mkdir(mode=0o700)
    if RECORD.exists() or RECORD.is_symlink():
        previous = backup / 'previous-native-update.json'
        previous.write_bytes(regular(RECORD))
        previous.chmod(0o600)
    # The stopped world is consistent; this archive remains private on the host.
    with tarfile.open(backup / 'world.tar.gz', 'w:gz', dereference=False) as archive:
        archive.add(BASE / 'world', arcname='world')
    (backup / 'world.tar.gz').chmod(0o600)
    originals = {}
    for index, path in enumerate(targets):
        if path.exists():
            content = regular(path)
            st = path.stat()
            saved = backup / f'file-{index}'
            saved.write_bytes(content)
            saved.chmod(0o600)
            originals[str(path)] = {'file': saved.name, 'mode': stat.S_IMODE(st.st_mode),
                                    'uid': st.st_uid, 'gid': st.st_gid, 'sha256': digest(content)}
        else:
            originals[str(path)] = None
    (backup / 'files.json').write_text(json.dumps(originals, indent=2) + '\n')
    (backup / 'files.json').chmod(0o600)
    return originals


def restore_files(stage, originals):
    for name, metadata in originals.items():
        path = Path(name)
        if metadata is None:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise RuntimeError(f'Rollback found a changed file type: {path}')
            path.unlink(missing_ok=True)
        else:
            content = regular(stage / 'backup' / metadata['file'])
            if digest(content) != metadata['sha256']:
                raise RuntimeError('A backup checksum differs; automatic rollback stopped.')
            atomic_write(path, content, mode=metadata['mode'], uid=metadata['uid'], gid=metadata['gid'])


def remove_maintenance():
    if MAINTENANCE.exists():
        if regular(MAINTENANCE).decode() != maintenance_override():
            raise RuntimeError('The maintenance override was edited; it will be preserved.')
        MAINTENANCE.unlink()
    read_command('systemctl', 'daemon-reload')


def activate(data, stage, candidate, account, public):
    require_empty()
    original_binary = regular(BASE / 'world/src_3.00/frp.new')
    if not DROPINS.exists():
        DROPINS.mkdir(mode=0o755)
    directory(DROPINS)
    if MAINTENANCE.exists() or MAINTENANCE.is_symlink():
        raise RuntimeError('A maintenance override already exists; no restart performed.')
    originals = None
    stopped = False
    owned_override = False
    try:
        atomic_write(MAINTENANCE, maintenance_override().encode(), mode=0o644, uid=0, gid=0)
        owned_override = True
        read_command('systemctl', 'daemon-reload')
        require_empty()
        service('stop')
        stopped = True
        targets = changed_targets(data, candidate)
        originals = back_up(stage, targets)
        write_record(stage, 'installing', candidate)
        for path, content in targets.items():
            if not path.parent.exists():
                path.parent.mkdir(parents=True, mode=0o755)
            is_world = path.is_relative_to(BASE / 'world')
            atomic_write(path, content, mode=0o700 if path.name == 'frp.new' else 0o644,
                         uid=account.pw_uid if is_world else 0, gid=account.pw_gid if is_world else 0)
        service('reset-failed')
        service('start')
        stopped = False
        check_greeting(public=False)
        # The maintenance bind prevented new public sessions while validating.
        require_empty()
        service('stop')
        stopped = True
        remove_maintenance()
        owned_override = False
        service('reset-failed')
        service('start')
        stopped = False
        check_greeting(public=public)
        write_record(stage, 'complete', candidate)
    except BaseException as failure:
        if originals is None and not stopped:
            if owned_override:
                remove_maintenance()
            raise
        # Never terminate someone who connected during final public verification.
        if not wait_for_empty():
            write_record(stage, 'needs-review', candidate)
            raise RuntimeError(f'Update needs review: {failure}. Clients are connected, so no rollback restart was attempted. Backup: {stage / "backup"}') from failure
        try:
            if not stopped:
                service('stop')
            if originals is not None:
                restore_files(stage, originals)
            if owned_override or MAINTENANCE.exists():
                remove_maintenance()
            service('reset-failed')
            service('start')
            check_greeting(public=public)
            write_record(stage, 'rolled-back', original_binary)
        except BaseException as rollback_error:
            write_record(stage, 'needs-review', candidate)
            raise RuntimeError(f'Update failed ({failure}); rollback requires review ({rollback_error}). Backup: {stage / "backup"}') from failure
        raise RuntimeError(f'Update failed; original game files restored and login verified. Reason: {failure}') from failure


def main():
    data = decode_payload(PAYLOAD_BASE64, PAYLOAD_SHA256)
    account, public, installed = preflight(data)
    if installed:
        print('This native update is already installed; the game was not restarted.')
        return
    lock_path = CONFIG / 'native-update.lock'
    if lock_path.is_symlink():
        raise RuntimeError('Unexpected update lock symlink.')
    with lock_path.open('a') as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_empty()
        stage = create_stage(data, account)
        print('Building and testing a separate candidate; the live world is unchanged.', flush=True)
        candidate = test_candidate(data, stage)
        # The build takes time: recheck every original file and service guard.
        account, public, installed = preflight(data)
        if installed:
            return
        activate(data, stage, candidate, account, public)
        print(f'Native update installed and login verified. Private backup: {stage / "backup"}', flush=True)
        print('Existing player, room, object, and chronicle data retained. Service access settings retained.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        print(f'Native update stopped: {error}', file=sys.stderr)
        print('Keep the output and any backup files for diagnosis. Do not rerun a fresh installer.', file=sys.stderr)
        sys.exit(1)
