/* R6A: native owner + actual atomic four-receipt PREVIEW, no game I/O. */
#include "hd_player_store.h"
#include "hd79_ad_authenticated_action.h"
#include "hd79_ad_private_transitions.h"
#include "hd79_mount_world_identity.h"
#include "hd79_stable_registry.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static const char EPOCH[]="1234567890abcdef12345678";
static room arena={42,0,0};
static creature owner={"NativeOwner",PLAYER,1,150,150,0,0,-1,42,&arena};
static ctag tag={0,&owner};
static hd79_mount_roster saved;
static hd79_mount_presence position;
static hd79_ad_death_receipt death;
static int missing,broken_present,stable_ok,poisoned_proof;
static unsigned reads,world_checks,stable_checks;

int hd79_ad_four_store_read(const char *name,hd79_mount_roster *r,
                            hd79_mount_presence *p,
                            hd79_ad_death_receipt *d)
{
    reads++;
    if(missing||strcmp(name,owner.name))return HD79_AD_FOUR_FAILURE;
    *r=saved;*p=position;*d=death;
    if(poisoned_proof)d->epoch[0]='a';
    return HD79_AD_FOUR_OK;
}
int hd79_world_mount_present(creature *actor,unsigned id,
                              const hd79_mount_roster *r,
                              const hd79_mount_presence *p)
{
    world_checks++;
    return !broken_present&&actor==&owner&&id==1&&
           r->count==1&&r->epoch[0]=='1'&&p->room[0]==42;
}
int hd79_stable_registry_check(const char *dir,const char *file,
                               unsigned room_id)
{
    stable_checks++;
    assert(!strcmp(dir,"hollowdeep-data"));
    assert(!strcmp(file,"mount-stables.hds"));
    return stable_ok&&room_id==42?1:0;
}
static void reset(void)
{
    hd79_mount_roster empty;
    hd79_ad_death_receipt fresh;
    unsigned id=0;
    assert(hd79_mount_roster_new(&empty,EPOCH)==1);
    assert(hd79_ad_death_new_empty(&empty,&fresh)==1);
    assert(hd79_mount_award(&empty,&saved,EPOCH,HD_MOUNT_HORSE,&id)==1);
    assert(id==1);
    assert(hd79_ad_death_award_step(&empty,&fresh,&saved,&death)==1);
    memset(&position,0,sizeof position);
    position.count=1;position.revision=saved.revision;position.room[0]=42;
    assert(hd79_presence_valid(&saved,&position));
    arena.first_ply=&tag;
    arena.rom_num=42;
    owner.rom_num=42;owner.parent_rom=&arena;owner.hpcur=150;
    broken_present=missing=stable_ok=poisoned_proof=0;
    reads=world_checks=stable_checks=0;
}
#define PREVIEW(action) hd79_ad_authenticated_action_plan(&owner,action,1,\
                     &before,&where,&got_death,&after,&next_where)
int main(void)
{
    hd79_mount_roster before,after;
    hd79_mount_presence where,next_where;
    hd79_ad_death_receipt got_death,marked;
    hd79_mount_roster saved_before;
    hd79_mount_presence saved_position;
    unsigned prior_reads;
    reset();
    assert(PREVIEW(HD79_PRESENCE_BOARD)==1);
    assert(after.active_id==1 && next_where.room[0]==0);
    assert(got_death.serial==death.serial && got_death.dead_mask==0);
    assert(world_checks==2 && reads==1 && stable_checks==0);
    assert(saved.active_id==0 && position.room[0]==42);
    puts("PASS: authenticated native #83 + exact-pointer board preview, no mutation");

    reset();
    assert(PREVIEW(HD79_PRESENCE_STABLE)==0);
    assert(stable_checks==1);
    stable_ok=1;
    assert(PREVIEW(HD79_PRESENCE_STABLE)==1);
    assert(after.entries[0].stabled==1 && after.entries[0].stable_room==42);
    assert(next_where.room[0]==0);
    saved=after;position=next_where;
    assert(PREVIEW(HD79_PRESENCE_RETRIEVE)==1);
    assert(!after.entries[0].stabled && next_where.room[0]==42);
    puts("PASS: root-owned native stable authority required for store/retrieve preview");

    reset();
    saved_before=saved;saved_position=position;
    broken_present=1;
    memset(&after,0xA5,sizeof after);
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    assert(memcmp(&saved,&saved_before,sizeof saved)==0 &&
           memcmp(&position,&saved_position,sizeof position)==0);
    broken_present=0;
    poisoned_proof=1;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    poisoned_proof=0;
    assert(hd79_ad_death_mark(&saved,&death,1,&marked)==1);
    death=marked;
    prior_reads=reads;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    assert(reads==prior_reads+1);
    assert(PREVIEW(HD79_PRESENCE_STABLE)==0);
    assert(PREVIEW(HD79_PRESENCE_RETRIEVE)==0);
    puts("PASS: forged location, corrupt #83, permanent death denies all action previews");

    reset();
    missing=1;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    missing=0;
    arena.first_ply=NULL;
    prior_reads=reads;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    assert(reads==prior_reads);
    arena.first_ply=&tag;
    tag.next_tag=&tag;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    tag.next_tag=NULL;
    owner.hpcur=0;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    owner.hpcur=150;owner.rom_num=43;
    assert(PREVIEW(HD79_PRESENCE_BOARD)==0);
    owner.rom_num=42;
    assert(PREVIEW(77)==-1);
    assert(hd79_ad_authenticated_action_plan(&owner,HD79_PRESENCE_BOARD,0,
           &before,&where,&got_death,&after,&next_where)==-1);
    puts("PASS: missing save, dead/forged/duplicate owner, wrong room and malformed requests denied");

    reset();
    assert(PREVIEW(HD79_PRESENCE_BOARD)==1);
    saved=after;position=next_where;
    assert(PREVIEW(HD79_PRESENCE_DISMOUNT)==1);
    assert(after.active_id==0 && next_where.room[0]==42);
    assert(saved.active_id==1 && position.room[0]==0);
    assert(hd79_ad_death_reconnect_allowed(&saved,&death,1)==0);
    puts("PASS: dismount preview preserves mount resources, reconnect remains disabled");
    puts("ROUND79AD R6A: PRIVATE AUTHENTICATED FOUR-RECEIPT READ-ONLY ACTION GATE PASS");
    return 0;
}
