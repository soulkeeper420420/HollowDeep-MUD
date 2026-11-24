#!/usr/bin/env python3
"""Stage unexposed native R6A authenticated #83 action preflight in disposable ELF32 tree."""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79addeath-'
DEST_PREFIX='hd-army-game-round79adauth-'
FLAG='MOUNT_AD_AUTH_ACTION'
ADD=('hd79_ad_authenticated_action.c','hd79_ad_authenticated_action.h')
NEEDED=('frp.new','Makefile','room.c','creature.c','hd_player_store.c',
        'global.c','hd79_ad_four_store.h','hd79_ad_four_store.inc',
        'hd79_ad_death_receipt.c','hd79_ad_combat_death.c',
        'hd79_ad_private_transitions.c','hd79_mount_presence.c',
        'hd79_stable_registry.c','hd79_mount_world_identity.c',
        'hd79_mount_command.c','hd79_ad_private_fleet.c','wilderness.c')
ANCHOR='OBJECTS += hd79_ad_combat_death.o\nendif\n'

def private(root,prefix,existing):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.resolve(strict=False)!=root.absolute()):
        raise ValueError('Disposable /tmp/'+prefix+'*/src required')
    if existing:
        if not root.is_dir():raise ValueError('Native R4 source is absent')
        for name in NEEDED:
            entry=root/name
            if not entry.is_file() or entry.is_symlink():
                raise ValueError('Missing/symlinked R4 input '+name)
        with (root/'frp.new').open('rb') as stream:
            if stream.read(5)!=b'\x7fELF\x01':
                raise ValueError('Private ELF32 source required')
        for parent,dirs,files in os.walk(root,followlinks=False):
            if any((Path(parent)/name).is_symlink() for name in dirs+files):
                raise ValueError('Input contains symlink')
        if any((root/name).exists() for name in ADD):
            raise ValueError('R6A already installed')
    elif root.exists() or not root.parent.is_dir():
        raise ValueError('Fresh private destination required')
    return root

def patch_make(original):
    if (original.count(ANCHOR)!=1 or FLAG in original or
        'MOUNT_AD_COMBAT_DEATH' not in original or
        'HD79_AD_FOUR_STORE_PLAYTEST' not in original or
        'HD79_AD_SOCKET_TESTING' in original):
        raise ValueError('Untrusted native Makefile, test-only fixture or source drift')
    block=(
        '# R6A authenticated four-record read-only native action planner.\n'
        'ifeq ($(MOUNT_AD_AUTH_ACTION),1)\n'
        'ifneq ($(MOUNT_AD_COMBAT_DEATH),1)\n'
        '$(error MOUNT_AD_AUTH_ACTION requires MOUNT_AD_COMBAT_DEATH=1)\n'
        'endif\n'
        'CFLAGS += -DHD79_AD_AUTH_ACTION_PLAYTEST\n'
        'OBJECTS += hd79_ad_authenticated_action.o\n'
        'endif\n')
    result=original.replace(ANCHOR,ANCHOR+block,1)
    if (result.index('OBJECTS += hd79_ad_authenticated_action.o')>=
            result.index('frp.new:')):
        raise ValueError('R6A object declared after ELF32 dependency')
    return result

def stage(source,target):
    source=private(source,SOURCE_PREFIX,True)
    target=private(target,DEST_PREFIX,False)
    updated=patch_make((source/'Makefile').read_text(encoding='latin-1'))
    if 'adfixture' in (source/'global.c').read_text(encoding='latin-1'):
        raise ValueError('Test-only native command fixture cannot be a baseline')
    for name in ADD:
        file=HERE/name
        if not file.is_file() or file.is_symlink():
            raise ValueError('Missing or symlinked reviewed R6A source '+name)
    originals={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,target,symlinks=False)
    try:
        (target/'Makefile').write_text(updated,encoding='latin-1')
        for name in ADD:shutil.copyfile(HERE/name,target/name)
        for name,blob in originals.items():
            if (source/name).read_bytes()!=blob or (
                name!='Makefile' and (target/name).read_bytes()!=blob):
                raise ValueError('Prior validated native source changed '+name)
        for name in ('hd_player_store.c','global.c','room.c','creature.c',
                     'wilderness.c','hd79_ad_four_store.inc',
                     'hd79_ad_private_fleet.c','hd79_mount_command.c'):
            if (source/name).read_bytes()!=(target/name).read_bytes():
                raise ValueError('Native save/command/gameplay mutation '+name)
    except BaseException:
        shutil.rmtree(target)
        raise
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_r4_source',type=Path)
    parser.add_argument('new_private_r6a_source',type=Path)
    args=parser.parse_args()
    try:out=stage(args.private_r4_source,args.new_private_r6a_source)
    except (ValueError,OSError) as error:
        print('ROUND79AD R6A STAGING REFUSED:',error,file=sys.stderr)
        return 1
    print('ROUND79AD R6A PRIVATE AUTHENTICATED FOUR-RECEIPT ACTION GATE STAGED:',out)
    print('NATIVE COMMAND/SAVE COMMIT/MOUNT RESTORE/TRAVEL: DISABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
