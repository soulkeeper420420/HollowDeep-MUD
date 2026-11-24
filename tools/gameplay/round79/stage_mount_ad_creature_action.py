#!/usr/bin/env python3
"""R6C: stage native receipt/physical action bridge in a fresh disposable ELF32 tree.

Only Makefile and existing private world-identity translation unit change;
source is added into a new /tmp path. Production, player saves and all native
command/combat/movement functions remain byte-for-byte untouched.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE_PREFIX = 'hd-army-game-round79adcas-'
DEST_PREFIX = 'hd-army-game-round79adcreature-'
FLAG = 'HD79_AD_CREATURE_ACTION_PLAYTEST'
MAKE_ANCHOR = 'CFLAGS += -DHD79_AD_ACTION_CAS_PLAYTEST\nendif\n'
INCLUDE = '\n#ifdef HD79_AD_CREATURE_ACTION_PLAYTEST\n#include "hd79_ad_creature_action.h"\n#include "hd79_ad_bound_creature.inc"\n#endif\n'
ADD = ('hd79_ad_bound_creature.inc', 'hd79_ad_creature_action.c',
       'hd79_ad_creature_action.h')
NEEDED = ('frp.new', 'Makefile', 'hd_player_store.c', 'global.c',
          'room.c', 'creature.c', 'wilderness.c',
          'hd79_mount_world_identity.c', 'hd79_ad_death_identity.inc',
          'hd79_ad_authenticated_action.c', 'hd79_ad_private_fleet.c',
          'hd79_ad_four_action_store.inc', 'hd79_ad_four_store.inc')
UNCHANGED = ('hd_player_store.c', 'global.c', 'room.c', 'creature.c',
             'wilderness.c', 'hd79_ad_private_fleet.c',
             'hd79_ad_authenticated_action.c',
             'hd79_ad_four_store.inc', 'hd79_ad_four_action_store.inc',
             'hd79_ad_combat_death.c', 'hd79_mount_command.c')

def private(path, prefix, input_source):
    path = Path(path)
    if (path.name != 'src' or path.parent.parent != Path('/tmp') or
        not path.parent.name.startswith(prefix) or
        path.resolve(strict=False) != path.absolute() or
        path.is_symlink() or path.parent.is_symlink()):
        raise ValueError('Disposable /tmp/'+prefix+'*/src required')
    if input_source:
        if not path.is_dir():
            raise ValueError('Missing previous private R6B native source')
        for name in NEEDED:
            item = path/name
            if not item.is_file() or item.is_symlink():
                raise ValueError('Missing/symlinked native source: '+name)
        if (path/'frp.new').read_bytes()[:5] != b'\x7fELF\x01':
            raise ValueError('Previous real ELF32 game required')
        for root, dirs, files in os.walk(path, followlinks=False):
            if any((Path(root)/n).is_symlink() for n in dirs+files):
                raise ValueError('Symlink in previous private source')
        if any((path/n).exists() for n in ADD):
            raise ValueError('R6C already staged')
    elif path.exists() or not path.parent.is_dir():
        raise ValueError('Fresh destination required')
    return path

def patch_make(text):
    if (text.count(MAKE_ANCHOR)!=1 or FLAG in text or
        'MOUNT_AD_AUTH_ACTION' not in text or
        'MOUNT_AD_ACTION_CAS' not in text or
        'HD79_AD_SOCKET_TESTING' in text):
        raise ValueError('Untrusted R6B Makefile or test-only fixture')
    block = (
        '# R6C: unexposed native mount creature/receipt reconciler.\n'
        'ifeq ($(MOUNT_AD_CREATURE_ACTION),1)\n'
        'ifneq ($(MOUNT_AD_ACTION_CAS),1)\n'
        '$(error MOUNT_AD_CREATURE_ACTION requires MOUNT_AD_ACTION_CAS=1)\n'
        'endif\n'
        'CFLAGS += -DHD79_AD_CREATURE_ACTION_PLAYTEST\n'
        'OBJECTS += hd79_ad_creature_action.o\n'
        'endif\n')
    result = text.replace(MAKE_ANCHOR, MAKE_ANCHOR+block, 1)
    if result.index('OBJECTS += hd79_ad_creature_action.o') >= result.index('frp.new:'):
        raise ValueError('R6C native ELF32 dependency ordering drift')
    return result

def patch_identity(text):
    if (FLAG in text or 'hd79_ad_bound_creature.inc' in text or
        'hd79_ad_death_identity.inc' not in text or
        'HD79_AD_COMBAT_DEATH_PLAYTEST' not in text):
        raise ValueError('Native private world identity/death proof drift')
    return text + INCLUDE

def stage(source, dest):
    source = private(source, SOURCE_PREFIX, True)
    dest = private(dest, DEST_PREFIX, False)
    make = patch_make((source/'Makefile').read_text(encoding='latin-1'))
    identity = patch_identity((source/'hd79_mount_world_identity.c').read_text(encoding='latin-1'))
    original_global = (source/'global.c').read_text(encoding='latin-1')
    if 'adfixture' in original_global or 'hd79_ad_socket_fixture' in original_global:
        raise ValueError('Test-only socket fixture cannot be a production candidate baseline')
    for name in ADD:
        item=HERE/name
        if not item.is_file() or item.is_symlink():
            raise ValueError('Missing/symlinked reviewed R6C file '+name)
    old = {p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/'Makefile').write_text(make, encoding='latin-1')
        (dest/'hd79_mount_world_identity.c').write_text(identity,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        for name, blob in old.items():
            if (source/name).read_bytes()!=blob or (
                name not in ('Makefile','hd79_mount_world_identity.c') and
                (dest/name).read_bytes()!=blob):
                raise ValueError('Prior native baseline changed: '+name)
        for name in UNCHANGED:
            if (source/name).read_bytes() != (dest/name).read_bytes():
                raise ValueError('Native command/player/world boundary changed: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_r6b_source',type=Path)
    p.add_argument('fresh_private_r6c_source',type=Path)
    args=p.parse_args()
    try:
        output=stage(args.private_r6b_source,args.fresh_private_r6c_source)
    except (ValueError,OSError) as error:
        print('ROUND79AD R6C PRIVATE STAGING REFUSED:',error,file=sys.stderr)
        return 1
    print('ROUND79AD R6C PHYSICAL MOUNT RECONCILER STAGED:',output)
    print('PUBLIC MOUNT COMMANDS, RESTART RESTORATION, MOUNTED TRAVEL: DISABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__=='__main__':sys.exit(main())
