#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
static void ck(int ok,const char *why){if(!ok){fprintf(stderr,"FAIL: %s\n",why);exit(1);}}
int main(void){
 long xp=-11,gold=-11,legacy=hd74_xp_for_next(1);
 ck(legacy==1050,"baseline XP level 2 = 1050");
 ck(hd74_training_cost_for_remorts(1,0,&xp,&gold)==0 && xp==525 && gold==262,
    "first life: 525 XP required and 262 gold");
 ck(hd74_training_cost_for_remorts(1,1,&xp,&gold)==0 && xp==1050 && gold==525,
    "post-remort full XP and gold");
 ck(hd74_training_cost_for_remorts(1,2,&xp,&gold)==0 && xp==1050 && gold==525,
    "subsequent lives use standard price");
 ck(hd74_training_cost_for_remorts(1,-1,&xp,&gold)==0 && xp==1050 && gold==525,
    "unknown life never qualifies for discount");
 ck(hd74_training_cost_for_remorts(1,-2,&xp,&gold)!=0,"invalid life marker denied");
 ck(hd74_training_cost_for_remorts(2,0,&xp,&gold)==0 && xp==2200 && gold==1100,
    "level 3 first-life price");
 ck(hd74_training_cost_for_remorts(2,1,&xp,&gold)==0 && xp==4400 && gold==2200,
    "level 3 reborn price");
 ck(hd74_xp_for_life_next(1,0)==525 && hd74_gold_for_life_next(1,0)==262,
    "first life costs consistently shared");
 ck(hd74_xp_for_life_next(1,-1)==1050 && hd74_gold_for_life_next(1,-1)==525,
    "no discount without trusted lookup");
 ck(hd74_level_from_xp_for_life(524,0)==1 && hd74_level_from_xp_for_life(525,0)==2,
    "first-life threshold inversion");
 ck(hd74_level_from_xp_for_life(1049,1)==1 && hd74_level_from_xp_for_life(1050,1)==2,
    "reborn threshold inversion");
 ck(hd74_level_from_xp_for_life(525,-1)==1,"unknown uses full XP curve");
 ck(hd74_training_cost_for_remorts(60,0,&xp,&gold)!=0,"no first-life training at cap");
 ck(hd74_training_cost_for_remorts(60,1,&xp,&gold)!=0,"no reborn training at cap");
 ck(hd74_training_cost_for_remorts(0,0,&xp,&gold)!=0,"invalid level denied");
 ck(hd74_training_cost_for_remorts(1,0,NULL,&gold)!=0,"null output denied");
 ck(hd74_training_cost_for_remorts(1,0,&xp,NULL)!=0,"null gold output denied");
 ck(hd74_training_cost_for_remorts(59,0,&xp,&gold)==0 && xp>0 && gold>=0,
    "first-life cap-1 safe XP/gold");
 puts("ROUND 74B: first-life 50% XP / 50% normal gold cost policy and cap checks PASS");
 return 0;
}
