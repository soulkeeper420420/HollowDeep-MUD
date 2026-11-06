#!/usr/bin/env python3
"""Template for the generated, self-contained Lish console setup block."""
import base64
import hashlib
import io
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile
import urllib.request

TARGET_IP = '172.233.176.81'
UPSTREAM_SHA256 = '05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0'
ORIGINAL_KIT_SHA256 = '9982875dea95ffdb9f360f86eae8cbd9f6bcff4cf20bad0b0ca7d147786d8bd1'
PUBLISHED_KIT_SHA256 = '9982875dea95ffdb9f360f86eae8cbd9f6bcff4cf20bad0b0ca7d147786d8bd1'
ARCHIVE_URL = 'https://godwars.net/~mudbytes/files/codebases/Mordor_3.00.tar.gz'
PUBLISHED_KIT_URL = 'https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/public/workshop-files/hollowdeep-server-kit.tar.gz'
STAGE = Path('/root/hollowdeep-console')

# EMBEDDED_SOURCE
PAYLOAD_SHA256 = None
PAYLOAD_BASE64 = ''
# END_EMBEDDED_SOURCE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_source(encoded, expected_sha):
    packed = base64.b64decode(encoded)
    if digest(packed) != expected_sha:
        raise ValueError('The pasted source is incomplete or changed. No installation was attempted.')
    decoder = lzma.LZMADecompressor()
    raw = decoder.decompress(packed, max_length=2 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('Unexpected source payload size or format.')
    files = json.loads(raw)
    required = {'install-ubuntu.sh', 'enable-public.py', 'kit/manage.py', 'kit/tests/test_runtime.py'}
    if not isinstance(files, dict) or not required.issubset(files):
        raise ValueError('Source payload is missing required files.')
    for name, content in files.items():
        path = PurePosixPath(name)
        if (path.is_absolute() or '..' in path.parts or '\\' in name or
                not path.parts or not isinstance(content, str) or
                (path.parts[0] != 'kit' and name not in ('install-ubuntu.sh', 'enable-public.py', 'README.md'))):
            raise ValueError('Unexpected source payload path.')
    return files


def fetch(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'Hollowdeep-console-installer/1'})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Downloaded file is larger than expected.')
    return data


def upstream_archive():
    try:
        data = fetch(ARCHIVE_URL, 8 * 1024 * 1024)
        if digest(data) != UPSTREAM_SHA256:
            raise ValueError('Original distribution checksum mismatch.')
        return data
    except (OSError, ValueError):
        # The existing public kit is only a mirror for its unmodified original
        # archive. All executable toolkit source comes from the checked payload.
        print('Trying the verified distribution mirror…', flush=True)
        data = fetch(PUBLISHED_KIT_URL, 8 * 1024 * 1024)
        if digest(data) != PUBLISHED_KIT_SHA256:
            raise ValueError('Distribution mirror changed; refusing to install it.')
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            member = archive.getmember('hollowdeep-server-kit/Mordor_3.00.tar.gz')
            if not member.isfile() or member.size > 8 * 1024 * 1024:
                raise ValueError('Unexpected original distribution in mirror.')
            original = archive.extractfile(member).read()
        if digest(original) != UPSTREAM_SHA256:
            raise ValueError('Original distribution checksum mismatch.')
        return original


def preflight():
    if os.geteuid() != 0:
        raise RuntimeError('Run this block in the Linode root console.')
    if platform.machine() != 'x86_64':
        raise RuntimeError('This installer requires x86_64 Linux.')
    release = platform.freedesktop_os_release()
    if release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04':
        raise RuntimeError('This installer requires Ubuntu 24.04 LTS.')
    addresses = subprocess.run(['ip', '-4', '-o', 'addr', 'show'], check=True,
                               capture_output=True, text=True).stdout.split()
    if not any(address.split('/')[0] == TARGET_IP for address in addresses):
        raise RuntimeError(f'This console is not on the expected server {TARGET_IP}. No changes made.')
    for path in (STAGE, Path('/srv/hollowdeep'), Path('/etc/hollowdeep'),
                 Path('/etc/systemd/system/hollowdeep.service')):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f'{path} already exists. Keep it intact and share the installer output before retrying.')


def prepare(stage, files, original):
    if digest(original) != UPSTREAM_SHA256:
        raise ValueError('Original distribution checksum mismatch.')
    stage.mkdir(mode=0o700)
    for name, content in files.items():
        destination = stage / name
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination.write_text(content, encoding='utf-8')
        destination.chmod(0o600)
    (stage / 'kit/Mordor_3.00.tar.gz').write_bytes(original)
    bundle = stage / 'hollowdeep-server-kit.tar.gz'
    with tarfile.open(bundle, mode='w:gz') as archive:
        archive.add(stage / 'kit', arcname='hollowdeep-server-kit')
    kit_sha = digest(bundle.read_bytes())
    replacements = {
        'install-ubuntu.sh': (f'kit_sha256={ORIGINAL_KIT_SHA256}', f'kit_sha256={kit_sha}'),
        'enable-public.py': (f"KIT_SHA256 = '{ORIGINAL_KIT_SHA256}'", f"KIT_SHA256 = '{kit_sha}'"),
    }
    for filename, (before, after) in replacements.items():
        target = stage / filename
        source = target.read_text()
        if source.count(before) != 1:
            raise ValueError('Installer checksum configuration differs from the reviewed source.')
        target.write_text(source.replace(before, after, 1))
    (stage / 'source-manifest.json').write_text(json.dumps({
        'source_payload_sha256': PAYLOAD_SHA256,
        'upstream_archive_sha256': UPSTREAM_SHA256,
        'assembled_kit_sha256': kit_sha,
    }, indent=2) + '\n')
    return bundle


def main():
    preflight()
    files = decode_source(PAYLOAD_BASE64, PAYLOAD_SHA256)
    print('Fetching the checksum-pinned original Mordor distribution…', flush=True)
    bundle = prepare(STAGE, files, upstream_archive())
    print(f'Corrected kit assembled and verified in {STAGE}. Starting host tests and installation…', flush=True)
    subprocess.run(['bash', str(STAGE / 'install-ubuntu.sh'), str(bundle)], cwd=STAGE, check=True)
    print('\nNext: telnet 127.0.0.1 4040', flush=True)
    print('Create Realmkeeper, choose its password privately, then type save and quit.', flush=True)
    print(f'Afterwards: python3 {STAGE}/enable-public.py', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Installation stopped: {error}', file=sys.stderr)
        print('Keep the output and any created files for diagnosis. No public startup was requested.', file=sys.stderr)
        sys.exit(1)
