#!/usr/bin/env python3
"""Replay the corrected private Necromancer runner against a pinned existing ELF32.

Use the operator's corrected onepass_linode.py as RUNNER. Pass the existing
private runtime directory and its accepted SHA256, then the same prior and cache
replay files used by onepass_linode.py. Run under unshare --net --mount --fork.
Use --prepare-only to inspect which north calls need correction without running
the native game. The original runner and accepted runtime are read only.
"""

import argparse
import ast
import hashlib
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import tempfile


ROOT = Path('/root/hollowdeep-dev')
RETRY = '''    def replay_north(client):
        destination = 'Necromancer Trial Annex'
        cooldown = re.compile(r'please wait (\\d+) more seconds?\\b', re.I)
        deadline = time.monotonic() + 30
        for attempt in range(6):
            reply = command(client, 'north')
            if destination.casefold() in reply.casefold():
                return
            wait = cooldown.search(reply)
            if wait is None:
                require(view(client), destination)
                return
            delay = int(wait.group(1)) + 0.2
            if attempt == 5 or time.monotonic() + delay >= deadline:
                break
            time.sleep(delay)
        raise RuntimeError('North movement cooldown exceeded retry budget')
'''


def extract_payload(runner):
    module = ast.parse(runner.read_text(encoding='utf-8'))
    (assignment,) = [
        node for node in module.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'PAYLOAD'
                for target in node.targets)
    ]
    return ast.literal_eval(assignment.value)


def correct_movement(source):
    (replay,) = [
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == 'replay'
    ]
    pending = []
    for node in ast.walk(replay):
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
            continue
        call = node.value
        if not (isinstance(call.func, ast.Name) and call.func.id == 'command'
                and len(call.args) == 2 and isinstance(call.args[0], ast.Name)
                and call.args[0].id in {'owner', 'faithful'}
                and isinstance(call.args[1], ast.Constant)
                and call.args[1].value == 'north'):
            continue
        pending.append(call)

    if not pending:
        return source, 0

    lines = source.splitlines(keepends=True)
    for call in sorted(pending, key=lambda value: (value.lineno, value.col_offset),
                       reverse=True):
        if call.lineno != call.end_lineno:
            raise ValueError('Review multiline north command before replay')
        idx = call.lineno - 1
        line = lines[idx].encode('utf-8')
        replacement = f'replay_north({call.args[0].id})'.encode('utf-8')
        lines[idx] = (line[:call.col_offset] + replacement
                      + line[call.end_col_offset:]).decode('utf-8')
    lines.insert(replay.body[0].lineno - 1, RETRY)
    corrected = ''.join(lines)
    compile(corrected, '<runtime_gameplay>', 'exec')
    return corrected, len(pending)


def stage_payload(work, payload, replay):
    package = work / 'pkg'
    package.mkdir()
    for name, body in payload.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('Invalid replay payload path: ' + name)
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(replay if name == 'runtime_gameplay.py' else body,
                        encoding='ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runner', type=Path)
    parser.add_argument('runtime', type=Path)
    parser.add_argument('sha256')
    parser.add_argument('prior', type=Path)
    parser.add_argument('cache', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    payload = extract_payload(args.runner)
    source = payload['runtime_gameplay.py']
    replay, changed = correct_movement(source)
    print(f'Direct north calls wrapped: {changed}', flush=True)
    if args.prepare_only:
        return
    if hashlib.sha256(source.encode('utf-8')).hexdigest() == (
            '0df714323655d2d38353d8a64121615e78541249a6ae152b8aaaaeb05db7b369'):
        raise SystemExit('Published replay lacks the durable logout and disk assertions; '
                         'use the corrected operator checkout')
    if os.geteuid() or os.readlink('/proc/self/ns/net') == os.readlink('/proc/1/ns/net'):
        raise SystemExit('Replay requires root and an isolated network namespace')
    runtime = args.runtime.resolve(strict=True)
    src = runtime / 'src'
    if (runtime.parent != ROOT or not runtime.name.startswith('necromancer-playtest-runtime-')
            or src.is_symlink() or any(entry.is_symlink() for entry in src.rglob('*'))):
        raise SystemExit('Expected private runtime source under the development root')
    exe = src / 'frp.new'

    def check_binary(path):
        with path.open('rb') as stream:
            if stream.read(5) != b'\x7fELF\x01':
                raise RuntimeError('Expected ELF32 binary')
            stream.seek(0)
            if hashlib.file_digest(stream, 'sha256').hexdigest() != args.sha256:
                raise RuntimeError('Private runtime checksum mismatch')

    def production_pid():
        value = subprocess.check_output(
            ['systemctl', 'show', 'hollowdeep.service', '-p', 'MainPID', '--value'],
            text=True).strip()
        if not value.isdecimal() or int(value) < 1:
            raise RuntimeError('Expected a running production service')
        return value

    check_binary(exe)
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    before = production_pid()
    try:
        work = Path(tempfile.mkdtemp(prefix='necromancer-playtest-runtime-', dir=ROOT))
        copied = work / 'src'
        shutil.copytree(src, copied)
        check_binary(copied / 'frp.new')
        stage_payload(work, payload, replay)
        print(f'Private replay results: {work}', flush=True)
        scope = {'__name__': 'runtime_gameplay'}
        exec(compile(replay, '<runtime_gameplay>', 'exec'), scope)
        scope['replay'](copied, {key[5:]: value for key, value in payload.items()
                               if key.startswith('help/')},
                        args.prior.resolve(strict=True), args.cache.resolve(strict=True), work)
    finally:
        if production_pid() != before:
            raise RuntimeError('Production service PID changed during replay')
        print('PRODUCTION SERVICE PID: UNCHANGED', flush=True)
        check_binary(exe)


if __name__ == '__main__':
    main()
