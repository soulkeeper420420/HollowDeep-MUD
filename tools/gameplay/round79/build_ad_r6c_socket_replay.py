#!/usr/bin/env python3
"""One private R6C board/dismount socket test + all six R5 real combat deaths."""
from pathlib import Path
import argparse

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('R5 socket anchor drift: '+old[:80])
    return text.replace(old,new,1)

def build(text):
    text=once(text,
        'SOURCE.parent.name.startswith("hd-army-game-round79addeath-")',
        'SOURCE.parent.name.startswith("hd-army-game-round79adcreature-")')
    anchor='''            if mount_id==1:
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")'''
    extra='''            if mount_id==1:
                ask(returning,"adfixture r6cstatus",
                    "R6C ACTION rev=7 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")
                ask(returning,"adfixture r6cboard 1","R6C ACTION PENDING")
                ask(returning,"adfixture r6cstatus",
                    "R6C ACTION rev=7 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
                ask(returning,"adfixture failafter","AD FIXTURE FAULT ARMED")
                ask(returning,"adfixture r6cboard 1","R6C ACTION COMPLETE")
                ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
                ask(returning,"adfixture r6cstatus",
                    "R6C ACTION rev=8 active=1 room1=0 mask=0 serial=7.")
                ask(returning,"adfixture r6cboard 1","R6C ACTION DENIED")
                ask(returning,"adfixture r6cdismount 1","R6C ACTION COMPLETE")
                ask(returning,"adfixture r6cstatus",
                    "R6C ACTION rev=9 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture r6ctune 1","R6C NATIVE TARGET PREPARED")
                ask(returning,"adfixture spawn 1","AD FIXTURE DENIED")
                print("PASS: native R6C creature removed on atomic board; "
                      "dismount exactly one, rename reconciliation, no duplication",flush=True)
                # R5 genuine combat death fault and permanent tombstone replay.
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")'''
    text=once(text,anchor,extra)
    return text+'\nprint("ROUND79AD R6C: PRIVATE NATIVE PHYSICAL BOARD/DISMOUNT SOCKET PASS",flush=True)\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('r5_socket_replay',type=Path)
    p.add_argument('fresh_private_replay',type=Path)
    a=p.parse_args()
    if a.fresh_private_replay.exists():raise ValueError('Fresh replay required')
    a.fresh_private_replay.write_text(build(a.r5_socket_replay.read_text()))

if __name__=='__main__':main()
