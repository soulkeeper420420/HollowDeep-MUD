/* Exact registry identity tests, compiled with the real staged registry and
 * a synthetic native-model boundary. Does not write a player/world file. */
#include "hd_player_store.h"
#include "hd79_mount_world_identity.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
extern int hd79_ad_death_identity(creature *,creature **,unsigned *,char [25]);
int main(void)
{
    creature owner={0},mount={0},forged={0};
    creature *got=NULL;
    unsigned id=0;
    char epoch[25]={0};
    room world={0};
    ctag player_tag={0},monster_tag={0},duplicate={0};
    hd79_mount_roster r;
    hd79_mount_presence p;
    assert(hd79_mount_roster_new(&r,"1234567890abcdef12345678")==1);
    assert(hd79_mount_award(&r,&r,r.epoch,HD_MOUNT_HORSE,&id)==1);
    memset(&p,0,sizeof p);p.count=r.count;p.revision=r.revision;p.room[0]=42;
    strcpy(owner.name,"SyntheticOwner");owner.type=PLAYER;owner.hpcur=100;
    mount.type=MONSTER;mount.hpcur=mount.hpmax=80;
    world.rom_num=42;world.first_ply=&player_tag;world.first_mon=&monster_tag;
    player_tag.crt=&owner;monster_tag.crt=&mount;
    owner.parent_rom=mount.parent_rom=&world;owner.rom_num=mount.rom_num=42;
    assert(hd79_world_mount_bind(&owner,&mount,1,&r,&p)==1);
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==0);
    mount.hpcur=0;
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==1);
    assert(got==&owner && id==1 && !strcmp(epoch,r.epoch));
    owner.hpcur=0;
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==1);
    puts("PASS: exact native death identity survives simultaneous owner death");
    forged=mount;
    assert(hd79_ad_death_identity(&forged,&got,&id,epoch)==0);
    duplicate.crt=&owner;player_tag.next_tag=&duplicate;
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==0);
    player_tag.next_tag=NULL;
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==1);
    hd79_world_mount_unbind_owner(&owner);
    assert(hd79_ad_death_identity(&mount,&got,&id,epoch)==0);
    puts("PASS: forged pointers, duplicated membership and revoked owner denied");
    return 0;
}
