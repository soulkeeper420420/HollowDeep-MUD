#!/usr/bin/env python3
"""Build and smoke-test original Mordor in a new, disposable localhost world.

Requires Linux and a working 32-bit compiler/runtime. This never connects to an
existing game or accepts a world path. All players, credentials and saves are
temporary. Example:
  python3 tests/test_runtime.py --archive Mordor_3.00.tar.gz --cc gcc
"""
import argparse
import importlib.util
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
PROMPT = re.compile(r'\(-?\d+ H -?\d+ M\): ')
PLAIN_PROMPT = re.compile(r'^: ', re.MULTILINE)
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
TIMEOUT = 12
QUIT_TIMEOUT = 45
QUIT_RESPONSE = re.compile(r'Goodbye!|Please wait ([1-9][0-9]*) more seconds?\.\n')


class SmokeFailure(Exception):
    pass


class Client:
    """Small incremental Telnet reader; sends only ordinary test input lines."""
    def __init__(self, connection, process, passwords, *, prompt_pattern=PROMPT):
        self.connection = connection
        self.process = process
        self.passwords = passwords
        self.prompt_pattern = prompt_pattern
        self.pending = ''
        self.telnet = 'text'
        self.telnet_command = 0
        self.echo = True
        self.connection.settimeout(0.2)

    def close(self):
        self.connection.close()

    def clean(self, data):
        output = bytearray()
        for byte in data:
            if self.telnet == 'text':
                if byte == 255:
                    self.telnet = 'iac'
                else:
                    output.append(byte)
            elif self.telnet == 'iac':
                if byte == 255:
                    output.append(byte)
                    self.telnet = 'text'
                elif byte in (251, 252, 253, 254):
                    self.telnet_command = byte
                    self.telnet = 'option'
                elif byte == 250:
                    self.telnet = 'subnegotiation'
                else:
                    self.telnet = 'text'
            elif self.telnet == 'option':
                if byte == 1 and self.telnet_command in (251, 252):
                    self.echo = self.telnet_command == 252
                    reply = 254 if self.echo else 253
                    self.connection.sendall(bytes([255, reply, 1]))
                self.telnet = 'text'
            elif self.telnet == 'subnegotiation' and byte == 255:
                self.telnet = 'subnegotiation-iac'
            elif self.telnet == 'subnegotiation-iac':
                self.telnet = 'text' if byte == 240 else 'subnegotiation'
        return output.decode('latin-1').replace('\r', '')

    def read_until(self, expected, *, prompt=False, label='server response', timeout=TIMEOUT):
        deadline = time.monotonic() + timeout
        pattern = expected if isinstance(expected, re.Pattern) else None
        if pattern is None:
            expected = (expected,) if isinstance(expected, str) else tuple(expected)
        while True:
            visible = ANSI.sub('', self.pending)
            if pattern is not None:
                response = pattern.search(visible)
                ends = [response.end()] if response is not None else []
                complete = response is not None
            else:
                ends = [visible.find(token) + len(token) for token in expected
                        if token in visible]
                complete = len(ends) == len(expected)
            if complete:
                end = max(ends, default=0)
                match = self.prompt_pattern.search(visible, end) if prompt else None
                if not prompt or match:
                    end = match.end() if match else end
                    result, self.pending = visible[:end], visible[end:]
                    return result
            if self.process.poll() is not None:
                raise SmokeFailure(f'{label}: engine exited with {self.process.returncode}')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                excerpt = visible[-700:]
                for password in self.passwords:
                    excerpt = excerpt.replace(password, '[redacted]')
                raise SmokeFailure(f'{label}: timed out waiting for {expected!r}; received {excerpt!r}')
            try:
                self.connection.settimeout(min(0.2, remaining))
                data = self.connection.recv(8192)
            except socket.timeout:
                continue
            if not data:
                raise SmokeFailure(f'{label}: connection closed unexpectedly')
            self.pending += self.clean(data)
            if len(self.pending) > 128 * 1024:
                raise SmokeFailure(f'{label}: excessive server output')

    def send(self, line):
        self.connection.sendall(line.encode('ascii') + b'\r\n')

    def command(self, line, expected):
        self.send(line)
        return self.read_until(expected, prompt=True, label=line)

    def create(self, name, password):
        self.read_until('Please enter name: ', label='new connection')
        # Printable option IDs and TTYPE payloads must never prefix a name.
        self.connection.sendall(bytes([255, 253, 86, 255, 250, 24, 0]) +
                                b'MUDLET' + bytes([255, 240]))
        steps = [
            (name, 'Did I get that right? '),
            ('y', 'Hit return: '),
            ('', 'Male or Female: '),
            ('m', 'Choose one: '),
            ('fighter', 'Use the following format: ## ## ## ## ##\n: '),
            ('14 10 12 10 8', 'Sharp, Thrusting, Blunt, Pole, Missile.\n: '),
            ('sharp', 'Chaotic or Lawful: '),
            ('lawful', 'Choose one: '),
            ('human', 'Choose a password (up to 14 chars): '),
        ]
        for number, (line, expected) in enumerate(steps, 1):
            self.send(line)
            self.read_until(expected, label=f'create {name}, step {number}')
        if self.echo:
            raise SmokeFailure('new character password prompt did not disable client echo')
        self.send(password)
        self.read_until("Type 'welcome'", prompt=True, label=f'finish creating {name}')
        if not self.echo:
            raise SmokeFailure('client echo was not restored after character creation')

    def login(self, name, password, *, welcome='Hollowdeep: original Mordor 3.00'):
        self.read_until('Please enter name: ', label='reconnect')
        self.connection.sendall(name.encode('ascii') + b'\r')
        self.read_until('Please enter password: ', label='existing character login')
        if self.echo:
            raise SmokeFailure('existing character password prompt did not disable client echo')
        # The password prompt proves the first CR was processed by read(). The
        # following LF must be consumed, not submitted as an empty password.
        self.connection.sendall(b'\n')
        self.send(password)
        self.read_until(welcome, prompt=True,
                        label='finish existing character login')
        if not self.echo:
            raise SmokeFailure('client echo was not restored after successful login')

    def quit(self):
        # Original Mordor also applies its attack/spell cooldown on a new
        # character's first login. A refused quit must be retried explicitly;
        # waiting longer for Goodbye alone can never complete that command.
        deadline = time.monotonic() + QUIT_TIMEOUT
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SmokeFailure('save and quit: cooldown retry deadline exceeded')
            self.send('quit')
            response = self.read_until(QUIT_RESPONSE, label='save and quit',
                                       timeout=min(TIMEOUT, remaining))
            match = QUIT_RESPONSE.search(response)
            if match.group(1) is None:
                self.close()
                return
            delay = int(match.group(1)) + 0.1
            if delay >= deadline - time.monotonic():
                raise SmokeFailure('save and quit: cooldown exceeds the 45-second retry limit')
            time.sleep(delay)


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def available_port(requested):
    # Refuse an occupied explicit port before starting or connecting to anything.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', requested or 0))
        return probe.getsockname()[1]


