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


prior['SOURCE']='#include "hd_conjure.h"\n'+prior['SOURCE']

def fixture_replace(old,new):
    assert prior['SOURCE'].count(old)==1,old
    prior['SOURCE']=prior['SOURCE'].replace(old,new,1)

fixture_replace('mage.ndice = 5;', 'mage.ndice = 1;')
fixture_replace('mage.sdice = 20;', 'mage.sdice = 1;')

fixture_replace(
    'v->hpmax = 147 + i; v->hpcur = 1;',
    'v->hpmax = 147 + i; v->hpcur = 1;\n'
    '        v->hpmax = v->hpcur = 12;')

fixture_replace(
    'assert(hd_store_is_necromancer(mage.name));',
    """assert(hd_store_is_necromancer(mage.name));
    {
        hd_conjure_state a,b;
        assert(hd_conjure_store_apply(
            mage.name,NULL,HD_CJ_INIT,0,0,0,&a)==0);
        assert(hd_conjure_store_apply(
            mage.name,&a,HD_CJ_SUMMON,1000,1,0,&b)==0);
        assert(hd_conjure_store_apply(
            mage.name,&b,HD_CJ_XP,1001,4800,0,&a)==0);
        assert(a.level==7);
    }""")

army['seed'](src,world,prior,cache)

for page in (here/'help').iterdir():
    if page.is_file():
        shutil.copyfile(page,world/'help'/page.name)

prior['prepare_chroot'](src/'frp.new',world)

def command(client,line):
    result=prior['command'](client,line)
    for _ in range(20):
        if '[hit return, q to quit]' not in result.lower().splitlines()[-1]:
            return result
        page=prior['command'](client,'')
        result += '\n'+page
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
        require(command(owner,'conjure status'),'XP 4800')

        count=0
        success=False

        for target in ('trialwretch','trialghoul','trialshade'):
            transcript=[]
            deadline=time.monotonic()+90

            while time.monotonic()<deadline:
                text=command(owner,'look')
                transcript.append(text)

                if ('the corpse of '+target) in text.lower():
                    count+=1
                    break

                transcript.append(command(owner,'attack '+target))
                transcript.append(command(owner,'conjure attack '+target))
                time.sleep(3.2)
            else:
                raise RuntimeError('No native corpse for '+target)

            status=command(owner,'conjure status')

            if 'XP 5050' in status:
                require(status,'Level 8')
                require('\n'.join(transcript),
                        'finishes '+target)
                success=True
                break

        assert success,'No companion final blow observed'

        require(command(owner,'save'),'Player saved.')

        result=subprocess.check_output(
            [str(world/'seed'),'1'],
            cwd=world,text=True)

        match=re.search(
            r'DURABLE OWNER XP: (\d+) GOLD:',result)

        assert match,result

        assert int(match[1])==10000+250*count,result

        logout(owner,p,port)
finally:
    stop(p)

p,port=start()

try:
    with prior['connect_game'](port,p) as owner:
        login(owner,'Hdnecroqa')
        status=command(owner,'conjure status')
        require(status,'Level 8')
        require(status,'XP 5050')
        require(view(owner),'spectral wolf')
        logout(owner,p,port)
finally:
    stop(p)

print('ROUND 75D: NATIVE OWNER AND COMPANION XP PASS',flush=True)
