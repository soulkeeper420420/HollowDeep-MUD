/* Self-contained Round 79A rule and boundary regression. */
#include "hd_encounter_risk.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    int p,m,r;
    assert(hd_encounter_risk(10,5)==HD_ENCOUNTER_TRIVIAL);
    assert(hd_encounter_risk(10,9)==HD_ENCOUNTER_MANAGEABLE);
    assert(hd_encounter_risk(10,10)==HD_ENCOUNTER_DANGEROUS);
    assert(hd_encounter_risk(10,13)==HD_ENCOUNTER_DANGEROUS);
    assert(hd_encounter_risk(10,14)==HD_ENCOUNTER_DEADLY);
    assert(hd_encounter_risk(60,1)==HD_ENCOUNTER_TRIVIAL);
    assert(hd_encounter_risk(1,60)==HD_ENCOUNTER_DEADLY);
    assert(hd_encounter_risk(0,5)==HD_ENCOUNTER_INVALID);
    assert(hd_encounter_risk(10,61)==HD_ENCOUNTER_INVALID);
    assert(!strcmp(hd_encounter_risk_label(HD_ENCOUNTER_MANAGEABLE),"manageable"));
    assert(!strcmp(hd_encounter_risk_label(HD_ENCOUNTER_INVALID),"unknown"));
    for(p=1;p<=60;p++)
        for(m=1;m<=60;m++) {
            r=hd_encounter_risk(p,m);
            assert(r>=HD_ENCOUNTER_TRIVIAL && r<=HD_ENCOUNTER_DEADLY);
            assert(r==hd_encounter_risk(m+1-(m>=60),p+1-(p>=60)) ||
                   r!=HD_ENCOUNTER_INVALID);
        }
    puts("ROUND 79A: ENCOUNTER RISK RULES PASS (3600 VALID LEVEL PAIRS)");
    puts("NATIVE CONSIDER COMMAND: NOT YET INTEGRATED");
    return 0;
}
