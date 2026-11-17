from apply_deity_private import PROFILES, accepted_profile
assert len(PROFILES)==2
for i,p in enumerate(PROFILES): assert accepted_profile(p)==i
for a,b in ((0,1),(1,0)):
    assert accepted_profile({**PROFILES[a], 'global.c':PROFILES[b]['global.c']}) is None
    assert accepted_profile({**PROFILES[a], 'Makefile':PROFILES[b]['Makefile']}) is None
for f in PROFILES[1]: assert accepted_profile({**PROFILES[1],f:'0'*64}) is None
print('DEITY: coupled source profiles, mixed and drifted fingerprints refused PASS')
