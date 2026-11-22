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


# Synthetic starting rooms only. Never copy the live world.
room_ids=set(range(201))

for path in (src/'player.c',src/'command1.c'):
    body=path.read_text(encoding='latin-1')
    for match in re.finditer(
            r'(?:rom_num\s*=\s*|load_rom\s*\(\s*)(\d+)',body):
        room_ids.add(int(match[1]))

for number in room_ids:
    if 0<=number<=99999:
        destination=world/'rooms'/f'r{number:05d}'
        if not destination.exists():
            shutil.copyfile(world/'rooms/r00002',destination)

probe=world/'creation-probe'

subprocess.run([
    'cc','-m32','-std=gnu89','-O1','-fcommon',
    '-DCOMPRESS','-DHD_NECROMANCER_PLAYTEST','-DHD_PET_STORE_PLAYTEST',
    '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
    '-Wno-implicit-function-declaration',
    '-Wno-int-conversion','-Wno-incompatible-pointer-types',
    '-I',str(src),
    str(here.parent/'creation/probe_created_player.c'),
    *[str(src/(name+'.c')) for name in (
        'files1','files3','compress','hd_player_store',
        'treasure_receipt','atomic_player_snapshot',
        'hd74_xp','hd74_progression')],
    '-o',str(probe)
],check=True)

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



def create(client,name,profession):
    text=prior['collect'](client)
    submitted=None
    submitted_password=False
    create.ansi_choice_seen=False

    for _ in range(20):
        low=text.lower()

        if 'please enter name' in low:
            answer=name
        elif 'did i get that right' in low:
            answer='y'
        elif 'hit return' in low:
            answer=''
        elif 'male or female' in low:
            answer='m'
        elif 'available classes' in low:
            require(text,'Necromancer')
            answer=profession
        elif 'points' in low and (
            'strength' in low or
            re.search(r'\bstr\s+dex\s+con\s+int\s+pie\b',low)):
            match=re.search(r'(\d+)\s+(?:total\s+)?points\b',low)
            if not match:
                raise RuntimeError('Unrecognized attribute point pool')
            total=int(match[1])
            low_stat=max(3,8,(total-54+1)//2)
            remaining=total-2*low_stat
            a,b=divmod(remaining,3)
            submitted=[a+(i<b) for i in range(3)]+[low_stat]*2

            assert sum(submitted)==total
            assert all(3<=v<=18 for v in submitted)

            answer=' '.join(map(str,submitted))
        elif 'weapons proficiency' in low:
            answer='Blunt'
        elif 'choose an alignment' in low:
            answer='Lawful'
        elif 'available races' in low:
            answer='Human'
        elif 'enable ansi colors' in low:
            answer='yes' if profession=='Necromancer' else 'no'
            create.ansi_choice_seen=True
        elif 'choose a password' in low:
            answer='Fixturepass'
            submitted_password=True
        elif submitted_password and (
            'welcome' in low or
            re.search(r'\(\d+ H \d+ M\):',text)):
            return submitted
        else:
            raise RuntimeError('Unknown creation prompt: '+repr(text[-1200:]))

        prior['send'](client,answer)
        text=prior['collect'](client)

        print('CREATION RESPONSE:',text,flush=True)

    raise RuntimeError('Creation menu step limit exceeded')


p,port=start()

try:
    for name,profession in (
        ('Hdcreatenec','Necromancer'),
        ('Hdcreatemag','Mage'),
    ):
        necro=profession=='Necromancer'

        with prior['connect_game'](port,p) as client:
            submitted=create(client,name,profession)

            skills=command(client,'skills')
            require(skills,'conjure [all classes]')
            if 'HD79_STATUS_HUD_PLAYTEST' in (src/'player.c').read_text(encoding='latin-1'):
                cleaned=re.sub(r'\x1b\[[0-9;]*m','',skills)
                require(cleaned,' | MP ')
                require(cleaned,' | Breath --')
                assert re.search(r'HP \d+/\d+ \| MP \d+/\d+ \| Breath --',cleaned)
                if necro:
                    require(skills,'\x1b[1;32mHP ')
                    print('PASS: ANSI colorized HP/MP/unknown Breath HUD',flush=True)
                else:
                    assert '\x1b[' not in skills, 'ANSI leaked into plain status'
                    print('PASS: plain HP/MP/unknown Breath HUD without ANSI',flush=True)

            if necro:
                require(skills,'raise corpse [eligible]')
                require(command(client,'conjure wolf'),'You conjure')
            else:
                assert 'raise corpse [eligible]' not in skills.lower()

            require(command(client,'save'),'Player saved.')
            logout(client,p,port)

        with tempfile.TemporaryDirectory(
                prefix='hd-creation-save-probe-') as scratch:
            copied=Path(scratch)
            (copied/'player').mkdir(mode=0o700)

            shutil.copyfile(
                world/'player'/name,
                copied/'player'/name)

            result=subprocess.check_output(
                [str(probe),name,str(int(necro))],
                cwd=copied,text=True)

        print(result,flush=True)

        if create.ansi_choice_seen:
            match=re.search(r'ANSI=(\d+)',result)
            assert match, 'Saved ANSI preference absent from native probe'
            assert int(match[1])==int(necro), 'Wrong saved ANSI preference'
            print('PASS: Character ANSI choice saved for '+profession,flush=True)

        if not necro:
            assert submitted is not None
            actual=list(map(int,re.search(
                r'STR=(\d+) DEX=(\d+) CON=(\d+) INT=(\d+) PIETY=(\d+)',
                result).groups()))
            submitted[2]+=1
            assert actual==submitted,(actual,submitted)

        if 'HD79_STATUS_HUD_PLAYTEST' in (src/'player.c').read_text(encoding='latin-1'):
            with prior['connect_game'](port,p) as reconnected:
                login(reconnected,name)
                again=command(reconnected,'skills')
                clean=re.sub(r'\x1b\[[0-9;]*m','',again)
                require(clean,' | MP ')
                require(clean,' | Breath --')
                if necro:
                    require(again,'\x1b[1;32mHP ')
                else:
                    assert '\x1b[' not in again, 'ANSI leaked after reconnect'
                print('PASS: Saved ANSI HUD restored on reconnect for '+profession,flush=True)
                logout(reconnected,p,port)

        print('PASS: Native creation and saved identity '+profession,flush=True)

finally:
    stop(p)

print('ROUND 75F: NATIVE CHARACTER CREATION PASS',flush=True)
