#!/usr/bin/env python3
"""Round79Z: stage read-only root-owned stable verification in fresh ELF32 tree.

Does not edit live world/config, player saves, mounts, movement or service.
Board/stable/retrieve remain disabled in native mount command adapter.
"""
from pathlib import Path
import argparse
import os
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
FROM='hd-army-game-round79commands-'
TO='hd-army-game-round79stable-'
ADD=('hd79_stable_registry.h','hd79_stable_registry.c','hd79_stablecheck.c')
NEEDED=('frp.new','Makefile','global.c','hd79_mount_command.c',
        'command1.c','hd_breath_store.inc','hd79_mount_store.inc')
FEATURE=('ifeq ($(MOUNT_COMMAND_PLAYTEST),1)\n'
         'ifneq ($(MOUNT_ACTION_PLAYTEST),1)\n'
         '$(error MOUNT_COMMAND_PLAYTEST requires MOUNT_ACTION_PLAYTEST=1)\n'
         'endif\n'
         'CFLAGS += -DHD79_MOUNT_COMMAND_PLAYTEST\n'
         'OBJECTS += hd79_mount_command.o\n'
         'endif\n')
ADDITION=('ifeq ($(MOUNT_STABLECHECK_PLAYTEST),1)\n'
          'ifneq ($(MOUNT_COMMAND_PLAYTEST),1)\n'
          '$(error MOUNT_STABLECHECK_PLAYTEST requires MOUNT_COMMAND_PLAYTEST=1)\n'
          'endif\n'
          'CFLAGS += -DHD79_MOUNT_STABLECHECK_PLAYTEST\n'
          'OBJECTS += hd79_stable_registry.o hd79_stablecheck.o\n'
          'endif\n')
TABLE=re.compile(r'\bcmdlist[ \t]*\[[ \t]*\][ \t]*=[ \t]*\{')
SLEEP=re.compile(r'(?m)^(?P<indent>[ \t]*)\{[ \t]*"sleep"[ \t]*,'
                 r'[ \t]*100[ \t]*,[ \t]*action[ \t]*\}[ \t]*,'
                 r'[^\r\n]*(?:\r?\n|$)')

def check(root,prefix,existing):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.resolve(strict=False)!=root.absolute()):
        raise ValueError('Only fresh disposable /tmp/'+prefix+'*/src accepted')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('New private source destination must be unused')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Private accepted source missing')
    for name in NEEDED:
        p=root/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing ELF32 native source prerequisite: '+name)
    with (root/'frp.new').open('rb') as f:
        if f.read(5)!=b'\x7fELF\x01':
            raise ValueError('Expected accepted private ELF32 game')
    for dirpath,dirs,files in os.walk(root,followlinks=False):
        if any((Path(dirpath)/name).is_symlink() for name in dirs+files):
            raise ValueError('Private source tree contains a symlink')
    if any((root/name).exists() for name in ADD):
        raise ValueError('Stable registry already staged')
    return root

def patch(source):
    make=(source/'Makefile').read_text(encoding='latin-1')
    if make.count(FEATURE)!=1 or 'MOUNT_STABLECHECK_PLAYTEST' in make:
        raise ValueError('Native mount-command Makefile gate drift')
    glob=(source/'global.c').read_text(encoding='latin-1')
    if re.search(r'(?m)^\s*\{\s*"stablecheck"\s*,',glob,re.I):
        raise ValueError('Existing command collision: stablecheck')
    if 'hd79_stablecheck' in glob:
        raise ValueError('Stable command symbol already registered')
    tables=list(TABLE.finditer(glob))
    sleeps=list(SLEEP.finditer(glob))
    if len(tables)!=1 or len(sleeps)!=1:
        raise ValueError('Native command table or sleep row changed')
    end=re.search(r'(?m)^[ \t]*\}[ \t]*;[ \t]*$',glob[tables[0].end():])
    if not end or not tables[0].end()<sleeps[0].start()<tables[0].end()+end.start():
        raise ValueError('Native stablecheck command anchor cannot be verified')
    indent=sleeps[0].group('indent')
    row=('#ifdef HD79_MOUNT_STABLECHECK_PLAYTEST\n'+indent+
         '{ "stablecheck", 100, hd79_stablecheck },\n#endif\n')
    glob=('#ifdef HD79_MOUNT_STABLECHECK_PLAYTEST\n'
          'extern int hd79_stablecheck();\n#endif\n'+
          glob[:sleeps[0].start()]+row+glob[sleeps[0].start():])
    # Never patch any mount command, movement handler or player save.
    adapter=(source/'hd79_mount_command.c').read_text(encoding='latin-1')
    if 'requires native presence/stable verification' not in adapter or \
       'hd79_mount_action_store' not in adapter:
        raise ValueError('Accepted fail-closed native mount command changed')
    return {'Makefile':make.replace(FEATURE,FEATURE+ADDITION,1),
            'global.c':glob}

def stage(source,dest):
    source=check(source,FROM,True)
    dest=check(dest,TO,False)
    changes=patch(source)
    baseline={n:(source/n).read_bytes() for n in changes}
    for name in ADD:
        path=HERE/name
        if not path.is_file() or path.is_symlink():
            raise ValueError('Stable authority source missing or unsafe: '+name)
    shutil.copytree(source,dest,symlinks=False)
    try:
        for name,value in changes.items():
            (dest/name).write_text(value,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        if any((source/n).read_bytes()!=blob for n,blob in baseline.items()):
            raise ValueError('Accepted source changed during staging')
        for name in ('command1.c','hd79_mount_command.c','wilderness.c',
                     'hd_player_store.c','hd79_mount_store.inc'):
            if (dest/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError('Native gameplay/save boundary modified')
    except Exception:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_round79y_source',type=Path)
    p.add_argument('new_private_round79z_source',type=Path)
    a=p.parse_args()
    try:
        dest=stage(a.accepted_round79y_source,a.new_private_round79z_source)
    except (OSError,ValueError) as e:
        print('ROUND79Z: STABLE REGISTRY STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79Z: READ-ONLY STABLE WORLD AUTHORITY STAGED:',dest)
    print('MOUNT PRESENCE / BOARD / STABLE / RETRIEVE: NOT ACTIVE')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
