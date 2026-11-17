#!/usr/bin/env python3
"""Replay pet orders, combat death, and restart on the private ELF32 game."""
import os
from pathlib import Path
import re
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def seed(src, world, prior, cache):
    body = cache['fixture_source'](prior['SOURCE'])
    body = '#include "hd_pet_store.h"\n#include "hd_pet_roster.h"\n' + body
    anchor = '    strcpy(mage.name, "Hdfaithqa");'
    if body.count(anchor) != 1:
        raise ValueError('Private fixture seed anchor changed')
    body = body.replace(anchor, '''    {
        hd_pet_state legacy;
        hd_pet_roster roster;
        hd_roster_pet pet = {0};
        long awarded;
        extern int hd_roster_store_read(const char *, hd_pet_roster *);
        extern int hd_roster_store_raise(const char *, const hd_pet_roster *,
            const hd_roster_pet *, creature *, uint32_t, long *, hd_pet_roster *);
        assert(hd_pet_store_init(mage.name, &legacy) == 0);
        assert(hd_roster_store_read(mage.name, &roster) == 0);
        strcpy(pet.name, "cryptsentinel");
        pet.template_id = 1; pet.level = 2; pet.room = 1;
        pet.hpmax = pet.hpcur = 84; pet.mpmax = pet.mpcur = 20;
        pet.unique = 1; pet.strength = 20; pet.dexterity = 22;
        assert(hd_roster_store_raise(mage.name, &roster, &pet, &mage, 0, &awarded, &roster) == 0);
        mage.mpcur -= 8;
        strcpy(pet.name, "bonehound");
        pet.template_id = 2; pet.unique = 0;
        pet.hpmax = pet.hpcur = 15;
        assert(hd_roster_store_raise(mage.name, &roster, &pet, &mage, 0, &awarded, &roster) == 0);
        mage.mpcur += 8;
    }
''' + anchor)
    fixture = world / 'seed.c'
    fixture.write_text(body)
    components = ['files1', 'files3', 'compress', 'hd_player_store', 'treasure_receipt',
                  'atomic_player_snapshot', 'hd74_xp', 'hd74_progression']
    executable = world / 'seed'
    subprocess.run(['cc', '-m32', '-std=gnu89', '-O1', '-fcommon', '-DCOMPRESS',
                    '-DHD_NECROMANCER_PLAYTEST', '-DHD_PET_STORE_PLAYTEST',
                    '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                    '-Wno-implicit-function-declaration', '-Wno-int-conversion',
                    '-Wno-incompatible-pointer-types', '-I', str(src), str(fixture),
                    *(str(src / (name + '.c')) for name in components),
                    '-o', str(executable)], check=True, cwd=world)
    subprocess.run([str(executable)], check=True, cwd=world)


