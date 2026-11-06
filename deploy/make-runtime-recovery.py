#!/usr/bin/env python3
"""Build a standalone repair without contacting or modifying the Linode."""
import base64
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import tarfile
import textwrap
import zlib

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SHA = 'c50a99730f83a16e994f941006f2b64b7943b12f6fd60f0d3c087481208d3537'


def original(path):
    spec = importlib.util.spec_from_file_location('native_package', ROOT / 'deploy/make-native-update.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata, kit = module.load_baseline()
    if path == 'public/workshop-files/hollowdeep-server-kit.tar.gz':
        return kit
    name = Path(path).name
    raw = (ROOT / 'deploy/baseline' / name).read_bytes()
    if name not in metadata['files'] or hashlib.sha256(raw).hexdigest() != metadata['files'][name]:
        raise ValueError('Legacy recovery source checksum differs.')
    return raw


def main():
    kit = original('public/workshop-files/hollowdeep-server-kit.tar.gz')
    if hashlib.sha256(kit).hexdigest() != LEGACY_SHA:
        raise ValueError('Legacy kit hash differs from the deployed installer.')
    manifest = {}
    old_runtime = None
    with tarfile.open(fileobj=io.BytesIO(kit), mode='r:gz') as archive:
        for member in archive:
            if member.isfile():
                if not member.name.startswith('hollowdeep-server-kit/'):
                    raise ValueError('Unexpected archive root.')
                name = member.name.removeprefix('hollowdeep-server-kit/')
                content = archive.extractfile(member).read()
                manifest[name] = hashlib.sha256(content).hexdigest()
                if name == 'tests/test_runtime.py':
                    old_runtime = content.decode()
    # This repair targets the old engine, before stance/staff commands existed.
    runtime = original('deploy/recovered-runtime.py').decode()
    if not old_runtime or runtime == old_runtime:
        raise ValueError('No corrected runtime test is available.')
    installer = original('deploy/install-ubuntu.sh').decode()
    marker = 'as_game /usr/bin/python3 "$base/kit/manage.py" build --work "$base/world" --cc "$base/gcc32"\n'
    if installer.count(marker) != 1:
        raise ValueError('Legacy installer continuation differs from reviewed source.')
    continuation = installer[installer.index(marker):]
    resume = '''#!/usr/bin/env bash
set -Eeuo pipefail
umask 027
trap 'printf "Recovery stopped at line %s; keep the output and all existing files.\\n" "$LINENO" >&2' ERR
base=/srv/hollowdeep
admin_name=Realmkeeper
game_port=4040
kit_sha256=''' + LEGACY_SHA + '''
as_game() {
  runuser -u hollowdeep -- env --chdir="$base" PYTHONDONTWRITEBYTECODE=1 "$@"
}
''' + continuation
    data = {'expected_files': manifest, 'old_runtime': old_runtime, 'runtime': runtime,
            'resume': resume, 'enable_public': original('deploy/enable-public.py').decode()}
    packed = zlib.compress(json.dumps(data, sort_keys=True).encode(), level=9)
    encoded = '\n'.join(textwrap.wrap(base64.b64encode(packed).decode(), 96))
    template = (ROOT / 'deploy/recover-runtime.py').read_text()
    placeholder = "PAYLOAD_SHA256 = None\nPAYLOAD_BASE64 = ''"
    if template.count(placeholder) != 1:
        raise ValueError('Recovery template marker differs.')
    code = template.replace(placeholder,
        f'PAYLOAD_SHA256 = "{hashlib.sha256(packed).hexdigest()}"\nPAYLOAD_BASE64 = """\n{encoded}\n"""')
    output = ROOT / 'outputs/hollowdeep-repair.py'
    output.parent.mkdir(exist_ok=True)
    output.write_text(code)
    print(f'Created {output.name}: {len(code.encode())} bytes; SHA256 {hashlib.sha256(code.encode()).hexdigest()}')


if __name__ == '__main__':
    main()
