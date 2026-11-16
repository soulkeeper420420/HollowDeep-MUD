#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
static void ck(int ok,const char *why){if(!ok){fprintf(stderr,"FAIL: %s\n",why);exit(1);}}
int main(void)
{
    int level; long last=-1;
    ck(hd74_xp_for_level(1)==0,"level 1 begins at zero");
    ck(hd74_xp_for_level(2)==1050,"first train cost matches sample");
    ck(hd74_xp_for_level(3)==4400,"quadratic/cubic second step");
    ck(hd74_xp_for_next(1)==1050,"next threshold");
    ck(hd74_xp_for_next(60)==-1,"no training at cap");
    ck(hd74_xp_for_next(61)==-1,"reject existing over-cap level");
    ck(hd74_xp_for_next(0)==-1,"reject malformed level");
    ck(hd74_xp_for_level(0)==-1,"reject zero level");
    ck(hd74_xp_for_level(61)==-1,"reject out of range");
    ck(hd74_level_from_xp(-8)==1,"negative xp is level 1");
    ck(hd74_level_from_xp(1049)==1,"threshold not reached");
    ck(hd74_level_from_xp(1050)==2,"threshold reached");
    ck(hd74_level_from_xp(4399)==2,"second threshold not reached");
    ck(hd74_level_from_xp(4400)==3,"second threshold reached");
    for(level=1;level<=60;level++){
        long cur=hd74_xp_for_level(level);
        ck(cur>=0 && cur>last,"thresholds strictly rise");
        ck(hd74_level_from_xp(cur)==level,"level inversion");
        if(level<60) ck(hd74_xp_for_next(level)==hd74_xp_for_level(level+1),"next-level consistency");
        last=cur;
    }
    ck(hd74_level_from_xp(2147483647L)==60,"xp capped to 60");
    ck(hd74_xp_add_bounded(2147483640L,100L)==2147483647L,"saturate high");
    ck(hd74_xp_add_bounded(100L,70L)==170L,"normal gain");
    ck(hd74_xp_add_bounded(100L,-20L)==100L,"negative reward denied");
    ck(hd74_xp_add_bounded(-1L,10L)==10L,"corrupt negative source normalized");
    ck(hd74_xp_add_bounded(0L,2147483647L)==2147483647L,"full range cap");
    puts("ROUND 74B: level-60 native XP/training threshold and overflow regression PASS");
    return 0;
}
