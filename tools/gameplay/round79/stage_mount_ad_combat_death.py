#!/usr/bin/env python3
"""R4 private ELF32 staged pre-removal death checkpoint.

Only the disposable room.c, world identity, Makefile and new dead-bridge
source are changed. No production world, player or service may be written.
"""
import argparse
import os
import re
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79adfour-'
DEST_PREFIX='hd-army-game-round79addeath-'
FLAG='HD79_AD_COMBAT_DEATH_PLAYTEST'
ADD=('hd79_ad_combat_death.c','hd79_ad_combat_death.h',
     'hd79_ad_death_identity.inc')
NEEDED=('frp.new','Makefile','room.c','files1.c','hd_player_store.c',
        'hd79_mount_world_identity.c','hd79_mount_world_identity.h',
        'hd79_ad_four_store.inc','hd79_ad_four_store.h',
        'hd79_ad_death_receipt.c','hd79_mount_presence.c',
        'hd79_mount_command.c','wilderness.c')
MAKE_ANCHOR='CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST\nendif\n'

# Match only a verified modern or old-style K&R native definition.
# Do NOT patch prototypes, comments, or a similarly named command.
def strict_death_hook(body):
    name='del_crt_rom'
    modern=re.compile(r'(?m)^[ \t]*void\s+del_crt_rom\s*\(\s*'
        r'creature\s*\*\s*crt_ptr\s*,\s*room\s*\*\s*rom_ptr'
        r'\s*\)\s*\{')
    classic=re.compile(r'(?m)^[ \t]*void\s+del_crt_rom\s*'
        r'\(\s*crt_ptr\s*,\s*rom_ptr\s*\)\s*'
        r'((?:(?:creature|room)\s*\*\s*\w+\s*;\s*){2})\{')
    indexes=[m.end() for m in modern.finditer(body)]
    for m in classic.finditer(body):
        typed=re.findall(r'(creature|room)\s*\*\s*(\w+)\s*;',m.group(1))
        if sorted(typed)==[('creature','crt_ptr'),('room','rom_ptr')]:
            indexes.append(m.end())
    if len(indexes)!=1:raise ValueError('Exact native del_crt_rom signature drift')
    pos=indexes[0]
    return body[:pos]+'\n#ifdef '+FLAG+'\n    (void)hd79_ad_combat_death_before_remove(crt_ptr);\n#endif\n'+body[pos:]

def private(path,prefix,existing):
    path=Path(path)
    if (path.name!='src' or path.parent.parent!=Path('/tmp') or
        not path.parent.name.startswith(prefix) or path.is_symlink() or
        path.parent.is_symlink() or path.resolve(strict=False)!=path.absolute()):
        raise ValueError('Expected disposable /tmp/'+prefix+'*/src')
    if existing:
        if not path.is_dir():raise ValueError('Missing private R3 ELF32 source')
        for name in NEEDED:
            f=path/name
            if not f.is_file() or f.is_symlink():
                raise ValueError('Missing or symlinked native source '+name)
        with (path/'frp.new').open('rb') as fd:
            if fd.read(5)!=b'\x7fELF\x01':
                raise ValueError('Previous R3 private ELF32 binary required')
        for directory,dirs,files in os.walk(path,followlinks=False):
            if any((Path(directory)/name).is_symlink() for name in dirs+files):
                raise ValueError('Symlink in private source')
        for name in ADD:
            if (path/name).exists():raise ValueError('Death bridge already installed')
    elif path.exists() or not path.parent.is_dir():
        raise ValueError('Fresh private destination required')
    return path

def patch(source):
    room=(source/'room.c').read_text(encoding='latin-1')
    identity=(source/'hd79_mount_world_identity.c').read_text(encoding='latin-1')
    make=(source/'Makefile').read_text(encoding='latin-1')
    if (FLAG in room or FLAG in identity or FLAG in make or
        'hd79_ad_death_identity.inc' in identity):
        raise ValueError('Death callback already staged')
    if ('HD79_MOUNT_LIFECYCLE_PLAYTEST' not in room or
        'hd79_world_mount_unbind_creature(crt_ptr);' not in room or
        'hd79_world_mount_unbind_all' not in identity or
        make.count(MAKE_ANCHOR)!=1):
        raise ValueError('Accepted R3/AC3B native lifecycle anchor drift')
    # Verified old-style K&R or modern function definition. This inserts
    # BEFORE existing AC3B removal unbind; never after pointer revocation.
    room=strict_death_hook(room)
    room=('#ifdef '+FLAG+'\n'
          '#include "hd79_ad_combat_death.h"\n#endif\n')+room
    identity+='\n/* R4 private registry-owning death identity proof. */\n'
    identity+='#ifdef '+FLAG+'\n#include "hd79_ad_death_identity.inc"\n#endif\n'
    make=make.replace(MAKE_ANCHOR,MAKE_ANCHOR+
        '# R4: private native removal/death marker; no new commands.\n'
        'ifeq ($(MOUNT_AD_COMBAT_DEATH),1)\n'
        'ifneq ($(MOUNT_AD_FOUR_STORE),1)\n'
        '$(error MOUNT_AD_COMBAT_DEATH requires MOUNT_AD_FOUR_STORE=1)\n'
        'endif\n'
        'CFLAGS += -D'+FLAG+'\n'
        'OBJECTS += hd79_ad_combat_death.o\n'
        'endif\n',1)
    if make.index('OBJECTS += hd79_ad_combat_death.o')>=make.index('frp.new:'):
        raise ValueError('R4 native object is not an ELF32 prerequisite')
    if not room.index('hd79_ad_combat_death_before_remove')<room.index(
            'hd79_world_mount_unbind_creature(crt_ptr);'):
        raise ValueError('Death hook must precede lifecycle unbind')
    return {'room.c':room,'hd79_mount_world_identity.c':identity,
            'Makefile':make}

def stage(source,dest):
    source=private(source,SOURCE_PREFIX,True)
    dest=private(dest,DEST_PREFIX,False)
    modifications=patch(source)
    for name in ADD:
        f=HERE/name
        if not f.is_file() or f.is_symlink():
            raise ValueError('Missing new reviewed native file '+name)
    original={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
    shutil.copytree(source,dest,symlinks=False)
    try:
        for name,contents in modifications.items():
            (dest/name).write_text(contents,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        for name,blob in original.items():
            if (source/name).read_bytes()!=blob or (name not in modifications and
                    (dest/name).read_bytes()!=blob):
                raise ValueError('Previously validated native source changed '+name)
        for name in ('hd_player_store.c','files1.c','wilderness.c',
                     'hd79_mount_command.c','hd79_ad_four_store.inc'):
            if (source/name).read_bytes()!=(dest/name).read_bytes():
                raise ValueError('Native save/command/room-free boundary modified '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_private_r3_source',type=Path)
    p.add_argument('new_private_r4_source',type=Path)
    args=p.parse_args()
    try:target=stage(args.accepted_private_r3_source,args.new_private_r4_source)
    except (ValueError,OSError) as error:
        print('ROUND79AD R4: PRIVATE STAGING REFUSED:',error,file=sys.stderr)
        return 1
    print('ROUND79AD R4: PRIVATE MONSTER DEATH PRE-REMOVE HOOK STAGED:',target)
    print('NO PLAYER MOUNT COMMANDS, RESTORE OR MOUNTED TRAVEL ENABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
