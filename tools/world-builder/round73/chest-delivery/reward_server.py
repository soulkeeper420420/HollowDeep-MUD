#!/usr/bin/env python3
"""Round 73J private-only PID-bound claim/manifest/receipt ledger server.

TEST-ONLY. Same-UID socket fixtures and verifier are not a production trust
boundary. Do not run this on the deployed MUD or with live player records.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'bridge'))
from ledger_server import LedgerBoundary, _load_sites, _open_trusted_file, _hex32, _token, MAX_REQUEST
from durable_delivery import DurableRewardCoordinator, DeliveryError
from claim_ledger import TreasureError

REPLY_CAP = 4096


def trusted_templates(path):
    data = json.loads(_open_trusted_file(path))
    if type(data) is not dict or set(data) != {'templates'} or type(data['templates']) is not dict:
        raise ValueError('Invalid trusted reward template catalog')
    out = {}
    for key, row in data['templates'].items():
        if not isinstance(key, str) or not key.isascii() or not key.isdecimal():
            raise ValueError('Invalid template ID')
        template_id = int(key)
        if (not 1 <= template_id < 1000 or str(template_id) != key or
                type(row) is not dict or set(row) != {'kind', 'enchant_caps'} or
                row['kind'] not in ('item', 'material') or type(row['enchant_caps']) is not dict or
                row['enchant_caps']):
            raise ValueError('Unsupported native template/enchant policy')
        out[template_id] = row
    if not 1 <= len(out) <= 128:
        raise ValueError('Template catalog size invalid')
    return out


class RewardBoundary(LedgerBoundary):
    def __init__(self, db, sites, templates, receipt_probe):
        super().__init__(db, sites)
        self.templates = templates
        self.probe = receipt_probe
        self.coordinator = DurableRewardCoordinator(self.ledger, None)

    def _get_pending(self, encounter, owner, map_id):
        if not (_hex32(encounter) and _token(owner, 3, 79) and _token(map_id, 3, 32)):
            raise ValueError('Invalid claim fields')
        # Only the pinned native game PID is allowed to assert a held map,
        # but the native map identity is still a test fixture, not minted proof.
        claim = self.ledger.claim(encounter, owner, [map_id])
        if claim['delivery_state'] == 'delivered':
            return claim, None, None
        manifest, digest = self.coordinator._prepare(claim, self.templates)
        return claim, manifest, digest

    def dispatch(self, req):
        if not isinstance(req, bytes) or not req.endswith(b'\n') or len(req) > MAX_REQUEST:
            return 'DENIED'
        try:
            fields = req[:-1].decode('ascii').split('|')
        except UnicodeError:
            return 'DENIED'
        if not fields:
            return 'DENIED'
        try:
            if fields[0] == 'GRANT' and len(fields) == 4:
                _, encounter, owner, map_id = fields
                claim, manifest, digest = self._get_pending(encounter, owner, map_id)
                if manifest is None:
                    # Even delivered claims must retain a matching durable
                    # native receipt; never hide a missing player save.
                    with self.ledger.transaction() as db:
                        row = db.execute('SELECT digest FROM reward_manifests WHERE claim_id=?',
                                         (claim['claim_id'],)).fetchone()
                    if row is None or not self.probe(owner, claim['claim_id'], row[0]):
                        return 'DENIED'
                    return 'ALREADY'
                units = []
                for unit in manifest['items']:
                    if unit['enchantment'] is not None:
                        return 'DENIED'  # No native enchantment mapping yet.
                    kind = {'item': 'i', 'material': 'm'}.get(unit['kind'])
                    if kind is None or unit['template_id'] not in self.templates:
                        return 'DENIED'
                    units.append('%s,%d,%s,0' % (unit['instance_id'], unit['template_id'], kind))
                body = '|'.join(['MANIFEST', claim['claim_id'], digest, str(manifest['gold']),
                                 str(len(units))] + units)
                return body if len(body.encode('ascii')) + 1 <= REPLY_CAP else 'DENIED'
            if fields[0] == 'ACK' and len(fields) == 6:
                _, encounter, owner, map_id, claim_id, digest = fields
                if not (_hex32(claim_id) and len(digest) == 64 and
                        all(x in '0123456789abcdef' for x in digest)):
                    return 'DENIED'
                claim, manifest, current_digest = self._get_pending(encounter, owner, map_id)
                if claim['claim_id'] != claim_id:
                    return 'DENIED'
                if manifest is None:
                    # Replayed acknowledged claims require the same persisted
                    # digest in the immutable manifest table.
                    with self.ledger.transaction() as db:
                        row = db.execute('SELECT digest FROM reward_manifests WHERE claim_id=?',
                                         (claim_id,)).fetchone()
                    if row is None or row[0] != digest or not self.probe(owner, claim_id, digest):
                        return 'DENIED'
                    return 'DELIVERED'
                if current_digest != digest:
                    return 'DENIED'
                # Do not trust a native "saved successfully" message. A *separate*
                # on-disk native decoder first fsyncs the player directory and
                # independently reads the claim receipt out of compressed save.
                if not self.probe(owner, claim_id, digest):
                    return 'DENIED'
                self.ledger.acknowledge_native_delivery(claim_id, owner,
                                                         'native.' + digest[:32])
                return 'DELIVERED'
        except (TreasureError, DeliveryError, ValueError, TypeError, KeyError,
                OverflowError, UnicodeError):
            return 'DENIED'
        return super().dispatch(req)


def receipt_probe(exe, root):
    if exe.is_symlink() or root.is_symlink():
        raise ValueError('Refusing symlinked test fixture')
    exe = exe.resolve(strict=True)
    root = root.resolve(strict=True)
    if (str(root).startswith('/srv/hollowdeep') or
            not root.is_dir() or stat.S_IMODE(root.stat().st_mode) != 0o700 or
            root.stat().st_uid != os.geteuid()):
        raise ValueError('Refusing unsafe player fixture root')
    s = exe.stat()
    if (not stat.S_ISREG(s.st_mode) or s.st_uid != os.geteuid() or
            s.st_nlink != 1 or s.st_mode & 0o022 or not os.access(exe, os.X_OK)):
        raise ValueError('Refusing unsafe verifier binary')
    def probe(owner, claim_id, digest):
        if not (_token(owner, 3, 79) and _hex32(claim_id) and
                len(digest) == 64 and all(x in '0123456789abcdef' for x in digest)):
            return False
        try:
            proc = subprocess.run([str(exe), owner, claim_id, digest],
                                  cwd=root, env={'PATH': '/usr/bin:/bin'},
                                  capture_output=True, timeout=4, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return proc.returncode == 0
    return probe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--catalog', type=Path, required=True)
    ap.add_argument('--templates', type=Path, required=True)
    ap.add_argument('--player-root', type=Path, required=True)
    ap.add_argument('--verifier', type=Path, required=True)
    ap.add_argument('--peer-pid', type=int, required=True)
    ap.add_argument('--peer-uid', type=int, required=True)
    args = ap.parse_args()
    root = args.root
    if (not root.is_absolute() or str(root).startswith('/srv/hollowdeep') or
            root.is_symlink() or not root.is_dir() or
            root.stat().st_uid != os.geteuid() or stat.S_IMODE(root.stat().st_mode) != 0o700 or
            args.peer_pid < 2 or args.peer_uid < 0):
        raise ValueError('Invalid private ledger root or peer identity')
    sockpath = root / 'ledger.sock'
    if len(os.fsencode(sockpath)) >= 107 or sockpath.exists() or sockpath.is_symlink():
        raise ValueError('Unsafe or occupied socket path')
    boundary = RewardBoundary(root / 'claims.sqlite3', _load_sites(args.catalog),
                              trusted_templates(args.templates),
                              receipt_probe(args.verifier, args.player_root))
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        old = os.umask(0o077)
        try:
            server.bind(str(sockpath))
        finally:
            os.umask(old)
        os.chmod(sockpath, 0o600)
        server.listen(8)
        server.settimeout(1)
        print('ROUND 73J REWARD LEDGER READY', flush=True)
        while True:
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            with conn:
                conn.settimeout(2)
                try:
                    pid, uid, _gid = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                    if pid != args.peer_pid or uid != args.peer_uid:
                        conn.sendall(b'DENIED\n')
                        continue
                    req = bytearray()
                    while len(req) <= MAX_REQUEST and b'\n' not in req:
                        chunk = conn.recv(128)
                        if not chunk:
                            break
                        req.extend(chunk)
                    reply = boundary.dispatch(bytes(req)) if req.endswith(b'\n') and req.count(b'\n') == 1 else 'DENIED'
                    conn.sendall(reply.encode('ascii') + b'\n')
                except (OSError, TimeoutError, ConnectionError):
                    pass
    finally:
        server.close()
        try:
            if sockpath.is_socket() and not sockpath.is_symlink():
                sockpath.unlink()
        except OSError:
            pass


if __name__ == '__main__':
    main()
