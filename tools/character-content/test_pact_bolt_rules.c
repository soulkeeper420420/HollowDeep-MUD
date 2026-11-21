/* Round 78F: deterministic private Pact Bolt arithmetic unit tests. */
#include "hd_pact_bolt_rules.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static hd_pact_bolt_request base(void)
{
    hd_pact_bolt_request r;
    memset(&r,0,sizeof r);
    r.level=1;
    r.intelligence=16;
    r.mana=15;
    r.pact_charges=1;
    r.now=100;
    return r;
}

int main(void)
{
    hd_pact_bolt_request in=base();
    hd_pact_bolt_result out;
    int status;
    memset(&out,0,sizeof out);
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_OK);
    assert(out.damage==10 && out.mana_cost==6 &&
           out.charges_consumed==0 && out.seconds_remaining==0);

    in.empower=1;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_OK);
    assert(out.damage==20 && out.mana_cost==6 && out.charges_consumed==1);
    in.pact_charges=0;
    out.damage=777;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_NO_CHARGE);
    assert(out.damage==777);

    in.empower=0;
    in.mana=5;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_NO_MANA);
    assert(out.damage==777);
    in.mana=15;
    in.last_cast=99;
    status=hd_pact_bolt_check(&in,&out);
    assert(status==HD_PACT_BOLT_COOLDOWN && out.seconds_remaining==7);
    in.last_cast=105;
    status=hd_pact_bolt_check(&in,&out);
    assert(status==HD_PACT_BOLT_COOLDOWN && out.seconds_remaining==8);
    in.last_cast=92;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_OK);

    in.level=60;
    in.intelligence=35;
    in.pact_charges=3;
    in.empower=1;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_OK);
    assert(out.damage==92 && out.mana_cost==6 && out.charges_consumed==1);

    in.level=61;
    out.damage=999;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_INVALID);
    assert(out.damage==999);
    in.level=1;
    in.intelligence=36;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_INVALID);
    in.intelligence=16;
    in.empower=2;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_INVALID);
    in.empower=0;
    in.now=0;
    assert(hd_pact_bolt_check(&in,&out)==HD_PACT_BOLT_INVALID);
    assert(hd_pact_bolt_check(NULL,&out)==HD_PACT_BOLT_INVALID);
    assert(hd_pact_bolt_check(&in,NULL)==HD_PACT_BOLT_INVALID);

    puts("ROUND 78F: PRIVATE PACT BOLT RESOURCE/COOLDOWN RULES PASS");
    puts("Native targeting, class identity and combat damage: NOT YET INTEGRATED");
    return 0;
}
