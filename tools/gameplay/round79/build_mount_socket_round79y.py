#!/usr/bin/env python3
"""Adapt previously tested Round79P socket fixture for private mount commands.

Never write into the pinned repo, accepted source or a live world.
"""
from pathlib import Path
import argparse
import sys

OLD='SOURCE.parent.name.startswith("hd-army-game-round79rest-")'
NEW='SOURCE.parent.name.startswith("hd-army-game-round79commands-")'
HERE='HERE=Path(__file__).resolve().parent'
LOGIN='        prior["login"](player,"Hdnecroqa")\n'
RETURN='        ask(returning,"skills","Breath 94/100")\n'
IMPORT='from breath_socket_reconnect import require_saved_login_banner\n'
INTRO='''        # Read-only/default-denied native mount commands on a synthetic
        # player without a mount receipt. No awards or world stables.
        for query in ("mount list","mount status","mount 1",
                      "stable 1","retrieve 1","dismount"):
            ask(player,query,"No mounts registered")
        ask(player,"mount 0","Usage: mount")
        print("PASS: real native mount commands registered and no roster auto-created",
              flush=True)
'''
RECONNECT='''        ask(returning,"mount list","No mounts registered")
        print("PASS: no mount receipt created by read-only commands across reconnect",
              flush=True)
'''

def once(text,old,new,label):
    if text.count(old)!=1:
        raise ValueError('Prior verified socket harness changed: '+label)
    return text.replace(old,new,1)

def build(source_repo,target):
    repo=Path(source_repo)
    if not repo.is_dir() or repo.is_symlink():
        raise ValueError('Expected pinned source-only repository')
    prior=repo/'tools/gameplay/round79/check_breath_rest_socket.py'
    if not prior.is_file() or prior.is_symlink():
        raise ValueError('Verified Round79P socket script missing')
    out=Path(target)
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise ValueError('Socket harness target must be new')
    if not str(out.absolute()).startswith('/root/hollowdeep-dev/round79y-'):
        raise ValueError('Only Round79Y private results are allowed')
    text=prior.read_text(encoding='utf-8')
    text=once(text,OLD,NEW,'private accepted source prefix')
    directory=repo/'tools/gameplay/round79'
    inject=('sys.path.insert(0,'+repr(str(directory))+')\n'+IMPORT)
    text=once(text,IMPORT,inject,'local harness imports')
    text=once(text,HERE,'HERE=Path('+repr(str(directory))+')', 'pinned helpers')
    text=once(text,LOGIN,LOGIN+INTRO,'new character login')
    text=once(text,RETURN,RETURN+RECONNECT,'character reconnect')
    out.write_text(text,encoding='utf-8')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pinned_repository',type=Path)
    p.add_argument('new_socket_harness',type=Path)
    args=p.parse_args()
    try:
        generated=build(args.pinned_repository,args.new_socket_harness)
    except (ValueError,OSError) as e:
        print('ROUND79Y: SOCKET FIXTURE REFUSED:',e,file=sys.stderr)
        return 1
    print('ROUND79Y: PRIVATE SOCKET FIXTURE:',generated)
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0
if __name__=='__main__':
    sys.exit(main())
