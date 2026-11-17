#!/usr/bin/env python3
"""Guard regression: only exact coupled Necromancer source profiles may patch."""
import hashlib
import importlib.util
from pathlib import Path

p=Path(__file__).with_name('apply_permanent_private.py')
spec=importlib.util.spec_from_file_location('necromancer_private_profiles',str(p))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

baseline=module.BASE_SHA256
integrated=module.ROUND74B_INTEGRATED_SHA256

def classify(creature_sha,command_sha):
    return module.accepted_source_profile({
        'creature.c':creature_sha,
        'command1.c':command_sha,
    })

assert classify(baseline['creature.c'],baseline['command1.c'])=='first-skill-only'
assert classify(integrated['creature.c'],integrated['command1.c'])=='round74b-integrated'
assert classify(integrated['creature.c'],baseline['command1.c']) is None
assert classify(baseline['creature.c'],integrated['command1.c']) is None
assert classify('0'*64,integrated['command1.c']) is None
assert classify(integrated['creature.c'],'0'*64) is None
assert classify(baseline['creature.c'][:-1]+'0',baseline['command1.c']) is None
print('NECROMANCER: coupled Round74B creature/creation SHA allowlist; mixed and drifted profiles refused PASS')
