#!/usr/bin/env python3
"""Build R6B private socket action-CAS replay from verified R5 death replay.

Requires exact anchor text and preserves all prior six native combat tests.
"""
import argparse
from pathlib import Path


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('R5 socket anchor drift: '+old[:90])
    return text.replace(old,new,1)


def build(text):
    text=once(text,
        'SOURCE.parent.name.startswith("hd-army-game-round79addeath-")',
        'SOURCE.parent.name.startswith("hd-army-game-round79adcas-")')
    anchor='''            if mount_id==1:
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")'''
    test='''            if mount_id==1:
                ask(returning,"adfixture actionstatus",
                    "R6B ACTION rev=7 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")
                ask(returning,"adfixture board 1","R6B ACTION DENIED")
                ask(returning,"adfixture actionstatus",
                    "R6B ACTION rev=7 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
                print("PASS: failed native action rename leaves all four receipts intact",flush=True)
                ask(returning,"adfixture board 1","R6B ACTION COMMITTED")
                ask(returning,"adfixture actionstatus",
                    "R6B ACTION rev=8 active=1 room1=0 mask=0 serial=7.")
                ask(returning,"adfixture board 1","R6B ACTION DENIED")
                ask(returning,"adfixture failafter","AD FIXTURE FAULT ARMED")
                ask(returning,"adfixture dismount 1","R6B ACTION UNCERTAIN")
                ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
                ask(returning,"adfixture actionstatus",
                    "R6B ACTION rev=9 active=0 room1=2 mask=0 serial=7.")
                ask(returning,"adfixture dismount 1","R6B ACTION DENIED")
                print("PASS: native R6B action CAS board/dismount, uncertain rename, "
                      "no repeat or death receipt drift",flush=True)
                # Continue the R5 native combat fault/replay checks unmodified.
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")'''
    text=once(text,anchor,test)
    return text+'\nprint("ROUND79AD R6B: PRIVATE NATIVE ATOMIC BOARD/DISMOUNT CAS SOCKET PASS",flush=True)\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_r5_socket',type=Path)
    parser.add_argument('private_output',type=Path)
    args=parser.parse_args()
    if args.private_output.exists():raise ValueError('Fresh private socket replay required')
    args.private_output.write_text(build(args.accepted_r5_socket.read_text()),
                                   encoding='utf-8')

if __name__=='__main__':main()
