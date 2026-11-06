#!/usr/bin/env python3
"""Bundle the exact reviewed updater variants into one uploadable file."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import textwrap
import zlib

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('hollowdeep-native-update.py', 'hollowdeep-native-update-from-repair.py',
         'hollowdeep-native-update-from-legacy.py')


def build():
    release = ROOT / 'deploy/artifacts'
    metadata = json.loads((release / 'RELEASE.json').read_text())
    records = {item['file']: item for item in metadata['artifacts']}
    artifacts, predecessors, files = {}, {}, {}
    for name in NAMES:
        raw = (release / name).read_bytes()
        expected = records[name]
        if hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError(f'Reviewed file checksum differs: {name}')
        payloads = [ast.literal_eval(node.value) for node in ast.parse(raw).body
                    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == 'PAYLOAD_SHA256']
        if payloads != [expected['payload_sha256']]:
            raise ValueError(f'Reviewed payload checksum differs: {name}')
        artifacts[name] = {key: expected[key] for key in ('sha256', 'payload_sha256')}
        if name != 'hollowdeep-native-update-from-legacy.py':
            predecessor = metadata['native_predecessors'][name]
            if len(predecessor) != 64 or any(ch not in '0123456789abcdef' for ch in predecessor):
                raise ValueError('Invalid predecessor identifier.')
            predecessors[predecessor] = name
        files[name] = raw.decode('utf-8')
    packed = zlib.compress(json.dumps(files, sort_keys=True).encode(), 9)
    replacements = {
        'ARTIFACTS = {}': 'ARTIFACTS = ' + repr(artifacts),
        'PREDECESSORS = {}': 'PREDECESSORS = ' + repr(predecessors),
        "BUNDLE_SHA256 = ''": 'BUNDLE_SHA256 = ' + repr(hashlib.sha256(packed).hexdigest()),
        "BUNDLE_BASE64 = ''": 'BUNDLE_BASE64 = """\n' + '\n'.join(textwrap.wrap(base64.b64encode(packed).decode(), 96)) + '\n"""',
    }
    code = (ROOT / 'deploy/select-native-update.py').read_text()
    for before, after in replacements.items():
        if code.count(before) != 1:
            raise ValueError('Launcher template differs.')
        code = code.replace(before, after, 1)
    compile(code, 'hollowdeep-update.py', 'exec')
    target = ROOT / 'outputs/hollowdeep-update.py'
    target.parent.mkdir(exist_ok=True)
    target.write_text(code)
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.sha256').write_text(f'{sha}  {target.name}\n')
    print(f'Created {target.name}: {target.stat().st_size} bytes; SHA256 {sha}')
    return target


if __name__ == '__main__':
    build()
