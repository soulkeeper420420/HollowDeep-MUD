#!/usr/bin/env python3
"""Round11U private transaction-preserving rollback snapshot / verification.

Use ONLY in /root/hollowdeep-dev/guild-social-batch1/round11u-rollback-*/rootfs
with synthetic Hd[a-z0-9]+ saves. Never run on live player records.

Actions:
  snapshot           archive committed ledger and disposable saved players
  verify-archive     verify all archive bytes, recorded digests and paths
  verify-ledger      verify active private ledger == archived committed ledger
  record-relocated   record hashes after offline native occupant relocation
  verify-relocated   verify relocated private saves have not changed
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

BASE=Path("/root/hollowdeep-dev/guild-social-batch1")
VALID_NAME=re.compile(r"Hd[a-z0-9]{3,17}\Z")
MAX_PLAYER=8*1024*1024
MAX_LEDGER=64*1024
ACTIONS={"snapshot","verify-archive","verify-ledger",
         "record-relocated","verify-relocated"}

if len(sys.argv)!=3 or sys.argv[1] not in ACTIONS:
    raise SystemExit("Usage: rollback_archive.py ACTION PRIVATE_ROOTFS")
action=sys.argv[1]
root=Path(sys.argv[2]).resolve(strict=True)
stage=root.parent
if (root.name!="rootfs" or stage.parent!=BASE or
        not stage.name.startswith("round11u-rollback-")):
    raise SystemExit("STOP: not a disposable Round11U rollback stage")
players=root/"player"
data=root/"hollowdeep-data"
archive=stage/"archive"
ledger=data/"player-guilds.v1"
before=archive/"before.json"
after=archive/"relocated.json"

def ensure_file(p,maxsize):
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size<=0 or info.st_size>maxsize:
        raise RuntimeError("STOP: unexpected file kind, count or size: "+p.name)
    return p.read_bytes()

def digest(buf):
    return hashlib.sha256(buf).hexdigest()

def write_unique(path,buf):
    if path.exists() or path.is_symlink():
        raise RuntimeError("STOP: archive path already exists: "+path.name)
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,"wb",closefd=False) as f:
            f.write(buf)
            f.flush()
        os.fsync(fd)
    finally:
        os.close(fd)

def sync_dir(path):
    fd=os.open(str(path),os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def parse_files():
    if not players.is_dir() or not data.is_dir():
        raise RuntimeError("STOP: private player or guild data directory missing")
    result={}
    for p in sorted(players.iterdir()):
        if not VALID_NAME.fullmatch(p.name):
            raise RuntimeError("STOP: non-disposable player filename: "+p.name)
        result[p.name]=ensure_file(p,MAX_PLAYER)
    return result

def recorded():
    if archive.is_symlink() or not archive.is_dir():
        raise RuntimeError("STOP: private archive missing")
    b=ensure_file(before,MAX_LEDGER)
    obj=json.loads(b)
    if obj.get("version")!=1 or "ledger" not in obj or "players" not in obj:
        raise RuntimeError("STOP: invalid private archive manifest")
    for name in obj["players"]:
        if not VALID_NAME.fullmatch(name):
            raise RuntimeError("STOP: invalid saved-character filename in manifest")
    return obj

def verify_archive():
    obj=recorded()
    original_ledger=ensure_file(archive/"ledger",MAX_LEDGER)
    if digest(original_ledger)!=obj["ledger"]["sha256"] or len(original_ledger)!=obj["ledger"]["size"]:
        raise RuntimeError("STOP: committed ledger archive hash mismatch")
    for name,meta in obj["players"].items():
        blob=ensure_file(archive/"players"/name,MAX_PLAYER)
        if digest(blob)!=meta["sha256"] or len(blob)!=meta["size"]:
            raise RuntimeError("STOP: archived player bytes differ: "+name)
    return obj,original_ledger

if action=="snapshot":
    if archive.exists() or archive.is_symlink():
        raise SystemExit("STOP: existing snapshot archive; refuse overwrite")
    if not ledger.exists() or ledger.is_symlink():
        raise SystemExit("STOP: committed guild ledger missing")
    led=ensure_file(ledger,MAX_LEDGER)
    if not led.startswith(b"HDGUILD2\n"):
        raise SystemExit("STOP: guild ledger version invalid")
    saved=parse_files()
    if not saved:
        raise SystemExit("STOP: no disposable saved characters to protect")
    archive.mkdir(mode=0o700)
    (archive/"players").mkdir(mode=0o700)
    write_unique(archive/"ledger",led)
    info={"version":1,
          "ledger":{"sha256":digest(led),"size":len(led)},
          "players":{}}
    for name,blob in saved.items():
        write_unique(archive/"players"/name,blob)
        info["players"][name]={"sha256":digest(blob),"size":len(blob)}
    write_unique(before,json.dumps(info,sort_keys=True,indent=2).encode("utf-8"))
    sync_dir(archive/"players")
    sync_dir(archive)
    sync_dir(stage)
    print("PASS: committed private ledger and",len(saved),"disposable native saves archived durably")
elif action=="verify-archive":
    obj,_=verify_archive()
    print("PASS: original ledger and",len(obj["players"]),"private saved files match archive SHA-256")
elif action=="verify-ledger":
    obj,original=verify_archive()
    current=ensure_file(ledger,MAX_LEDGER)
    if current!=original:
        raise SystemExit("STOP: post-activation committed ledger changed or missing")
    print("PASS: committed private ledger preserved byte-for-byte")
elif action=="record-relocated":
    obj,_=verify_archive()
    if after.exists() or after.is_symlink():
        raise SystemExit("STOP: relocated save manifest already exists")
    saved=parse_files()
    if set(saved)!=set(obj["players"]):
        raise SystemExit("STOP: unexpected character added/lost before rollback")
    info={"version":1,"players":{name:{"sha256":digest(blob),"size":len(blob)}
                                 for name,blob in saved.items()}}
    write_unique(after,json.dumps(info,sort_keys=True,indent=2).encode("utf-8"))
    sync_dir(archive)
    print("PASS: post-relocation",len(saved),"private native character hashes recorded")
elif action=="verify-relocated":
    obj,_=verify_archive()
    info=json.loads(ensure_file(after,MAX_LEDGER))
    saved=parse_files()
    if set(saved)!=set(obj["players"]) or set(saved)!=set(info["players"]):
        raise SystemExit("STOP: unexpected private character files after rollback")
    for name,blob in saved.items():
        expected=info["players"][name]
        if expected["sha256"]!=digest(blob) or expected["size"]!=len(blob):
            raise SystemExit("STOP: relocated save changed unexpectedly: "+name)
    print("PASS: all relocated private character saves remain byte-identical")
else:
    raise AssertionError(action)
print("Original player secrets and live account files: NOT ACCESSED")
