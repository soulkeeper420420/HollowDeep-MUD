#!/usr/bin/env python3
"""Extend the accepted private socket replay with genuine native combat deaths.

The output remains private. The synthetic grant command is compiled only by
the explicit test build; the normal ELF32 candidate never contains it.
"""
import argparse
from pathlib import Path


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Accepted socket anchor drift: ' + old[:70])
    return text.replace(old, new, 1)


def build(text):
    text = once(text,
        'SOURCE.parent.name.startswith("hd-army-game-round79stable-")',
        'SOURCE.parent.name.startswith("hd-army-game-round79addeath-")')
    anchor = '        prior["quit_with_cooldown"](returning,process)'
    extra = '''        ask(returning,"adfixture seed","AD FIXTURE SEEDED")
        ask(returning,"adfixture status","mask=0 serial=7 count=6")
        for mount_id in range(1,7):
            ask(returning,"adfixture spawn %d"%mount_id,"AD FIXTURE SPAWNED")
            ask(returning,"adfixture spawn %d"%mount_id,"AD FIXTURE DENIED")
            if mount_id==1:
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")
                failed=""
                for attempt in range(20):
                    failed+=prior["command"](returning,"attack adtarget")
                    if "Mount death save pending" in failed:
                        break
                    time.sleep(2)
                assert "Mount death save pending" in failed
                assert "You gained" not in failed and "A corpse remains" not in failed
                ask(returning,"adfixture status","mask=0 serial=7 count=6")
                ask(returning,"adfixture pending","pending=1")
                ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
                print("PASS: failed native death save retains exact dead entity "
                      "before rewards, unlink and free",flush=True)
            if mount_id==2:
                ask(returning,"adfixture failafter","AD FIXTURE FAULT ARMED")
            transcript=""
            for attempt in range(20):
                transcript+=prior["command"](returning,"attack adtarget")
                if "You killed" in transcript:
                    break
                time.sleep(2)
            assert "You killed" in transcript, "No explicit native mount death"
            ask(returning,"adfixture clear","AD FIXTURE FAULT CLEARED")
            mask=(1<<mount_id)-1
            ask(returning,"adfixture status",
                "mask=%d serial=%d count=6"%(mask,7+mount_id))
            ask(returning,"adfixture spawn %d"%mount_id,"AD FIXTURE DENIED")
            ask(returning,"adfixture pending","pending=0")
            print("PASS: native combat killed species %d; durable death before "
                  "release; duplicate and dead spawn denied"%mount_id,flush=True)
'''
    text = once(text, anchor, extra + anchor)
    restart = '''    # Restart only this disposable native process and reuse its synthetic save.
    process.terminate()
    process.wait(timeout=10)
    # Native reuse-address is opt-in; use a fresh private port after restart.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1",0))
        port=reservation.getsockname()[1]
    with log.open("ab") as out:
        process=subprocess.Popen([
            chroot,"--userspec=65534:65534","--groups=65534",
            str(world),"/bin/hollowdeep",str(port)
        ],cwd=world,
          env={"PATH":"/usr/bin:/bin","HOLLOWDEEP_BIND":"127.0.0.1"},
          stdout=out,stderr=subprocess.STDOUT)
    with prior["connect_game"](port,process) as restarted:
        prior["recv_until"](restarted,b"Please enter name:")
        prior["send"](restarted,"Hdnecroqa")
        prior["recv_until"](restarted,b"Please enter password:")
        prior["send"](restarted,"Fixturepass")
        prior["recv_until"](restarted,b"Breath",seconds=15)
        ask(restarted,"adfixture status","mask=63 serial=13 count=6")
        for mount_id in range(1,7):
            ask(restarted,"adfixture spawn %d"%mount_id,"AD FIXTURE DENIED")
        prior["quit_with_cooldown"](restarted,process)
    print("PASS: six permanent tombstones survive native save/logout and "
          "process restart; no dead species can respawn",flush=True)
'''
    text = once(text, 'finally:\n    if process is not None',
                restart + 'finally:\n    if process is not None')
    # Existing output is retained, so callers must require this additional gate.
    return text + '\nprint("ROUND79AD: SIX REAL NATIVE COMBAT DEATHS PASS",flush=True)\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_replay', type=Path)
    parser.add_argument('private_output', type=Path)
    args = parser.parse_args()
    if args.private_output.exists():
        raise ValueError('Fresh private output required')
    args.private_output.write_text(build(args.accepted_replay.read_text()),
                                   encoding='utf-8')


if __name__ == '__main__':
    main()
