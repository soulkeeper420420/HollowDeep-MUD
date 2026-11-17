#!/usr/bin/env python3
"""Replay live raising, healing, pet orders, and restart on the private ELF32 game."""
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


class RevivalResisted(Exception):
    """The ordinary revival roll failed in this disposable world."""


def seed(src, world, prior, cache):
    body = cache['fixture_source'](prior['SOURCE'])
    body = '#include "hd_pet_store.h"\n#include "hd_pet_roster.h"\n' + body
    body = body.replace('        v->hpmax = 147 + i; v->hpcur = 1;',
                        '        v->hpmax = 147 + i; v->hpcur = 1; v->experience = 250;')
    body = body.replace('    mage.experience = 10000;',
                        '    mage.experience = 10000; S_SET(&mage, SMENDW);')
    anchor = '    strcpy(mage.name, "Hdfaithqa");'
    faithful = anchor + '\n    mage.ndice = 2; mage.sdice = 4;'
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
''' + faithful)
    main = 'int main(void)\n{'
    end_declarations = '    int i, fd;'
    if body.count(main) != 1 or body.count(end_declarations) != 1:
        raise ValueError('Private fixture probe anchor changed')
    body = body.replace(main, r'''static int probe_room(const char *expected)
{
    static char compressed[100001], native[100000];
    creature player;
    size_t bytes;
    int decoded;
    FILE *save = fopen("player/Hdnecroqa", "rb");
    extern int hd_uncompress_bounded(char *, char *, int, int);
    if (!save) return 2;
    bytes = fread(compressed, 1, sizeof compressed, save);
    if (ferror(save) || !feof(save)) {
        fclose(save);
        return 2;
    }
    fclose(save);
    decoded = hd_uncompress_bounded(compressed, native, (int)bytes, sizeof native);
    if (decoded < (int)sizeof player) return 2;
    memcpy(&player, native, sizeof player);
    if (memcmp(player.name, "Hdnecroqa", sizeof "Hdnecroqa")) return 2;
    printf("DURABLE OWNER ROOM: %d\n", (int)player.rom_num);
    printf("DURABLE OWNER XP: %ld GOLD: %ld\n", player.experience, player.gold);
    return player.rom_num == atoi(expected) ? 0 : 1;
}

