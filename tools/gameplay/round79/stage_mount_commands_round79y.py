#!/usr/bin/env python3
"""Round79Y: feature-gated native mount commands in an isolated source COPY.

Adds command table rows and one native adapter. Boarding, stable/retrieve
fail closed pending authoritative same-room mount/stable world checks.
"""
from pathlib import Path
import argparse
import os
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX='hd-army-game-round79actions-'
TARGET_PREFIX='hd-army-game-round79commands-'
NEW=('hd79_mount_command.c',)
REQUIRED=('frp.new','Makefile','global.c','command1.c','mstruct.h',
          'hd79_mount_actions.c','hd79_mount_action_store.c',
          'hd79_mount_store.inc','hd79_mount_wire.c','hd79_mount_roster.c',
          'hd79_rest_game.c','hd_player_store.c')
FEATURE=('ifeq ($(MOUNT_ACTION_PLAYTEST),1)\n'
         'CFLAGS += -DHD79_MOUNT_ACTION_PLAYTEST\n'
         'OBJECTS += hd79_mount_actions.o hd79_mount_action_store.o\n'
         'endif\n')
NEW_FEATURE=('ifeq ($(MOUNT_COMMAND_PLAYTEST),1)\n'
             'ifneq ($(MOUNT_ACTION_PLAYTEST),1)\n'
             '$(error MOUNT_COMMAND_PLAYTEST requires MOUNT_ACTION_PLAYTEST=1)\n'
             'endif\n'
             'CFLAGS += -DHD79_MOUNT_COMMAND_PLAYTEST\n'
             'OBJECTS += hd79_mount_command.o\n'
             'endif\n')
CANDIDATES=('mount','dismount','stable','retrieve')
TABLE=re.compile(r'\bcmdlist[ \t]*\[[ \t]*\][ \t]*=[ \t]*\{')
SLEEP=re.compile(r'(?m)^(?P<indent>[ \t]*)\{[ \t]*"sleep"[ \t]*,'
                 r'[ \t]*100[ \t]*,[ \t]*action[ \t]*\}[ \t]*,'
                 r'[^\r\n]*(?:\r?\n|$)')

def check(root,prefix,existing):
    root=Path(root)
    if (root.name!='src' or root.parent.parent!=Path('/tmp') or
        not root.parent.name.startswith(prefix) or root.is_symlink() or
        root.parent.is_symlink() or root.resolve(strict=False)!=root.absolute()):
        raise ValueError('Only strict disposable /tmp/'+prefix+'*/src allowed')
    if not existing:
        if root.exists() or not root.parent.is_dir():
            raise ValueError('Destination must be new with a private parent')
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError('Unsafe private source')
    for filename in REQUIRED:
        p=root/filename
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing or unsafe private prerequisite: '+filename)
    with (root/'frp.new').open('rb') as stream:
        if stream.read(5)!=b'\x7fELF\x01':
            raise ValueError('Expected private ELF32 game executable')
    for folder,dirs,files in os.walk(root,followlinks=False):
        if any((Path(folder)/f).is_symlink() for f in dirs+files):
            raise ValueError('Symlink in private native source')
    if any((root/name).exists() for name in NEW):
        raise ValueError('Native mount command adapter already installed')
    return root