def replay(src, world):
    root = Path(__file__).resolve().parents[2]
    prior = runpy.run_path(str(root / 'corpse/gameplay_smoke.py'))
    cache = runpy.run_path(str(root / 'cache/cache_gameplay.py'))
    for name in ('rooms', 'player', 'log', 'objmon', 'post', 'help', 'bin', 'hollowdeep-data'):
        (world / name).mkdir(mode=0o700)
    (world / 'hollowdeep-data/deities.db').write_text('HOLLOWDEEP_DEITIES 1 1\nHdfaithqa 3\n')
    seed(src, world, prior, cache)
    chroot = shutil.which('chroot', path='/usr/sbin:/usr/bin:/sbin:/bin')
    if not chroot:
        raise RuntimeError('Required chroot missing')
    prior['prepare_chroot'](src / 'frp.new', world)
    launcher = [chroot, '--userspec=65534:65534', '--groups=65534', str(world),
                '/bin/hollowdeep']
    env = {'PATH': '/usr/bin:/bin', 'HOLLOWDEEP_BIND': '127.0.0.1'}
    command, require, view = (prior[key] for key in ('command', 'require', 'room_view'))

    def login(client, name, destination):
        recv, send = prior['recv_until'], prior['send']
        recv(client, b'Please enter name:')
        send(client, name)
        recv(client, b'Please enter password:')
        send(client, 'Fixturepass')
        recv(client, destination.encode('ascii'), seconds=15)

    def start(label):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        with (world.parent / (label + '.log')).open('wb') as log:
            process = subprocess.Popen(launcher + [str(port)], cwd=world, env=env,
                                       stdout=log, stderr=subprocess.STDOUT)
        return process, port

    def move(client, verb, destination):
        for _ in range(6):
            reply = command(client, verb)
            match = re.search(r'Please wait (\d+) more seconds?', reply, re.I)
            if not match:
                require(view(client), destination)
                return
            if int(match[1]) > 10:
                break
            time.sleep(int(match[1]) + 0.2)
        raise RuntimeError('Movement cooldown exceeded replay limit')

    def stop(process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    process, port = start('first-listener')
    try:
        with prior['connect_game'](port, process) as owner:
            login(owner, 'Hdnecroqa', 'Necromancer Grave Trial')
            require(command(owner, 'pets'), 'Pet 2: Unique cryptsentinel')
            require(command(owner, 'pet stay 2'), 'Pet order: stay')
            move(owner, 'north', 'Necromancer Trial Annex')
            status = command(owner, 'pet status')
            require(status, 'Pet 3: bonehound')
            if 'cryptsentinel' in view(owner).lower():
                raise RuntimeError('Staying pet followed its owner')
            require(command(owner, 'pet follow 2'), 'Pet order: follow')
            require(view(owner), 'cryptsentinel')
            prior['quit_with_cooldown'](owner, process)
    finally:
        stop(process)
    print('PASS: native pet orders and durable logout', flush=True)

    process, port = start('second-listener')
    try:
        with prior['connect_game'](port, process) as owner:
            login(owner, 'Hdnecroqa', 'Necromancer Trial Annex')
            status = command(owner, 'pets')
            require(status, 'Pet 2: Unique cryptsentinel')
            require(status, 'HP 84/84 MP 20/20')
            require(status, 'Pet 3: bonehound')
            require(view(owner), 'bonehound')
            with prior['connect_game'](port, process) as faithful:
                login(faithful, 'Hdfaithqa', 'Necromancer Grave Trial')
                move(faithful, 'north', 'Necromancer Trial Annex')
                for _ in range(30):
                    command(faithful, 'attack bonehound')
                    status = command(owner, 'pets')
                    require(status, 'Pet 2: Unique cryptsentinel')
                    if 'Pet 3:' not in status:
                        break
                    time.sleep(3.2)
                else:
                    raise RuntimeError('Native combat never removed bonehound')
                require(status, 'Pet 2: Unique cryptsentinel')
                prior['quit_with_cooldown'](faithful, process)
            prior['quit_with_cooldown'](owner, process)
    finally:
        stop(process)

    process, port = start('third-listener')
    try:
        with prior['connect_game'](port, process) as owner:
            login(owner, 'Hdnecroqa', 'Necromancer Trial Annex')
            status = command(owner, 'pets')
            require(status, 'Pet 2: Unique cryptsentinel')
            if 'Pet 3:' in status or 'bonehound' in view(owner).lower():
                raise RuntimeError('Dead pet returned after restart')
            require(command(owner, 'pet dismiss 2'), 'You dismiss')
            require(command(owner, 'pets'), 'Pets: 0/')
            prior['quit_with_cooldown'](owner, process)
    finally:
        stop(process)
    print('PASS: private Undead Army socket orders, unique restore and combat death', flush=True)


if __name__ == '__main__':
    source = Path(sys.argv[1]).resolve(strict=True)
    if (os.geteuid() or os.readlink('/proc/self/ns/net') == os.readlink('/proc/1/ns/net') or
            source.parent.parent != Path('/tmp') or
            not source.parent.name.startswith('hd-army-game-') or source.name != 'src'):
        raise SystemExit('Expected a disposable private Army build in a separate network namespace')
    def pid():
        value = subprocess.check_output(['systemctl', 'show', 'hollowdeep.service', '-p', 'MainPID', '--value'],
                             text=True).strip()
        if not value.isdecimal() or int(value) < 1:
            raise RuntimeError('Expected a running production service')
        return value
    os.umask(0o077)
    work = Path(tempfile.mkdtemp(prefix='hd-army-socket-'))
    world = work / 'world'
    world.mkdir()
    print(f'Private socket replay: {work}', flush=True)
    before = pid()
    try:
        replay(source, world)
    except Exception:
        for log in sorted(work.glob('*-listener.log')):
            print(log.name + ':\n' + log.read_text(errors='replace')[-2500:], flush=True)
        raise
    finally:
        if pid() != before:
            raise RuntimeError('Production service PID changed during replay')
        print('PRODUCTION SERVICE PID: UNCHANGED', flush=True)
