#!/usr/bin/env python3
"""One-file launcher for the reviewed HollowDeep native update variants."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zlib

RECORD = Path('/etc/hollowdeep/native-update.json')
LEGACY = 'hollowdeep-native-update-from-legacy.py'
LIMIT = 4 * 1024 * 1024

# Generated from the reviewed release. No network download is required.
ARTIFACTS = {}
PREDECESSORS = {}
BUNDLE_SHA256 = ''
BUNDLE_BASE64 = ''


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate field in update data; keep the existing installation intact.')
        result[key] = value
    return result


def read_record(path=RECORD, owner=0):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner
                or info.st_mode & 0o022 or info.st_size > 65536):
            raise ValueError('Unexpected update record; preserve it and any backups for review.')
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('The update record is too large; preserve it for review.')
    record = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(record, dict):
        raise ValueError('Unexpected update record format; no update was started.')
    return record


def select_artifact(record):
    if record is None:
        # The selected legacy updater still verifies the exact original world,
        # installation metadata and binary/source before changing anything.
        return LEGACY
    payload, status = record.get('payload_sha256'), record.get('status')
    if not isinstance(payload, str) or not isinstance(status, str):
        raise ValueError('Incomplete update record; preserve the world and backups for review.')
    if status == 'complete' and payload in PREDECESSORS:
        return PREDECESSORS[payload]
    for name, details in ARTIFACTS.items():
        if payload == details['payload_sha256'] and status in ('complete', 'rolled-back'):
            # The original updater verifies a completed installation and reports
            # it as current, or verifies its own rollback before retrying.
            return name
    raise ValueError('Unknown or unfinished update. Keep the world and backups intact and share this message with the host.')


def unpack_bundle():
    packed = base64.b64decode(''.join(BUNDLE_BASE64.split()), validate=True)
    if hashlib.sha256(packed).hexdigest() != BUNDLE_SHA256:
        raise ValueError('This updater file is incomplete or changed. Download a fresh copy.')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, LIMIT + 1)
    if len(raw) > LIMIT or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Unexpected bundled update size or format.')
    files = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(files, dict) or set(files) != set(ARTIFACTS):
        raise ValueError('Bundled update files do not match this release.')
    for name, content in files.items():
        if (not isinstance(content, str)
                or hashlib.sha256(content.encode()).hexdigest() != ARTIFACTS[name]['sha256']):
            raise ValueError('A bundled installer checksum differs; no update was started.')
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Check the bundled files without installing or reading server state')
    args = parser.parse_args(argv)
    files = unpack_bundle()
    if args.verify:
        print('Verified all three bundled installers. No installation attempted.')
        return 0
    if os.geteuid() != 0:
        raise ValueError('Run this file in the Linode root Lish console: python3 /root/hollowdeep-update.py')
    name = select_artifact(read_record())
    print(f'Selected {name} for the installed version.', flush=True)
    print('The updater will verify this host and test a separate world before replacing the game.', flush=True)
    print('Players must save and quit. Existing world data and installation checks are retained.', flush=True)
    with tempfile.TemporaryDirectory(prefix='hollowdeep-selected-update-') as temporary:
        path = Path(temporary) / 'verified-update.py'
        path.write_text(files[name], encoding='utf-8')
        path.chmod(0o600)
        return subprocess.run([sys.executable, '-B', str(path)], check=False).returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, zlib.error) as error:
        print(f'Update stopped: {error}', file=sys.stderr)
        print('Keep the output and any backups. Do not rerun a fresh installer over your world.', file=sys.stderr)
        sys.exit(1)
