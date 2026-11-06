#!/usr/bin/env python3
"""Exercise help, skills, native permissions and private staff chat with real tables."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
parser.add_argument('--runner')
args = parser.parse_args()
source = args.source.resolve()
root = Path(__file__).resolve().parents[1]
global_c = (source / 'global.c').read_text()
commands = re.findall(r'\{\s*"([^"]+)"\s*,\s*(-?\d+)\s*,', global_c.split('cmdlist[] = {', 1)[1].split('};', 1)[0])
spells = re.findall(r'\{\s*"([^"]+)"\s*,\s*(-?\d+)\s*,', global_c.split('spllist[] = {', 1)[1].split('};', 1)[0])
commands = [(name, number) for name, number in commands if number != '0']
spells = re.findall(r'\{\s*"([^"]+)"\s*,\s*(S[A-Z0-9_]+)\s*,', global_c.split('spllist[] = {', 1)[1].split('};', 1)[0])
assert commands and spells
for name, number in commands:
    assert (source.parent / 'help' / f'help.{number}').is_file(), f'Missing help for {name}'
with tempfile.TemporaryDirectory(prefix='hollowdeep-help-test-') as temporary:
    work = Path(temporary)
    shutil.copytree(source.parent / 'help', work / 'help')
    declarations = []
    for table, rows, field in [('cmdlist', commands, 'cmd'), ('spllist', spells, 'spl')]:
        declarations.append(f'struct {{ char *{field}str; int {field}no; int (*{field}fn)(); }} {table}[] = {{')
        declarations.extend(f'{{"{name}", {number}, 0}},' for name, number in rows)
        declarations.append('{0, ' + ('0' if field == 'cmd' else '-1') + ', 0}};')
    (work / 'test_tables.h').write_text('\n'.join(declarations))
    executable = work / 'help-test'
    subprocess.run([args.cc, '-std=gnu99', '-O2', '-D_FORTIFY_SOURCE=3', '-fstack-protector-strong',
                    '-Wall', '-Wextra', '-Werror', '-DHOLLOWDEEP_STAFF_TEST_TIME',
                    '-I', str(source), '-I', str(root / 'extensions'), '-I', str(work),
                    str(root / 'tests/help_test.c'), str(root / 'extensions/hollowdeep_help.c'),
                    str(root / 'extensions/hollowdeep_staff.c'), str(root / 'extensions/hollowdeep_ranges.c'),
                    '-o', str(executable)], check=True)
    subprocess.run(([args.runner] if args.runner else []) + [str(executable), temporary], check=True, timeout=25)
print(f'PASS: help files cover {len(set(name for name, _ in commands))} registered command names/aliases')
