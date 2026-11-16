#!/usr/bin/env python3
"""TEST ONLY: process-authenticated Round 73I native-to-ledger Unix socket.

Not an installed service. Not wired into a production build. A trusted
supervisor must choose exact native engine PID/UID, and operate this process
under a *separate* OS identity for real security; the offline harness deliberately
uses a single identity and tests exact PID checks, not privilege separation.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import stat
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
# A published checkout runs this script alongside this read-only *test* module.
try:
    from claim_ledger import TreasureLedger, TreasureError
except ImportError:
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from claim_ledger import TreasureLedger, TreasureError

MAX_REQUEST = 1024
MAX_CLIENTS = 64


def _open_trusted_file(path):
    # Only isolated, owner-controlled fixture directories are supported.
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid() or st.st_nlink != 1 or st.st_mode & 0o077:
        raise ValueError('Fixture must be singly-linked, private and owned by service')
    if path.is_symlink():
        raise ValueError('Fixture symlink refused')
    return path.read_text('utf-8')


def _token(s, minimum=3, maximum=96):
    return isinstance(s, str) and minimum <= len(s) <= maximum and all(
        c.isascii() and (c.isalnum() or c in '._:-') for c in s)


def _name(s):
    return (isinstance(s, str) and 1 <= len(s) < 80 and s == s.strip()
            and all(32 <= ord(c) <= 126 and c not in '|\r\n' for c in s))


def _hex32(s):
    return isinstance(s, str) and len(s) == 32 and all(c in '0123456789abcdef' for c in s)


def _load_sites(path):
    body = json.loads(_open_trusted_file(path))
    if type(body) is not dict or set(body) != {'sites'} or type(body['sites']) is not list or not 1 <= len(body['sites']) <= MAX_CLIENTS:
        raise ValueError('Invalid trusted site catalog')
    sites = {}
    for site in body['sites']:
        if type(site) is not dict or set(site) != {'map_id', 'room_id', 'guard_names', 'rewards', 'clue'}:
            raise ValueError('Invalid site')
        mid = site['map_id']
        names = site['guard_names']
        if (not _token(mid, 3, 32) or mid in sites or
                type(site['room_id']) is not int or not 10000 <= site['room_id'] < 16000 or
                type(names) is not list or not 1 <= len(names) <= 5 or
                any(not _name(n) for n in names) or len(set(names)) != len(names) or
                type(site['rewards']) is not list or type(site['clue']) is not str):
            raise ValueError('Invalid trusted site fields')
        sites[mid] = site
    return sites


class LedgerBoundary:
    def __init__(self, database, sites):
        self.ledger = TreasureLedger(database)
        self.sites = sites

    def dispatch(self, request):
        if not isinstance(request, bytes) or not request.endswith(b'\n') or len(request) > MAX_REQUEST:
            return 'DENIED'
        try:
            parts = request[:-1].decode('ascii').split('|')
        except UnicodeError:
            return 'DENIED'
        if not parts:
            return 'DENIED'
        op = parts[0]
        try:
            if op == 'BEGIN':
                if len(parts) < 8:
                    return 'DENIED'
                _, encounter, map_id, owner, room_raw, count_raw, *items = parts
                if (not _hex32(encounter) or not _token(map_id, 3, 32) or
                        not _token(owner, 3, 79) or not room_raw.isdecimal() or
                        not count_raw.isdecimal()):
                    return 'DENIED'
                site = self.sites.get(map_id)
                count = int(count_raw)
                room = int(room_raw)
                if (site is None or count != len(site['guard_names']) or
                        len(items) != count * 2 or room != site['room_id']):
                    return 'DENIED'
                guardians = items[::2]
                names = items[1::2]
                if (any(not _hex32(g) for g in guardians) or
                        len(set(guardians)) != count or names != site['guard_names']):
                    return 'DENIED'
                # Only server-side configured rewards and clue are used.
                self.ledger.register(encounter, map_id, owner, room, guardians,
                                     site['rewards'], clue=site['clue'])
                return 'OK'
            if op == 'KILL' and len(parts) == 5:
                _, encounter, guardian, event, owner = parts
                if not (_hex32(encounter) and _hex32(guardian) and _hex32(event) and _token(owner, 3, 79)):
                    return 'DENIED'
                complete = self.ledger.record_verified_kill(encounter, guardian, event, owner)
                return 'READY' if complete else 'OK'
            if op == 'CLAIM' and len(parts) == 4:
                _, encounter, owner, map_id = parts
                if not (_hex32(encounter) and _token(owner, 3, 79) and _token(map_id, 3, 32)):
                    return 'DENIED'
                # The exact PID-authenticated native caller must have traversed
                # the actual carried map before asserting this map_id. This
                # server cannot independently see the live in-memory inventory.
                row = self.ledger.claim(encounter, owner, [map_id])
                return 'PENDING' if row['delivery_state'] == 'pending' else 'DELIVERED'
        except (TreasureError, ValueError, OverflowError, KeyError, TypeError):
            return 'DENIED'
        return 'DENIED'


def _serve(root, fixture, game_pid, game_uid):
    if not root.is_absolute() or str(root).startswith('/srv/hollowdeep'):
        raise ValueError('Refusing production or relative root')
    if root.is_symlink():
        raise ValueError('Symlink root refused')
    st = root.stat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
        raise ValueError('Root must be precreated, private 0700, and owned by server')
    sites = _load_sites(fixture)
    boundary = LedgerBoundary(root / 'claims.sqlite3', sites)
    address = root / 'ledger.sock'
    if len(os.fsencode(address)) >= 107 or address.exists() or address.is_symlink():
        raise ValueError('Socket path unsafe or occupied')
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        old = os.umask(0o077)
        try:
            sock.bind(str(address))
        finally:
            os.umask(old)
        os.chmod(address, 0o600)
        sock.listen(8)
        sock.settimeout(1)
        print('ROUND 73I LEDGER READY', flush=True)
        while True:
            try:
                conn, _ = sock.accept()
            except socket.timeout:
                continue
            with conn:
                conn.settimeout(2)
                try:
                    pid, uid, _gid = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                    if pid != game_pid or uid != game_uid:
                        conn.sendall(b'DENIED\n')
                        continue
                    # Read bounded single-line protocol. No follow-up commands.
                    req = b''
                    while len(req) <= MAX_REQUEST and b'\n' not in req:
                        part = conn.recv(256)
                        if not part:
                            break
                        req += part
                    if req.count(b'\n') != 1 or req[-1:] != b'\n':
                        verdict = 'DENIED'
                    else:
                        verdict = boundary.dispatch(req)
                    conn.sendall(verdict.encode('ascii') + b'\n')
                except (ConnectionError, OSError, TimeoutError, socket.timeout):
                    pass
    finally:
        sock.close()
        try:
            if address.is_socket() and not address.is_symlink():
                address.unlink()
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--catalog', required=True, type=Path)
    ap.add_argument('--peer-pid', type=int, required=True)
    ap.add_argument('--peer-uid', type=int, required=True)
    args = ap.parse_args()
    if args.peer_pid < 2 or args.peer_uid < 0:
        ap.error('Invalid trusted peer PID/UID')
    _serve(args.root, args.catalog, args.peer_pid, args.peer_uid)


if __name__ == '__main__':
    main()
