#!/usr/bin/env python3
"""Exercise actual stance code against original Mordor types, without sockets."""
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
if not (args.source / 'mstruct.h').is_file():
    parser.error('--source must contain original Mordor headers')
with tempfile.TemporaryDirectory(prefix='hollowdeep-stance-test-') as temporary:
    executable = Path(temporary) / 'stance-test'
    subprocess.run([
        args.cc, '-std=gnu99', '-Wall', '-Wextra', '-Werror',
        '-DHOLLOWDEEP_STANCE_TEST_TIME',
        '-I', str(args.source.resolve()), '-I', str(root / 'extensions'),
        str(root / 'tests/stance_test.c'), str(root / 'extensions/hollowdeep_stance.c'),
        '-o', str(executable),
    ], check=True)
    command = ([args.runner] if args.runner else []) + [str(executable), temporary]
    subprocess.run(command, check=True)
