#!/usr/bin/env python3
"""Round79W: stage mount receipt CAS into a NEW disposable private ELF32 tree.

Requires the independently accepted Round79P REST/Breath private source.
Does not touch production, world/player files, commands or movement.
"""
from pathlib import Path
import argparse
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79rest-'
TARGET_PREFIX='hd-army-game-round79mount-'
ADD=('hd79_mount_store.h','hd79_mount_store.inc','hd79_mount_ids.h')
PURE=('hd79_mount_roster.h','hd79_mount_roster.c',
      'hd79_mount_wire.h','hd79_mount_wire.c',
      'hd_mount_travel.h','hd_mount_travel.c')
REQUIRED=('frp.new','Makefile','hd_player_store.c','treasure_receipt.h',
          'treasure_receipt.c','hd_breath_store.inc','hd_conjure_store.inc',
          'hd_pet_store.inc','hd_wilderness_breath.h')
FIRST_ID='ffffffffffffffffffffffffffffff80'
SECOND_ID='ffffffffffffffffffffffffffffff81'

def private_path(root,prefix,existing):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or
        root.is_symlink() or root.parent.is_symlink()):
        raise ValueError('Only disposable /tmp/'+prefix+'*/src permitted')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination must not exist')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Existing native source is not canonical')
    for name in REQUIRED:
        p=root/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing or symlinked native file '+name)
    with (root/'frp.new').open('rb') as fp:
        if fp.read(5)!=b'\x7fELF\x01':
            raise ValueError('Expected private ELF32 game executable')
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            if (Path(directory)/name).is_symlink():
                raise ValueError('Symlinks forbidden in native source')
    if any((root/name).exists() for name in ADD+PURE):
        raise ValueError('Mount source already present')
    for path in root.iterdir():
        if path.is_file() and path.suffix in ('.c','.h','.inc'):
            data=path.read_text(encoding='latin-1')
            if FIRST_ID in data or SECOND_ID in data:
                raise ValueError('Mount receipt ID already referenced in native source')
    return root

def once(body,needle,label):
    if body.count(needle)!=1:
        raise ValueError('Native mount source anchor drift: '+label)
    return body

def patched(source):
    player=(source/'hd_player_store.c').read_text(encoding='latin-1')
    make=(source/'Makefile').read_text(encoding='latin-1')
    anchor='static const char breath_id[] = "ffffffffffffffffffffffffffffff79";'
    once(player,anchor,'Breath claim identifier')
    guard='!strcmp(claim, breath_id)'
    once(player,guard,'reserved Breath claim guard')
    include='#include "hd_breath_store.inc"'
    once(player,include,'verified Breath store include')
    if 'HD79_MOUNT_STORE_PLAYTEST' in player or 'MOUNT_STORE_PLAYTEST' in make:
        raise ValueError('Mount storage already staged')
    if 'HD79_BREATH_STORE_PLAYTEST' not in player:
        raise ValueError('Verified Breath store not found')
    # Exactly two mount IDs become reserved even for ordinary loot claims.
    player=player.replace(anchor,anchor+'\n#ifdef HD79_MOUNT_STORE_PLAYTEST\n'
                          '#include "hd79_mount_ids.h"\n#endif',1)
    player=player.replace(guard,guard+'\n#ifdef HD79_MOUNT_STORE_PLAYTEST\n'
                          '        || !strcmp(claim, hd79_mount_a_id)\n'
                          '        || !strcmp(claim, hd79_mount_b_id)\n#endif',1)
    player=player.replace(include,include+'\n#ifdef HD79_MOUNT_STORE_PLAYTEST\n'
                          '#include "hd79_mount_store.inc"\n#endif',1)
    make_anchor=('ifeq ($(BREATH_STORE_PLAYTEST),1)\n'
                 'CFLAGS += -DHD79_BREATH_STORE_PLAYTEST\n'
                 'endif\n')
    once(make,make_anchor,'existing Breath gate in Makefile')
    mount_gate=('# Round79W: save only, no movement or commands\n'
                'ifeq ($(MOUNT_STORE_PLAYTEST),1)\n'
                'CFLAGS += -DHD79_MOUNT_STORE_PLAYTEST\n'
                'OBJECTS += hd_mount_travel.o hd79_mount_roster.o hd79_mount_wire.o\n'
                'endif\n')
    make=make.replace(make_anchor,make_anchor+mount_gate,1)
    return {'hd_player_store.c':player,'Makefile':make}

def stage(source,target,pure_root):
    source=private_path(source,SOURCE_PREFIX,True)
    target=private_path(target,TARGET_PREFIX,False)
    updates=patched(source)
    pure_root=Path(pure_root)
    if not pure_root.is_dir() or pure_root.is_symlink():
        raise ValueError('Pinned public source directory missing')
    for name in PURE:
        p=pure_root/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Pinned public mount code missing '+name)
    old={name:(source/name).read_bytes() for name in updates}
    for name in ADD:
        p=HERE/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Bundle missing or unsafe '+name)
    shutil.copytree(source,target,symlinks=False)
    try:
        for name,text in updates.items():
            (target/name).write_text(text,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,target/name)
        for name in PURE:
            shutil.copyfile(pure_root/name,target/name)
        if any((source/name).read_bytes()!=prior
               for name,prior in old.items()):
            raise ValueError('Native baseline changed during staging')
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('target',type=Path)
    p.add_argument('pinned_public_mount_dir',type=Path)
    options=p.parse_args()
    try:
        dest=stage(options.source,options.target,options.pinned_public_mount_dir)
    except (OSError,ValueError) as error:
        print('ROUND79W: STAGING REFUSED:',error,file=sys.stderr)
        return 1
    print('ROUND79W: PRIVATE MOUNT SAVE STAGED:',dest)
    print('NATIVE ATOMIC PLAYER TEST: NOT YET VERIFIED')
    print('MOUNT COMMANDS/MOVEMENT: NOT INSTALLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__=='__main__':
    sys.exit(main())
