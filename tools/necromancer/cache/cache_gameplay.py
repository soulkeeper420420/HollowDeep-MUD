#!/usr/bin/env python3
"""Run the accepted cache build in isolated native gameplay, and export only
explicitly selected private persistence source files for the next milestone.
Requires the pinned prior gameplay and cache bundles as separate arguments.
Never reads live world, player files, credentials or private server config.
"""
import hashlib
import os
from pathlib import Path
import re
import resource
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/root/hollowdeep-dev')
CANDIDATE = ROOT / 'necromancer-playtest-cache-jyf14lkl/src'
EXPECTED = {
    'hd_corpse.c': '8fa9fde462ee588838d50c60d82de9fd4f34ad0e85a648839bf752208829cb09',
    'hd_necro_skeleton.c': '74083ff5e5d7171f5b22217173b766904fe0a39dad6e196ac9744fe71064efe3',
    'hd_necro_skeleton.h': '4ef4a33e61595cbd6061e4e2072e80efcc15a4d709f04afded534aba1e5385b2',
    'files1.c': 'd54386bd9d0c57ab6e947c06afa49e7847ace2beff6f88c826cb4ff32c465799',
    'files2.c': 'b72e78e3ce0e59f8a543ec9020aaafc440ff03e823ce5886258312e83f7d51c5',
    'global.c': '55d7891e1d8766e4dc23b5d24cb3d0655f8ae7f33a39a8f649b7dcc72f97c894',
}
# Explicit source-only allowlist: no server settings, shell history, world
# files, players, logs, binary objects, staff databases or credentials.
SOURCE_FILES = tuple('''hd_player_store.c hd_player_store.h treasure_receipt.c
 treasure_receipt.h atomic_player_snapshot.c atomic_player_snapshot.h
 hd_necro_skeleton.c hd_necro_skeleton.h hd_corpse.c hd_corpse.h
 hd_deity.c hd_deity.h files1.c files2.c files3.c mstruct.h mtype.h mextern.h
 creature.c command1.c command2.c command5.c player.c magic1.c magic2.c
 magic3.c update.c main.c io.c global.c hollowdeep_staff.c hollowdeep_staff.h
 hollowdeep_help.c hollowdeep_help.h hollowdeep_bonus.c hollowdeep_bonus.h
 hd74_xp.c hd74_xp.h compress.c object.c room.c combat.c misc.c logic.c Makefile'''.split())


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pid():
    out = subprocess.check_output(['systemctl', 'show', 'hollowdeep.service', '-p', 'MainPID', '--value'], text=True).strip()
    if not out.isdigit() or int(out) < 1:
        raise RuntimeError('Production service not confirmed active')
    return out


def guard(raw):
    src = raw.resolve(strict=True)
    if src != CANDIDATE or raw.is_symlink() or any(p.is_symlink() for p in [src, src.parent, ROOT]):
        raise RuntimeError('Only the accepted private cache candidate is allowed')
    for name, sha in EXPECTED.items():
        p = src/name
        if p.is_symlink() or not p.is_file() or digest(p) != sha:
            raise RuntimeError('Exact cache source mismatch: ' + name)
    exe = src/'frp.new'
    if not exe.is_file() or exe.is_symlink() or not os.access(exe, os.X_OK) or exe.open('rb').read(5) != b'\x7fELF\x01':
        raise RuntimeError('Expected accepted cache ELF32 executable')
    return src, exe


def export_source(src, exe, dest):
    # Use one archive with a manifest; do not upload it to GitHub. Source can
    # contain operational details, so the resulting file remains root-only.
    entries = {}
    for name in SOURCE_FILES:
        p = src/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 2_000_000:
            raise RuntimeError('Source-only handoff input missing or unsafe: '+name)
        entries['src/'+name] = p.read_bytes()
    manifest = ['# Private source-only restart integration handoff', 'binary SHA256 '+digest(exe)]
    manifest += [hashlib.sha256(body).hexdigest()+'  '+name for name, body in sorted(entries.items())]
    with zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in sorted(entries.items()):
            z.writestr(name, body)
        z.writestr('SHA256SUMS.txt', '\n'.join(manifest)+'\n')
    dest.chmod(0o600)
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:
            raise RuntimeError('Source archive failed CRC check')
    print('PRIVATE PERSISTENCE SOURCE ZIP: '+str(dest), flush=True)
    print('SOURCE ZIP SHA256: '+digest(dest), flush=True)


