/* Round79AD: real pure roster/presence/wilderness transitions on ELF32. */
#include "hd79_ad_private_transitions.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static const char epoch[]="1234567890abcdef12345678";

int main(void)
{
 hd79_mount_roster prior,owned,next,final;
 hd79_mount_presence where,after,where2;
 hd_travel_plan travel;
 unsigned id=0,breath=100;
 assert(hd79_mount_roster_new(&prior,epoch)==1);
 assert(hd79_mount_award(&prior,&owned,epoch,HD_MOUNT_HORSE,&id)==1);
 assert(id==1);
 memset(&where,0,sizeof where);
 where.revision=owned.revision;where.count=1;where.room[0]=42;
 assert(hd79_presence_valid(&owned,&where));

 assert(hd79_ad_private_plan_action(&owned,&where,HD79_PRESENCE_BOARD,1,42,
                                   0,0,&next,&after)==0);
 assert(hd79_ad_private_plan_action(&owned,&where,HD79_PRESENCE_BOARD,1,42,
                                   1,0,&next,&after)==1);
 assert(next.active_id==1 && after.room[0]==0);
 puts("PASS: native-presence-only boarding moves triple receipts consistently");

 assert(hd79_ad_private_plan_action(&next,&after,HD79_PRESENCE_DISMOUNT,1,42,
                                   0,0,&final,&where2)==1);
 assert(final.active_id==0 && where2.room[0]==42);
 assert(final.entries[0].endurance==owned.entries[0].endurance);
 puts("PASS: verified dismount returns owned mount to native location");

 assert(hd79_ad_private_plan_action(&final,&where2,HD79_PRESENCE_STABLE,1,42,
                                   1,0,&next,&after)==0);
 assert(hd79_ad_private_plan_action(&final,&where2,HD79_PRESENCE_STABLE,1,42,
                                   1,1,&next,&after)==1);
 assert(next.entries[0].stabled==1 && after.room[0]==0);
 assert(hd79_ad_private_plan_action(&next,&after,HD79_PRESENCE_RETRIEVE,1,43,
                                   0,1,&final,&where2)==0);
 assert(hd79_ad_private_plan_action(&next,&after,HD79_PRESENCE_RETRIEVE,1,42,
                                   0,1,&final,&where2)==1);
 assert(final.entries[0].stabled==0 && where2.room[0]==42);
 puts("PASS: same-stable physical authority enforced for stable/retrieve");

 assert(hd79_ad_private_plan_action(&final,&where2,HD79_PRESENCE_BOARD,1,42,
                                   1,0,&next,&after)==1);
 assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'F',100,
                                next.entries[0].endurance,&travel)==1);
 assert(hd79_ad_private_plan_mounted_move(&next,&after,&travel,100,0,
                                          &prior,&where,&breath)==0);
 assert(hd79_ad_private_plan_mounted_move(&next,&after,&travel,100,1,
                                          &final,&where2,&breath)==1);
 assert(final.entries[0].endurance<next.entries[0].endurance);
 assert(where2.revision==final.revision && breath==100);
 puts("PASS: confirmed wilderness move debits only mount Endurance once");

 assert(hd_mount_travel_preview(HD_MOUNT_HORSE,0,0,100,
                                final.entries[0].endurance,&travel)==1);
 assert(hd79_ad_private_plan_mounted_move(&final,&where2,&travel,100,1,
                                          &next,&after,&breath)==2);
 assert(next.revision==final.revision && breath==100);
 puts("PASS: safe retreat requires no receipt save or Endurance refill");
 puts("ROUND79AD: PRIVATE ACTION+TRAVEL PLANNER PASS");
 return 0;
}
