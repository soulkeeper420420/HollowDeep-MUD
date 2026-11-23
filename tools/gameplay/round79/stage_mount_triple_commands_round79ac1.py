#!/usr/bin/env python3
"""Round79AC1: disposable game with fail-closed 3-claim mount command adapter."""
from pathlib import Path
import argparse, os, shutil, sys
HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79presence-'
TARGET_PREFIX='hd-army-game-round79triplecmd-'
ADD=('hd79_presence_dismount_store.c','hd79_presence_dismount_store.h')
FLAG='MOUNT_TRIPLE_COMMAND_PLAYTEST'
MAKE_ANCHOR='OBJECTS += hd79_mount_presence.o\nendif\n'
NEEDED=('frp.new','Makefile','global.c','command1.c','hd_player_store.c',
        'hd79_mount_command.c','hd79_mount_presence_store.inc',
        'hd79_mount_presence_store.h','hd79_mount_presence.c',
        'hd79_mount_presence.h','hd79_mount_store.inc','wilderness.c')

def check(root,prefix,existing):
    root=Path(root)
    if root.name!='src' or root.parent.parent!=Path('/tmp') or \
       not root.parent.name.startswith(prefix) or root.is_symlink() or \
       root.parent.is_symlink() or root.absolute()!=root.resolve(strict=False):
        raise ValueError('Only disposable /tmp/'+prefix+'*/src')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination must be new')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Native source missing')
    for name in NEEDED:
        p=root/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing native source: '+name)
    if (root/'frp.new').read_bytes()[:5]!=b'\x7fELF\x01':
        raise ValueError('Native executable is not ELF32')
    for base,dirs,files in os.walk(root,followlinks=False):
        if any((Path(base)/n).is_symlink() for n in dirs+files):
            raise ValueError('Source symlinks denied')
    if any((root/n).exists() for n in ADD) or FLAG in (root/'Makefile').read_text(encoding='latin-1'):
        raise ValueError('Triple command already installed')
    return root

def update(root):
    make=(root/'Makefile').read_text(encoding='latin-1')
    if make.count(MAKE_ANCHOR)!=1 or 'MOUNT_PRESENCE_STORE_PLAYTEST' not in make:
        raise ValueError('Round79AB verified Makefile anchor drift')
    addition=('# Round79AC1: read-only 3-claim status + exact dismount.\n'
              'ifeq ($(MOUNT_TRIPLE_COMMAND_PLAYTEST),1)\n'
              'ifneq ($(MOUNT_PRESENCE_STORE_PLAYTEST),1)\n'
              '$(error MOUNT_TRIPLE_COMMAND_PLAYTEST requires MOUNT_PRESENCE_STORE_PLAYTEST)\n'
              'endif\n'
              'CFLAGS += -DHD79_MOUNT_TRIPLE_COMMAND_PLAYTEST\n'
              'OBJECTS += hd79_presence_dismount_store.o\n'
              'endif\n')
    make=make.replace(MAKE_ANCHOR,MAKE_ANCHOR+addition,1)
    # All extra objects must be registered before the frp.new dependency.
    if make.find('OBJECTS += hd79_presence_dismount_store.o')>=make.find('frp.new:') or make.find('frp.new:')<0:
        raise ValueError('Native make target prerequisite ordering drift')
    original=(root/'hd79_mount_command.c').read_bytes()
    verified=(HERE/'hd79_mount_command_ac.c').read_bytes()
    # Existing adapter is the exact Round79Y source unchanged through 79AB.
    if original==verified or b'HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST' in original:
        raise ValueError('Already modified native command')
    expected=(HERE/'hd79_mount_command_y_baseline.c').read_bytes()
    if original!=expected:
        raise ValueError('Native command source changed: do not guess')
    for token in (b'HD79_PRESENCE_STORE_OK',b'HD79_DISMOUNT_SUCCESS',
                  b'HD79_ACTION_BOARD',b'HD79_ACTION_RETRIEVE'):
        if token not in verified:
            raise ValueError('Candidate command authorization changed')
    return {'Makefile':make.encode('latin-1'),
            'hd79_mount_command.c':verified}

def stage(source,dest):
    source=check(source,SOURCE_PREFIX,True)
    dest=check(dest,TARGET_PREFIX,False)
    changes=update(source)
    for name in ADD:
        p=HERE/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Published source missing: '+name)
    saved={p:(source/p).read_bytes() for p in changes}
    shutil.copytree(source,dest,symlinks=False)
    try:
        for p,data in changes.items():
            (dest/p).write_bytes(data)
        for p in ADD:
            shutil.copyfile(HERE/p,dest/p)
        if any((source/p).read_bytes()!=saved[p] for p in saved):
            raise ValueError('Accepted source changed during copy')
        for p in ('global.c','command1.c','wilderness.c',
                  'hd_player_store.c','hd79_mount_presence_store.inc'):
            if (source/p).read_bytes()!=(dest/p).read_bytes():
                raise ValueError('Gameplay, movement, save boundary changed')
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_round79ab_private_source',type=Path)
    p.add_argument('new_private_round79ac_source',type=Path)
    a=p.parse_args()
    try:
        dest=stage(a.accepted_round79ab_private_source,a.new_private_round79ac_source)
    except (OSError,ValueError) as err:
        print('ROUND79AC1: STAGING REFUSED:',err,file=sys.stderr)
        return 1
    print('ROUND79AC1: TRIPLE-RECEIPT NATIVE COMMANDS STAGED:',dest)
    print('BOARD/STABLE/RETRIEVE/MOVEMENT: STILL DISABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
