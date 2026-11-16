#define _GNU_SOURCE
#include "hd_guard_proof.h"
#include "hd_ledger_bridge.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc,char **argv) {
    char names[HD_GPROOF_MAX][80]={{"Native Guardian"}};
    hd_guard_proof proof,bad;
    const char *sock;
    if(argc!=2 || chdir(argv[1])) return 2;
    sock=getenv("HD_LEDGER_BRIDGE_TEST_SOCKET");
    assert(sock);
    assert(hd_guard_proof_begin("hollowdeep-data/treasure-proof",10001,
                                "map.0001","Nativeqa",(const char (*)[80])names,1,&proof)==0);
    assert(hd_guard_proof_ready(&proof));
    if(getenv("HD_LEDGER_EXPECT_DOWN")) {
        assert(hd_ledger_begin(sock,HD_LEDGER_TRUSTED_UID,&proof)==HD_LEDGER_DENIED);
        assert(hd_ledger_claim(sock,HD_LEDGER_TRUSTED_UID,&proof)==HD_LEDGER_DENIED);
        puts("ROUND 73I: daemon outage refuses native authorization PASS");
        return 0;
    }
    assert(hd_ledger_begin(sock,HD_LEDGER_TRUSTED_UID,&proof)==HD_LEDGER_OK);
    assert(hd_ledger_kill(sock,HD_LEDGER_TRUSTED_UID,&proof,0)==HD_LEDGER_READY);
    assert(hd_ledger_claim(sock,HD_LEDGER_TRUSTED_UID,&proof)==HD_LEDGER_PENDING);
    bad=proof;strcpy(bad.owner,"Anotherqa");
    assert(hd_ledger_claim(sock,HD_LEDGER_TRUSTED_UID,&bad)==HD_LEDGER_DENIED);
    bad=proof;bad.event_ids[0][0]=(bad.event_ids[0][0]=='a'?'b':'a');
    assert(hd_ledger_kill(sock,HD_LEDGER_TRUSTED_UID,&bad,0)==HD_LEDGER_DENIED);
    assert(hd_ledger_claim(sock,HD_LEDGER_TRUSTED_UID,&proof)==HD_LEDGER_PENDING);
    puts("ROUND 73I: trusted daemon restart + same claim replay + conflicting kill denial PASS");
    return 0;
}
