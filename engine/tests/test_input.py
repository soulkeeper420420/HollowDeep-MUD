#!/usr/bin/env python3
"""Exercise prepared Mordor accept_input using pipes; no networking is required."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Prepared src_3.00 with normalized io.c')
    parser.add_argument('--cc', default=os.environ.get('CC', 'cc'), help='Compiler executable or wrapper path')
    parser.add_argument('--runner', help='Optional execution helper, such as qemu-i386')
    args = parser.parse_args()
    source = args.source.resolve()
    if any(not (source / filename).is_file() for filename in ('io.c', 'hollowdeep_net.c', 'hollowdeep_net.h')):
        parser.error('--source must contain a freshly prepared engine with hollowdeep_net.c/.h')
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='hollowdeep-input-test-') as temporary:
        executable = Path(temporary) / 'input-test'
        command = [
            args.cc, '-std=gnu89', '-O1', '-fcommon', '-ffunction-sections', '-fdata-sections',
            '-Wno-implicit-function-declaration', '-Wno-int-conversion',
            '-Wno-incompatible-pointer-types', '-Wno-return-type',
            '-I', str(source), '-I', str(root / 'extensions'),
            str(root / 'tests/input_test.c'), str(source / 'io.c'),
            str(source / 'hollowdeep_net.c'), '-Wl,--gc-sections', '-o', str(executable),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise SystemExit('Cannot compile original input integration test:\n' + result.stderr[-8000:])
        run = ([args.runner] if args.runner else []) + [str(executable)]
        subprocess.run(run, check=True, timeout=20)


if __name__ == '__main__':
    main()
