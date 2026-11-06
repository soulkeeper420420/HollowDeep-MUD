#!/usr/bin/env python3
"""Package reviewed source into a pasteable console block; no server changes."""
import base64
import hashlib
import html
import json
import lzma
from pathlib import Path
import tarfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
kit = ROOT / 'public/workshop-files/hollowdeep-server-kit.tar.gz'
if hashlib.sha256(kit.read_bytes()).hexdigest() != '946d69e0afb2be03964a4b76eb51dc5b0945aa26e57e3c7304b46e2347e89cb3':
    raise SystemExit('The corrected source kit has changed; review it before generating an installer.')
files = {}
with tarfile.open(kit, 'r:gz') as archive:
    for member in archive:
        if member.isfile() and not member.name.endswith('/Mordor_3.00.tar.gz'):
            relative = member.name.removeprefix('hollowdeep-server-kit/')
            files['kit/' + relative] = archive.extractfile(member).read().decode('utf-8')
for filename in ('install-ubuntu.sh', 'enable-public.py', 'README.md'):
    files[filename] = (ROOT / 'deploy' / filename).read_text()
packed = lzma.compress(json.dumps(files, sort_keys=True).encode(), preset=9)
encoded = '\n'.join(textwrap.wrap(base64.b64encode(packed).decode(), 96))
template = (ROOT / 'deploy/console-bootstrap.py').read_text()
placeholder = "PAYLOAD_SHA256 = None\nPAYLOAD_BASE64 = ''"
assert template.count(placeholder) == 1
code = template.replace(placeholder, f'PAYLOAD_SHA256 = "{hashlib.sha256(packed).hexdigest()}"\nPAYLOAD_BASE64 = """\n{encoded}\n"""')
block = "python3 - <<'HOLLOWDEEP_CONSOLE_SETUP'\n" + code + '\nHOLLOWDEEP_CONSOLE_SETUP\n'
output = ROOT / 'outputs'
output.mkdir(exist_ok=True)
(output / 'hollowdeep-console-setup.txt').write_text(block)
(output / 'hollowdeep-console-setup.html').write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hollowdeep console installer</title>
<style>body{max-width:850px;margin:3rem auto;padding:0 1.2rem;background:#171c20;color:#e6eceb;font:17px/1.6 system-ui}button{background:#e3bb70;color:#171c20;border:0;border-radius:8px;padding:14px 24px;font:600 17px system-ui;cursor:pointer}textarea{width:100%;height:340px;box-sizing:border-box;background:#0e1215;color:#dce8e3;border:1px solid #52605b;padding:14px;font:12px/1.4 monospace}code{color:#e3bb70}#status{min-height:2em}</style>
<h1>Install Hollowdeep from Lish</h1>
<p>Target: <strong>172.233.176.81</strong> · Ubuntu 24.04 · x86_64</p>
<p>Copy this complete setup block, paste it into the signed-in <strong>root Lish console</strong>, and press Enter if needed. There is no SCP or file-upload step.</p>
<p>It verifies the target, downloads the original distribution with a pinned checksum, installs the 32-bit toolchain, builds and tests the corrected engine, then starts it on localhost for administrator creation. Existing installations are preserved. It does not purchase services, reboot, or open public access yet.</p>
<button id="copy" type="button">Copy complete installer</button><p id="status" aria-live="polite"></p>
<details><summary>Review the commands and embedded source</summary>
<p>The compressed section contains the reviewed kit source and deployment scripts, without passwords or keys. The installer verifies its checksum before extracting it. The original Mordor archive is downloaded separately and verified.</p></details>
<textarea id="commands" aria-label="Complete console setup block" readonly>''' + html.escape(block) + '''</textarea>
<p>When it finishes, use <code>telnet 127.0.0.1 4040</code> to create <strong>Realmkeeper</strong>. Choose the game password privately in that console, then <code>save</code> and <code>quit</code>. The installer prints the next command for opening native MUD access.</p>
<p>If installation stops, keep the error output and share it in the chat. This page only copies commands; installation happens after you paste them into Lish.</p>
<script>const area=document.getElementById('commands'),status=document.getElementById('status');document.getElementById('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(area.value);status.textContent='Copied. Paste the complete block into the root Lish console.'}catch{area.focus();area.select();status.textContent=document.execCommand('copy')?'Copied. Paste into the root Lish console.':'Commands selected. Press Ctrl+C (or Command+C), then paste into Lish.'}});</script></html>''')
print(f'Created console setup: {len(block.encode())} bytes, {len(files)} embedded source files; original game archive fetched separately.')
