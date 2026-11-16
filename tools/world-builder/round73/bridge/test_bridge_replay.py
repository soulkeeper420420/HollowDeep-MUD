#!/usr/bin/env python3
"""Private Round 73I cross-process native/SQLite tests. No MUD service startup."""
import json
import os
from pathlib import Path
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent


def start_server(root, catalog, peer_pid):
    args = [sys.executable, str(HERE / 'ledger_server.py'),
            '--root', str(root), '--catalog', str(catalog),
            '--peer-pid', str(peer_pid), '--peer-uid', str(os.geteuid())]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    sock = root / 'ledger.sock'
    for _ in range(150):
        if sock.exists():
            if proc.poll() is not None:
                raise AssertionError('Ledger daemon exited: ' + proc.stderr.read())
            return proc, sock
        if proc.poll() is not None:
            raise AssertionError('Ledger daemon exited: ' + proc.stderr.read())
        time.sleep(.02)
    proc.terminate()
    proc.wait(timeout=4)
    raise AssertionError('Ledger daemon failed to create socket: ' + proc.stderr.read())


def stop_server(proc, sock):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
    if sock.exists() and stat.S_ISSOCK(sock.lstat().st_mode) and sock.lstat().st_uid == os.geteuid():
        sock.unlink()


def spawn_paused(executable, cwd, env):
    a, b = os.pipe()
    script = 'import os,sys;os.read(int(sys.argv[1]),1);os.execv(sys.argv[2],sys.argv[2:])'
    proc = subprocess.Popen([sys.executable, '-c', script, str(a), str(executable), str(cwd)],
                            pass_fds=(a,), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=env)
    os.close(a)
    return proc, b


def run_with_pid_gate(executable, cwd, root, catalog, env, test_bad_pid=False):
    game, gate = spawn_paused(executable, cwd, env)
    daemon = None
    sock = None
    try:
        daemon, sock = start_server(root, catalog, game.pid)
        if test_bad_pid:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as attacker:
                attacker.settimeout(2)
                attacker.connect(str(sock))
                attacker.sendall(b'BEGIN|spoof|map.0001|Nativeqa|10001|1|fake|Native Guardian\n')
                assert attacker.recv(64) == b'DENIED\n'
            print('ROUND 73I: same-UID wrong-PID socket forgery DENIED PASS', flush=True)
        os.write(gate, b'X')
        os.close(gate)
        gate = -1
        output, errors = game.communicate(timeout=20)
        if game.returncode:
            raise AssertionError('Native C bridge failed (%s):\n%s\n%s' % (game.returncode,output,errors))
        print(output.strip(), flush=True)
        return output
    finally:
        if gate >= 0:
            os.close(gate)
        if game.poll() is None:
            game.kill()
            game.communicate(timeout=3)
        if daemon is not None:
            stop_server(daemon, sock)


def main(native_exe, replay_exe):
    with tempfile.TemporaryDirectory(prefix='hollowdeep-73i-') as tmp:
        base = Path(tmp)
        service = base / 'private-ledger'
        game = base / 'private-game'
        service.mkdir(mode=0o700)
        game.mkdir(mode=0o700)
        catalog = service / 'trusted-sites.json'
        site = {'sites': [{'map_id':'map.0001','room_id':10001,
                           'guard_names':['Native Guardian'],
                           'rewards':[{'kind':'gold','amount':100}],
                           'clue':'Find the old cairn.'}]}
        catalog.write_text(json.dumps(site), encoding='utf-8')
        catalog.chmod(0o600)
        env = os.environ.copy()
        env['HD_LEDGER_BRIDGE_TEST_SOCKET'] = str(service / 'ledger.sock')
        run_with_pid_gate(native_exe, game, service, catalog, env, test_bad_pid=True)
        # Native private guard minted the encounter; trusted SQLite has the
        # *exact* guardian/event and one (still pending) claim.
        with sqlite3.connect(service / 'claims.sqlite3') as db:
            assert db.execute('select count(*) from encounters').fetchone()[0] == 1
            assert db.execute('select count(*) from defeats').fetchone()[0] == 1
            assert db.execute('select count(*) from claims').fetchone()[0] == 1
            assert db.execute('select delivery_state from claims').fetchone()[0] == 'pending'
            assert json.loads(db.execute('select reward_json from encounters').fetchone()[0]) == site['sites'][0]['rewards']
        print('ROUND 73I: server-selected rewards, unique defeat, pending claim persisted PASS', flush=True)
        # Test daemon outage. The caller still has a valid, persisted proof,
        # but cannot obtain claim authorization with no trusted daemon.
        down_env = dict(env, HD_LEDGER_EXPECT_DOWN='1')
        down = subprocess.run([str(replay_exe),str(game)],env=down_env,
                              capture_output=True,text=True,timeout=10)
        if down.returncode:
            raise AssertionError(down.stdout+'\n'+down.stderr)
        print(down.stdout.strip(),flush=True)
        # New native process and new daemon, same SQLite file. PID must be
        # reauthorized by a trusted supervisor; old proof cannot forge grants.
        run_with_pid_gate(replay_exe, game, service, catalog, env)
        with sqlite3.connect(service / 'claims.sqlite3') as db:
            assert db.execute('select count(*) from encounters').fetchone()[0] == 1
            assert db.execute('select count(*) from defeats').fetchone()[0] == 1
            assert db.execute('select count(*) from claims').fetchone()[0] == 1
            assert db.execute('select delivery_state from claims').fetchone()[0] == 'pending'
        print('ROUND 73I: private exact-PID combat-to-SQLite integration PASS; rewards DISABLED', flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: test_bridge_replay.py NATIVE_CLIENT REPLAY_CLIENT')
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
