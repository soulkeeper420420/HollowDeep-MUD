#!/usr/bin/env python3
import os
import re
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parents[1]
src=Path(sys.argv[1]).resolve(strict=True)

assert os.geteuid()==0
assert os.readlink('/proc/self/ns/net')!=os.readlink('/proc/1/ns/net')
assert src.parent.parent==Path('/tmp')
assert src.parent.name.startswith('hd-army-game-')

prior=runpy.run_path(str(root/'corpse/gameplay_smoke.py'))
cache=runpy.run_path(str(root/'cache/cache_gameplay.py'))
army=runpy.run_path(str(here/'check_army_socket.py'))

world=Path(tempfile.mkdtemp(prefix='hd-conjure-socket-'))

print("Private gameplay world:",world,flush=True)

for name in ('rooms','player','log','objmon','post',
             'help','bin','hollowdeep-data'):
    (world/name).mkdir()

anchor='    strcpy(mage.name, "Hdfaithqa");'

assert prior['SOURCE'].count(anchor)==1

prior['SOURCE']=prior['SOURCE'].replace(
    anchor,anchor+'\n    mage.class=FIGHTER;\n    mage.level=40;')

army['seed'](src,world,prior,cache)

for page in (here/'help').iterdir():
    if page.is_file():
        shutil.copyfile(page,world/'help'/page.name)

prior['prepare_chroot'](src/'frp.new',world)

def command(client,line):
    page=prior['command'](client,line)
    result=page
    for _ in range(20):
        if '[hit return, q to quit]' not in page.lower():
            return result
        page=prior['command'](client,'')
        result += '\\n'+page
    raise RuntimeError('Help pagination limit exceeded')

require=prior['require']
view=prior['room_view']

def start():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        port=s.getsockname()[1]

    with (world/f'listener-{port}.log').open('wb') as f:
        p=subprocess.Popen(
            [shutil.which('chroot'),
             '--userspec=65534:65534',
             '--groups=65534',str(world),
             '/bin/hollowdeep',str(port)],
            cwd=world,
            env={'PATH':'/usr/bin:/bin',
                 'HOLLOWDEEP_BIND':'127.0.0.1'},
            stdout=f,stderr=subprocess.STDOUT)

    return p,port

def stop(p):
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()

def login(client,name,room='Necromancer Grave Trial'):
    prior['recv_until'](client,b'Please enter name:')
    prior['send'](client,name)
    prior['recv_until'](client,b'Please enter password:')
    prior['send'](client,'Fixturepass')
    prior['recv_until'](client,room.encode(),seconds=15)

def logout(client,p,port):
    prior['quit_with_cooldown'](client,p)

    with prior['connect_game'](port,p) as barrier:
        prior['recv_until'](
            barrier,b'Please enter name:',seconds=15)

def north(client):
    for _ in range(8):
        result=command(client,'north')
        delay=re.search(
            r'Please wait (\d+) more seconds?',result,re.I)
        if delay:
            time.sleep(int(delay[1])+1)
            continue
        require(view(client),'Necromancer Trial Annex')
        return

    raise RuntimeError('Movement timeout')


p,port=start()

try:
    with prior['connect_game'](port,p) as owner:
        login(owner,'Hdnecroqa')

        for topic,marker in [
            ('necromancer','Intelligence and Piety'),
            ('raise corpse','120 seconds'),
            ('rc','5 percent unique chance'),
            ('corpse','sacrifice corpse'),
            ('pets','Undead army orders'),
            ('pet experience','348100 XP'),
            ('conjure','Available to all classes'),
            ('drain mana','20 percent'),
        ]:
            require(command(owner,'help '+topic),marker)

        result=command(owner,'skills')
        require(result,'raise corpse [eligible]')
        require(result,'conjure [all classes]')

        logout(owner,p,port)

    with prior['connect_game'](port,p) as fighter:
        login(fighter,'Hdfaithqa')

        result=command(fighter,'skills')
        require(result,'conjure [all classes]')

        assert 'raise corpse [eligible]' not in result.lower()

        logout(fighter,p,port)
finally:
    stop(p)

print('ROUND 75E: NATIVE HELP AND SKILL CATALOG PASS',flush=True)
