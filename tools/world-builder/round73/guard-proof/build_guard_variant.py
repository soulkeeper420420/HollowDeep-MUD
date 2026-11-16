#!/usr/bin/env python3
"""Generate a *test-flagged* native guard from the exact Round 73D baseline.

This does not patch any game source tree. The existing private runner can
continue compiling the unchanged 73D file without the new feature.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('Usage: build_guard_variant.py ORIGINAL_TREASURE_GUARD.c OUTPUT.c')
source = Path(sys.argv[1]).read_bytes()
expected = 'b6cbf96854855d9079ca543a0b8689d21d4e523cc9b6db35089060aa55cfb598'
if hashlib.sha256(source).hexdigest() != expected:
    raise SystemExit('Source changed: refusing non-audited guard source')
s = source.decode('ascii')

def replace_once(a,b):
    global s
    if s.count(a) != 1:
        raise SystemExit('Unexpected guard source for patch: ' + repr(a[:80]))
    s=s.replace(a,b,1)

replace_once('#include "mstruct.h"',
'''#include "mstruct.h"
#ifdef HD_GUARD_EVIDENCE_TEST
#include "hd_guard_proof.h"
#define HD_GPROOF_DIR "hollowdeep-data/treasure-proof"
#endif''')
replace_once('    unsigned char dead[HD_MAX_GUARDS];\n};',
'''    unsigned char dead[HD_MAX_GUARDS];
#ifdef HD_GUARD_EVIDENCE_TEST
    hd_guard_proof proof;
#endif
};''')
replace_once('    int i, count, j;\n    for (i = 0; i < site->n; ++i) {',
'''    int i, count, j;
#ifdef HD_GUARD_EVIDENCE_TEST
    hd_guard_proof proof;
    if (hd_guard_proof_begin(HD_GPROOF_DIR, (unsigned)site->room, site->map,
                             player->name, (const char (*)[80])site->name,
                             (unsigned)site->n, &proof) != HD_GPROOF_OK)
        return NULL; /* Persisted witness missing/corrupt/uncertain: fail closed. */
#endif
    for (i = 0; i < site->n; ++i) {''')
replace_once('''        matches[i] = NULL;
        for (tag = player->parent_rom->first_mon; tag; tag = tag->next_tag) {''',
'''        matches[i] = NULL;
#ifdef HD_GUARD_EVIDENCE_TEST
        if (proof.dead[i]) continue; /* Proven dead in this exact challenge. */
#endif
        for (tag = player->parent_rom->first_mon; tag; tag = tag->next_tag) {''')
replace_once('''        for (j = 0; j < i; ++j) if (matches[j] == matches[i]) return NULL;''',
'''        for (j = 0; j < i; ++j)
            if (matches[i] && matches[j] == matches[i]) return NULL;''')
replace_once('''    strcpy(slot->owner, player->name);
    for (i = 0; i < site->n; ++i) slot->guardian[i] = matches[i];''',
'''    strcpy(slot->owner, player->name);
#ifdef HD_GUARD_EVIDENCE_TEST
    slot->proof=proof;
#endif
    for (i = 0; i < site->n; ++i) {
        slot->guardian[i] = matches[i];
#ifdef HD_GUARD_EVIDENCE_TEST
        slot->dead[i] = proof.dead[i];
#endif
    }''')
replace_once('''            hd_chests[i].dead[j] = (killer && killer->type == PLAYER &&
                !strcmp(hd_chests[i].owner, killer->name) &&
                victim->rom_num == hd_chests[i].room && killer->rom_num == hd_chests[i].room);''',
'''            {
                int correct_owner=(killer && killer->type == PLAYER &&
                    !strcmp(hd_chests[i].owner, killer->name) &&
                    victim->rom_num == hd_chests[i].room &&
                    killer->rom_num == hd_chests[i].room);
#ifdef HD_GUARD_EVIDENCE_TEST
                if (correct_owner) {
                    int rc=hd_guard_proof_mark(HD_GPROOF_DIR,
                                               &hd_chests[i].proof,(unsigned)j);
                    hd_chests[i].dead[j]=(rc==HD_GPROOF_OK || rc==HD_GPROOF_ALREADY);
                } else hd_chests[i].dead[j]=0;
#else
                hd_chests[i].dead[j]=correct_owner;
#endif
            }''')
s += '''\n#ifdef HD_GUARD_EVIDENCE_TEST
/* Harness only: simulate a game restart without killing the test process. */
void hd_guard_evidence_test_restart(void) {
    memset(hd_chests,0,sizeof hd_chests);
}
#endif
'''
Path(sys.argv[2]).write_text(s)
print('ROUND 73H: test-gated guardian proof variant generated')
