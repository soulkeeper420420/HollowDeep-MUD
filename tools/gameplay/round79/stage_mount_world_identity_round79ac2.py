#!/usr/bin/env python3
"""Stage Round79AC2 read-only native mount identity attestation privately.

Not an owned mount spawner. No command, save, world, or lifecycle hook added.
No production paths allowed. Reject symlinks or unverified Makefile structure.
"""
from pathlib import Path
import argparse
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79triplecmd-'
DEST_PREFIX='hd-army-game-round79worldproof-'
FILES=('hd79_mount_world_identity.h','hd79_mount_world_identity.c')
NEEDED=('frp.new','Makefile','global.c','mextern.h','hd79_mount_command.c',
        'hd79_mount_presence.c','hd79_mount_presence.h',
        'hd79_mount_roster.c','hd79_mount_roster.h',
        'hd79_presence_dismount_store.c','hd_player_store.c',
        'wilderness.c','room.c','command1.c','command2.c','command6.c')
MAKE_ANCHOR='OBJECTS += hd79_presence_dismount_store.o\nendif\n'


def check(root,prefix,exists):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.absolute()!=root.resolve(strict=False)):
        raise ValueError('Private /tmp/'+prefix+'*/src required')
    if not exists:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('New destination required')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Missing verified private ELF32 native source')
    for n in NEEDED:
        p=root/n
        if p.is_symlink() or not p.is_file():
            raise ValueError('Missing/symlink native '+n)
    if (root/'frp.new').read_bytes()[:5]!=b'\x7fELF\x01':
        raise ValueError('Expected accepted ELF32 game')
    for base,dirs,files in os.walk(root,followlinks=False):
        if any((Path(base)/n).is_symlink() for n in dirs+files):
            raise ValueError('Unsafe source symlink')
    if any((root/n).exists() for n in FILES):
        raise ValueError('World proof already staged')
    return root


def patch_make(source):
    m=(source/'Makefile').read_text(encoding='latin-1')
    if m.count(MAKE_ANCHOR)!=1 or 'MOUNT_TRIPLE_COMMAND_PLAYTEST' not in m or \
       'MOUNT_WORLD_IDENTITY_PLAYTEST' in m:
        raise ValueError('Accepted AC1 Makefile anchor changed')
    block=('# Round79AC2: private live-native-pointer identity (no gameplay).\n'
           'ifeq ($(MOUNT_WORLD_IDENTITY_PLAYTEST),1)\n'
           'ifneq ($(MOUNT_TRIPLE_COMMAND_PLAYTEST),1)\n'
           '$(error MOUNT_WORLD_IDENTITY_PLAYTEST requires MOUNT_TRIPLE_COMMAND_PLAYTEST)\n'
           'endif\n'
           'CFLAGS += -DHD79_MOUNT_WORLD_IDENTITY_PLAYTEST\n'
           'OBJECTS += hd79_mount_world_identity.o\n'
           'endif\n')
    result=m.replace(MAKE_ANCHOR,MAKE_ANCHOR+block,1)
    target=result.find('frp.new:')
    if target<0 or result.find('OBJECTS += hd79_mount_world_identity.o')>=target:
        raise ValueError('Native make prerequisite must precede frp.new target')
    return result


def stage(source,dest):
    source=check(source,SOURCE_PREFIX,True)
    dest=check(dest,DEST_PREFIX,False)
    new_make=patch_make(source)
    for n in FILES:
        p=HERE/n
        if p.is_symlink() or not p.is_file():
            raise ValueError('Missing candidate '+n)
    original_make=(source/'Makefile').read_bytes()
    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/'Makefile').write_text(new_make,encoding='latin-1')
        for n in FILES:
            shutil.copyfile(HERE/n,dest/n)
        if (source/'Makefile').read_bytes()!=original_make:
            raise ValueError('Source Makefile changed during staging')
        for n in ('global.c','mextern.h','room.c','command1.c','command2.c',
                  'command6.c','wilderness.c','hd79_mount_command.c',
                  'hd_player_store.c','hd79_mount_presence_store.inc',
                  'hd79_presence_dismount_store.c'):
            if (source/n).read_bytes()!=(dest/n).read_bytes():
                raise ValueError('Native gameplay/save boundary modified: '+n)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_round79ac1_source',type=Path)
    p.add_argument('new_private_round79ac2_source',type=Path)
    args=p.parse_args()
    try:
        result=stage(args.accepted_round79ac1_source,
                     args.new_private_round79ac2_source)
    except (OSError,ValueError) as e:
        print('ROUND79AC2: PRIVATE STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79AC2: READ-ONLY NATIVE MOUNT WORLD IDENTITY STAGED:',result)
    print('NO TRUSTED SPAWNER/LIFECYCLE HOOK: BOARD/STABLE/RETRIEVE DISABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0


if __name__=='__main__':
    sys.exit(main())
