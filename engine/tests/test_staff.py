#!/usr/bin/env python3
"""Test actual staff commands using native types and isolated account files."""
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
with tempfile.TemporaryDirectory(prefix='hollowdeep-staff-test-') as temporary:
    executable = Path(temporary) / 'staff-test'
    subprocess.run([args.cc, '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-DHOLLOWDEEP_STAFF_TEST_TIME', '-I', str(args.source.resolve()),
                    '-I', str(root / 'extensions'), str(root / 'tests/staff_test.c'),
                    str(root / 'extensions/hollowdeep_staff.c'), '-o', str(executable)], check=True)
    subprocess.run(([args.runner] if args.runner else []) + [str(executable), temporary], check=True, timeout=15)