def source_patch(source):
    edits={}
    make=(source/'Makefile').read_text(encoding='latin-1')
    if make.count(FEATURE)!=1 or 'MOUNT_COMMAND_PLAYTEST' in make:
        raise ValueError('Round79X exact Makefile feature gate drift')
    edits['Makefile']=make.replace(FEATURE,FEATURE+NEW_FEATURE,1)
    global_c=(source/'global.c').read_text(encoding='latin-1')
    tables=list(TABLE.finditer(global_c))
    sleeps=list(SLEEP.finditer(global_c))
    if len(tables)!=1 or len(sleeps)!=1:
        raise ValueError('Cannot prove exact native cmdlist/sleep insertion')
    closing=re.search(r'(?m)^[ \t]*\}[ \t]*;[ \t]*$',
                      global_c[tables[0].end():])
    if not closing:
        raise ValueError('Unclosed native command table')
    table_end=tables[0].end()+closing.start()
    if not tables[0].end()<sleeps[0].start()<table_end:
        raise ValueError('Sleep row is not in native command table')
    for word in CANDIDATES:
        if re.search(r'(?m)^\s*\{\s*"'+word+r'"\s*,',global_c,re.I):
            raise ValueError('Existing native command collision: '+word)
    if global_c.count('hd79_mount_command'):
        raise ValueError('Native mount command symbol already exists')
    indent=sleeps[0].group('indent')
    rows='#ifdef HD79_MOUNT_COMMAND_PLAYTEST\n'
    rows+=''.join(indent+'{ "'+v+'", 100, hd79_mount_command },\n'
                  for v in CANDIDATES)
    rows+='#endif\n'
    edits['global.c']=('#ifdef HD79_MOUNT_COMMAND_PLAYTEST\n'
                       'extern int hd79_mount_command();\n'
                       '#endif\n'+
                       global_c[:sleeps[0].start()]+rows+
                       global_c[sleeps[0].start():])
    # Check the field TYPES that the native adapter actually reads, not
    # the historical sizes/layout/order of unrelated cmd fields. The
    # engine's native compiler is authoritative about declared sizes.
    # In particular, older Mordor headers may use a different typedef
    # spelling or a non-256-byte fullstr: sizeof(command->fullstr) in the
    # adapter already bounds its reads against the actual C member.
    structs=(source/'mstruct.h').read_text(encoding='latin-1')
    # Strip C comments so fields mentioned only in comments cannot pass.
    declarations=re.sub(r'/\*.*?\*/|//[^\r\n]*',' ',structs,flags=re.S)
    cmd_types=re.findall(
        r'\btypedef\s+struct(?:\s+[A-Za-z_]\w*)?\s*\{'
        r'(.*?)\}\s*cmd\s*;',declarations,flags=re.S)
    if len(cmd_types)!=1:
        raise ValueError('Native cmd typedef not uniquely identified: refusing parsing guess')
    fields=cmd_types[0]
    # Require actual fixed arrays, not pointers, so sizeof(fullstr) and
    # str[0] are valid bounded operations in the native adapter.
    full=re.search(r'\bchar\s+fullstr\s*\[\s*([^]\s]+)\s*\]\s*;',fields)
    token=re.search(r'\bchar\s+str\s*\[\s*([^]\s]+)\s*\]'
                    r'\s*\[\s*([^]\s]+)\s*\]\s*;',fields)
    if not full or not token:
        raise ValueError('Native cmd fixed character arrays missing: refusing parsing guess')
    if full.group(1)=='0' or token.group(1)=='0' or token.group(2)=='0':
        raise ValueError('Native cmd zero-sized field: refusing parsing guess')
    dispatch=(source/'command1.c').read_text(encoding='latin-1')
    if ('cmdlist[cmdno].cmdfn' not in dispatch or
        'process_cmd' not in dispatch or
        not re.search(r'\bfullstr\b',dispatch)):
        raise ValueError('Native command raw-input or dispatch not verified')
    return edits

def stage(source,target):
    source=check(source,SOURCE_PREFIX,True)
    target=check(target,TARGET_PREFIX,False)
    edits=source_patch(source)
    baseline={name:(source/name).read_bytes() for name in edits}
    shutil.copytree(source,target,symlinks=False)
    try:
        for name,contents in edits.items():
            (target/name).write_text(contents,encoding='latin-1')
        for name in NEW:
            shutil.copyfile(HERE/name,target/name)
        if any((source/name).read_bytes()!=old
               for name,old in baseline.items()):
            raise ValueError('Accepted private source changed during staging')
        if (target/'command1.c').read_bytes()!=(source/'command1.c').read_bytes():
            raise ValueError('Native dispatcher changed unexpectedly')
        if (target/'wilderness.c').read_bytes()!=(source/'wilderness.c').read_bytes():
            raise ValueError('Native movement changed unexpectedly')
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accepted_round79x_source',type=Path)
    p.add_argument('new_private_round79y_source',type=Path)
    args=p.parse_args()
    try:
        result=stage(args.accepted_round79x_source,args.new_private_round79y_source)
    except (OSError,ValueError) as exc:
        print('ROUND79Y: NATIVE COMMAND STAGING REFUSED:',exc,file=sys.stderr)
        return 1
    print('ROUND79Y: NATIVE MOUNT COMMANDS STAGED:',result)
    print('Board/stable/retrieve disabled until native world authority is installed')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0

if __name__=='__main__':
    sys.exit(main())
