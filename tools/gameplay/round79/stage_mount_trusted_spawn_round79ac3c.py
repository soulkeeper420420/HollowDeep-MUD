#!/usr/bin/env python3
"""Round79AC3C: stage an UNEXPOSED native mount template spawner privately.

Requires accepted AC3B revocation and AC2 real identity verification. Does
not modify any live source, player file, world, command, login, or logout hook.
"""
from pathlib import Path
import argparse
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79lifecycle-'
TARGET_PREFIX='hd-army-game-round79trustedspawn-'
ADD=('hd79_mount_trusted_spawn.c','hd79_mount_trusted_spawn.h')
NEEDED=('frp.new','Makefile','room.c','files1.c','hd_player_store.c',
        'hd79_mount_world_identity.c','hd79_mount_world_identity.h',
        'hd79_mount_presence_store.h','hd79_mount_presence_store.inc',
        'hd79_mount_presence.c','hd79_mount_roster.c',
        'hd_mount_travel.c','hd_mount_travel.h','hd_wilderness_breath.h',
        'global.c','wilderness.c','command1.c','command2.c',
        'command5.c','command6.c','hd79_mount_command.c')
FLAG='MOUNT_TRUSTED_SPAWN_PLAYTEST'
ANCHOR='CFLAGS += -DHD79_MOUNT_LIFECYCLE_PLAYTEST\nendif\n'

def private(root,prefix,existing):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.resolve(strict=False)!=root.absolute()):
        raise ValueError('Disposable /tmp/'+prefix+'*/src required')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination must be new private directory')
        return root
    if not root.is_dir():
        raise ValueError('Missing accepted private source')
    for name in NEEDED:
        p=root/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing/symlink native source: '+name)
    with (root/'frp.new').open('rb') as f:
        if f.read(5)!=b'\x7fELF\x01':
            raise ValueError('Required accepted private ELF32 engine')
    for dirname,dirs,files in os.walk(root,followlinks=False):
        if any((Path(dirname)/x).is_symlink() for x in dirs+files):
            raise ValueError('Symlink inside accepted source')
    for name in ADD:
        if (root/name).exists():
            raise ValueError('Trusted spawn source already staged')
    return root

def patch_make(original):
    if (original.count(ANCHOR)!=1 or FLAG in original or
        'MOUNT_WORLD_IDENTITY_PLAYTEST' not in original or
        'OBJECTS += hd79_mount_world_identity.o' not in original):
        raise ValueError('Accepted AC3B Makefile gate drift')
    block=('# Round79AC3C: server-only native template loading; no commands.\n'
           'ifeq ($(MOUNT_TRUSTED_SPAWN_PLAYTEST),1)\n'
           'ifneq ($(MOUNT_LIFECYCLE_PLAYTEST),1)\n'
           '$(error MOUNT_TRUSTED_SPAWN_PLAYTEST requires MOUNT_LIFECYCLE_PLAYTEST=1)\n'
           'endif\n'
           'CFLAGS += -DHD79_MOUNT_TRUSTED_SPAWN_PLAYTEST\n'
           'OBJECTS += hd79_mount_trusted_spawn.o\n'
           'endif\n')
    new=original.replace(ANCHOR,ANCHOR+block,1)
    target=new.find('frp.new:')
    if target<0 or new.index('OBJECTS += hd79_mount_trusted_spawn.o')>=target:
        raise ValueError('Native object must be prerequisite before frp.new')
    return new

def stage(source,dest):
    source=private(source,SOURCE_PREFIX,True)
    dest=private(dest,TARGET_PREFIX,False)
    new_make=patch_make((source/'Makefile').read_text(encoding='latin-1'))
    for name in ADD:
        f=HERE/name
        if f.is_symlink() or not f.is_file():
            raise ValueError('Missing trusted candidate file '+name)
    originals={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/'Makefile').write_text(new_make,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        for name,blob in originals.items():
            if (source/name).read_bytes()!=blob:
                raise ValueError('Accepted private native source was modified')
            if name!='Makefile' and (dest/name).read_bytes()!=blob:
                raise ValueError('Unexpected native file mutation: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_round79ac3b_source',type=Path)
    p.add_argument('fresh_round79ac3c_source',type=Path)
    args=p.parse_args()
    try:
        target=stage(args.accepted_round79ac3b_source,args.fresh_round79ac3c_source)
    except (OSError,ValueError) as e:
        print('ROUND79AC3C: PRIVATE STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79AC3C: PRIVATE TRUSTED MOUNT SPAWNER BACKEND STAGED:',target)
    print('NO TEMPLATE IDS CONFIGURED / NO PLAYER OR LOGIN CALLERS')
    print('BOARD/STABLE/RETRIEVE/RIDDEN TRAVEL: NOT ENABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__=='__main__':
    sys.exit(main())