def fixture_source(s):
    def replace_one(a, b):
        nonlocal s
        if s.count(a) != 1:
            raise RuntimeError('Pinned native fixture anchor mismatch: '+a[:100])
        s = s.replace(a, b)
    replace_one('    room site = {0};', '    room site = {0}, annex = {0};\n    exit_ north = {0}, south = {0};\n    xtag ntag = {0}, stag = {0};')
    replace_one('    creature mob[3] = {{0}}, mage = {0};', '    creature mob[3] = {{0}}, mage = {0};\n    object coin = {0};')
    replace_one('    site.hilevel = 60;', '''    site.hilevel = 60;
    strcpy(north.name, "north"); north.room = 2;
    strcpy(south.name, "south"); south.room = 1;
    ntag.ext = &north; stag.ext = &south;
    site.first_ext = &ntag;
    strcpy(annex.name, "Necromancer Trial Annex");
    annex.long_desc = "A private second room for follower verification.";
    annex.rom_num = 2; annex.hilevel = 60; annex.first_ext = &stag;''')
    replace_one('        v->ndice = 1; v->sdice = 1; v->thaco = 20; v->armor = 0;', '''        v->ndice = 1; v->sdice = 1; v->thaco = 20; v->armor = 0;
        if (i == 0) v->gold = 13;''')
    replace_one('    strcpy(mage.name, "Hdnecroqa");', '''    fd = open("rooms/r00002", O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600);
    assert(fd >= 0); assert(write_rom(fd, &annex, ALLITEMS) == 0);
    assert(fsync(fd) == 0); assert(close(fd) == 0);
    strcpy(coin.name, "gold coins"); strcpy(coin.key[0], "gold"); coin.type = MONEY;
    fd = open("objmon/o00", O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600);
    assert(fd >= 0); assert(write(fd, &coin, sizeof coin) == sizeof coin);
    assert(fsync(fd) == 0); assert(close(fd) == 0);
    strcpy(mage.name, "Hdnecroqa");''')
    return s


