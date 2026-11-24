#!/usr/bin/env python3
"""Generate disposable R6B action CAS socket fixture from accepted R5 test source.

Only test builds may compile this generated fixture. Never register it in a
normal candidate or production global command table.
"""
import argparse
from pathlib import Path


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('R5 fixture anchor drift: '+old[:70])
    return text.replace(old,new,1)


def build(text):
    text=once(text,'#include "hd79_ad_four_store.h"',
        '#include "hd79_ad_four_store.h"\n'
        '#include "hd79_ad_four_action_store.h"\n'
        '#ifndef HD79_AD_ACTION_CAS_PLAYTEST\n'
        '#error "R6B socket fixture requires private action-CAS flag"\n'
        '#endif')
    extra='''    if(!strcmp(action,"actionstatus")) {
        print(owner->fd,"R6B ACTION rev=%u active=%u room1=%u mask=%u serial=%u.\\n",
              r.revision,r.active_id,p.room[0],d.dead_mask,d.serial);
        return 0;
    }
    if((!strcmp(action,"board") || !strcmp(action,"dismount")) && id==1) {
        rc=hd79_ad_four_action_commit_native(owner,
              !strcmp(action,"board") ? HD79_PRESENCE_BOARD:
                                           HD79_PRESENCE_DISMOUNT,
              id,&nr,&np,&nd);
        if(rc==HD79_AD_FOUR_OK)
            print(owner->fd,"R6B ACTION COMMITTED.\\n");
        else if(rc==HD79_AD_FOUR_UNCERTAIN)
            print(owner->fd,"R6B ACTION UNCERTAIN.\\n");
        else
            print(owner->fd,"R6B ACTION DENIED.\\n");
        return 0;
    }
'''
    return once(text,'    if(!strcmp(action,"pending")) {',
                extra+'    if(!strcmp(action,"pending")) {')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_fixture',type=Path)
    parser.add_argument('private_output',type=Path)
    args=parser.parse_args()
    if args.private_output.exists():raise ValueError('Fresh private C fixture required')
    args.private_output.write_text(build(args.accepted_fixture.read_text()),
                                   encoding='utf-8')

if __name__=='__main__':main()
