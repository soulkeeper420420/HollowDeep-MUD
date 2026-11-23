#!/usr/bin/env python3
"""R79AD R3: stage private ELF32 four-receipt writer; never touch live world.

Only disposable hd_player_store.c, Makefile, old mount writer wrappers and new
native store headers/includes change. All other private game sources preserved.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79adgate-'
DEST_PREFIX='hd-army-game-round79adfour-'
ADD=('hd79_ad_four_store.h','hd79_ad_four_store.inc')
NEEDED=('frp.new','Makefile','hd_player_store.c',
        'hd79_mount_presence_store.inc','hd79_mount_store.inc',
        'hd79_ad_death_receipt.c','hd79_ad_death_receipt.h',
        'hd79_ad_verified_action.c','room.c','files1.c',
        'hd79_mount_wire.c','hd79_mount_roster.c',
        'hd79_mount_presence.c','treasure_receipt.c',
        'atomic_player_snapshot.c')
FLAG='HD79_AD_FOUR_STORE_PLAYTEST'

def change_once(body,old,new,label):
    if body.count(old)!=1:
        raise ValueError('Refused source anchor drift: '+label)
    return body.replace(old,new,1)

def private(path,prefix,exists):
    path=Path(path)
    if (path.name!='src' or path.parent.parent!=Path('/tmp') or
        not path.parent.name.startswith(prefix) or
        path.is_symlink() or path.parent.is_symlink() or
        path.resolve(strict=False)!=path.absolute()):
        raise ValueError('Expected /tmp/'+prefix+'*/src')
    if exists:
        if not path.is_dir():raise ValueError('Private source unavailable')
        for name in NEEDED:
            p=path/name
            if not p.is_file() or p.is_symlink():
                raise ValueError('Missing/symlink native source '+name)
        with (path/'frp.new').open('rb') as handle:
            if handle.read(5)!=b'\x7fELF\x01':
                raise ValueError('Expected accepted private ELF32 binary')
        for parent,dirs,files in os.walk(path,followlinks=False):
            if any((Path(parent)/n).is_symlink() for n in dirs+files):
                raise ValueError('Symlink inside native private source')
        if any((path/n).exists() for n in ADD):
            raise ValueError('Four-store already staged')
    elif path.exists() or not path.parent.is_dir():
        raise ValueError('Destination must be fresh private directory')
    return path

def patch(source):
    player=(source/'hd_player_store.c').read_text(encoding='latin-1')
    presence=(source/'hd79_mount_presence_store.inc').read_text(encoding='latin-1')
    make=(source/'Makefile').read_text(encoding='latin-1')
    if FLAG in player or FLAG in presence or 'MOUNT_AD_FOUR_STORE' in make:
        raise ValueError('Four-receipt store already installed')
    if 'HD79_MOUNT_PRESENCE_STORE_PLAYTEST' not in player or \
       'MOUNT_AD_DEATH_GATE' not in make:
        raise ValueError('Required trusted R2 native baseline absent')
    player=change_once(player,'#include "hd79_mount_presence_store.h"',
        '#include "hd79_mount_presence_store.h"\n'
        '#ifdef HD79_AD_FOUR_STORE_PLAYTEST\n'
        '#include "hd79_ad_four_store.h"\n#endif',
        'receipt header definition')
    player=change_once(player,
        '        || !strcmp(claim, HD79_MOUNT_PRESENCE_ID)\n'
        '#endif',
        '        || !strcmp(claim, HD79_MOUNT_PRESENCE_ID)\n'
        '#endif\n'
        '#ifdef HD79_AD_FOUR_STORE_PLAYTEST\n'
        '        || !strcmp(claim, HD79_AD_DEATH_RECEIPT_ID)\n'
        '#endif',
        'loot-claim reservation for receipt 83')
    player=change_once(player,
        '#include "hd79_mount_presence_store.inc"',
        '#include "hd79_mount_presence_store.inc"\n'
        '#ifdef HD79_AD_FOUR_STORE_PLAYTEST\n'
        '#include "hd79_ad_four_store.inc"\n'
        '#endif',
        'native locked four-way include')
    # The old three-way writer MUST NOT remain enabled even if #83 is absent:
    # otherwise a legacy command could create records without death history.
    presence=change_once(presence,
        '    return hd79_presence_transaction(name,NULL,NULL,NULL,NULL,\n'
        '                                     roster,position);',
        '#ifdef HD79_AD_FOUR_STORE_PLAYTEST\n'
        '    (void)name; (void)roster; (void)position;\n'
        '    return HD79_PRESENCE_STORE_FAILURE;\n'
        '#else\n'
        '    return hd79_presence_transaction(name,NULL,NULL,NULL,NULL,\n'
        '                                     roster,position);\n'
        '#endif',
        'disable legacy triple initializer')
    presence=change_once(presence,
        '    return hd79_presence_transaction(name,expected,expected_position,\n'
        '                                     desired,desired_position,\n'
        '                                     out_roster,out_position);',
        '#ifdef HD79_AD_FOUR_STORE_PLAYTEST\n'
        '    (void)name; (void)expected; (void)expected_position;\n'
        '    (void)desired; (void)desired_position;\n'
        '    (void)out_roster; (void)out_position;\n'
        '    return HD79_PRESENCE_STORE_FAILURE;\n'
        '#else\n'
        '    return hd79_presence_transaction(name,expected,expected_position,\n'
        '                                     desired,desired_position,\n'
        '                                     out_roster,out_position);\n'
        '#endif',
        'disable legacy triple CAS')
    make=change_once(make,
        'OBJECTS += hd79_ad_verified_action.o\nendif\n',
        'OBJECTS += hd79_ad_verified_action.o\nendif\n'
        '# Round79AD R3: single native 80/81/82/83 atomic writer only.\n'
        'ifeq ($(MOUNT_AD_FOUR_STORE),1)\n'
        'ifneq ($(MOUNT_AD_DEATH_GATE),1)\n'
        '$(error MOUNT_AD_FOUR_STORE requires MOUNT_AD_DEATH_GATE=1)\n'
        'endif\n'
        'CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST\n'
        'endif\n',
        'private Makefile gate')
    if make.index('CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST')>=make.index('frp.new:'):
        raise ValueError('Make gate linked after native frp.new target')
    return {'hd_player_store.c':player,
            'hd79_mount_presence_store.inc':presence,
            'Makefile':make}

def stage(source,dest):
    source=private(source,SOURCE_PREFIX,True)
    dest=private(dest,DEST_PREFIX,False)
    updates=patch(source)
    for name in ADD:
        file=HERE/name
        if not file.is_file() or file.is_symlink():
            raise ValueError('Missing/symlink new four-store source '+name)
    originals={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        for name,text in updates.items():
            (dest/name).write_text(text,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        for name,data in originals.items():
            if (source/name).read_bytes()!=data:
                raise ValueError('Accepted private source changed: '+name)
            if name not in updates and (dest/name).read_bytes()!=data:
                raise ValueError('Native boundary unexpectedly changed: '+name)
        for name in ('room.c','files1.c','wilderness.c',
                     'hd79_mount_command.c','hd79_ad_private_fleet.c'):
            if (source/name).read_bytes()!=(dest/name).read_bytes():
                raise ValueError('World/command/lifecycle boundary modified: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_r2_source',type=Path)
    p.add_argument('fresh_r3_source',type=Path)
    a=p.parse_args()
    try: new=stage(a.accepted_r2_source,a.fresh_r3_source)
    except (OSError,ValueError) as e:
        print('ROUND79AD R3: PRIVATE STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79AD R3: PRIVATE FOUR-RECEIPT NATIVE STORE STAGED:',new)
    print('NO PLAYER-COMMAND/COMBAT/LOGIN/MOVE CALLERS ENABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