def connect(port, process, passwords, *, prompt_pattern=PROMPT):
    deadline = time.monotonic() + TIMEOUT
    while process.poll() is None and time.monotonic() < deadline:
        try:
            connection = socket.create_connection(('127.0.0.1', port), timeout=0.2)
            return Client(connection, process, passwords, prompt_pattern=prompt_pattern)
        except (ConnectionRefusedError, TimeoutError):
            time.sleep(0.05)
    raise SmokeFailure(f'engine did not open its localhost listener (exit={process.poll()})')


def wait_for_completed_quit(port, process, passwords):
    # disconnect() sends Goodbye and closes the socket before writing the
    # character save. Accepting a fresh connection on the same single-threaded
    # event loop proves that the previous disconnect handler has completed.
    checkpoint = connect(port, process, passwords)
    try:
        checkpoint.read_until('Please enter name: ', label='quit save completion')
    finally:
        checkpoint.close()


def run(args):
    spec = importlib.util.spec_from_file_location('hollowdeep_manage', ROOT / 'manage.py')
    manage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manage)
    passwords = [secrets.token_hex(6), secrets.token_hex(6)]
    clients, process = [], None
    with tempfile.TemporaryDirectory(prefix='hollowdeep-runtime-') as temporary:
        base = Path(temporary)
        world = manage.prepare_archive(args.archive.resolve(), base / 'world', 'Realmkeeper')
        build_command = [sys.executable, str(ROOT / 'manage.py'), 'build', '--work', str(world), '--cc', args.cc]
        if args.runner:
            build_command.extend(['--runner', args.runner])
        build = subprocess.run(
            build_command,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=240)
        if build.returncode:
            raise SmokeFailure('32-bit engine build failed:\n' + build.stdout[-8000:])
        executable = world / manage.SOURCE_DIR / 'frp.new'
        if executable.read_bytes()[:5] != b'\x7fELF\x01':
            raise SmokeFailure('engine is not a 32-bit ELF executable')
        print('PASS: prepared and linked original engine as ELF32', flush=True)
        port = available_port(args.port)
        log_path = base / 'engine.log'
        try:
            with log_path.open('ab') as log:
                def launch():
                    environment = os.environ.copy()
                    environment['HOLLOWDEEP_BIND'] = '127.0.0.1'
                    command = ([args.runner] if args.runner else []) + [str(executable), str(port), '-r']
                    return subprocess.Popen(command, cwd=world,
                                            env=environment, stdin=subprocess.DEVNULL,
                                            stdout=log, stderr=subprocess.STDOUT)

                process = launch()
                hero = connect(port, process, passwords)
                clients.append(hero)
                hero.create('Smokehero', passwords[0])
                hero.command('look', 'The Tree of Life')
                hero.command('score', ('Smokehero', '(level 1)'))
                hero.command('hcommands', 'HOLLOWDEEP COMMANDS')
                hero.command('hclass', 'Fighter:')
                hero.command('hclass mage', 'Mage:')
                hero.command('hprofile status', ('HP ', 'MP ', 'XP '))
                hero.command('hclass progress', '512')
                hero.command('hcommands mobile', 'MOBILE')
                hero.command('spells', ('YOUR KNOWN SPELLS', 'Spells known:', 'Mana:'))
                hero.command('spell', 'YOUR KNOWN SPELLS')
                hero.command('spells fireball', 'Usage: spells')
                hero.command('help spell', 'SPELLS - Your learned spells')
                hero.command('hstance', 'Combat stance: balanced.')
                hero.command('hstaff whoami', 'role: player')
                hero.command('help', 'HOLLOWDEEP HELP')
                hero.command('help commands 2', 'Page 2/')
                hero.command('help search staff', 'hstaffclan')
                hero.command('help wave', 'SOCIAL')
                hero.command('skills', ('bash -', 'circle -'))
                hero.command('skills all', ('18 skills listed', 'touch [monk, level 10]'))
                hero.command('dmcommands', 'No staff or DM powers assigned')
                hero.command('staffclan', 'staff role is required')
                hero.command('*memory', 'Native caretaker/DM permission required')
                print('PASS: character creation, world loading, class and command guides', flush=True)

                friend = connect(port, process, passwords)
                clients.append(friend)
                friend.create('Smokefriend', passwords[1])
                hero.command('who', ('Smokehero', 'Smokefriend'))
                hero.command('say hello companion', 'Ok.')
                friend.read_until('hello companion.', prompt=True, label='room chat delivery')
                hero.command('tell Smokefriend private greeting', 'Message sent to Smokefriend.')
                friend.read_until('private greeting', prompt=True, label='private message delivery')
                friend.command('follow Smokehero', 'You start following Smokehero.')
                hero.command('group', ('People in your group:', 'Smokefriend'))
                hero.command('gtalk party greeting', 'party greeting')
                friend.read_until('party greeting', prompt=True, label='group message delivery')
                friend.command('follow Smokefriend', 'You stop following Smokehero.')
                friend.command('save', 'Player saved.')
                hero.command('save', 'Player saved.')
                # The configured founder becomes a native DM during creation.
                # Mordor leaves its HP/MP prompt flag off for that class.
                owner = connect(port, process, passwords, prompt_pattern=PLAIN_PROMPT)
                clients.append(owner)
                owner.create('Realmkeeper', passwords[0])
                owner.command('hstaff whoami', 'role: owner')
                owner.command('hstaff grant Smokehero admin', 'now has the admin role')
                hero.command('hstaff grant Smokefriend mod', 'now has the mod role')
                friend.command('hstaff grant Smokehero owner', 'permission required')
                hero.command('who', ('[ADMIN]', '[MOD]'))
                hero.command('dmcommands', 'x1-x10, 1-1440')
                friend.command('dmhelp', 'x1-x5, 1-60')
                owner.command('dmcommands native', 'NATIVE DM COMMANDS')
                friend.command('staffclan', ('HOLLOWDEEP STAFF CLAN', '[MOD]'))
                friend.command('staffclan say Keep the lantern burning', 'Keep the lantern burning')
                hero.read_until('[MOD] Smokefriend: Keep the lantern burning', prompt=True, label='staff clan delivery')
                owner.read_until('[MOD] Smokefriend: Keep the lantern burning', prompt=True, label='staff clan owner delivery')
                friend.command('hbuild info', 'Room ')
                friend.command('hbuild name Unauthorized edit', 'assigned room range')
                friend.command('hdm goto 8998', 'Admin permission required')
                owner.command('hbuild assign Smokehero 8950', '8950-8999 (50 rooms)')
                hero.command('hbuild mine', '8950-8999')
                owner.command('hbuild assign Smokefriend 8990', 'count 1-500')
                owner.command('hbuild assign Smokefriend 8975 20', 'overlaps Smokehero')
                owner.command('hbuild assign Smokefriend 8900', '8900-8949 (50 rooms)')
                home_room = int(re.search(r'Room (\d+):', hero.command('hbuild info', 'Room ')).group(1))
                hero.command('hbuild create 8998', 'Created room 8998')
                hero.command('hbuild create 8998', 'already exists')
                hero.command('hdm goto 8998', 'Teleported Smokehero to room 8998')
                hero.command('hbuild name Hall of the Seven Lanterns', 'name saved')
                hero.command('hbuild describe Seven lanterns light the quiet hall of the builders.', 'describe saved')
                hero.command(f'hbuild link down {home_room}', 'destination must also')
                owner.command('hdm goto 8998', 'Teleported Realmkeeper to room 8998')
                owner.command(f'hbuild link down {home_room}', 'one-way')
                owner.command(f'hdm goto {home_room}', f'to room {home_room}')
                hero.command('hbuild info', ('Hall of the Seven Lanterns', f'down -> {home_room}'))
                hero.command('hdm restore', 'Restored Smokehero')
                hero.command('hdm restore Smokefriend', 'Owner permission required')
                hero.command('hclass', 'Fighter:')
                owner.command('hdm bring Smokehero', f'Teleported Smokehero to room {home_room}')
                owner.command('hdm restore Smokehero', 'Restored Smokehero')
                friend.command('hbonus start both 5 60', 'Bonus event started')
                owner.command('hbonus stop', 'Bonus event stopped')
                hero.command('hstaff grant Smokefriend implementor', 'now has the implementor role')
                friend.command('hstaff whoami', 'role: implementor')
                hero.command('who', '[IMPLEMENTOR]')
                friend.command('staffclan who', '[IMPLEMENTOR] Smokefriend')
                friend.command('hstaff audit', 'Admin permission required')
                friend.command('hbonus start both 6 60', 'Moderators/Implementors: x1-x5')
                friend.command('hbonus start both 5 61', 'Moderators/Implementors: x1-x5')
                friend.command('hbonus start both 5 60', 'Bonus event started')
                hero.command('hbonus stop', 'Bonus event stopped')
                hero.command('hbonus start both 10 1440', 'Bonus event started')
                friend.command('hbonus', ('monster XP x10', 'monster gold x10'))
                owner.command('hbonus stop', 'Bonus event stopped')
                owner.command('hbonus start gold 20 1440', 'Bonus event started')
                hero.command('hbonus stop', "creator's rank or higher")
                hero.command('hmoderate mute Smokefriend 1', 'muted for 1')
                friend.command('say muted test', 'You are muted')
                friend.command('staffclan say muted clan test', 'You are muted')
                hero.command('hmoderate unmute Smokefriend', 'may chat again')
                friend.command('say speaking again', 'Ok.')
                owner.command('hstaff revoke Smokehero', 'now has the player role')
                owner.command('hbuild unassign Smokehero', 'revoked immediately')
                hero.command('staffclan', 'staff role is required')
                hero.command('hbuild name Revoked edit', 'assigned room range')
                hero.command('hdm restore', 'Admin permission required')
                owner.command('hstaff revoke Smokefriend', 'now has the player role')
                friend.command('hbonus stop', 'permission required')
                owner.command('hstaff grant Smokefriend implementor', 'now has the implementor role')
                owner.quit()
                friend.quit()
                hero.command('hstance aggressive', 'Combat stance: aggressive.')
                print('PASS: two simultaneous players, who, say, tell, follow, group and gtalk', flush=True)

                hero.command('hquest', 'THE HOLLOWDEEP CHRONICLES')
                hero.command('hquest next', 'first-steps')
                hero.command('hquest accept first-steps', 'Accepted: Beyond the threshold.')
                hero.command('hquest survey', 'Unique places: 1.')
                hero.command('hquest survey', 'This place is already in your chronicle.')
                hero.command('hquest claim first-steps', 'Not complete: 1/3 places; level 1/1.')
                hero.command('down', 'The Tree of Life')
                hero.command('hquest survey', 'Unique places: 2.')
                # Room 1784 has an unrestricted north exit to room 1724.
                hero.send('north')
                hero.read_until((), prompt=True, label='move north')
                hero.command('hquest survey', 'Unique places: 3.')
                hero.command('hquest claim first-steps', 'You earned the Wayfarer badge!')
                hero.command('hquest claim first-steps', 'You already earned that badge.')
                hero.command('hprofile', ('Recorded places: 3.', 'Badge: Wayfarer'))
                hero.command('save', 'Player saved.')
                hero.quit()
                print('PASS: movement, unique surveys, early/repeated claim guards and earned badge', flush=True)

                # A process restart ensures persistence is not just in-memory state.
                wait_for_completed_quit(port, process, passwords)
                stop(process)
                process = launch()
                hero = connect(port, process, passwords)
                clients.append(hero)
                hero.login('Smokehero', passwords[0])
                hero.command('score', ('Smokehero', '(level 1)'))
                hero.command('hclass', 'Fighter:')
                hero.command('hstance', 'Combat stance: aggressive.')
                hero.command('hprofile', ('Recorded places: 3.', 'Badge: Wayfarer'))
                hero.command('hquest', 'first-steps')
                hero.command('hquest claim first-steps', 'You already earned that badge.')
                hero.quit()
                print('PASS: saved character and chronicle survive engine restart and login', flush=True)
                owner = connect(port, process, passwords, prompt_pattern=PLAIN_PROMPT)
                clients.append(owner)
                owner.login('Realmkeeper', passwords[0], welcome='Realmkeeper the ')
                owner.command('hbuild ranges', 'Smokefriend: 8900-8949')
                owner.command('hstaff list', 'Smokefriend: implementor')
                owner.command('staffclan who', '[IMPLEMENTOR] Smokefriend')
                owner.command('hbonus', ('monster XP x1', 'monster gold x20'))
                owner.command('hbonus stop', 'Bonus event stopped')
                owner.command('hdm goto 8998', 'Teleported Realmkeeper to room 8998')
                owner.command('look', ('Hall of the Seven Lanterns', 'Seven lanterns light'))
                owner.command('hbuild info', f'down -> {home_room}')
                owner.command('hbuild unlink down', 'removed and saved')
                owner.command(f'hbuild link down {home_room}', 'one-way')
                owner.command(f'hdm goto {home_room}', f'to room {home_room}')
                owner.quit()
                print('PASS: role-scoped building, DM powers, immediate revocation and room persistence', flush=True)
        except (SmokeFailure, OSError) as error:
            log_tail = log_path.read_text(errors='replace')[-4000:] if log_path.exists() else ''
            detail = str(error) + ('\nEngine log:\n' + log_tail if log_tail else '')
            for password in passwords:
                detail = detail.replace(password, '[redacted]')
            raise SmokeFailure(detail) from None
        finally:
            for client in clients:
                client.close()
            stop(process)
    print('Native runtime smoke test passed; disposable world removed.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True,
                        help='Unmodified checksum-pinned Mordor_3.00.tar.gz')
    parser.add_argument('--cc', default=os.environ.get('CC', 'cc'),
                        help='Compiler executable or wrapper path (default: CC or cc)')
    parser.add_argument('--runner', help='Single executable such as qemu-i386 for running ELF32')
    parser.add_argument('--port', type=int, help='Unused localhost TCP port; default: select one')
    args = parser.parse_args()
    if args.port is not None and not 1024 <= args.port <= 65535:
        parser.error('--port must be between 1024 and 65535')
    try:
        run(args)
    except (SmokeFailure, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
