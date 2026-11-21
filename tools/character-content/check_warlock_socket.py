#!/usr/bin/env python3
"""Round 78E private real-socket Warlock creation + durable receipt regression.

Run as root in a separate network namespace, against a disposable ELF32
source tree already staged from the Round 77 candidate. Never accesses live.
"""
import ast
import os
from pathlib import Path
import re
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
GAMEPLAY=HERE.parent/'necromancer/petruntime/gameplay'
NECRO=HERE.parent/'necromancer'
SRC=Path(sys.argv[1]).resolve(strict=True)

if (os.geteuid()!=0 or
        os.readlink('/proc/self/ns/net')==os.readlink('/proc/1/ns/net') or
        SRC.name!='src' or SRC.parent.parent!=Path('/tmp') or
        not SRC.parent.name.startswith('hd-army-game-round78-') or
        SRC.is_symlink() or not (SRC/'frp.new').is_file()):
    raise SystemExit('Private root, network namespace and disposable build required')

prior=runpy.run_path(str(NECRO/'corpse/gameplay_smoke.py'))
cache=runpy.run_path(str(NECRO/'cache/cache_gameplay.py'))
army=runpy.run_path(str(GAMEPLAY/'check_army_socket.py'))

WORLD=Path(tempfile.mkdtemp(prefix='hd-warlock-socket-'))
print('Private Warlock world:',WORLD,flush=True)

for name in ('rooms','player','log','objmon','post','help','bin','hollowdeep-data'):
    (WORLD/name).mkdir()

anchor='    strcpy(mage.name, "Hdfaithqa");'
assert prior['SOURCE'].count(anchor)==1
prior['SOURCE']=prior['SOURCE'].replace(
    anchor,anchor+'\n    mage.class=FIGHTER;\n    mage.level=40;')

army['seed'](SRC,WORLD,prior,cache)

for page in (GAMEPLAY/'help').iterdir():
    if page.is_file():
        shutil.copyfile(page,WORLD/'help'/page.name)
shutil.copyfile(SRC/'help/warlock',WORLD/'help/warlock')

# Existing Round 75F creation fixture creates native fallback room IDs;
# never read or copy the production world.
room_ids=set(range(201))
for path in (SRC/'player.c',SRC/'command1.c'):
    body=path.read_text(encoding='latin-1')
    for match in re.finditer(r'(?:rom_num\s*=\s*|load_rom\s*\(\s*)(\d+)',body):
        room_ids.add(int(match[1]))
for number in room_ids:
    if 0<=number<=99999:
        destination=WORLD/'rooms'/f'r{number:05d}'
        if not destination.exists():
            shutil.copyfile(WORLD/'rooms/r00002',destination)

# Reuse the verified text-driven creation parser rather than duplicate it.
parser_file=GAMEPLAY/'check_new_character.py'
tree=ast.parse(parser_file.read_text())
tree.body=[node for node in tree.body
           if isinstance(node,ast.FunctionDef) and node.name=='create']
scope={'prior':prior,'require':prior['require'],'re':re}
exec(compile(tree,str(parser_file),'exec'),scope)
create=scope['create']

probe=WORLD/'warlock-receipt-probe'
cmd=[
    'cc','-m32','-std=gnu89','-O1','-fcommon',
    '-DCOMPRESS','-DHD_NECROMANCER_PLAYTEST',
    '-DHD_WARLOCK_PLAYTEST','-DHD_PET_STORE_PLAYTEST',
    '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
    '-Wno-implicit-function-declaration','-Wno-int-conversion',
    '-Wno-incompatible-pointer-types','-I',str(SRC),
    str(HERE/'test_native_warlock_identity.c'),
    *[str(SRC/(name+'.c')) for name in (
        'files1','files3','compress','hd_player_store',
        'treasure_receipt','atomic_player_snapshot',
        'hd74_xp','hd74_progression')],
    '-o',str(probe),
]
subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)

prior['prepare_chroot'](SRC/'frp.new',WORLD)

with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]

log=WORLD/f'listener-{port}.log'
process=None
try:
    with log.open('wb') as out:
        process=subprocess.Popen([
            shutil.which('chroot'),
            '--userspec=65534:65534','--groups=65534',str(WORLD),
            '/bin/hollowdeep',str(port)],
            cwd=WORLD,
            env={'PATH':'/usr/bin:/bin','HOLLOWDEEP_BIND':'127.0.0.1'},
            stdout=out,stderr=subprocess.STDOUT)

    name='Hdwarcreate'
    with prior['connect_game'](port,process) as client:
        submitted=create(client,name,'Warlock')
        assert submitted is not None
        skills=prior['command'](client,'skills')
        prior['require'](skills,'conjure [all classes]')
        assert 'raise corpse [eligible]' not in skills.lower()
        guide=prior['command'](client,'help warlock')
        prior['require'](guide,'PRIVATE CHARACTER-CREATION TEST')
        prior['require'](prior['command'](client,'save'),'Player saved.')
        prior['quit_with_cooldown'](client,process)

    with tempfile.TemporaryDirectory(prefix='hd-warlock-receipt-check-') as scratch:
        scratch=Path(scratch)
        (scratch/'player').mkdir()
        shutil.copyfile(WORLD/'player'/name,scratch/'player'/name)
        env=dict(os.environ)
        env['HD_PRIVATE_WARLOCK_TEST_ROOT']=str(scratch)
        result=subprocess.check_output([str(probe),name],cwd=scratch,
                                       env=env,text=True)
        print(result.strip(),flush=True)

    with prior['connect_game'](port,process) as client:
        prior['recv_until'](client,b'Please enter name:')
        prior['send'](client,name)
        prior['recv_until'](client,b'Please enter password:')
        prior['send'](client,'Fixturepass')
        prior['recv_until'](client,b'Necromancer Grave Trial',seconds=15)
        skills=prior['command'](client,'skills')
        prior['require'](skills,'conjure [all classes]')
        assert 'raise corpse [eligible]' not in skills.lower()
        print('PASS: Warlock reconnected and remains excluded from Raise Corpse',flush=True)
    print('ROUND 78E: NATIVE WARLOCK CREATION AND RECONNECT PASS',flush=True)
except Exception:
    if log.exists():
        print('PRIVATE LISTENER LOG (tail):',log.read_text(errors='replace')[-2200:],flush=True)
    raise
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
