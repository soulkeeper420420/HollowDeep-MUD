#include "hd79_ad_species.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
    int id;
    unsigned previous_hp=0;
    assert(!hd79_ad_species_get(0) && !hd79_ad_species_get(7));
    for(id=HD_MOUNT_HORSE;id<=HD_MOUNT_DARK_DRAGON;id++) {
        const hd79_ad_species_profile *p=hd79_ad_species_get(id);
        const hd_mount_profile *travel=hd_mount_get(id);
        hd_travel_plan plan;
        unsigned breath,endurance;
        assert(p && travel && p->species==id);
        assert(!strcmp(p->name,travel->name));
        assert(strlen(p->name)<80 && strlen(p->key)<20 && p->key[0]);
        assert(p->hp>previous_hp && p->hp<=SHRT_MAX);
        assert(p->level>=1 && p->level<=60 && p->level<=SCHAR_MAX);
        assert(p->armor<=SCHAR_MAX && p->thaco<=SCHAR_MAX);
        assert(p->dice>0 && p->sides>=2 && p->dice*p->sides+p->plus<100);
        assert(hd_mount_travel_preview(id,1,'.',72,
                   travel->endurance_max,&plan)==1);
        assert(hd_mount_travel_finish(&plan,72,travel->endurance_max,1,
                   &breath,&endurance)==1);
        assert(breath==72 && endurance==travel->endurance_max-plan.cost);
        assert(hd_mount_travel_preview(id,1,'.',72,0,&plan)==0);
        assert(hd_mount_travel_preview(id,0,0,72,0,&plan)==1);
        assert(hd_mount_travel_finish(&plan,72,0,1,&breath,&endurance)==1);
        assert(breath==72 && endurance==0);
        assert(hd_mount_travel_preview(id,1,'~',72,
                   travel->endurance_max,&plan)==(travel->can_fly?1:0));
        previous_hp=p->hp;
    }
    puts("PASS: six dedicated bounded native profiles; existing Endurance, terrain, exhaustion and free-retreat policy preserved");
    return 0;
}
