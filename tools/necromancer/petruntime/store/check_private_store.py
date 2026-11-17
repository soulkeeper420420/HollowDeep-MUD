#!/usr/bin/env python3
"""Stage and run both native storage suites in one disposable directory."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from stage_roster import stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--native64', action='store_true')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    work = Path(tempfile.mkdtemp(prefix='hd-roster-store-'))
    print('Private roster results:', work, flush=True)
    source = work / 'src'
    stage(args.source, source)
    # Extract the published fixture as data. Its Linode main is never invoked.
    import ast
    legacy = here.parents[1] / 'petstore' / 'onepass_linode.py'
    payload = next(node.value for node in ast.parse(legacy.read_text()).body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'PAYLOAD'
                           for target in node.targets))
    fixture_source = work / 'test_pet_store.c'
    fixture_source.write_text(ast.literal_eval(payload)['test_pet_store.c'])
    command = [os.environ.get('CC', 'cc'), '-m64' if args.native64 else '-m32',
               '-std=gnu89', '-O1', '-g', '-fcommon', '-DCOMPRESS',
               '-Wno-implicit-function-declaration', '-Wno-int-conversion',
               '-Wno-incompatible-pointer-types',
               '-DHD_NECROMANCER_PLAYTEST', '-DHD_PET_STORE_PLAYTEST',
               '-DHD_ATOMIC_TESTING', '-ffunction-sections', '-fdata-sections',
               '-Wl,--gc-sections', '-I', str(source), '-I', str(work)]
    components = [str(source / (name + '.c')) for name in
                  ('files1', 'files3', 'compress', 'hd_player_store',
                   'treasure_receipt', 'atomic_player_snapshot', 'hd74_xp', 'hd74_progression')]
    env = dict(os.environ)
    env.pop('HD_ATOMIC_FAIL', None)
    for test, path in [('legacy', fixture_source), ('roster', here / 'test_roster_store.c')]:
        executable = work / ('test-' + test)
        subprocess.run(command + [str(path)] + components + ['-o', str(executable)], check=True)
        with executable.open('rb') as binary:
            if binary.read(5) != (b'\x7fELF\x02' if args.native64 else b'\x7fELF\x01'):
                raise RuntimeError('Unexpected test executable architecture')
        fixture = work / test
        (fixture / 'player').mkdir(parents=True)
        subprocess.run([str(executable)], cwd=fixture, env=env, check=True)


if __name__ == '__main__':
    main()
