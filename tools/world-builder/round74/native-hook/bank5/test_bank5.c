#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
static void ck(int ok, const char *msg) {if(!ok){fprintf(stderr,"FAIL: %s\n",msg);exit(1);}}
int main(void){
    long full=hd74_xp_for_level(6),half=full/2L;
    long grow=hd74_xp_for_level(7);
    ck(hd74_xp_bank_limit(1,0)==half, "first life bank level 1 -> 6");
    ck(hd74_xp_bank_limit(1,1)==full, "reborn bank level 1 -> 6");
    ck(hd74_xp_bank_limit(1,-1)==full, "unknown is standard cost");
    ck(hd74_xp_add_banked(0,2147483647L,1,0)==half,"firstlife saturates at five levels ahead");
    ck(hd74_xp_add_banked(0,2147483647L,1,1)==full,"reborn saturates at five levels ahead");
    ck(hd74_xp_add_banked(half,5000,1,0)==half,"no sixth level via new firstlife XP");
    ck(hd74_bankable_levels(1,half,0)==5,"all five levels eligible");
    ck(hd74_bankable_levels(1,half-1,0)==4,"not sixth level prematurely");
    ck(hd74_bankable_levels(1,full,1)==5,"reborn five levels eligible");
    ck(hd74_bankable_levels(1,full-1,1)==4,"reborn fifth threshold exact");
    ck(hd74_bankable_levels(2,half,0)==4,"after one train only four banked levels remain");
    ck(hd74_xp_add_banked(half,2147483647L,2,0)==grow/2L,"bank refills one more future level after training");
    ck(hd74_xp_bank_limit(59,0)==hd74_xp_for_level(60)/2L,"near cap only one level bankable");
    ck(hd74_bankable_levels(59,hd74_xp_for_level(60),0)==1,"cannot exceed level cap");
    ck(hd74_bankable_levels(60,2147483647L,0)==0,"at cap no future levels");
    ck(hd74_xp_bank_limit(0,0)==-1,"invalid level denied");
    ck(hd74_xp_bank_limit(1,-2)==-1,"invalid life denied");
    ck(hd74_xp_add_banked(101,100,0,0)==101,"invalid level earns nothing");
    ck(hd74_xp_add_banked(101,100,1,-2)==101,"invalid status earns nothing");
    ck(hd74_xp_add_banked(full+50,100,1,1)==full+50,"legacy over-cap XP is preserved, not silently deleted");
    ck(hd74_xp_add_banked(100, -20,1,0)==100,"negative XP reward not added");
    puts("ROUND 74B: five-level cumulative XP bank, life-based thresholds, cap, legacy XP preservation PASS");
    return 0;
}
