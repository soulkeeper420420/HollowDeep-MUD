#!/usr/bin/env python3
"""Patch the exact Round 73H generated C guard for TEST-ONLY ledger calls.

Never patch original source or publish a production/native deploy script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('Usage: build_ledger_variant.py ROUND73H_GENERATED_GUARD.c OUTPUT.c')
source = Path(sys.argv[1]).read_bytes()
expected = 'd516960c2a70e32015eb8e43dee9c3c7aa8993687a8d8757ed5ab27e2f52269c'
if hashlib.sha256(source).hexdigest() != expected:
    raise SystemExit('Source drift from verified Round 73H generated baseline')
s = source.decode('ascii')

def once(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit('Refusing changed/ambiguous guard patch anchor: ' + repr(old[:80]))
    s = s.replace(old, new, 1)

once('#define HD_GPROOF_DIR "hollowdeep-data/treasure-proof"', '''#define HD_GPROOF_DIR "hollowdeep-data/treasure-proof"
#ifdef HD_LEDGER_BRIDGE_TEST
#include "hd_ledger_bridge.h"
#include <stdlib.h>
#ifndef HD_LEDGER_TRUSTED_UID
#error "Test-only bridge requires explicit trusted service UID"
#endif
static const char *hd_bridge_test_socket(void) {
    /* PRIVATE-TEST ONLY. Never turn this env-selected socket into production auth. */
    const char *value=getenv("HD_LEDGER_BRIDGE_TEST_SOCKET");
    return value && value[0] ? value : NULL;
}
#endif''')
once('''        return NULL; /* Persisted witness missing/corrupt/uncertain: fail closed. */
#endif''', '''        return NULL; /* Persisted witness missing/corrupt/uncertain: fail closed. */
#ifdef HD_LEDGER_BRIDGE_TEST
    if (hd_ledger_begin(hd_bridge_test_socket(),HD_LEDGER_TRUSTED_UID,
                        &proof) != HD_LEDGER_OK)
        return NULL; /* Native game is NOT ledger authority. */
#endif
#endif''')
once('''                    hd_chests[i].dead[j]=(rc==HD_GPROOF_OK || rc==HD_GPROOF_ALREADY);
''', '''                    hd_chests[i].dead[j]=(rc==HD_GPROOF_OK || rc==HD_GPROOF_ALREADY);
#ifdef HD_LEDGER_BRIDGE_TEST
                    if (rc==HD_GPROOF_OK && hd_ledger_kill(
                            hd_bridge_test_socket(),HD_LEDGER_TRUSTED_UID,
                            &hd_chests[i].proof,(unsigned)j) < 0)
                        hd_chests[i].dead[j]=0;
#endif
''')
once('''    print(player->fd, "The guardian seals dissolve. The chest opens, but reward delivery is disabled in this test build.\\n");''', '''#ifdef HD_LEDGER_BRIDGE_TEST
    if (hd_ledger_claim(hd_bridge_test_socket(),HD_LEDGER_TRUSTED_UID,
                        &state->proof) != HD_LEDGER_PENDING) {
        print(player->fd, "The seals dissolve, but the trusted ledger has not approved this chest.\\n");
        return 0;
    }
#endif
    print(player->fd, "The guardian seals dissolve. The chest opens, but reward delivery is disabled in this test build.\\n");''')
Path(sys.argv[2]).write_text(s, encoding='ascii')
print('ROUND 73I: test-gated exact-PID guardian/SQLite guard variant generated')
