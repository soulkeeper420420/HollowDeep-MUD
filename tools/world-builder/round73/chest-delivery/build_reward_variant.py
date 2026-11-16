#!/usr/bin/env python3
"""Exact-hash gated test-only amendment to generated 73I treasure guard."""
import hashlib
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit('Usage: build_reward_variant.py GENERATED_73I.c OUTPUT.c')
data = Path(sys.argv[1]).read_bytes()
if hashlib.sha256(data).hexdigest() != '44f7c3b70cf8b3aa1706d8185dfd002b338806944ef1addf701a185a57fb6d1d':
    raise SystemExit('Refusing source drift in previously tested 73I guard')
s = data.decode('ascii')
old = '''#ifdef HD_LEDGER_BRIDGE_TEST
    if (hd_ledger_claim(hd_bridge_test_socket(),HD_LEDGER_TRUSTED_UID,
                        &state->proof) != HD_LEDGER_PENDING) {
        print(player->fd, "The seals dissolve, but the trusted ledger has not approved this chest.\\n");
        return 0;
    }
#endif
    print(player->fd, "The guardian seals dissolve. The chest opens, but reward delivery is disabled in this test build.\\n");'''
new = '''#ifdef HD_J_REWARD_TEST
    {
        extern int hd_claim_test_deliver(creature *, const hd_guard_proof *);
        int r=hd_claim_test_deliver(player,&state->proof);
        if (r==0) print(player->fd, "The chest yields a securely saved treasure reward.\\n");
        else if (r==1) print(player->fd, "You have already claimed this treasure.\\n");
        else if (r==2) print(player->fd, "Reward saved; ledger acknowledgment pending.\\n");
        else if (r==-2) print(player->fd, "Treasure save uncertain; reconnect required.\\n");
        else print(player->fd, "The trusted ledger has denied this reward.\\n");
    }
#else
#ifdef HD_LEDGER_BRIDGE_TEST
    if (hd_ledger_claim(hd_bridge_test_socket(),HD_LEDGER_TRUSTED_UID,
                        &state->proof) != HD_LEDGER_PENDING) {
        print(player->fd, "The seals dissolve, but the trusted ledger has not approved this chest.\\n");
        return 0;
    }
#endif
    print(player->fd, "The guardian seals dissolve. The chest opens, but reward delivery is disabled in this test build.\\n");
#endif'''
if s.count(old) != 1:
    raise SystemExit('Refusing unmatched disabled reward anchor')
s=s.replace(old,new)
Path(sys.argv[2]).write_text(s,encoding='ascii')
print('ROUND 73J: private-only reward-to-chest variant generated')
