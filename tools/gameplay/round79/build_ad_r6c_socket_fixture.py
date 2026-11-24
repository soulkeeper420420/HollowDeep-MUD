#!/usr/bin/env python3
"""Extend R5 test-only socket fixture with R6C real native lifecycle verbs."""
from pathlib import Path
import argparse

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('R5 fixture drift at '+old[:75])
    return text.replace(old,new,1)

def build(text):
    if 'HD79_AD_CREATURE_ACTION_PLAYTEST' in text or 'r6cboard' in text:
        raise ValueError('R6C socket fixture already transformed')
    text=once(text,'#include "hd79_ad_four_store.h"',
            '#include "hd79_ad_four_store.h"\n'
            '#include "hd79_ad_creature_action.h"\n'
            '#ifndef HD79_AD_CREATURE_ACTION_PLAYTEST\n'
            '#error "R6C fixture requires explicit private native lifecycle flag"\n'
            '#endif')
    extra='''    if(!strcmp(action,"r6cstatus")) {
        print(owner->fd,"R6C ACTION rev=%u active=%u room1=%u mask=%u serial=%u.\\n",
              r.revision,r.active_id,p.room[0],d.dead_mask,d.serial);
        return 0;
    }
    if(!strcmp(action,"r6ctune") && id==1) {
        creature *target=hd79_ad_native_bound_creature(owner,id,&r,&p);
        if(!target)goto denied;
        strcpy(target->key[0],"adtarget");
        target->hpcur=1;target->armor=0;owner->thaco=1;
        print(owner->fd,"R6C NATIVE TARGET PREPARED.\\n");
        return 0;
    }
    if(!strcmp(action,"r6cboard") || !strcmp(action,"r6cdismount")) {
        if(id!=1)goto denied;
        rc=hd79_ad_creature_action(owner,
              !strcmp(action,"r6cboard")?HD79_PRESENCE_BOARD:
                                          HD79_PRESENCE_DISMOUNT,id);
        if(rc==HD79_AD_CREATURE_COMPLETE)
            print(owner->fd,"R6C ACTION COMPLETE.\\n");
        else if(rc==HD79_AD_CREATURE_PENDING)
            print(owner->fd,"R6C ACTION PENDING.\\n");
        else print(owner->fd,"R6C ACTION DENIED.\\n");
        return 0;
    }
'''
    return once(text,'    if(!strcmp(action,"pending")) {',
                extra+'    if(!strcmp(action,"pending")) {')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('r5_test_fixture',type=Path)
    p.add_argument('new_private_fixture',type=Path)
    a=p.parse_args()
    if a.new_private_fixture.exists():raise ValueError('Fresh fixture required')
    output=build(a.r5_test_fixture.read_text())
    a.new_private_fixture.write_text(output)

if __name__=='__main__':main()
