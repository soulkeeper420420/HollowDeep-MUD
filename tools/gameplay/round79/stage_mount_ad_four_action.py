#!/usr/bin/env python3
"""Stage R6B unexposed native four-receipt mount action CAS in fresh ELF32 tree.

Clone the verified R6A private source; patch only its private Makefile and
hd_player_store.c include boundary. Never modify the source tree or live data.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79adauth-'
DEST_PREFIX='hd-army-game-round79adcas-'
FLAG='HD79_AD_ACTION_CAS_PLAYTEST'
ADD=('hd79_ad_four_action_store.inc','hd79_ad_four_action_store.h')
NEEDED=('frp.new','Makefile','hd_player_store.c','global.c','room.c',
        'creature.c','wilderness.c','hd79_ad_four_store.inc',
        'hd79_ad_four_store.h','hd79_ad_authenticated_action.c',
        'hd79_ad_authenticated_action.h','hd79_ad_private_transitions.c',
        'hd79_mount_world_identity.c','hd79_stable_registry.c',
        'hd79_mount_command.c','hd79_ad_private_fleet.c',
        'hd79_ad_combat_death.c')
ANCHOR='OBJECTS += hd79_ad_authenticated_action.o\nendif\n'
STORE_ANCHOR='#include "hd79_ad_four_store.inc"\n#endif'

def private(path,prefix,existing):
    path=Path(path)
    if (path.name!='src' or path.parent.parent!=Path('/tmp') or
        not path.parent.name.startswith(prefix) or path.is_symlink() or
        path.parent.is_symlink() or
        path.resolve(strict=False)!=path.absolute()):
        raise ValueError('Disposable /tmp/'+prefix+'*/src required')
    if existing:
        if not path.is_dir():raise ValueError('Native R6A source is absent')
        for name in NEEDED:
            f=path/name
            if not f.is_file() or f.is_symlink():
                raise ValueError('Missing/symlinked R6A input '+name)
        if (path/'frp.new').read_bytes()[:5]!=b'\x7fELF\x01':
            raise ValueError('Private ELF32 source required')
        for parent,dirs,files in os.walk(path,followlinks=False):
            if any((Path(parent)/name).is_symlink() for name in dirs+files):
                raise ValueError('Symlink in native R6A source')
        if any((path/name).exists() for name in ADD):
            raise ValueError('R6B already installed')
    elif path.exists() or not path.parent.is_dir():
        raise ValueError('Fresh private destination required')
    return path

def patch_make(text):
    if (text.count(ANCHOR)!=1 or 'MOUNT_AD_ACTION_CAS' in text or
        'MOUNT_AD_AUTH_ACTION' not in text or
        'MOUNT_AD_COMBAT_DEATH' not in text or
        'HD79_AD_FOUR_STORE_PLAYTEST' not in text or
        'HD79_AD_SOCKET_TESTING' in text):
        raise ValueError('Untrusted R6A Makefile or test-only fixture')
    block=(
        '# R6B unexposed native four-way locked action transaction.\n'
        'ifeq ($(MOUNT_AD_ACTION_CAS),1)\n'
        'ifneq ($(MOUNT_AD_AUTH_ACTION),1)\n'
        '$(error MOUNT_AD_ACTION_CAS requires MOUNT_AD_AUTH_ACTION=1)\n'
        'endif\n'
        'CFLAGS += -DHD79_AD_ACTION_CAS_PLAYTEST\n'
        'endif\n')
    result=text.replace(ANCHOR,ANCHOR+block,1)
    if result.index('CFLAGS += -DHD79_AD_ACTION_CAS_PLAYTEST')>=result.index('frp.new:'):
        raise ValueError('R6B gate must precede native ELF32 dependencies')
    return result

def patch_store(text):
    if (text.count(STORE_ANCHOR)!=1 or FLAG in text or
        'HD79_AD_FOUR_STORE_PLAYTEST' not in text or
        'hd79_ad_four_action_store.inc' in text):
        raise ValueError('Untrusted R6A native store include anchor')
    return text.replace(STORE_ANCHOR, STORE_ANCHOR + '\n'
                        '#ifdef HD79_AD_ACTION_CAS_PLAYTEST\n'
                        '#include "hd79_ad_four_action_store.inc"\n'
                        '#endif',1)

def stage(source,target):
    source=private(source,SOURCE_PREFIX,True)
    target=private(target,DEST_PREFIX,False)
    make=patch_make((source/'Makefile').read_text(encoding='latin-1'))
    player=patch_store((source/'hd_player_store.c').read_text(encoding='latin-1'))
    for text_name in ('adfixture','hd79_ad_socket_fixture'):
        if text_name in (source/'global.c').read_text(encoding='latin-1'):
            raise ValueError('Test-only socket command is not a trusted baseline')
    for name in ADD:
        file=HERE/name
        if not file.is_file() or file.is_symlink():
            raise ValueError('Missing/symlinked reviewed R6B source '+name)
    originals={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,target,symlinks=False)
    try:
        (target/'Makefile').write_text(make,encoding='latin-1')
        (target/'hd_player_store.c').write_text(player,encoding='latin-1')
        for name in ADD:shutil.copyfile(HERE/name,target/name)
        for name,blob in originals.items():
            if (source/name).read_bytes()!=blob or (
                name not in ('Makefile','hd_player_store.c') and
                (target/name).read_bytes()!=blob):
                raise ValueError('Prior native R6A source unexpectedly changed '+name)
        for name in ('global.c','room.c','creature.c','wilderness.c',
                     'hd79_ad_four_store.inc','hd79_mount_command.c',
                     'hd79_ad_private_fleet.c','hd79_ad_combat_death.c'):
            if (source/name).read_bytes()!=(target/name).read_bytes():
                raise ValueError('Native command/combat/world boundary modified '+name)
    except BaseException:
        shutil.rmtree(target)
        raise
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_r6a_source',type=Path)
    parser.add_argument('fresh_private_r6b_source',type=Path)
    args=parser.parse_args()
    try:out=stage(args.private_r6a_source,args.fresh_private_r6b_source)
    except (ValueError,OSError) as e:
        print('ROUND79AD R6B STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79AD R6B PRIVATE FOUR-RECEIPT ACTION CAS STAGED:',out)
    print('NATIVE CREATURE ACTIONS, PLAYER COMMANDS, RESTORE, MOUNTED TRAVEL: DISABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
