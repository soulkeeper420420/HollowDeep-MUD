/* Local 64-bit harness only. Linode compiles the accepted real implementations. */
#include "hd_player_store.h"
#include "hd79_mount_world_identity.h"
#include <string.h>
static creature *bound_owner,*bound_mount;
static unsigned bound_id;
int hd79_mount_roster_new(hd79_mount_roster *out,const char *epoch)
{
    if(!out || strlen(epoch)!=24)return -1;
    memset(out,0,sizeof *out);memcpy(out->epoch,epoch,25);
    out->revision=1;return 1;
}
int hd79_mount_award(const hd79_mount_roster *before,hd79_mount_roster *out,const char *epoch,int species,unsigned *id)
{
    if(!before || !out || !epoch || strcmp(before->epoch,epoch)||species<1||species>6||before->count>=6)return -1;
    *out=*before;*id=++out->count;
    out->entries[*id-1].species=species;out->entries[*id-1].id=*id;
    out->revision++;return 1;
}
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    unsigned i;
    if(!r || !p ||r->revision!=p->revision||r->count!=p->count||r->count>6||r->active_id!=p->active_id)return 0;
    for(i=0;i<r->count;i++)if(!r->entries[i].id||!p->room[i])return 0;
    return 1;
}
int hd79_world_mount_bind(creature *owner,creature *mount,unsigned id,const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    ctag *tag;
    if(!owner||!mount||!r||!p||bound_mount||!owner->parent_rom||
      p->room[id-1]!=(unsigned)owner->rom_num||mount->parent_rom!=owner->parent_rom)return 0;
    for(tag=owner->parent_rom->first_mon;tag;tag=tag->next_tag)
      if(tag->crt==mount){bound_mount=mount;bound_owner=owner;bound_id=id;return 1;}
    return 0;
}
int hd79_world_mount_present(creature *owner,unsigned id,const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    ctag *tag;
    (void)r;
    if(owner!=bound_owner||!bound_mount||id!=bound_id||!owner->parent_rom)return 0;
    for(tag=owner->parent_rom->first_mon;tag;tag=tag->next_tag)
      if(tag->crt==bound_mount &&p->room[id-1]==(unsigned)owner->rom_num)return 1;
    return 0;
}
void hd79_world_mount_unbind_creature(const creature *mount)
{
    if(mount==bound_mount)bound_mount=bound_owner=0;
}
