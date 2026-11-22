"""Round79Q: real connected ELF32 socket +15 resting tick replay.

Runs *inside* the prior Round79P disposable network namespace and chroot
socket fixture. No clock injection, game source mutation, player-file
writing, production socket access, or fake native recovery calls.
The fixture is deliberately depleted below 80 Breath through actual
native wilderness movement. Polling skills then measures discrete
Breath recovery *events*, not merely a capped final value.
"""
import re
import time

BREATH=re.compile(r"\bBreath\s+(\d{1,3})/100\b",re.I)
TARGET=76
MAX_MOVES=64
MAX_PULSE_WAIT=125

def parse_breath(data):
    if not isinstance(data,str):
        raise ValueError("Native text output must be a string")
    all_values=[int(m.group(1)) for m in BREATH.finditer(data)]
    if not all_values:
        raise AssertionError("Native numeric Breath HUD missing: "+repr(data[-350:]))
    value=all_values[-1]
    if value<0 or value>100:
        raise AssertionError("Invalid numeric Breath HUD "+repr(value))
    return value

def check_pulse_transition(previous,current):
    if not (0<=previous<=100 and 0<=current<=100):
        raise AssertionError("Out-of-range Breath recovery event")
    if current==previous:
        return "unchanged"
    delta=current-previous
    # At least 15 points of room are required for *unclipped* +15.
    # This prevents false positives caused by two +5 pulses over time
    # or a capped recovery at 100.
    if delta==15 and previous<=85:
        return "rest_plus15"
    if delta==5:
        return "normal_plus5"
    raise AssertionError(
        "Unexpected live Breath delta %d (%d -> %d)"%
        (delta,previous,current))

def run(player,prior,ask,clean):
    def sample():
        response=prior["command"](player,"skills")
        return parse_breath(clean(response))

    print("=== ROUND79Q: CONNECTED SOCKET NATURAL BREATH RECOVERY ===",
          flush=True)
    initial=sample()
    if initial!=94:
        raise AssertionError(
            "Expected saved Round79P Annex Breath 94, got %d"%initial)

    # First spend Breath by *real* native movements, while the
    # source area and rooms remain synthetic and network-isolated.
    ask(player,"east","Test Wilderness Meadow")
    location="meadow"
    value=sample()
    moves=1
    while value>TARGET:
        if moves>=MAX_MOVES:
            raise AssertionError(
                "Could not deplete native Breath below %d in %d moves; "
                "last value %d"%(TARGET,moves,value))
        if location=="meadow":
            ask(player,"north","Test Wilderness Ridge")
            location="ridge"
        else:
            ask(player,"south","Test Wilderness Meadow")
            location="meadow"
        value=sample()
        moves+=1
    if location=="ridge":
        ask(player,"south","Test Wilderness Meadow")
        location="meadow"
    ask(player,"go west","Necromancer Trial Annex")

    before=sample()
    if before>80 or before<0:
        raise AssertionError("Insufficient native recovery headroom: %d"%before)
    print("PASS: depleted real native Breath to %d/100 in %d wilderness "
          "moves (interior retreat free)"%(before,moves),flush=True)

    ask(player,"rest","You settle down to rest.")
    baseline=sample()
    if baseline>80:
        raise AssertionError("Breath recovered too early before rest timer: "
                             "%d"%baseline)
    print("PASS: explicit native rest entered; Breath=%d/100"%baseline,
          flush=True)

    started=time.monotonic()
    current=baseline
    ticks=[]
    while time.monotonic()-started<MAX_PULSE_WAIT:
        time.sleep(3)
        observed=sample()
        outcome=check_pulse_transition(current,observed)
        if outcome=="unchanged":
            continue
        ticks.append((outcome,observed))
        print("Observed natural native timer recovery: %s %d -> %d"%
              (outcome,current,observed),flush=True)
        if outcome=="rest_plus15":
            # Read-only commands must not produce extra awards before
            # the next durable 45-second recovery gate.
            immediately=sample()
            if immediately!=observed:
                raise AssertionError(
                    "Duplicate/early native recovery after +15: %d -> %d"%
                    (observed,immediately))
            print("PASS: real connected 45-second rest tick grants "
                  "exactly +15 with no immediate duplicate",flush=True)
            print("ROUND79Q: REAL SOCKET REST +15 TIMER PASS",flush=True)
            return
        current=observed
    raise AssertionError(
        "No genuine +15 native rest pulse during %d-second socket window; "
        "observed events=%r. Check if update_ply() runs for idle "
        "connected players (not only login/logout)."%
        (MAX_PULSE_WAIT,ticks))
