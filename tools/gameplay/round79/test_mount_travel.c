/* Round 79G: deterministic foot Breath vs six mount Endurance tests. */
#include "hd_mount_travel.h"
#include "hd_wilderness_breath.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void check_names_and_capacities(void)
{
    static const char *names[]={
        "Horse","Warhorse","Dire wolf","Nightmare","Griffin","Dark dragon"
    };
    static const unsigned limits[]={120,140,130,160,175,220};
    int id;
    for(id=HD_MOUNT_HORSE;id<=HD_MOUNT_DARK_DRAGON;id++) {
        const hd_mount_profile *p=hd_mount_get(id);
        assert(p!=0);
        assert(!strcmp(p->name,names[id-1]));
        assert(p->endurance_max==limits[id-1]);
        assert(p->base_step_cost>=1);
        assert(p->can_fly<=1);
    }
    assert(hd_mount_get(HD_MOUNT_FOOT)==0);
    assert(hd_mount_get(-1)==0);
    assert(hd_mount_get(99)==0);
}

static void check_foot(void)
{
    hd_travel_plan p;
    unsigned breath=100, endurance=0, next_breath=777, next_endurance=888;
    int i;
    for(i=0;i<50;i++) {
        assert(hd_mount_travel_preview(HD_MOUNT_FOOT,1,'F',
            breath,endurance,&p)==1);
        assert(p.resource==HD_TRAVEL_PLAYER_BREATH && p.cost==2);
        assert(hd_mount_travel_finish(&p,breath,endurance,1,
            &next_breath,&next_endurance)==1);
        assert(next_endurance==0 && next_breath==breath-2);
        breath=next_breath;
    }
    assert(breath==0);
    assert(hd_mount_travel_preview(HD_MOUNT_FOOT,1,'=',
        breath,endurance,&p)==0);
    /* Safe retreat to an interior remains free at zero Breath. */
    assert(hd_mount_travel_preview(HD_MOUNT_FOOT,0,0,
        breath,endurance,&p)==1);
    assert(p.resource==HD_TRAVEL_FREE && p.cost==0);
    assert(hd_mount_travel_finish(&p,breath,endurance,1,
        &next_breath,&next_endurance)==1);
    assert(next_breath==0 && next_endurance==0);
}

static void check_horse(void)
{
    hd_travel_plan p,stale;
    unsigned next_player=500, next_mount=600;
    /* A horse spends its own Endurance, never the rider's Breath. */
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'.',
        40,120,&p)==1);
    assert(p.cost==1 && p.resource==HD_TRAVEL_MOUNT_ENDURANCE);
    assert(hd_mount_travel_finish(&p,40,120,1,
        &next_player,&next_mount)==1);
    assert(next_player==40 && next_mount==119);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'F',
        40,119,&p)==1);
    assert(p.cost==2);
    assert(hd_mount_travel_finish(&p,40,119,1,
        &next_player,&next_mount)==1);
    assert(next_player==40 && next_mount==117);
    /* No native exit success means no charge, no output mutation. */
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'=',
        40,117,&p)==1);
    next_player=500; next_mount=600;
    assert(hd_mount_travel_finish(&p,40,117,0,
        &next_player,&next_mount)==0);
    assert(next_player==500 && next_mount==600);
    stale=p;
    assert(hd_mount_travel_finish(&stale,40,116,1,
        &next_player,&next_mount)==-1);
    assert(next_player==500 && next_mount==600);

    /* Terrain denial preserves a previously prepared plan. */
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'^',
        40,117,&p)==0);
    assert(p.resource==stale.resource && p.cost==stale.cost);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'~',
        40,117,&p)==0);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'=',
        40,0,&p)==0);
    /* Mount out of endurance cannot trap its rider indoors. */
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,0,0,
        0,0,&p)==1);
    assert(hd_mount_travel_finish(&p,0,0,1,
        &next_player,&next_mount)==1);
    assert(next_player==0 && next_mount==0);
    /* The exhausted rider and mount never refill by dismounting. */
    assert(hd_mount_travel_preview(HD_MOUNT_FOOT,1,'.',
        0,0,&p)==0);
}

static void check_flying_and_ground(void)
{
    hd_travel_plan p;
    unsigned next_player=0,next_mount=0;
    /* Mount capabilities are terrain access, NOT teleport or door bypass. */
    assert(hd_mount_get(HD_MOUNT_GRIFFIN)->can_fly==1);
    assert(hd_mount_get(HD_MOUNT_DARK_DRAGON)->can_fly==1);
    assert(hd_mount_get(HD_MOUNT_HORSE)->can_fly==0);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'~',
        100,120,&p)==0);
    assert(hd_mount_travel_preview(HD_MOUNT_NIGHTMARE,1,'~',
        100,160,&p)==0);
    assert(hd_mount_travel_preview(HD_MOUNT_GRIFFIN,1,'~',
        100,175,&p)==1);
    assert(p.cost==2);
    assert(hd_mount_travel_finish(&p,100,175,1,
        &next_player,&next_mount)==1);
    assert(next_player==100 && next_mount==173);
    assert(hd_mount_travel_preview(HD_MOUNT_DARK_DRAGON,1,'^',
        0,220,&p)==1);
    assert(p.cost==1);
    assert(hd_mount_travel_finish(&p,0,220,1,
        &next_player,&next_mount)==1);
    assert(next_player==0 && next_mount==219);

    assert(hd_mount_travel_preview(HD_MOUNT_WARHORSE,1,'S',
        90,140,&p)==1 && p.cost==2);
    assert(hd_mount_travel_preview(HD_MOUNT_DIRE_WOLF,1,'^',
        90,130,&p)==1 && p.cost==2);
    assert(hd_mount_travel_preview(HD_MOUNT_NIGHTMARE,1,'#',
        90,160,&p)==1 && p.cost==2);
}

static void check_invalid(void)
{
    hd_travel_plan p;
    unsigned a=100,b=200;
    memset(&p,0,sizeof p);
    p.cost=77;
    assert(hd_mount_travel_preview(-1,1,'.',100,0,&p)==-1);
    assert(hd_mount_travel_preview(7,1,'.',100,0,&p)==-1);
    assert(hd_mount_travel_preview(0,2,'.',100,0,&p)==-1);
    assert(hd_mount_travel_preview(0,1,'?',100,0,&p)==-1);
    assert(hd_mount_travel_preview(0,1,'.',101,0,&p)==-1);
    assert(hd_mount_travel_preview(0,1,'.',100,1,&p)==-1);
    assert(hd_mount_travel_preview(1,1,'.',100,121,&p)==-1);
    assert(hd_mount_travel_preview(1,1,'.',100,120,0)==-1);
    assert(p.cost==77);
    assert(hd_mount_travel_finish(&p,100,0,1,&a,&b)==-1);
    assert(a==100 && b==200);
    assert(hd_mount_travel_preview(0,1,'.',100,0,&p)==1);
    assert(hd_mount_travel_finish(&p,100,0,2,&a,&b)==-1);
    assert(hd_mount_travel_finish(&p,100,0,1,0,&b)==-1);
    assert(hd_mount_travel_finish(&p,99,0,1,&a,&b)==-1);
    assert(a==100 && b==200);
}

int main(void)
{
    check_names_and_capacities();
    check_foot();
    check_horse();
    check_flying_and_ground();
    check_invalid();
    puts("ROUND 79G: FOOT BREATH / MOUNT ENDURANCE / TERRAIN RULES PASS");
    puts("NATIVE MOUNTS, STABLES, FLIGHT, SAVES: NOT YET IMPLEMENTED");
    return 0;
}