int main(int argc, char **argv)
{''')
    body = body.replace(end_declarations, end_declarations +
                        '\n    if (argc == 2) return probe_room(argv[1]);')
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
    return executable


def replay(src, world):
    root = Path(__file__).resolve().parents[2]
    prior = runpy.run_path(str(root / 'corpse/gameplay_smoke.py'))
    cache = runpy.run_path(str(root / 'cache/cache_gameplay.py'))
    for name in ('rooms', 'player', 'log', 'objmon', 'post', 'help', 'bin', 'hollowdeep-data'):
        (world / name).mkdir(mode=0o700)
    (world / 'hollowdeep-data/deities.db').write_text('HOLLOWDEEP_DEITIES 1 1\nHdfaithqa 3\n')
    probe = seed(src, world, prior, cache)
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

    def saved_progress(expected_room):
        result = subprocess.check_output([str(probe), str(expected_room)], cwd=world,
                                         text=True, timeout=3)
        match = re.search(r'DURABLE OWNER XP: (\d+) GOLD: (\d+)', result)
        if not match:
            raise RuntimeError('Missing XP or gold in native save probe')
        return int(match[1]), int(match[2])

    def raised_hp(client):
        text = command(client, 'pets')
        match = re.search(r'Pet 4: (?:Unique )?trialwretch \| HP (\d+)/(\d+)',
                          text, re.I)
        if not match:
            raise RuntimeError('Raised pet absent from native roster: ' + repr(text[-900:]))
        return int(match[1]), int(match[2])

    def quit_owner(client, process, expected_room):
        save = world / 'player/Hdnecroqa'
        previous_inode = save.stat().st_ino
        prior['quit_with_cooldown'](client, process)
        deadline = time.monotonic() + 10
        result = None
        while time.monotonic() < deadline and process.poll() is None:
            if save.stat().st_ino != previous_inode:
                result = subprocess.run([str(probe), str(expected_room)], cwd=world,
                                        text=True, capture_output=True, timeout=3)
                if result.returncode == 0:
                    print(result.stdout.rstrip(), flush=True)
                    return
            time.sleep(0.1)
        detail = result.stdout.strip() if result else 'no replacement save observed'
        raise RuntimeError(f'Owner logout save did not reach room {expected_room}: {detail}')

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
            first = prior['kill_and_find'](owner, 'trialwretch', 'rubyfixture')
            second = prior['kill_and_find'](owner, 'trialghoul', 'amberfixture')
            require(command(owner, 'save'), 'Player saved.')
            earned, gold = saved_progress(1)
            if earned <= 10000 or gold != 1000:
                raise RuntimeError(f'Unexpected pre-raise kill XP or gold: {earned}, {gold}')
            result = command(owner, f'rc {first}')
            if 'resists your call' in result.lower():
                require(command(owner, f'raise corpse {second}'), 'Raise Corpse is ready in')
                raise RevivalResisted()
            require(result, 'You raise trialwretch [pet 4]')
            require(result, 'loot falls to the ground')
            require(command(owner, f'raise corpse {second}'), 'Raise Corpse is ready in')
            if saved_progress(1) != (earned + 25, gold):
                raise RuntimeError('Expected exactly 25 bonus XP on the atomic raise save')
            prior['after_release'](owner, first, 'rubyfixture')
            require(command(owner, 'get rubyfixture'), 'You get')
            require(command(owner, 'get gold'), '1013 gold')
            current, maximum = raised_hp(owner)
            if current != maximum or maximum not in (147, 294):
                raise RuntimeError('Unexpected starting vitals for raised pet')
            with prior['connect_game'](port, process) as faithful:
                login(faithful, 'Hdfaithqa', 'Necromancer Grave Trial')
                for _ in range(6):
                    command(faithful, 'attack trialwretch')
                    wounded, _ = raised_hp(owner)
                    if wounded < maximum:
                        break
                    time.sleep(3.2)
                else:
                    raise RuntimeError('Raised pet never took native combat damage')
                reply = command(owner, 'cast mend-wounds trialwretch')
                require(reply, 'Mend-wounds spell cast on')
                healed, _ = raised_hp(owner)
                if healed <= wounded:
                    raise RuntimeError(f'Targeted healing did not raise pet HP: {wounded} to {healed}')
                prior['quit_with_cooldown'](faithful, process)
            print('PASS: live RC, shared cooldown, original loot, exact bonus XP and targeted healing',
                  flush=True)
            require(command(owner, 'pet stay 2'), 'Pet order: stay')
            move(owner, 'north', 'Necromancer Trial Annex')
            status = command(owner, 'pet status')
            require(status, 'Pet 3: bonehound')
            if 'cryptsentinel' in view(owner).lower():
                raise RuntimeError('Staying pet followed its owner')
            require(command(owner, 'pet follow 2'), 'Pet order: follow')
            require(view(owner), 'cryptsentinel')
            quit_owner(owner, process, 2)
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
            raised_hp(owner)
            require(command(owner, 'inventory'), 'rubyfixture')
            restored_xp, restored_gold = saved_progress(2)
            if restored_xp != earned + 25 or restored_gold != 1013:
                raise RuntimeError('Live raise rewards changed across restart')
            require(command(owner, 'pet dismiss 4'), 'You dismiss')
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
            quit_owner(owner, process, 2)
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
            quit_owner(owner, process, 2)
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
    print(f'Private socket replay: {work}', flush=True)
    before = pid()
    try:
        for attempt in range(1, 4):
            case = work / f'attempt-{attempt}'
            case.mkdir()
            world = case / 'world'
            world.mkdir()
            try:
                replay(source, world)
            except RevivalResisted:
                print(f'Native revival resisted on attempt {attempt}; verified shared cooldown.',
                      flush=True)
            else:
                break
        else:
            raise RuntimeError('Three private attempts resisted revival')
    except Exception:
        for log in sorted(work.glob('attempt-*/*-listener.log')):
            print(log.name + ':\n' + log.read_text(errors='replace')[-2500:], flush=True)
        raise
    finally:
        if pid() != before:
            raise RuntimeError('Production service PID changed during replay')
        print('PRODUCTION SERVICE PID: UNCHANGED', flush=True)
