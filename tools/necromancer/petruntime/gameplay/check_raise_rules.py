#!/usr/bin/env python3
"""Stage and test the draft corpse command in a disposable ELF32 fixture."""
import argparse
import ast
from pathlib import Path
import shutil
import subprocess
import tempfile

from stage_corpse import stage, stage_command_and_login

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    source = parser.parse_args().source.resolve(strict=True)
    here = Path(__file__).resolve().parent
    cache = here.parents[1] / 'cache' / 'onepass_linode.py'
    payload = next(node.value for node in ast.parse(cache.read_text()).body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'PAYLOAD'
                           for target in node.targets))

    with tempfile.TemporaryDirectory(prefix='hd-raise-rules-') as storage:
        fixture = Path(storage)
        for name in ('hd_corpse.c', 'global.c', 'player.c'):
            shutil.copyfile(source / name, fixture / name)
        (fixture / 'test_corpse.c').write_text(ast.literal_eval(payload)['test_corpse.c'])
        stage(fixture)
        stage_command_and_login(fixture)
        roster = here.parent / 'roster'
        flags = ['cc', '-m32', '-std=gnu89', '-fcommon', '-ffunction-sections',
                 '-fdata-sections', '-DHD_UNDEAD_ARMY_PLAYTEST', '-DHD_CORPSE_PLAYTEST',
                 '-DHD_NECROMANCER_PLAYTEST', '-DHD_DEITY_PLAYTEST',
                 '-DHD_PET_RUNTIME_PLAYTEST', '-DHD_PET_STORE_PLAYTEST',
                 '-I', str(fixture), '-I', str(source), '-I', str(roster)]
        executable = fixture / 'check-raise-rules'
        subprocess.run(flags + ['-Wl,--gc-sections',
                       str(fixture / 'hd_corpse.c'), str(roster / 'hd_pet_roster.c'),
                       str(here / 'test_army_corpse.c'), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], cwd=fixture, check=True)


if __name__ == '__main__':
    main()
