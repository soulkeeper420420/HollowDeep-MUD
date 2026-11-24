/* R6C isolated deterministic physical-vs-durable action test. No real save. */
#include "hd_player_store.h"
#include "hd79_ad_creature_action.h"
#include "hd79_ad_authenticated_action.h"
#include "hd79_ad_four_action_store.h"
#include "hd79_mount_world_identity.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static room world={42,0,0};
static creature owner={"Owner",PLAYER,1,80,80,0,0,-1,42,&world};
static ctag owned={0,&owner},mounted_tag={0,0};
static hd79_mount_roster stored;
static hd79_mount_presence location;
static hd79_ad_death_receipt death;
static creature *bound;
static int stable_authorized,fault,spawn_fail,read_fail,corrupt_after;
static unsigned deletes,frees,spawns,commits,reads;

static int valid(void){return stored.count==1 && location.count==1 &&
 location.revision==stored.revision && death.count==1 && !death.dead_mask;}
static int authorized(unsigned action){
 if(action==HD79_PRESENCE_BOARD||action==HD79_PRESENCE_STABLE)
   return bound && stored.active_id==0 && !stored.entries[0].stabled &&
          location.room[0]==42 && mounted_tag.crt==bound;
 if(action==HD79_PRESENCE_DISMOUNT)return stored.active_id==1;
 return action==HD79_PRESENCE_RETRIEVE && stored.entries[0].stabled &&
        stored.entries[0].stable_room==42;
}
static int apply(unsigned action,hd79_mount_roster *r,hd79_mount_presence *p){
 if(!authorized(action))return 0;
 *r=stored;*p=location;
 switch(action){
 case HD79_PRESENCE_BOARD:r->active_id=1;p->room[0]=0;break;
 case HD79_PRESENCE_DISMOUNT:r->active_id=0;p->room[0]=42;break;
 case HD79_PRESENCE_STABLE: if(!stable_authorized)return 0;
    r->entries[0].stabled=1;r->entries[0].stable_room=42;p->room[0]=0;break;
 case HD79_PRESENCE_RETRIEVE:if(!stable_authorized)return 0;
    r->entries[0].stabled=0;r->entries[0].stable_room=0;p->room[0]=42;break;
 default:return 0;
 }
 r->revision++;p->revision++;p->active_id=r->active_id;
 return 1;
}
int hd79_ad_authenticated_action_plan(creature *actor,unsigned action,unsigned id,
 hd79_mount_roster *before,hd79_mount_presence *where,hd79_ad_death_receipt *d,
 hd79_mount_roster *after,hd79_mount_presence *next){
 if(actor!=&owner||!actor->hpcur||world.first_ply!=&owned||actor->rom_num!=42||
    id!=1||!valid()||!apply(action,after,next))return 0;
 *before=stored;*where=location;*d=death;return 1;
}
int hd79_ad_four_action_commit_native(creature *actor,unsigned action,unsigned id,
 hd79_mount_roster *r,hd79_mount_presence *p,hd79_ad_death_receipt *d){
 hd79_mount_roster next;hd79_mount_presence np;
 ++commits;
 if(actor!=&owner||id!=1||!apply(action,&next,&np))return HD79_AD_FOUR_CONFLICT;
 if(fault==1)return HD79_AD_FOUR_FAILURE; /* before-rename */
 stored=next;location=np;
 if(fault==3)corrupt_after=1; /* readback must deny */
 if(fault==2||fault==3)return HD79_AD_FOUR_UNCERTAIN;
 *r=stored;*p=location;*d=death;
 return HD79_AD_FOUR_OK;
}
int hd79_ad_four_store_read(const char *name,hd79_mount_roster *r,
 hd79_mount_presence *p,hd79_ad_death_receipt *d){
 ++reads;
 if(strcmp(name,owner.name)||read_fail)return HD79_AD_FOUR_FAILURE;
 *r=stored;*p=location;*d=death;
 if(corrupt_after)d->serial++;
 return HD79_AD_FOUR_OK;
}
creature *hd79_ad_native_bound_creature(creature *actor,unsigned id,
 const hd79_mount_roster *r,const hd79_mount_presence *p){
 if(actor!=&owner||id!=1||!bound||!r||!p||r->active_id ||
    p->room[0]!=42||!world.first_mon||world.first_mon->crt!=bound||
    bound->hpcur<=0)return NULL;
 return bound;
}
int hd79_world_mount_present(creature *actor,unsigned id,
 const hd79_mount_roster *r,const hd79_mount_presence *p){
 return hd79_ad_native_bound_creature(actor,id,r,p)!=NULL;
}
int hd79_ad_private_spawn(creature *actor,unsigned id,creature **out){
 if(spawn_fail||bound||actor!=&owner||id!=1||!valid()||
    stored.active_id||stored.entries[0].stabled||location.room[0]!=42)
    return 0;
 bound=calloc(1,sizeof *bound); assert(bound);
 bound->type=MONSTER;bound->hpcur=bound->hpmax=50;
 bound->parent_rom=&world;bound->rom_num=42;
 mounted_tag.crt=bound;world.first_mon=&mounted_tag;
 *out=bound;++spawns;return 1;
}
void del_crt_rom(creature *m,room *r){
 assert(m==bound&&r==&world&&r->first_mon==&mounted_tag);
 mounted_tag.crt=NULL;r->first_mon=NULL;
 m->parent_rom=NULL;m->rom_num=0;
 ++deletes;
}
void free_crt(creature *m){assert(m==bound);bound=NULL;free(m);++frees;}
int hd79_mount_wire_encode(const hd79_mount_roster *r,char a[65],char b[65]){
 snprintf(a,65,"%064u",r->revision);
 snprintf(b,65,"%064u",r->active_id*10+r->entries[0].stabled);
 return 0;
}
int hd79_presence_encode(const hd79_mount_roster *r,const hd79_mount_presence *p,char a[65]){
 (void)r;snprintf(a,65,"%064u",p->room[0]*100+p->revision);return 0;
}
int hd79_ad_death_wire_encode(const hd79_mount_roster *r,const hd79_ad_death_receipt *d,char a[65]){
 (void)r;snprintf(a,65,"%064u",d->serial*100+d->dead_mask);return 0;
}
static void reset(void){
 if(bound){del_crt_rom(bound,&world);free_crt(bound);}
 memset(&stored,0,sizeof stored);memset(&location,0,sizeof location);
 memset(&death,0,sizeof death);
 memcpy(stored.epoch,"1234567890abcdef12345678",25);
 memcpy(death.epoch,stored.epoch,25);
 stored.count=1;stored.revision=2;stored.entries[0].id=1;
 stored.entries[0].species=1;stored.entries[0].endurance=120;
 location.count=1;location.revision=2;location.room[0]=42;
 death.count=1;death.serial=2;
 owner.hpcur=80;owner.parent_rom=&world;owner.rom_num=42;
 world.first_ply=&owned;world.first_mon=NULL;
 stable_authorized=fault=spawn_fail=read_fail=corrupt_after=0;
 assert(hd79_ad_private_spawn(&owner,1,&bound)==1);
}
int main(void){
 unsigned start_frees;
 reset();fault=1;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_PENDING);
 assert(stored.active_id==0 && bound && location.room[0]==42);
 fault=0;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_COMPLETE);
 assert(stored.active_id==1 && location.room[0]==0 && !bound);
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_DENIED);
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_DISMOUNT,1)==HD79_AD_CREATURE_COMPLETE);
 assert(stored.active_id==0 && bound && location.room[0]==42);
 puts("PASS: board removes exact native pointer only after durable CAS; dismount spawns once");
 reset();
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_STABLE,1)==HD79_AD_CREATURE_DENIED);
 stable_authorized=1;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_STABLE,1)==HD79_AD_CREATURE_COMPLETE);
 assert(!bound && stored.entries[0].stabled && location.room[0]==0);
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_RETRIEVE,1)==HD79_AD_CREATURE_COMPLETE);
 assert(bound && !stored.entries[0].stabled && location.room[0]==42);
 puts("PASS: stable consumes exact native mount, retrieve rebinds one living mount");
 reset();fault=2;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_COMPLETE);
 assert(!bound && stored.active_id==1);
 puts("PASS: uncertain rename acknowledged only after exact four-receipt readback");
 reset();fault=3;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_PENDING);
 assert(bound && stored.active_id==1); /* malformed receipt => safe denial */
 puts("PASS: uncertain mismatched death receipt never mutates native creature");
 reset();death.dead_mask=1;start_frees=frees;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_DENIED);
 assert(bound && frees==start_frees);
 owner.hpcur=0;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_DENIED);
 assert(bound && frees==start_frees);
 puts("PASS: dead mount/owner denied without creature side effects");
 reset();
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,0)==HD79_AD_CREATURE_INVALID);
 assert(hd79_ad_creature_action(&owner,77,1)==HD79_AD_CREATURE_INVALID);
 spawn_fail=1;
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_BOARD,1)==HD79_AD_CREATURE_COMPLETE);
 assert(hd79_ad_creature_action(&owner,HD79_PRESENCE_DISMOUNT,1)==HD79_AD_CREATURE_PENDING);
 assert(!bound && location.room[0]==42 && !stored.active_id);
 puts("PASS: post-save native spawn failure is never acknowledged (recovery gate still needed)");
 if(bound){del_crt_rom(bound,&world);free_crt(bound);}
 puts("ROUND79AD R6C: PRIVATE NATIVE MOUNT CREATURE RECONCILIATION POLICY PASS");
 return 0;
}
