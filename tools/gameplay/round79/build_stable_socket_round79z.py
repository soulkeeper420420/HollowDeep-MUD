#!/usr/bin/env python3
"""Round79Z: generate isolated real-socket stablecheck replay from pinned 79P.

All edits apply to a NEW private harness, never to the source repo.
"""
from pathlib import Path
import argparse
import sys

OLD='SOURCE.parent.name.startswith("hd-army-game-round79rest-")'
NEW='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
IMPORT='from breath_socket_reconnect import require_saved_login_banner\n'
HERE='HERE=Path(__file__).resolve().parent'
LOGIN='        prior["login"](player,"Hdnecroqa")\n'
NORTH='        ask(player,"north","Necromancer Trial Annex")\n'
RETURN='        ask(returning,"skills","Breath 94/100")\n'
CHROOT='prior["prepare_chroot"](exe,world)'

def once(body,old,new,label):
    if body.count(old)!=1:
        raise ValueError('Verified native socket anchor drift: '+label)
    return body.replace(old,new,1)

def build(repo,out):
    repo=Path(repo);out=Path(out)
    if not repo.is_dir() or repo.is_symlink():
        raise ValueError('Private pinned repo unavailable')
    path=repo/'tools/gameplay/round79/check_breath_rest_socket.py'
    if not path.is_file() or path.is_symlink():
        raise ValueError('Pinned Round79P fixture missing')
    if out.exists() or out.is_symlink() or not out.parent.is_dir() or \
       not str(out.absolute()).startswith('/root/hollowdeep-dev/round79z-'):
        raise ValueError('Only new private Round79Z socket output accepted')
    body=path.read_text(encoding='utf-8')
    body=once(body,OLD,NEW,'private ELF32 native source')
    directory=repo/'tools/gameplay/round79'
    body=once(body,IMPORT,
        'sys.path.insert(0,'+repr(str(directory))+')\n'+IMPORT,
        'pinned imports')
    body=once(body,HERE,'HERE=Path('+repr(str(directory))+')',
              'fixture helper location')
    setup='''# Only synthetic fixture world gets a root-owned stable registry.
# No source world or production room/stable files are accessed.
registry=world/"hollowdeep-data"/"mount-stables.hds"
registry.write_text("HDST1\\n2\\n10001\\n",encoding="ascii")
registry.chmod(0o644)
'''
    # prepare_chroot() makes *all* synthetic data folders/files belong to
    # the unprivileged listener. The stable authority policy intentionally
    # rejects that ownership. Restore root ownership only to the newly
    # created registry and its parent inside this disposable fixture,
    # after prepare_chroot() has completed its permission normalization.
    authority_after_chroot='''
# The existing fixture chroot helper intentionally chowns runtime data to
# UID 65534. Mount stable authority is an exception: ONLY the synthetic
# stable registry and its directory must be owned by root (and traversable).
if (world.parent != Path("/tmp") or
    not world.name.startswith("hd79p-rest-socket-") or
    registry.parent != world/"hollowdeep-data" or
    registry.is_symlink() or not registry.is_file() or
    registry.parent.is_symlink()):
    raise RuntimeError("Refusing unsafe synthetic stable-registry fixture")
os.chown(registry.parent,0,0)
registry.parent.chmod(0o755)
os.chown(registry,0,0)
registry.chmod(0o644)
if (registry.stat().st_uid != 0 or
    registry.parent.stat().st_uid != 0 or
    (registry.stat().st_mode & 0o022) or
    (registry.parent.stat().st_mode & 0o022)):
    raise RuntimeError("Private root-owned stable registry not established")
'''
    body=once(body,CHROOT,setup+CHROOT+authority_after_chroot,
              'root-owned synthetic stable registry after chroot setup')
    body=once(body,LOGIN,LOGIN+
        '        ask(player,"stablecheck","There is no registered stable")\n'
        '        print("PASS: native non-stable room is not certified",flush=True)\n',
        'non-stable room check')
    body=once(body,NORTH,NORTH+
        '        ask(player,"stablecheck","This room is a verified stable")\n'
        '        print("PASS: native real-room stablecheck validates root-owned registry",flush=True)\n',
        'verified native room check')
    body=once(body,RETURN,RETURN+
        '        ask(returning,"mount list","No mounts registered")\n'
        '        print("PASS: read-only stablecheck never creates a mount roster",flush=True)\n',
        'mount receipt reconnect unchanged')
    body+='\nprint("ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS",flush=True)\n'
    out.write_text(body,encoding='utf-8')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pinned_round79t_repo',type=Path)
    p.add_argument('new_private_socket_script',type=Path)
    args=p.parse_args()
    try:
        path=build(args.pinned_round79t_repo,args.new_private_socket_script)
    except (OSError,ValueError) as e:
        print('ROUND79Z: SOCKET HARNESS REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79Z: PRIVATE SOCKET HARNESS CREATED:',path)
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':sys.exit(main())
