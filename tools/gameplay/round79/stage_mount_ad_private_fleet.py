#!/usr/bin/env python3
"""Stage Round79AD private six-species fleet into a disposable ELF32 source.

No command dispatch, existing player-save code or native room file is edited.
No live world/service is opened for writing.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

SOURCE_PREFIX='hd-army-game-round79trustedspawn-'
DEST_PREFIX='hd-army-game-round79adfleet-'
HERE=Path(__file__).resolve().parent
ADD=('hd79_ad_private_fleet.c','hd79_ad_private_fleet.h',
     'hd79_ad_private_transitions.c','hd79_ad_private_transitions.h')
NEEDED=('frp.new','Makefile','hd79_mount_world_identity.c',
        'hd79_mount_world_identity.h','hd79_mount_presence_store.h',
        'hd79_mount_roster.c','hd79_mount_presence.c',
        'hd79_mount_trusted_spawn.c','room.c','files1.c',
        'hd_player_store.c','hd79_mount_command.c','wilderness.c')
ANCHOR='OBJECTS += hd79_mount_trusted_spawn.o\nendif\n'
FLAG='MOUNT_AD_PRIVATE_FLEET'

def private(path,prefix,existing):
    path=Path(path)
    if (path.name!='src' or path.parent.parent!=Path('/tmp') or
        not path.parent.name.startswith(prefix) or
        path.is_symlink() or path.parent.is_symlink() or
        path.resolve(strict=False)!=path.absolute()):
        raise ValueError('Disposable /tmp/'+prefix+'*/src required')
    if not existing:
        if path.exists() or not path.parent.is_dir():
            raise ValueError('New private destination required')
        return path
    if not path.is_dir():
        raise ValueError('Accepted private ELF32 source missing')
    for name in NEEDED:
        f=path/name
        if not f.is_file() or f.is_symlink():
            raise ValueError('Required native file missing or symlinked: '+name)
    with (path/'frp.new').open('rb') as f:
        if f.read(5)!=b'\x7fELF\x01':
            raise ValueError('Accepted private ELF32 binary required')
    for parent,dirs,files in os.walk(path,followlinks=False):
        if any((Path(parent)/x).is_symlink() for x in dirs+files):
            raise ValueError('Symlink found in accepted native source')
    for name in ADD:
        if (path/name).exists():
            raise ValueError('Private fleet already staged')
    return path

def patch_make(original):
    if (original.count(ANCHOR)!=1 or FLAG in original or
        'MOUNT_TRUSTED_SPAWN_PLAYTEST' not in original or
        'MOUNT_LIFECYCLE_PLAYTEST' not in original):
        raise ValueError('Accepted AC3C private Makefile gate drift')
    extra=('# Round79AD: unexposed six-species private noncombat fleet.\n'
           'ifeq ($(MOUNT_AD_PRIVATE_FLEET),1)\n'
           'ifneq ($(MOUNT_TRUSTED_SPAWN_PLAYTEST),1)\n'
           '$(error MOUNT_AD_PRIVATE_FLEET requires MOUNT_TRUSTED_SPAWN_PLAYTEST=1)\n'
           'endif\n'
           'CFLAGS += -DHD79_AD_PRIVATE_FLEET\n'
           'OBJECTS += hd79_ad_private_fleet.o\n'
           'OBJECTS += hd79_ad_private_transitions.o\n'
           'endif\n')
    new=original.replace(ANCHOR,ANCHOR+extra,1)
    target=new.find('frp.new:')
    if target<0 or new.index('OBJECTS += hd79_ad_private_fleet.o')>=target or\
       new.index('OBJECTS += hd79_ad_private_transitions.o')>=target:
        raise ValueError('Fleet object not included before ELF32 target')
    return new

def stage(source,dest):
    source=private(source,SOURCE_PREFIX,True)
    dest=private(dest,DEST_PREFIX,False)
    patched=patch_make((source/'Makefile').read_text(encoding='latin-1'))
    for name in ADD:
        p=HERE/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('New trusted source absent/symlinked: '+name)
    originals={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/'Makefile').write_text(patched,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        for name,blob in originals.items():
            if (source/name).read_bytes()!=blob or (
                name!='Makefile' and (dest/name).read_bytes()!=blob):
                raise ValueError('Accepted source or forbidden boundary modified: '+name)
        for name in ('hd_player_store.c','hd79_mount_command.c',
                     'room.c','files1.c','wilderness.c'):
            if (dest/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError('Source gameplay boundary modified: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_ac3c_source',type=Path)
    p.add_argument('new_round79ad_source',type=Path)
    args=p.parse_args()
    try:
        dest=stage(args.accepted_ac3c_source,args.new_round79ad_source)
    except (ValueError,OSError) as err:
        print('ROUND79AD: PRIVATE STAGING REFUSED:',err,file=sys.stderr)
        return 1
    print('ROUND79AD: SIX-SPECIES PRIVATE FLEET STAGED:',dest)
    print('NO GAME COMMAND/LOGIN/SPAWN CALLS ENABLED')
    print('RECONNECT AUTO-REHYDRATION: DENIED UNTIL DURABLE MOUNT DEATH PROOF')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__=='__main__':
    sys.exit(main())
