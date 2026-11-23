/* Private, isolated native action precheck tests. Zero gameplay writes. */
#include "hd_player_store.h"
#include "hd79_ad_verified_action.h"
#include "hd79_ad_private_transitions.h"
#include "hd79_mount_presence_store.h"
#include "hd79_mount_world_identity.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static room arena={42,0,0};
static creature owner={"PrivateOwner",PLAYER,1,150,150,0,0,-1,42,&arena};
static ctag live={0,&owner};
static hd79_mount_roster saved;
static hd79_mount_presence position;
static int store_error,broken_presence,stable_room_ok,planning_allowed=1;
static unsigned reads,spawns,commits;

int hd79_mount_roster_valid(const hd79_mount_roster *r)
{
    return r&&r->revision&&r->count==1&&r->entries[0].id==1&&
           r->entries[0].species==1&&strlen(r->epoch)==24;
}
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    if(!hd79_mount_roster_valid(r)||!p||r->revision!=p->revision||
       r->count!=p->count||r->active_id!=p->active_id)return 0;
    if(r->active_id||r->entries[0].stabled)
        return p->room[0]==0;
    return p->room[0]==42;
}
int hd79_presence_store_read(const char *name,hd79_mount_roster *r,
                             hd79_mount_presence *p)
{
    ++reads;
    if(store_error||strcmp(name,owner.name))return HD79_PRESENCE_STORE_FAILURE;
    *r=saved;*p=position;return HD79_PRESENCE_STORE_OK;
}
int hd79_world_mount_present(creature *actor,unsigned id,
                              const hd79_mount_roster *r,
                              const hd79_mount_presence *p)
{
    return !broken_presence&&actor==&owner&&id==1&&
           r->count==1&&p->room[0]==42;
}
int hd79_stable_registry_check(const char *dir,const char *file,unsigned room)
{
    assert(strcmp(dir,"hollowdeep-data")==0);
    assert(strcmp(file,"mount-stables.hds")==0);
    return stable_room_ok&&room==42 ? 1:0;
}
int hd79_ad_private_plan_action(const hd79_mount_roster *r,
    const hd79_mount_presence *p,unsigned action,unsigned id,unsigned room,
    int present,int stable,hd79_mount_roster *next,hd79_mount_presence *np)
{
    if(!planning_allowed || id!=1 || room!=42 || !hd79_presence_valid(r,p))
        return 0;
    *next=*r;*np=*p;
    if(action==HD79_PRESENCE_BOARD&&present&&r->active_id==0){
        next->active_id=1;np->active_id=1;np->room[0]=0;
    }else if(action==HD79_PRESENCE_STABLE&&present&&stable){
        next->entries[0].stabled=1;next->entries[0].stable_room=42;
        np->room[0]=0;
    }else if(action==HD79_PRESENCE_RETRIEVE&&stable&&r->entries[0].stabled){
        next->entries[0].stabled=0;next->entries[0].stable_room=0;
        np->room[0]=42;
    }else if(action==HD79_PRESENCE_DISMOUNT&&r->active_id==1){
        next->active_id=0;np->active_id=0;np->room[0]=42;
    }else return 0;
    next->revision++;np->revision++;
    return 1;
}
static void fixture(hd79_ad_death_receipt *proof)
{
    memset(&saved,0,sizeof saved);
    memset(&position,0,sizeof position);
    memcpy(saved.epoch,"1234567890abcdef12345678",25);
    saved.revision=3;saved.count=1;saved.entries[0].id=1;
    saved.entries[0].species=1;
    position.revision=3;position.count=1;position.room[0]=42;
    memset(proof,0,sizeof *proof);
    memcpy(proof->epoch,saved.epoch,25);
    proof->count=1;proof->serial=2;
    arena.first_ply=&live;
    owner.hpcur=150;
    stable_room_ok=0;broken_presence=0;store_error=0;planning_allowed=1;
}
int main(void)
{
    hd79_ad_death_receipt proof;
    hd79_mount_roster before,next;
    hd79_mount_presence where,after;
    unsigned saved_reads;
    fixture(&proof);
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==1);
    assert(next.active_id==1 && after.room[0]==0);
    assert(spawns==0&&commits==0);
    puts("PASS: native exact-pointer boarding planned, no save or creature mutation");

    broken_presence=1;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==0);
    broken_presence=0;
    proof.dead_mask=1;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==0);
    proof.dead_mask=0;
    store_error=1;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==0);
    store_error=0;owner.hpcur=0;
    saved_reads=reads;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==0);
    assert(reads==saved_reads);
    owner.hpcur=150;
    arena.first_ply=0;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_BOARD,1,&proof,
                                         &before,&where,&next,&after)==0);
    arena.first_ply=&live;
    puts("PASS: dead/forged owner, missing receipt and dead mount denied");

    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_STABLE,1,&proof,
                                         &before,&where,&next,&after)==0);
    stable_room_ok=1;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_STABLE,1,&proof,
                                         &before,&where,&next,&after)==1);
    assert(next.entries[0].stabled==1 && after.room[0]==0);
    saved=next;position=after;
    assert(hd79_ad_verified_action_plan(&owner,HD79_PRESENCE_RETRIEVE,1,&proof,
                                         &before,&where,&next,&after)==1);
    assert(next.entries[0].stabled==0 && after.room[0]==42);
    puts("PASS: native stable room verification required for storage and retrieval");
    assert(spawns==0&&commits==0);
    puts("ROUND79AD: PRIVATE NATIVE ACTION PREFLIGHT PASS");
    return 0;
}
