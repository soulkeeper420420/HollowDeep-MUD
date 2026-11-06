#!/usr/bin/env python3
"""Generate one uploadable updater from reviewed engine files and a pinned baseline."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import textwrap
import zlib

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SHA = 'c50a99730f83a16e994f941006f2b64b7943b12f6fd60f0d3c087481208d3537'
BASELINE_SHA = '25b4683edcf86572a3d204bc392e8c71440b2bc2b943cd7de935cc554dbfc47f'


def load_baseline():
    baseline = ROOT / 'deploy/baseline'
    raw = (baseline / 'baseline.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA:
        raise ValueError('Legacy baseline metadata checksum differs.')
    metadata = json.loads(raw)
    kit = (baseline / 'legacy-kit.tar.gz').read_bytes()
    if hashlib.sha256(kit).hexdigest() != LEGACY_SHA or metadata['kit_sha256'] != LEGACY_SHA:
        raise ValueError('Legacy source checksum differs.')
    return metadata, kit


def import_manage(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_files(path):
    result = {}
    for item in path.rglob('*'):
        if item.is_file() and '__pycache__' not in item.parts and not item.name.startswith('.'):
            if item.is_symlink():
                raise ValueError('Linked source files are not supported.')
            result[item.relative_to(path).as_posix()] = item.read_bytes()
    return result


def prepared_files(world):
    result = {'src_3.00/' + name: content for name, content in source_files(world / 'src_3.00').items()}
    result.update({'help/' + name: content for name, content in source_files(world / 'help').items()})
    return result


def main():
    baseline, kit_archive = load_baseline()
    old_kit = {}
    with tarfile.open(fileobj=io.BytesIO(kit_archive), mode='r:gz') as bundle:
        for member in bundle:
            if member.isfile():
                if not member.name.startswith('hollowdeep-server-kit/'):
                    raise ValueError('Unexpected baseline path.')
                old_kit[member.name.removeprefix('hollowdeep-server-kit/')] = bundle.extractfile(member).read()
    engine = source_files(ROOT / 'engine')
    with tempfile.TemporaryDirectory(prefix='hollowdeep-update-package-') as temporary:
        temp = Path(temporary)
        for name, content in old_kit.items():
            target = temp / 'legacy-kit' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        old_manage = import_manage(temp / 'legacy-kit/manage.py', 'hollowdeep_baseline')
        new_manage = import_manage(ROOT / 'engine/manage.py', 'hollowdeep_update')
        archive = temp / 'legacy-kit/Mordor_3.00.tar.gz'
        old_world = old_manage.prepare_archive(archive, temp / 'old-world', 'Realmkeeper')
        new_world = new_manage.prepare_archive(archive, temp / 'new-world', 'Realmkeeper')
        before, after = prepared_files(old_world), prepared_files(new_world)
        if before['src_3.00/mstruct.h'] != after['src_3.00/mstruct.h']:
            raise ValueError('Serialized structure definitions changed; this requires a different migration.')
        if set(before) - set(after):
            raise ValueError('Removing source or help files requires a separately reviewed migration.')
        changes = {name: content for name, content in after.items() if before.get(name) != content}
        if not changes:
            raise ValueError('There are no native source changes to deploy.')
    tests = [
        ['/usr/bin/python3', '{kit}/tests/test_prepare.py', '--archive', '{archive}'],
        ['/usr/bin/python3', '{kit}/tests/test_extensions.py', '--source', '{source}'],
        ['/usr/bin/python3', '{kit}/tests/test_network.py', '--source', '{source}', '--cc', '{cc}'],
        ['/usr/bin/python3', '{kit}/tests/test_input.py', '--source', '{source}', '--cc', '{cc}'],
        ['/usr/bin/python3', '{kit}/tests/test_runtime_client.py'],
        ['/usr/bin/python3', '{kit}/tests/test_runtime.py', '--archive', '{archive}', '--cc', '{cc}'],
    ]
    # Optional new native modules use the same explicit source/compiler interface.
    for name in ('test_staff.py', 'test_stance.py'):
        if 'tests/' + name in engine:
            tests.insert(-1, ['/usr/bin/python3', '{kit}/tests/' + name, '--source', '{source}', '--cc', '{cc}'])
    data = {
        'engine': {name: base64.b64encode(content).decode() for name, content in engine.items()},
        'kit_baseline': {name: hashlib.sha256(content).hexdigest() for name, content in old_kit.items()},
        'world_baseline': {name: hashlib.sha256(content).hexdigest() for name, content in before.items()},
        'world_updates': {name: base64.b64encode(content).decode() for name, content in changes.items()},
        'runtime_fix_sha': baseline['runtime_fix_sha'],
        'unit_text': baseline['unit_text'],
        'tests': tests,
    }
    packed = zlib.compress(json.dumps(data, sort_keys=True).encode(), 9)
    checksum = hashlib.sha256(packed).hexdigest()
    encoded = '\n'.join(textwrap.wrap(base64.b64encode(packed).decode(), 96))
    template = (ROOT / 'deploy/update-native.py').read_text()
    marker = "PAYLOAD_SHA256 = None\nPAYLOAD_BASE64 = ''"
    if template.count(marker) != 1:
        raise ValueError('The updater template marker differs.')
    code = template.replace(marker, f'PAYLOAD_SHA256 = "{checksum}"\nPAYLOAD_BASE64 = """\n{encoded}\n"""')
    output = ROOT / 'outputs/hollowdeep-native-update.py'
    output.parent.mkdir(exist_ok=True)
    output.write_text(code)
    print(f'Created {output.name}: {len(code.encode())} bytes; {len(changes)} source/help changes; payload {checksum}.')


if __name__ == '__main__':
    main()
