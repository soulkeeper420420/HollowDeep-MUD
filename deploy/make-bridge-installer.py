#!/usr/bin/env python3
"""Generate an uploadable bridge installer containing only its public key."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import textwrap
import zlib

def main():
    root = Path(__file__).resolve().parents[1]
    template_path = root / 'deploy/install-bridge.py'
    spec = importlib.util.spec_from_file_location('bridge_installer', template_path)
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    config = json.loads((root / 'deploy/bridge-public.json').read_text())
    if config.get('host') != installer.TARGET_IP:
        raise ValueError('Public bridge configuration targets another host.')
    lock = json.loads((root / 'server/package-lock.json').read_text())
    ws = lock['packages']['node_modules/ws']
    data = {'public_key_spki': config['public_key_spki'], 'origin': config['origin'],
            'files': {name: (root / 'server' / name).read_text() for name in ('index.mjs', 'protocol.mjs', 'package.json', 'package-lock.json')},
            'ws_url': ws['resolved'], 'ws_integrity': ws['integrity']}
    packed = zlib.compress(json.dumps(data, sort_keys=True).encode(), 9)
    encoded = '\n'.join(textwrap.wrap(base64.b64encode(packed).decode(), 96))
    checksum = hashlib.sha256(packed).hexdigest()
    installer.decode_payload(encoded, checksum)
    template = template_path.read_text()
    marker = "PAYLOAD_SHA256 = None\nPAYLOAD_BASE64 = ''"
    if template.count(marker) != 1:
        raise ValueError('Installer template marker differs.')
    source = template.replace(marker, f'PAYLOAD_SHA256 = "{checksum}"\nPAYLOAD_BASE64 = """\n{encoded}\n"""')
    target = root / 'outputs/hollowdeep-browser-setup.py'
    target.parent.mkdir(exist_ok=True)
    target.write_text(source)
    print(f'Created {target.name}: {len(source.encode())} bytes. Public verification key only.')


if __name__ == '__main__':
    main()
