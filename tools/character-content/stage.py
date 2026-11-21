#!/usr/bin/env python3
"""Stage an existing race/class edit in a new, disposable native source copy.

Never edits the source, running game, production world, or existing saves.
"""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys

from content import read
from native import native_diff

PRIVATE_ROOTS = (Path('/root/hollowdeep-dev'), Path('/tmp'))
ALLOWED_FILES = frozenset(('global.c', 'command1.c'))


def private_path(path, label, exists=False):
    path = Path(path).expanduser()
    if path.is_symlink():
        raise ValueError(f'{label} must not be a symlink')
    full = path.resolve(strict=exists)
    if not any(full != root and full.is_relative_to(root) for root in PRIVATE_ROOTS):
        raise ValueError(f'{label} must be inside /root/hollowdeep-dev or /tmp')
    return full


def inventory(root):
    """Return the exact regular-file inventory, rejecting unsafe inputs."""
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in private native source: ' + str(path))
        if path.is_file():
            if not path.is_relative_to(root):
                raise ValueError('Source traversal rejected')
            result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).digest()
        elif not path.is_dir():
            raise ValueError('Unsupported special file in source: ' + str(path))
    return result


def staged_edits(source, target, definition):
    source = private_path(source, 'Native source', exists=True)
    if not source.is_dir():
        raise ValueError('Native source must be a directory')
    target = private_path(target, 'Destination')
    if target.exists() or target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError('Destination must be fresh and separate from input')
    if not target.parent.is_dir():
        raise ValueError('Create the private destination parent first')
    if not shutil.which('patch'):
        raise ValueError('The patch utility is required')

    draft = read(Path(definition))
    patch = native_diff(source, draft)
    if not patch:
        raise ValueError('No supported native changes to stage')

    old_names = re.findall(r'^--- a/([^/\n]+)$', patch, re.M)
    new_names = re.findall(r'^\+\+\+ b/([^/\n]+)$', patch, re.M)
    if not old_names or old_names != new_names or not set(old_names) <= ALLOWED_FILES:
        raise ValueError('Unsupported native patch paths')
    changed = set(old_names)
    originals = inventory(source)
    if not originals:
        raise ValueError('Empty native source')

    shutil.copytree(source, target, symlinks=False)
    try:
        args = ['patch', '--batch', '--forward', '--fuzz=0', '--no-backup-if-mismatch', '-p1', '-d', str(target)]
        for dry in (True, False):
            command = args + (['--dry-run'] if dry else [])
            result = subprocess.run(command, input=patch, text=True,
                                    capture_output=True, timeout=30)
            if result.returncode:
                raise ValueError('Native patch rejected: ' + (result.stdout + result.stderr)[-1000:])
        if inventory(source) != originals:
            raise ValueError('Source changed while staging; discard candidate')
        actual = inventory(target)
        if set(actual) != set(originals):
            raise ValueError('Staged source file inventory changed unexpectedly')
        differences = {name for name, digest in originals.items() if actual[name] != digest}
        if differences != changed:
            raise ValueError('Unexpected staged source differences: ' + repr(sorted(differences)))
    except Exception:
        shutil.rmtree(target)
        raise
    return sorted(changed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='existing PRIVATE native source tree')
    parser.add_argument('draft', type=Path, help='edited JSON exported by native.py')
    parser.add_argument('target', type=Path, help='NEW private source directory')
    args = parser.parse_args(argv)
    try:
        files = staged_edits(args.source, args.target, args.draft)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print('DENIED:', exc, file=sys.stderr)
        return 1
    print('ROUND 78: PRIVATE NATIVE STAGING PASS')
    print('Staged source:', args.target)
    print('Modified files:', ', '.join(files))
    print('Production deployment: NONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
