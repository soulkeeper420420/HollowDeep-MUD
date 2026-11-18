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
                        '        v->hpmax = 147 + i; v->hpcur = 1; v->experience = 250; v->hpmax = v->hpcur = 8;')
    body = body.replace('    mage.experience = 10000;',
                        '    mage.experience = 10000; S_SET(&mage, SMENDW);')
    anchor = '    strcpy(mage.name, "Hdfaithqa");'
    faithful = anchor + '\n    mage.class = FIGHTER; mage.level = 40; mage.ndice = 2; mage.sdice = 4;'
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

    logout_probe = r"""
static int probe_logout(const char *expected_room,
                        const char *expected_xp)
{
    creature *player = NULL;
    hd_pet_roster roster;
    otag *tag;
    int ruby = 0;

    extern int hd_roster_store_read(
        const char *, hd_pet_roster *);

    if (hd_store_load_player("Hdnecroqa", &player) ||
        !player)
        return 10;

    if (hd_roster_store_read("Hdnecroqa", &roster))
        return 11;

    for (tag = player->first_obj; tag; tag = tag->next_tag)
        if (tag->obj &&
            !strcmp(tag->obj->name, "rubyfixture"))
            ++ruby;

    printf("DURABLE LOGOUT: room=%d gold=%ld XP=%ld ruby=%d pets=%lu\n",
        (int)player->rom_num,
        player->gold, player->experience,
        ruby, (unsigned long)roster.count);

    if (player->rom_num != atoi(expected_room) ||
        player->experience != strtol(expected_xp, NULL, 10) ||
        player->gold != 1013 || ruby != 1 ||
        roster.count != 0)
        return 12;

    return 0;
}
"""
    main_anchor = 'int main(int argc, char **argv)\n{'
    assert body.count(main_anchor) == 1
    body = body.replace(
        main_anchor, logout_probe + '\n' + main_anchor)

    dispatch = '    if (argc == 2) return probe_room(argv[1]);'
    assert body.count(dispatch) == 1

    body = body.replace(dispatch,
        '    if (argc == 4 && !strcmp(argv[1], "logout"))\n'
        '        return probe_logout(argv[2], argv[3]);\n'
        + dispatch)

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
        prior['quit_with_cooldown'](client, process)

        # EOF can precede the native character save.
        # A fresh listener response establishes an event-loop barrier.
        with prior['connect_game'](port, process) as barrier:
            prior['recv_until'](
                barrier, b'Please enter name:', seconds=15)

        if process.poll() is not None:
            raise RuntimeError('Listener exited during logout')

        with tempfile.TemporaryDirectory(
                prefix='hd-logout-probe-') as storage:
            copied = Path(storage)
            (copied / 'player').mkdir(mode=0o700)
            shutil.copyfile(
                world / 'player/Hdnecroqa',
                copied / 'player/Hdnecroqa')

            subprocess.run(
                [str(probe), 'logout', str(expected_room),
                 str(earned + 25)],
                cwd=copied, check=True, timeout=5)

        print('PASS: durable owner rewards and empty undead roster',
              flush=True)

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
            require(command(owner, 'pets'), 'Pets: 0/')

            if 'cryptsentinel' in view(owner) or 'bonehound' in view(owner):
                raise RuntimeError('Expired summons returned')

            first = prior['kill_and_find'](
                owner, 'trialwretch', 'rubyfixture')
            second = prior['kill_and_find'](
                owner, 'trialghoul', 'amberfixture')

            require(command(owner, 'save'), 'Player saved.')
            earned, gold = saved_progress(1)

            result = command(owner, f'rc {first}')
            if 'resists your call' in result.lower():
                require(command(owner, f'raise corpse {second}'),
                        'Raise Corpse is ready in')
                raise RevivalResisted()

            require(result, 'You raise trialwretch [pet 4]')
            require(command(owner, f'raise corpse {second}'),
                    'Raise Corpse is ready in')

            assert saved_progress(1) == (earned + 25, gold)

            prior['after_release'](owner, first, 'rubyfixture')
            require(command(owner, 'get rubyfixture'), 'You get')
            require(command(owner, 'get gold'), '1013 gold')

            require(command(owner,'conjure wolf'),'You conjure')
            status = command(owner, 'pets')
            require(status, 'Pets: 1/')
            require(status, 'XP 0')
            require(status,'Companion: spectral wolf')
            require(view(owner),'trialwretch')
            require(view(owner),'spectral wolf')
            print('PASS: Both summon systems active independently',flush=True)


            require(command(owner, 'pet stay 4'), 'Pet order: stay')
            move(owner, 'north', 'Necromancer Trial Annex')

            if 'trialwretch' in view(owner):
                raise RuntimeError('Stay order failed')

            require(command(owner, 'pet follow 4'), 'Pet order: follow')
            require(view(owner), 'trialwretch')
            require(view(owner),'spectral wolf')

            if '--death-loot' in sys.argv:
                with prior['connect_game'](port,process) as fighter:
                    login(fighter,'Hdfaithqa','Necromancer Grave Trial')
                    move(fighter,'north','Necromancer Trial Annex')

                    for _ in range(20):
                        command(fighter,'attack trialwretch')
                        if 'Pets: 0/' in command(owner,'pets'):
                            break
                        time.sleep(3.2)
                    else:
                        raise RuntimeError('Raised undead death not observed')

                    require(view(fighter),'gold coin')
                    require(command(fighter,'get gold'),'1001 gold')
                    require(command(owner,'conjure status'),'spectral wolf')
                    prior['quit_with_cooldown'](fighter,process)

                    print('PASS: Raised undead has independent death loot',flush=True)


            quit_owner(owner, process, 2)

        with prior['connect_game'](port, process) as owner:
            login(owner, 'Hdnecroqa', 'Necromancer Trial Annex')
            require(command(owner, 'pets'), 'Pets: 0/')
            require(command(owner, 'inventory'), 'rubyfixture')
            require(command(owner,'conjure status'),'spectral wolf')
            require(view(owner),'spectral wolf')
            assert 'gold coin' not in view(owner)

            assert saved_progress(2) == (earned + 25, 1013)

            if 'trialwretch' in view(owner):
                raise RuntimeError('Summon survived logout')

            quit_owner(owner, process, 2)
    finally:
        stop(process)

    process, port = start('restart-listener')
    try:
        with prior['connect_game'](port, process) as owner:
            login(owner, 'Hdnecroqa', 'Necromancer Trial Annex')
            require(command(owner, 'pets'), 'Pets: 0/')
            require(command(owner, 'inventory'), 'rubyfixture')
            require(command(owner,'conjure status'),'spectral wolf')
            require(view(owner),'spectral wolf')
            assert 'gold coin' not in view(owner)

            assert saved_progress(2) == (earned + 25, 1013)
            quit_owner(owner, process, 2)
    finally:
        stop(process)

    print('ROUND 75F: INDEPENDENT SUMMON SYSTEMS PASS',
          flush=True)


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
