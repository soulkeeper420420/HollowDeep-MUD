#!/usr/bin/env python3
"""Round 73J isolated multi-process native game/save/ledger replay."""
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

def start_game_paused(exe, game_root, mode, env):
    r, w = os.pipe()
    script = 'import os,sys;os.read(int(sys.argv[1]),1);os.execv(sys.argv[2],sys.argv[2:])'
    p = subprocess.Popen([sys.executable, '-c', script, str(r), str(exe), str(game_root), mode],
                         pass_fds=(r,), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=env)
    os.close(r)
    return p, w

def launch_daemon(root, catalog, templates, game_root, verifier, game_pid):
    cmd = [sys.executable, str(HERE / 'reward_server.py'),
           '--root', str(root), '--catalog', str(catalog), '--templates', str(templates),
           '--player-root', str(game_root), '--verifier', str(verifier),
           '--peer-pid', str(game_pid), '--peer-uid', str(os.geteuid())]
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sock=root/'ledger.sock'
    for _ in range(150):
        if p.poll() is not None:
            raise RuntimeError('Ledger service rejected startup: '+p.stderr.read())
        if sock.exists():
            return p,sock
        time.sleep(.02)
    p.terminate();p.communicate(timeout=3)
    raise RuntimeError('Ledger service startup timed out')

def halt_daemon(proc, sock):
    proc.terminate()
    try:
        proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill();proc.communicate(timeout=3)
    if sock.exists() and stat.S_ISSOCK(sock.lstat().st_mode) and sock.lstat().st_uid==os.geteuid():
        sock.unlink()

def check_db(db, state):
    with sqlite3.connect(db) as con:
        assert con.execute('SELECT COUNT(*) FROM encounters').fetchone()[0] == 1
        assert con.execute('SELECT COUNT(*) FROM defeats').fetchone()[0] == 1
        assert con.execute('SELECT COUNT(*) FROM claims').fetchone()[0] == 1
        assert con.execute('SELECT COUNT(*) FROM reward_manifests').fetchone()[0] == 1
        found=con.execute('SELECT delivery_state FROM claims').fetchone()[0]
        assert found==state,(found,state)

def run_game(exe, verifier, game_root, service, catalog, templates, mode, overrides, spoof=False):
    env=dict(os.environ,HD_LEDGER_BRIDGE_TEST_SOCKET=str(service/'ledger.sock'))
    env.pop('HD_ATOMIC_FAIL',None)
    env.update(overrides)
    game,gate=start_game_paused(exe,game_root,mode,env)
    daemon=None
    try:
        daemon,sock=launch_daemon(service,catalog,templates,game_root,verifier,game.pid)
        if spoof:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as intruder:
                intruder.settimeout(3);intruder.connect(str(sock))
                intruder.sendall(b'GRANT|00000000000000000000000000000000|Nativeqa|map.0001\n')
                assert intruder.recv(64)==b'DENIED\n'
            print('ROUND 73J: same-UID wrong-PID manifest spoof DENIED PASS',flush=True)
        os.write(gate,b'x');os.close(gate);gate=-1
        stdout,stderr=game.communicate(timeout=30)
        if game.returncode:
            raise AssertionError('Native game failed (%d):\n%s\n%s' % (game.returncode,stdout,stderr))
        print(stdout.strip(),flush=True)
    finally:
        if gate>=0:os.close(gate)
        if game.poll() is None:
            game.kill();game.communicate(timeout=5)
        if daemon is not None:halt_daemon(daemon,sock)

def main(native, verifier):
    for scenario in ('normal','ack_lost','failed_before','uncertain_after'):
        with tempfile.TemporaryDirectory(prefix='hd73j-') as t:
            root=Path(t)
            service=root/'service';game=root/'game'
            service.mkdir(mode=0o700);game.mkdir(mode=0o700)
            catalog=service/'sites.json';templates=service/'templates.json'
            catalog.write_text(json.dumps({'sites':[{'map_id':'map.0001','room_id':10001,
                  'guard_names':['Native Guardian'],
                  'rewards':[{'kind':'item','template_id':123,'quantity':1,'enchantment':None},
                             {'kind':'material','template_id':124,'quantity':1},
                             {'kind':'gold','amount':150}],
                  'clue':'Find the old cairn.'}]}),encoding='utf-8')
            templates.write_text(json.dumps({'templates':{
                  '123':{'kind':'item','enchant_caps':{}},
                  '124':{'kind':'material','enchant_caps':{}}}}),encoding='utf-8')
            catalog.chmod(0o600);templates.chmod(0o600)
            overrides={'HD_J_PREACK':'1'}
            if scenario=='ack_lost':overrides['HD_J_SKIP_ACK']='1'
            if scenario=='failed_before':overrides['HD_J_FAULT']='before_rename'
            if scenario=='uncertain_after':overrides['HD_J_FAULT']='after_rename'
            run_game(native,verifier,game,service,catalog,templates,'initial',overrides,spoof=True)
            check_db(service/'claims.sqlite3','delivered' if scenario=='normal' else 'pending')
            if scenario=='uncertain_after':
                print('ROUND 73J: uncertain rename leaves ledger pending until fresh process+dir fsync PASS',flush=True)
            if scenario=='failed_before':
                print('ROUND 73J: failed native save does not acknowledge/alter existing player PASS',flush=True)
            if scenario=='ack_lost':
                print('ROUND 73J: successful save interrupted before ledger ack stays pending PASS',flush=True)
            run_game(native,verifier,game,service,catalog,templates,'replay',{},spoof=False)
            check_db(service/'claims.sqlite3','delivered')
            # Fresh daemon and native player session never produce a second grant.
            run_game(native,verifier,game,service,catalog,templates,'replay',{},spoof=False)
            check_db(service/'claims.sqlite3','delivered')
            print('ROUND 73J: '+scenario+' durable native chest->receipt->ledger recovery PASS',flush=True)
    print('ROUND 73J: isolated native playable-claim simulator PASS (production rewards disabled)',flush=True)

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: test_reward_replay.py NATIVE_HARNESS VERIFIER')
    main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
