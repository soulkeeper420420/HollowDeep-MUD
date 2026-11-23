#!/usr/bin/env python3
"""Round79AD R2: stage unexposed death-receipt and native preflight privately.
No native command/room/player-save/death lifecycle function is modified.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79adfleet-'
DEST_PREFIX='hd-army-game-round79adgate-'
ADD=('hd79_ad_death_receipt.c','hd79_ad_death_receipt.h',
     'hd79_ad_verified_action.c','hd79_ad_verified_action.h')
NEEDED=('frp.new','Makefile','hd79_ad_private_fleet.c',
        'hd79_ad_private_transitions.c','hd79_ad_private_transitions.h',
        'hd79_mount_world_identity.c','hd79_mount_presence_store.inc',
        'hd79_mount_presence_store.h','hd79_mount_roster.c',
        'hd79_mount_presence.c','hd79_stable_registry.c','room.c',
        'files1.c','hd_player_store.c','hd79_mount_command.c','wilderness.c')
ANCHOR='OBJECTS += hd79_ad_private_transitions.o\nendif\n'
FLAG='MOUNT_AD_DEATH_GATE'

def private(path,prefix,existing):
    path=Path(path)
    if (path.name!='src' or path.parent.parent!=Path('/tmp') or
        not path.parent.name.startswith(prefix) or
        path.is_symlink() or path.parent.is_symlink() or
        path.resolve(strict=False)!=path.absolute()):
        raise ValueError('Requires disposable /tmp/'+prefix+'*/src')
    if existing:
        if not path.is_dir():raise ValueError('Missing private ELF32 source')
        for name in NEEDED:
            file=path/name
            if not file.is_file() or file.is_symlink():
                raise ValueError('Missing/symlink private source: '+name)
        with (path/'frp.new').open('rb') as stream:
            if stream.read(5)!=b'\x7fELF\x01':
                raise ValueError('Accepted private ELF32 engine required')
        for root,dirs,files in os.walk(path,followlinks=False):
            if any((Path(root)/n).is_symlink() for n in dirs+files):
                raise ValueError('Symlink inside private source')
        for name in ADD:
            if (path/name).exists():
                raise ValueError('New death gate already present')
    elif path.exists() or not path.parent.is_dir():
        raise ValueError('Fresh private destination required')
    return path

def patch_make(text):
    if (text.count(ANCHOR)!=1 or FLAG in text or
        'MOUNT_AD_PRIVATE_FLEET' not in text or
        'MOUNT_TRUSTED_SPAWN_PLAYTEST' not in text):
        raise ValueError('Native AD fleet Makefile drift')
    addition=(
        '# Round79AD R2: unexposed death-wire/action-precheck only.\n'
        'ifeq ($(MOUNT_AD_DEATH_GATE),1)\n'
        'ifneq ($(MOUNT_AD_PRIVATE_FLEET),1)\n'
        '$(error MOUNT_AD_DEATH_GATE requires MOUNT_AD_PRIVATE_FLEET=1)\n'
        'endif\n'
        'CFLAGS += -DHD79_AD_DEATH_GATE\n'
        'OBJECTS += hd79_ad_death_receipt.o\n'
        'OBJECTS += hd79_ad_verified_action.o\n'
        'endif\n')
    result=text.replace(ANCHOR,ANCHOR+addition,1)
    target=result.find('frp.new:')
    if target<0 or any(result.index('OBJECTS += '+name+'.o')>=target for name in
                       ('hd79_ad_death_receipt','hd79_ad_verified_action')):
        raise ValueError('New native objects not linked before frp.new')
    return result

def stage(source,dest):
    source=private(source,SOURCE_PREFIX,True)
    dest=private(dest,DEST_PREFIX,False)
    make=patch_make((source/'Makefile').read_text(encoding='latin-1'))
    for name in ADD:
        path=HERE/name
        if not path.is_file() or path.is_symlink():
            raise ValueError('Missing/symlink tested source '+name)
    snapshot={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/'Makefile').write_text(make,encoding='latin-1')
        for name in ADD:shutil.copyfile(HERE/name,dest/name)
        for name,original in snapshot.items():
            if (source/name).read_bytes()!=original or (
                name!='Makefile' and (dest/name).read_bytes()!=original):
                raise ValueError('Existing native source changed: '+name)
        for name in ('room.c','files1.c','hd_player_store.c',
                     'hd79_mount_command.c','wilderness.c'):
            if (dest/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError('Gameplay/lifecycle source changed: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('dest',type=Path)
    args=parser.parse_args()
    try:out=stage(args.source,args.dest)
    except (OSError,ValueError) as error:
        print('ROUND79AD R2: PRIVATE STAGING REFUSED:',error,file=sys.stderr)
        return 1
    print('ROUND79AD R2: PRIVATE UNEXPOSED DEATH RECEIPT + ACTION GATE STAGED:',out)
    print('NO PLAYER SAVE #83 WRITER / NO COMMAND / NO DEATH HOOK / NO LOGIN RESTORE')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
