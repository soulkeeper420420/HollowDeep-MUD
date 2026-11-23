/* Simulated save boundary: parser/safety and atomic dismount outcomes. */
#include "hd79_presence_dismount_store.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static hd79_mount_roster disk;
static hd79_mount_presence diskpos;
static int mode,read_count,commit_count,has_record=1;
static void reset(void)
{
    memset(&disk,0,sizeof disk);
    memset(&diskpos,0,sizeof diskpos);
    strcpy(disk.epoch,"1234567890abcdef12345678");
    disk.revision=5;disk.count=1;disk.active_id=1;
    disk.entries[0].id=1;disk.entries[0].species=1;
    disk.entries[0].endurance=72;
    diskpos.revision=5;diskpos.count=1;diskpos.active_id=1;
    mode=0;read_count=commit_count=0;has_record=1;
}
int hd79_mount_dismount(const hd79_mount_roster *old,hd79_mount_roster *newstate,const char *epoch)
{
    if(!old->active_id || strcmp(epoch,old->epoch))return 0;
    *newstate=*old;newstate->active_id=0;newstate->revision++;
    return 1;
}
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    if (p->revision!=r->revision||p->count!=r->count||p->active_id!=r->active_id)
        return 0;
    return r->active_id ? p->room[0]==0 : p->room[0]!=0;
}
int hd79_presence_step(const hd79_mount_roster *old,const hd79_mount_presence *oldp,
                       const hd79_mount_roster *next,unsigned action,unsigned id,
                       unsigned room,int has_mount,int stable,hd79_mount_presence *out)
{
    if (action!=HD79_PRESENCE_DISMOUNT||id!=old->active_id||!hd79_presence_valid(old,oldp)||
        has_mount||stable||room==0||room>HD79_PRESENCE_MAX_ROOM) return -1;
    *out=*oldp;out->active_id=next->active_id;out->revision=next->revision;out->room[id-1]=room;
    return hd79_presence_valid(next,out)?1:-1;
}
int hd79_mount_wire_encode(const hd79_mount_roster *r,char a[65],char b[65])
{
    if (!r||!a||!b)return -1;
    snprintf(a,65,"%08x%08x%08x%08x",r->revision,r->active_id,r->count,r->entries[0].endurance);
    snprintf(b,65,"%08x%08x",r->entries[0].id,r->entries[0].stable_room);
    return 0;
}
int hd79_presence_encode(const hd79_mount_roster *r,const hd79_mount_presence *p,char out[65])
{
    if (!hd79_presence_valid(r,p))return -1;
    snprintf(out,65,"%08x%08x%08x",p->revision,p->active_id,p->room[0]);
    return 0;
}
int hd79_presence_store_read(const char *name,hd79_mount_roster *r,hd79_mount_presence *p)
{
    read_count++;
    if(strcmp(name,"TestRider")||!has_record)return HD79_PRESENCE_STORE_ABSENT;
    *r=disk;*p=diskpos;
    return HD79_PRESENCE_STORE_OK;
}
int hd79_presence_store_commit(const char *name,const hd79_mount_roster *prev,
        const hd79_mount_presence *prevpos,const hd79_mount_roster *next,
        const hd79_mount_presence *nextpos,hd79_mount_roster *saved,
        hd79_mount_presence *savedpos)
{
    commit_count++;
    if(strcmp(name,"TestRider")||prev->revision!=disk.revision||
       !hd79_presence_valid(prev,prevpos))return HD79_PRESENCE_STORE_CONFLICT;
    if(mode==1)return HD79_PRESENCE_STORE_FAILURE; /* before rename */
    if(mode==2)return HD79_PRESENCE_STORE_CONFLICT;
    disk=*next;diskpos=*nextpos;
    if(mode==4) diskpos.room[0]=43; /* mismatched post-rename disk */
    *saved=disk;*savedpos=diskpos;
    if(mode==3||mode==4)return HD79_PRESENCE_STORE_UNCERTAIN;
    return HD79_PRESENCE_STORE_OK;
}
int main(void)
{
    hd79_mount_roster out={0};
    reset();
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_SUCCESS);
    assert(commit_count==1&&read_count==1&&disk.active_id==0&&diskpos.room[0]==42);
    assert(disk.entries[0].endurance==72&&out.entries[0].endurance==72);
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_ON_FOOT);
    assert(commit_count==1);
    reset();mode=1;
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_FAILURE);
    assert(disk.active_id==1&&commit_count==1);
    reset();mode=2;
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_CONFLICT);
    assert(disk.active_id==1);
    reset();mode=3;
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_SUCCESS);
    assert(commit_count==1&&read_count==2&&diskpos.room[0]==42);
    reset();mode=4;
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_UNCERTAIN);
    assert(commit_count==1&&read_count==2);
    reset();
    assert(hd79_presence_dismount_store("TestRider",0,&out)==HD79_DISMOUNT_FAILURE);
    assert(hd79_presence_dismount_store("TestRider",0x1000000U,&out)==HD79_DISMOUNT_FAILURE);
    assert(commit_count==0&&read_count==0);
    has_record=0;
    assert(hd79_presence_dismount_store("TestRider",42,&out)==HD79_DISMOUNT_ABSENT);
    puts("PASS: triple dismount exact one commit and no Endurance refill");
    puts("PASS: before-rename failure, stale CAS and uncertain full record reconciliation");
    puts("PASS: missing roster / invalid native room fail closed");
    puts("ROUND79AC1: MOCK THREE-RECEIPT DISMOUNT PASS");
    return 0;
}
