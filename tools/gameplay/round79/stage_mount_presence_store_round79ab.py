#!/usr/bin/env python3
"""Round79AB: stage atomic three-receipt mount presence into a NEW ELF32 tree.

Never touch production, the accepted private baseline, player saves,
MUD world, live services or native command/movement dispatch.
"""
from pathlib import Path
import argparse
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79stable-'
TARGET_PREFIX='hd-army-game-round79presence-'
ADD=('hd79_mount_presence.h','hd79_mount_presence.c',
     'hd79_mount_presence_store.h','hd79_mount_presence_store.inc')
REQUIRED=('frp.new','hd_player_store.c','hd79_mount_store.inc',
          'hd79_mount_store.h','hd79_mount_ids.h','hd_breath_store.inc',
          'Makefile','global.c','hd79_mount_command.c',
          'hd79_stable_registry.c','treasure_receipt.c',
          'command1.c','command2.c','command6.c','wilderness.c',
          'hd79_stablecheck.c')
ID='ffffffffffffffffffffffffffffff82'
FLAG='HD79_MOUNT_PRESENCE_STORE_PLAYTEST'

def check(root,prefix,existing):
    root=Path(root)
    if root.name!='src' or root.parent.parent!=Path('/tmp') or \
       not root.parent.name.startswith(prefix) or root.is_symlink() or \
       root.parent.is_symlink() or root.resolve(strict=False)!=root.absolute():
        raise ValueError('Only disposable /tmp/'+prefix+'*/src is allowed')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination must be a fresh private directory')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Accepted private native source missing')
    for name in REQUIRED:
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Missing/symlink native baseline: '+name)
    with (root/'frp.new').open('rb') as f:
        if f.read(5)!=b'\x7fELF\x01':
            raise ValueError('Expected accepted private ELF32 MUD')
    for base,dirs,files in os.walk(root,followlinks=False):
        if any((Path(base)/n).is_symlink() for n in dirs+files):
            raise ValueError('Symlinks denied in accepted native tree')
    if any((root/n).exists() for n in ADD):
        raise ValueError('Presence files already installed')
    for path in root.glob('*'):
        if path.suffix in ('.c','.h','.inc') and path.is_file():
            if ID in path.read_text(encoding='latin-1'):
                raise ValueError('Presence receipt ID 82 collision')
    return root

def once(body,needle,replacement,label):
    if body.count(needle)!=1:
        raise ValueError('Accepted native source anchor drift: '+label)
    return body.replace(needle,replacement,1)

def patched(source):
    p=(source/'hd_player_store.c').read_text(encoding='latin-1')
    m=(source/'Makefile').read_text(encoding='latin-1')
    s=(source/'hd79_mount_store.inc').read_text(encoding='latin-1')
    if FLAG in p or FLAG in m or FLAG in s:
        raise ValueError('Presence store already staged')
    if '#include "hd79_mount_store.inc"' not in p or \
       'HD79_MOUNT_STORE_PLAYTEST' not in p:
        raise ValueError('Native mount storage prerequisite absent')
    if 'MOUNT_STABLECHECK_PLAYTEST' not in m:
        raise ValueError('Accepted Round79Z Makefile feature gate absent')
    if 'int hd79_mount_store_commit' not in s or \
       'static int hd79_mount_transaction' not in s:
        raise ValueError('Old two-receipt writer drift')
    p=once(p,'!strcmp(claim, hd79_mount_b_id)',
           '!strcmp(claim, hd79_mount_b_id)\n'
           '#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           '        || !strcmp(claim, HD79_MOUNT_PRESENCE_ID)\n'
           '#endif','reserved receipt claim guard')
    p=once(p,'#include "hd79_mount_store.inc"',
           '#include "hd79_mount_store.inc"\n'
           '#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           '#include "hd79_mount_presence_store.inc"\n'
           '#endif','native player-store include')
    p=once(p,'#include "hd79_mount_ids.h"',
           '#include "hd79_mount_ids.h"\n'
           '#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           '#include "hd79_mount_presence_store.h"\n'
           '#endif','receipt ID declaration')
    # Disable BOTH old 2-receipt mutators in the new feature gate, not
    # just when a presence record already happens to exist. This avoids
    # creating incomplete new records and blocks stale command adapters.
    s=once(s,'static int hd79_mount_transaction(',
           '#ifndef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           'static int hd79_mount_transaction(',
           'legacy two-fragment atomic transaction')
    s=once(s,'int hd79_mount_store_init(',
           '#endif /* no old two-fragment writer with presence active */\n'
           'int hd79_mount_store_init(',
           'legacy transaction boundary')
    s=once(s,'return hd79_mount_transaction(name,NULL,NULL,out);',
           '#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           '    (void)name; (void)out;\n'
           '    return HD79_MOUNT_STORE_FAILURE;\n'
           '#else\n'
           '    return hd79_mount_transaction(name,NULL,NULL,out);\n'
           '#endif','legacy initialization denial')
    s=once(s,'return hd79_mount_transaction(name,expected,next,out);',
           '#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST\n'
           '    (void)name; (void)expected; (void)next; (void)out;\n'
           '    return HD79_MOUNT_STORE_FAILURE;\n'
           '#else\n'
           '    return hd79_mount_transaction(name,expected,next,out);\n'
           '#endif','legacy atomic commit denial')
    m+='\n# Round79AB: 3-receipt mount location atomic store; NOT GAMEPLAY.\n' \
       'ifeq ($(MOUNT_PRESENCE_STORE_PLAYTEST),1)\n' \
       'ifneq ($(MOUNT_STORE_PLAYTEST),1)\n' \
       '$(error MOUNT_PRESENCE_STORE_PLAYTEST requires MOUNT_STORE_PLAYTEST)\n' \
       'endif\n' \
       'CFLAGS += -DHD79_MOUNT_PRESENCE_STORE_PLAYTEST\n' \
       'OBJECTS += hd79_mount_presence.o\n' \
       'endif\n'
    return {'hd_player_store.c':p,'hd79_mount_store.inc':s,'Makefile':m}

def stage(source,dest):
    source=check(source,SOURCE_PREFIX,True)
    dest=check(dest,TARGET_PREFIX,False)
    edits=patched(source)
    originals={n:(source/n).read_bytes() for n in edits}
    for name in ADD:
        p=HERE/name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing/symlinked published candidate '+name)
    shutil.copytree(source,dest,symlinks=False)
    try:
        for name,body in edits.items():
            (dest/name).write_text(body,encoding='latin-1')
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        if any((source/n).read_bytes()!=orig for n,orig in originals.items()):
            raise ValueError('Accepted source changed during private staging')
        # Explicit denylist of gameplay files that this milestone may not edit.
        for name in ('global.c','command1.c','command2.c','command6.c',
                     'wilderness.c','hd79_mount_command.c','hd79_stablecheck.c'):
            if (dest/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError('Gameplay command/movement modification: '+name)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_private_round79z_source',type=Path)
    p.add_argument('new_disposable_round79ab_source',type=Path)
    a=p.parse_args()
    try:
        target=stage(a.accepted_private_round79z_source,
                     a.new_disposable_round79ab_source)
    except (OSError,ValueError) as e:
        print('ROUND79AB: NATIVE STAGING REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79AB: PRIVATE THREE-RECEIPT NATIVE STORE STAGED:',target)
    print('BOARDING / STABLING / RETRIEVAL / RIDDEN MOVEMENT: NOT ENABLED')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
