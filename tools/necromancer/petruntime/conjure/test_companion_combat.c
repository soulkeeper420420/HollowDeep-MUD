#define main legacy_main
#define del_active legacy_del_active
#include "test_pet_store.c"
#undef main
#undef del_active

#include "hd_conjure.h"
#include "hd_conjure_runtime.h"

unsigned hd_cj_test_roll=100;
uint32_t hd_cj_test_now=2000;

static creature *live_pet, *victim, *master;
static unsigned kills, credited;
static int enemy;

void print(int fd,char *format,...)
{ (void)fd; (void)format; }

void del_active(creature *p)
{ (void)p; }

void add_crt_rom(creature *p,room *r,int announce)
{
    (void)announce;
    assert(!p->parent_rom);
    p->parent_rom=r;
    p->rom_num=r->rom_num;
    live_pet=p;
}

void del_crt_rom(creature *p,room *r)
{
    assert(p->parent_rom==r);
    p->parent_rom=NULL;
    if(live_pet==p) live_pet=NULL;
}

int hd_necro_skeleton_is_pet(creature *p)
{ return hd_cj_is_pet(p); }

int is_enm_crt(char *name,creature *p)
{
    return enemy && p==victim &&
        !strcmp(name,master->name);
}

void add_enm_dmg(char *name,creature *p,int n)
{
    assert(p==victim && n>0);
    assert(!strcmp(name,master->name));
    credited+=n;
}

void die(creature *p,creature *killer)
{
    assert(p==victim && killer==master);
    assert(!p->hpcur);
    ++kills;
    hd_cj_forget_target(p);
    p->parent_rom=NULL;
}

static void hit(creature *owner,creature *target,
                unsigned roll,int damage)
{
    int before=target->hpcur;

    hd_cj_test_now+=3;
    hd_cj_test_roll=roll;

    assert(hd_cj_assist(owner,target)==0);
    assert(before-target->hpcur==damage);
}

int main(void)
{
    const char *names[]={
        "Hdcjwolf","Hdcjscorp","Hdcjfire",
        "Hdcjmino","Hdcjwraith","Hdcjdragon"
    };

    unsigned id;

    for(id=1;id<=6;++id) {
        creature owner,target={0};
        room place={0};
        hd_conjure_state a,b;
        unsigned chance=hd_conjure_get(id)->proc;

        initial(&owner,names[id-1]);
        owner.class=FIGHTER;
        owner.level=60;
        owner.mpcur=50;

        place.rom_num=1;
        owner.parent_rom=&place;

        assert(hd_store_create_player(
            owner.name,&owner)==HD_STORE_OK);

        assert(hd_conjure_store_apply(
            owner.name,NULL,HD_CJ_INIT,0,0,0,&a)==0);

        assert(hd_conjure_store_apply(
            owner.name,&a,HD_CJ_SUMMON,1000,id,0,&b)==0);

        if(id==5) {
            a=b;
            assert(hd_conjure_store_apply(
                owner.name,&a,HD_CJ_VITALS,1001,
                a.hp,0,&b)==0);
        }

        hd_cj_login(&owner);
        assert(live_pet && hd_cj_is_pet(live_pet));

        strcpy(target.name,"trialtarget");
        target.type=MONSTER;
        target.hpcur=target.hpmax=1000;
        target.mpcur=target.mpmax=100;
        target.experience=250;
        target.parent_rom=&place;

        victim=&target;
        master=&owner;
        enemy=1;
        credited=0;
        kills=0;

        hit(&owner,&target,chance+1,4);

        if(id==1) {
            hit(&owner,&target,1,4);
        } else if(id==2) {
            hit(&owner,&target,10,6);
            hit(&owner,&target,100,6);
            hit(&owner,&target,100,6);
            hit(&owner,&target,100,4);
        } else if(id==3) {
            hit(&owner,&target,15,8);
        } else if(id==4) {
            hit(&owner,&target,10,4);
            assert(target.lasttime[LT_ATTCK].interval==3);
        } else if(id==5) {
            hit(&owner,&target,20,4);
            assert(target.mpcur==90);
            assert(owner.mpcur==55);
            assert(live_pet->mpcur==5);
        } else if(id==6) {
            hit(&owner,&target,15,12);
        }

        assert(credited>0);

        enemy=0;
        hd_cj_test_now+=3;

        assert(hd_cj_assist(&owner,&target)==0);

        enemy=1;
        target.hpcur=1;
        hd_cj_test_now+=3;
        hd_cj_test_roll=100;

        assert(hd_cj_assist(&owner,&target)==1);
        assert(kills==1);

        assert(hd_cj_assist(&owner,&target)==0);
        assert(kills==1);

        assert(hd_conjure_store_read(owner.name,&a)==0);
        assert(a.level==2 && a.xp==250);

        hd_cj_logout(&owner);

        assert(!live_pet);

        hd_cj_login(&owner);
        assert(live_pet && live_pet->level==2);

        hd_cj_logout(&owner);

        printf("PASS: %s proc, owner attribution, XP and restoration\n",
               hd_conjure_get(id)->name);
    }

    puts("ROUND 75D: ALL SIX COMPANION COMBAT TESTS PASS");
    return 0;
}
