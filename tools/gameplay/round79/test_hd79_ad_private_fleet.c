/* Round79AD: isolated server-only mount NPC construction and rollback. */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_private_fleet.h"
#include "hd79_mount_world_identity.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static hd79_mount_roster saved;
static hd79_mount_presence location;
static room arena={42,0,0};
static creature player={"PrivateOwner",PLAYER,1,200,200,0,0,-1,42,&arena,0,0,0,0,0,{0},{0}};
static ctag owner_tag={0,&player},mon_tag={0,0};
#ifndef HD79AD_REAL_AUTHORITY
static creature *bound;
static unsigned bound_id;
#endif
static int corrupt_save,broken_bind;
static unsigned adds,deletes,frees,reads;

int hd79_presence_store_read(const char *name,hd79_mount_roster *r,
                             hd79_mount_presence *p)
{
    ++reads;
    if(corrupt_save || strcmp(name,player.name))return HD79_PRESENCE_STORE_FAILURE;
    *r=saved;*p=location;
    return HD79_PRESENCE_STORE_OK;
}
#ifndef HD79AD_REAL_AUTHORITY
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    unsigned i;
    if (!r||!p||r->count>6||r->count==0||r->revision!=p->revision||
        r->count!=p->count||r->active_id!=p->active_id||!r->epoch[0])return 0;
    for(i=0;i<r->count;i++) {
        if(r->entries[i].id!=i+1 || !r->entries[i].species ||
           (r->active_id==i+1 && p->room[i]) ||
           (r->entries[i].stabled && p->room[i]))return 0;
    }
    return 1;
}
int hd79_world_mount_bind(creature *owner,creature *monster,unsigned id,
                          const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    (void)r;
    if(broken_bind||bound||owner!=&player||!monster||id!=1||
        monster->parent_rom!=&arena||!arena.first_mon||
        arena.first_mon->crt!=monster||p->room[id-1]!=42)return 0;
    bound=monster;bound_id=id;return 1;
}
int hd79_world_mount_present(creature *owner,unsigned id,
                            const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    (void)r;
    return owner==&player && bound && bound_id==id &&
           arena.first_mon && arena.first_mon->crt==bound &&
           p->room[id-1]==42;
}
void hd79_world_mount_unbind_creature(const creature *m)
{
    if(bound==m){bound=0;bound_id=0;}
}
#endif /* HD79AD_REAL_AUTHORITY */
void add_crt_rom(creature *monster,room *world,int number)
{
    assert(number==0 && world==&arena && !world->first_mon);
    ++adds;mon_tag.crt=broken_bind ? &player : monster;
    world->first_mon=&mon_tag;
    monster->parent_rom=world;monster->rom_num=world->rom_num;
}
void del_crt_rom(creature *monster,room *world)
{
    assert(world==&arena && world->first_mon &&
           (world->first_mon->crt==monster || broken_bind));
    ++deletes;hd79_world_mount_unbind_creature(monster);
    world->first_mon=0;mon_tag.crt=0;
    monster->parent_rom=0;monster->rom_num=0;
}
void free_crt(creature *monster)
{
    ++frees;hd79_world_mount_unbind_creature(monster);free(monster);
}
static void fixture(int species)
{
    memset(&saved,0,sizeof saved); memset(&location,0,sizeof location);
    memcpy(saved.epoch,"1234567890abcdef12345678",25);
    saved.revision=4;saved.count=1;saved.entries[0].id=1;
    saved.entries[0].species=species;
    location.revision=4;location.count=1;location.room[0]=42;
}
int main(void)
{
    creature *result=(creature *)0x1;
    unsigned i;
    arena.first_ply=&owner_tag;
    assert(hd79_ad_private_reconnect_allowed()==0);
    for(i=1;i<=6;i++){
        fixture((int)i);
        assert(hd79_ad_private_species_name((int)i));
        assert(hd79_ad_private_spawn(&player,1,&result)==1);
        assert(result && result!=(creature *)0x1);
        assert(result->type==MONSTER && result->level==1);
        assert(result->hpcur==1 && result->hpmax==1);
        assert(result->mpcur==0 && result->mpmax==0);
        assert(result->ndice==0 && result->sdice==0 && result->pdice==0);
        assert(result->gold==0 && result->experience==0);
        assert(strcmp(result->name,hd79_ad_private_species_name((int)i))==0);
        assert(hd79_world_mount_present(&player,1,&saved,&location)==1);
        { creature *again=(creature *)0x1;
          assert(hd79_ad_private_spawn(&player,1,&again)==0);
          assert(again==(creature *)0x1); }
        del_crt_rom(result,&arena);free_crt(result);
        result=(creature *)0x1;
    }
    assert(adds==6 && deletes==6 && frees==6);
    assert(!hd79_ad_private_species_name(0) && !hd79_ad_private_species_name(7));
    puts("PASS: six dedicated inert native monster blueprints, no duplicate or loot/XP");

    fixture(1);corrupt_save=1;
    assert(hd79_ad_private_spawn(&player,1,&result)==0);
    corrupt_save=0;location.room[0]=43;
    assert(hd79_ad_private_spawn(&player,1,&result)==0);
    location.room[0]=42;player.hpcur=0;
    assert(hd79_ad_private_spawn(&player,1,&result)==0);
    player.hpcur=200;arena.first_ply=0;
    assert(hd79_ad_private_spawn(&player,1,&result)==0);
    arena.first_ply=&owner_tag;saved.entries[0].stabled=1;location.room[0]=0;
    assert(hd79_ad_private_spawn(&player,1,&result)==0);
    puts("PASS: invalid/forged/dead/stabled owner or receipt state denied");

    fixture(2);broken_bind=1;
    assert(hd79_ad_private_spawn(&player,1,&result)==-1);
    assert(arena.first_mon==0 &&
           hd79_world_mount_present(&player,1,&saved,&location)==0);
    assert(adds==7 && deletes==7 && frees==7);
    assert(result==(creature *)0x1);
    broken_bind=0;
    puts("PASS: failed native world identity binding rolls back allocation");

    assert(hd79_ad_private_reconnect_allowed()==0);
    puts("PASS: reconnect auto-rehydration denied until durable mount death proof");
    puts("ROUND79AD: PRIVATE SIX-SPECIES FLEET POLICY PASS");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
