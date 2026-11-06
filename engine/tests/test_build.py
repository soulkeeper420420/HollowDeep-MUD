#!/usr/bin/env python3
"""Exercise real role, builder, audit and persistence code in a disposable world."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
parser.add_argument('--runner')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='hollowdeep-build-test-') as temporary:
    executable = Path(temporary) / 'build-test'
    subprocess.run([args.cc, '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-DHOLLOWDEEP_STAFF_TEST_TIME', '-I', str(args.source.resolve()),
                    '-I', str(root / 'extensions'), str(root / 'tests/build_test.c'),
                    str(root / 'extensions/hollowdeep_staff.c'),
                    str(root / 'extensions/hollowdeep_ranges.c'),
                    str(root / 'extensions/hollowdeep_bonus.c'),
                    str(root / 'extensions/hollowdeep_build.c'), '-o', str(executable)], check=True)
    subprocess.run(([args.runner] if args.runner else []) + [str(executable), temporary], check=True, timeout=20)
