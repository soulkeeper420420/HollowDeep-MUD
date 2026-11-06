#!/usr/bin/env python3
"""Compile/test real engine CRLF and Telnet input normalization without sockets."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Prepared/original src_3.00 with mtype.h')
    parser.add_argument('--cc', default=os.environ.get('CC', 'cc'), help='Compiler executable or wrapper path')
    parser.add_argument('--runner', help='Optional execution helper, such as qemu-i386')
    args = parser.parse_args()
    if not (args.source / 'mtype.h').is_file():
        parser.error('--source must contain the original mtype.h')
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='hollowdeep-network-test-') as temporary:
        executable = Path(temporary) / 'network-test'
        subprocess.run([
            args.cc, '-std=gnu89', '-Wall', '-Wextra', '-Werror',
            '-I', str(args.source.resolve()), '-I', str(root / 'extensions'),
            str(root / 'tests/network_test.c'), str(root / 'extensions/hollowdeep_net.c'),
            '-o', str(executable),
        ], check=True, timeout=60)
        command = ([args.runner] if args.runner else []) + [str(executable)]
        subprocess.run(command, check=True, timeout=20)


if __name__ == '__main__':
    main()
