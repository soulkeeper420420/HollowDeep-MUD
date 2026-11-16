#!/usr/bin/env python3
"""Install Round 73H test-gated evidence only in an isolated native source COPY.

Production, the running world and the previously validated candidate are
never valid targets. This script does not start, stop or signal any process.
"""
from pathlib import Path
import hashlib
import sys

GUARD_SHA = 'b6cbf96854855d9079ca543a0b8689d21d4e523cc9b6db35089060aa55cfb598'


def install(source, package):
    raw = Path(source)
    if raw.is_symlink():
        raise ValueError('Symlinked source directory refused')
    src = raw.resolve(strict=True)
    pkg = Path(package).resolve(strict=True)
    root = Path('/root/hollowdeep-dev')
    if root not in src.parents or src == root:
        raise ValueError('Only private /root/hollowdeep-dev source copies permitted')
    required = ('treasure_guard.c', 'Makefile', 'mstruct.h', 'mtype.h', 'mextern.h')
    for name in required:
        f = src / name
        if not f.is_file() or f.is_symlink():
            raise ValueError('Missing or linked private file: ' + name)
    original = (src / 'treasure_guard.c').read_bytes()
    if hashlib.sha256(original).hexdigest() != GUARD_SHA:
        raise ValueError('Native guard source drift or already patched')
    mk = (src / 'Makefile').read_text(encoding='latin-1')
    if mk.count('treasure_guard.o') != 1 or mk.count('CFLAGS =') != 1 or \
       'hd_guard_proof.o' in mk or 'HD_GUARD_EVIDENCE_TEST' in mk:
        raise ValueError('Makefile not the expected native candidate')
    for name in ('hd_guard_proof.c', 'hd_guard_proof.h'):
        if (src / name).exists() or not (pkg / name).is_file():
            raise ValueError('Source already patched or payload absent: ' + name)
    # Validate the entire patch before writing anything.
    import tempfile
    from subprocess import run
    with tempfile.TemporaryDirectory() as tmp:
        guard_file = Path(tmp) / 'treasure_guard.c'
        run([sys.executable, str(pkg / 'build_guard_variant.py'),
             str(src / 'treasure_guard.c'), str(guard_file)], check=True,
            capture_output=True)
        new_guard = guard_file.read_bytes()
    original_line = next(line for line in mk.splitlines() if line.startswith('CFLAGS ='))
    new_line = original_line + ' -DHD_GUARD_EVIDENCE_TEST'
    new_mk = mk.replace(original_line, new_line, 1).replace(
        'treasure_guard.o', 'treasure_guard.o hd_guard_proof.o', 1)
    # All writes occur only after exact guards and staged generation passed.
    for name in ('hd_guard_proof.c', 'hd_guard_proof.h'):
        (src / name).write_bytes((pkg / name).read_bytes())
    (src / 'treasure_guard.c').write_bytes(new_guard)
    (src / 'Makefile').write_text(new_mk, encoding='latin-1')
    print('ROUND 73H: verified private guardian-evidence source installed')
    print('REWARDS: DISABLED; no production or service changes')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: install_private.py PRIVATE_SOURCE_COPY PACKAGE_DIR')
    install(sys.argv[1], sys.argv[2])
