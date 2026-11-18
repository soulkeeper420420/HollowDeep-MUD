#!/usr/bin/env python3
"""Stage roster-backed Army gameplay and compile an isolated ELF32 binary."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from stage_corpse import stage as stage_corpse, stage_command_and_login

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'store'))
from stage_roster import stage as stage_roster


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix='hd-army-game-'))
    print(f'Private Army build: {work}', flush=True)
    source = work / 'src'
    stage_roster(args.source, source)
    skeleton = source / 'hd_necro_skeleton.c'
    if hashlib.sha256(skeleton.read_bytes()).hexdigest() != (
            'f544877d682bebebb747c244631b18cb1e0ea8192914515463aaa28c6ce58a41'):
        raise ValueError('Private runtime skeleton source fingerprint mismatch')
    stage_corpse(source)
    stage_command_and_login(source)
    table = source / 'global.c'
    commands = table.read_text(encoding='latin-1')
    alias = '\t{ "rc", 150, hd_corpse_raise },'
    if (commands.count(alias) != 1 or
            re.search(r'"pets?"\s*,|,\s*154\s*,', commands)):
        raise ValueError('Unexpected native pet command table')
    commands = commands.replace(alias, alias + '\n'
        '\t{ "pet", 154, hd_army_pet_command },\n'
        '\t{ "pets", 154, hd_army_pet_command },')
    table.write_text('struct creature; struct cmd;\n'
        'extern int hd_army_pet_command(struct creature *, struct cmd *);\n'
        + commands, encoding='latin-1')
    shutil.copyfile(HERE / 'hd_army_runtime.c', skeleton)
    for name in ('hd_army_restore.c', 'hd_army_restore.h'):
        shutil.copyfile(HERE / name, source / name)


    companion = HERE.parent / 'conjure'
    for name in ('hd_conjure_runtime.c','hd_conjure_runtime.h'):
        shutil.copyfile(companion/name,source/name)

    commands=table.read_text(encoding='latin-1')
    anchor='\t{ "pets", 154, hd_army_pet_command },'
    if commands.count(anchor)!=1 or re.search(
            r'"conjure"\s*,|,\s*155\s*,',commands):
        raise ValueError('Conjure command collision')

    commands=commands.replace(
        anchor,anchor+'\n\t{ "conjure", 155, hd_cj_command },')

    table.write_text(
        'struct creature; struct cmd;\n'
        'extern int hd_cj_command(struct creature *, struct cmd *);\n'
        +commands,encoding='latin-1')

    help_source=source/'hollowdeep_help.c'
    body=help_source.read_text(encoding='latin-1')
    anchor='    if (count == 2 && !strcmp(token[1], "raiseskeleton"))'
    assert body.count(anchor)==1

    routes="""    if (count == 2 && !strcmp(token[1], "conjure")) return show_page(player, "conjure");
    if (count == 2 && !strcmp(token[1], "rc")) return show_page(player, "raise-corpse");
    if (count == 2 && !strcmp(token[1], "pets")) return show_page(player, "help.154");
    if (count == 3 && !strcmp(token[1], "drain") && !strcmp(token[2], "mana")) return show_page(player, "drain-mana");
"""
    help_source.write_text(
        body.replace(anchor,routes+anchor,1),encoding='latin-1')

    makefile = source / 'Makefile'
    content = makefile.read_text(encoding='latin-1')
    target = 'frp.new: $(OBJECTS)'
    if content.count(target) != 1:
        raise ValueError('Unexpected private runtime link target')
    content = content.replace(target, 'CFLAGS += -DHD_UNDEAD_ARMY_PLAYTEST\n'
                              'CFLAGS += -DHD_CONJURE_RUNTIME\n'
                              'OBJECTS += hd_army_restore.o hd_conjure_runtime.o\n\n' + target)
    makefile.write_text(content, encoding='latin-1')
    log = work / 'build.log'
    with log.open('w') as output:
        result = subprocess.run(
            ['make', '-s', '-B', '-j2', 'NECROMANCER_PLAYTEST=1', 'DEITY_PLAYTEST=1',
             'CORPSE_PLAYTEST=1', 'PET_STORE_PLAYTEST=1', 'PET_RUNTIME_PLAYTEST=1', 'frp.new'],
            cwd=source, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join(log.read_text(errors='replace').splitlines()[-30:]))
        raise SystemExit(result.returncode)
    binary = source / 'frp.new'
    with binary.open('rb') as stream:
        if stream.read(5) != b'\x7fELF\x01':
            raise SystemExit('Expected a private ELF32 game')
    print(f'PASS: private Undead Army ELF32 build {binary}', flush=True)


if __name__ == '__main__':
    main()