def main():
    if len(sys.argv) != 4:
        raise SystemExit('Usage: cache_gameplay.py PRIVATE_CACHE_SRC PRIOR_GAMEPLAY_PY CACHE_BUNDLE_PY')
    if os.geteuid() != 0 or os.readlink('/proc/self/ns/net') == os.readlink('/proc/1/ns/net'):
        raise SystemExit('Use a fresh network namespace with loopback; root required for unprivileged chroot setup')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    src, exe = guard(Path(sys.argv[1]))
    before = pid()
    original_binary = digest(exe)
    print('CACHE executable SHA256: '+original_binary, flush=True)
    stage = Path(tempfile.mkdtemp(prefix='necromancer-cache-socket-', dir=ROOT))
    print('PRIVATE CACHE GAMEPLAY: '+str(stage), flush=True)
    # Archive first so the exact source is available even if a later native
    # gameplay assertion fails. Keep it outside the unprivileged chroot.
    handoff = stage.parent/(stage.name+'-persistence-source.zip')
    export_source(src, exe, handoff)
    replay = runpy.run_path(str(Path(sys.argv[2]).resolve(strict=True)))
    cache = runpy.run_path(str(Path(sys.argv[3]).resolve(strict=True)))
    if cache['AFTER'] != EXPECTED:
        raise RuntimeError('Cache package fingerprints do not match')
    payload = cache['PAYLOAD']
    for dirname in ('rooms', 'player', 'log', 'objmon', 'post', 'help', 'bin', 'hollowdeep-data'):
        (stage/dirname).mkdir(mode=0o700)
    for name, body in payload.items():
        if name.startswith('help/') and '/' not in name[5:]:
            (stage/name).write_bytes(body.encode('ascii'))
    (stage/'hollowdeep-data/deities.db').write_text('HOLLOWDEEP_DEITIES 1 1\nHdfaithqa 3\n')
    # Modify only the synthetic seed, never the accepted game source.
    compile_fixture = replay['compile_fixture']
    compile_fixture.__globals__['SOURCE'] = fixture_source(replay['SOURCE'])
    command = replay['command']
    require = replay['require']
    room_view = replay['room_view']
    kill = replay['kill_and_find']
    after_release = replay['after_release']
    login = replay['login']
    collect = replay['collect']
    connect = replay['connect_game']
    quit_game = replay['quit_with_cooldown']
    fixture = compile_fixture(src, stage, '-m32')
    subprocess.run([str(fixture)], check=True, cwd=stage)
    chroot = shutil.which('chroot', path='/usr/sbin:/usr/bin:/sbin:/bin')
    if not chroot:
        raise RuntimeError('Required chroot missing')
    interpreter = replay['prepare_chroot'](exe, stage)
    launcher = [chroot, '--userspec=65534:65534', '--groups=65534', str(stage)]
    env = {'PATH':'/usr/bin:/bin', 'HOLLOWDEEP_BIND':'127.0.0.1'}
    subprocess.run(launcher+[interpreter, '--list', '/bin/hollowdeep'], cwd=stage, env=env, check=True, timeout=15)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    logfile = stage/'isolated-game.log'
    process = None
    try:
        with logfile.open('wb') as log:
            process = subprocess.Popen(launcher+['/bin/hollowdeep', str(port)], cwd=stage, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            with connect(port, process) as necro:
                login(necro); collect(necro)
                for line, marker in [('help corpse','MONSTER CORPSES'),('help deity','DEITIES AND CORPSE SACRIFICE'),('help raise skeleton','RAISE SKELETON')]:
                    result = command(necro, line)
                    require(result, marker)
                    if any(ord(c)>127 for c in result):
                        # Telnet control bytes can be present in raw replies;
                        # check the actual help headline's printable text only.
                        title = next((x for x in result.splitlines() if marker in x), '')
                        if any(ord(c)>127 for c in title):
                            raise RuntimeError('Non-ASCII help headline: '+repr(title))
                first = kill(necro, 'trialwretch', 'rubyfixture')
                require(command(necro, f'sacrifice corpse {first}'), 'assigned deity')
                require(room_view(necro), f'[corpse {first}]')
                result = command(necro, f'raise corpse {first}')
                require(result, 'You raise a skeleton (147 HP / 51 MP).')
                require(result, 'loot falls to the ground')
                after_release(necro, first, 'rubyfixture')
                require(room_view(necro), 'gold coins')
                require(command(necro, 'get rubyfixture'), 'You get')
                if 'rubyfixture' in room_view(necro):
                    raise RuntimeError('Collected ruby remains on floor')
                require(command(necro, 'get gold'), 'You now have 1013 gold pieces.')
                if 'gold coins' in room_view(necro):
                    raise RuntimeError('Collected gold remains on floor')
                print('CACHE GAMEPLAY: actual corpse gold and item pickup PASS', flush=True)
                # The previous successful replay never moved between rooms.
                # Native movement may briefly be blocked after combat.
                import time
                time.sleep(4)
                command(necro, 'north')
                view = room_view(necro)
                require(view, 'necromancer trial annex'); require(view, 'skeleton servant')
                command(necro, 'south')
                view = room_view(necro)
                require(view, 'necromancer grave trial'); require(view, 'skeleton servant')
                print('CACHE GAMEPLAY: native reciprocal movement and skeleton follower PASS', flush=True)
                second = kill(necro, 'trialghoul', 'amberfixture')
                require(command(necro, f'raise corpse {second}'), 'already command a skeleton')
                require(room_view(necro), f'[corpse {second}]')
                require(command(necro, f'loot corpse {second}'), 'loot falls to the ground')
                after_release(necro, second, 'amberfixture')
                third = kill(necro, 'trialshade', 'jadefixture')
                with connect(port, process) as faithful:
                    login(faithful, 'Hdfaithqa'); collect(faithful)
                    who = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', command(faithful, 'who'))
                    for name, title in [('Hdnecroqa', 'Necromancer'), ('Hdfaithqa', 'Conjurer')]:
                        rows = [line for line in who.splitlines() if name.lower() in line.lower()]
                        if not any(re.search(r'\b'+re.escape(name)+r'\b.*\b'+title+r'\b', line, re.I) for line in rows):
                            raise RuntimeError('Expected native class title '+name+' / '+title)
                    print('CACHE GAMEPLAY: verified Necromancer vs ordinary Mage title PASS', flush=True)
                    require(command(faithful, f'raise corpse {third}'), 'Only Necromancers')
                    require(command(faithful, f'sacrifice corpse {third}'), 'You sacrifice the corpse')
                    after_release(faithful, third, 'jadefixture')
                    quit_game(necro, process)
                    witness = room_view(faithful)
                    require(witness, 'skeleton servant')
                    if any('hdnecroqa' in x for x in witness.splitlines() if x.strip().startswith('you see')):
                        raise RuntimeError('Logged out owner remains visible')
                    with connect(port, process) as relog:
                        login(relog)
                        view = room_view(relog)
                        if not any('skeleton servant' in x for x in view.splitlines() if x.strip().startswith('you see')):
                            raise RuntimeError('Living pet absent in fresh room view after reconnect')
            print('CACHE: EXTENDED REAL NATIVE GAMEPLAY PASS', flush=True)
    except Exception:
        if logfile.exists(): print('PRIVATE LISTENER LOG (tail):\n'+logfile.read_text(errors='replace')[-3000:], flush=True)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
        if digest(exe) != original_binary:
            raise RuntimeError('Accepted executable changed during replay')
        if pid() != before:
            raise RuntimeError('Production service PID changed; inspect independently')
        print('PRODUCTION SERVICE PID: UNCHANGED', flush=True)
        print('PRODUCTION DEPLOYMENT: NONE', flush=True)


if __name__ == '__main__':
    main()
