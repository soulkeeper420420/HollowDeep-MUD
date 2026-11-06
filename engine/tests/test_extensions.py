#!/usr/bin/env python3
"""Compile and exercise the actual extension using original Mordor type headers."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True, help='Original/prepared src_3.00 directory')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
if not (args.source / 'mstruct.h').is_file():
    parser.error('--source must contain mstruct.h and mtype.h')
with tempfile.TemporaryDirectory(prefix='hollowdeep-extension-') as work:
    executable = Path(work) / 'extension-test'
    subprocess.run([
        os.environ.get('CC', 'cc'), '-std=gnu99', '-Wall', '-Wextra', '-Werror',
        '-I', str(args.source.resolve()), '-I', str(root / 'extensions'),
        str(root / 'tests/extension_test.c'), str(root / 'extensions/hollowdeep.c'),
        '-o', str(executable),
    ], check=True)
    subprocess.run([str(executable), work], check=True)
