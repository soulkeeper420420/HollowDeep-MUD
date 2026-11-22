#!/usr/bin/env python3
"""Round79X: stage only private mount action backend in disposable ELF32 source.

Strictly no global command registration, native movement interception, stable
world edit, or production operation. Input must be verified Round79W source.
"""
from pathlib import Path
import argparse
import os
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE_PREFIX = 'hd-army-game-round79mount-'
TARGET_PREFIX = 'hd-army-game-round79actions-'
ADDED = ('hd79_mount_actions.h', 'hd79_mount_actions.c',
         'hd79_mount_action_store.h', 'hd79_mount_action_store.c')
REQUIRED = ('frp.new', 'Makefile', 'hd_player_store.c',
            'hd79_mount_store.h', 'hd79_mount_store.inc',
            'hd79_mount_wire.c', 'hd79_mount_roster.c',
            'treasure_receipt.c', 'global.c', 'wilderness.c')
GATE = ('ifeq ($(MOUNT_STORE_PLAYTEST),1)\n'
        'CFLAGS += -DHD79_MOUNT_STORE_PLAYTEST\n'
        'OBJECTS += hd_mount_travel.o hd79_mount_roster.o hd79_mount_wire.o\n'
        'endif\n')
EXTENSION = ('# Round79X: backend only. No native command registration.\n'
             'ifeq ($(MOUNT_ACTION_PLAYTEST),1)\n'
             'CFLAGS += -DHD79_MOUNT_ACTION_PLAYTEST\n'
             'OBJECTS += hd79_mount_actions.o hd79_mount_action_store.o\n'
             'endif\n')

def private(root, prefix, existing):
    root = Path(root)
    if (root.name != 'src' or root.parent.parent != Path('/tmp') or
            not root.parent.name.startswith(prefix) or
            root.is_symlink() or root.parent.is_symlink()):
        raise ValueError('Only disposable /tmp/'+prefix+'*/src allowed')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination already exists or parent missing')
        return root
    if not root.is_dir() or root.resolve(strict=True) != root.absolute():
        raise ValueError('Source must be canonical private directory')
    for name in REQUIRED:
        file = root / name
        if not file.is_file() or file.is_symlink():
            raise ValueError('Private source missing or unsafe: '+name)
    with (root / 'frp.new').open('rb') as fd:
        if fd.read(5) != b'\x7fELF\x01':
            raise ValueError('Native private source is not ELF32')
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            if (Path(base) / name).is_symlink():
                raise ValueError('Native private symlink denied')
    if any((root / name).exists() for name in ADDED):
        raise ValueError('Round79X sources already staged')
    return root

def stage(source, target):
    source = private(source, SOURCE_PREFIX, True)
    target = private(target, TARGET_PREFIX, False)
    makefile = (source / 'Makefile').read_text(encoding='latin-1')
    if makefile.count(GATE) != 1:
        raise ValueError('Round79W exact make gate drift')
    if 'MOUNT_ACTION_PLAYTEST' in makefile:
        raise ValueError('Round79X gate already installed')
    for name in ADDED:
        file = HERE / name
        if not file.is_file() or file.is_symlink():
            raise ValueError('Bundle source missing or unsafe: '+name)
    original = (source/'Makefile').read_bytes()
    shutil.copytree(source, target, symlinks=False)
    try:
        text = makefile.replace(GATE, GATE+EXTENSION, 1)
        (target/'Makefile').write_text(text, encoding='latin-1')
        for name in ADDED:
            shutil.copyfile(HERE/name, target/name)
        if (source/'Makefile').read_bytes() != original:
            raise ValueError('Private source changed during staging')
        if ((target/'global.c').read_bytes() !=
                (source/'global.c').read_bytes() or
            (target/'wilderness.c').read_bytes() !=
                (source/'wilderness.c').read_bytes()):
            raise ValueError('Gameplay dispatch or wilderness changed')
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_round79w_source', type=Path)
    parser.add_argument('new_round79x_source', type=Path)
    args = parser.parse_args()
    try:
        target = stage(args.accepted_round79w_source, args.new_round79x_source)
    except (ValueError, OSError) as e:
        print('ROUND79X: PRIVATE STAGING REFUSED:', e, file=sys.stderr)
        return 1
    print('ROUND79X: PRIVATE MOUNT ACTION BACKEND STAGED:', target)
    print('NATIVE COMMAND DISPATCH / VERIFIED STABLE ROOMS: NOT YET INSTALLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__ == '__main__':
    sys.exit(main())
