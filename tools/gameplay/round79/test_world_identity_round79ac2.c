/* Round79AC2 explicit live-room + process binding; no actual native spawn. */
#include "ac2-mock/mextern.h"
#include "hd79_mount_world_identity.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define EPOCH "1234567890abcdef12345678"
static hd79_mount_roster roster,next;
static hd79_mount_presence location;
static room world={42,0,0};
static creature owner={"Player",PLAYER,100,100,42,&world};
static creature impostor={"horse",MONSTER,100,100,42,&world};
static creature horse={"horse",MONSTER,100,100,42,&world};
static creature other={"Player",PLAYER,100,100,42,&world};
static ctag tag_horse={0,&horse};
static ctag tag_player={0,&owner};

int main(void)
{
    unsigned id=0;
    assert(hd79_mount_roster_new(&roster,EPOCH)==1);
    assert(hd79_mount_award(&roster,&next,EPOCH,HD_MOUNT_HORSE,&id)==1);
    roster=next;
    assert(id==1);
    memset(&location,0,sizeof location);
    location.revision=roster.revision;
    location.count=1;
    location.room[0]=42;
    assert(hd79_presence_valid(&roster,&location));
    world.first_mon=&tag_horse;
    world.first_ply=&tag_player;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==1);
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==0);
    assert(hd79_world_mount_bind(&other,&horse,1,&roster,&location)==0);
    assert(hd79_world_mount_present(&other,1,&roster,&location)==0);
    puts("PASS: explicit trusted registration, duplicate/foreign owner rejected");

    /* Exactly one monster in native room; an equal-name NPC isn't enough. */
    tag_horse.crt=&impostor;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    tag_horse.crt=&horse;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    horse.parent_rom=NULL;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    horse.parent_rom=&world;
    horse.hpcur=0;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    horse.hpcur=100;
    puts("PASS: renamed/copied monster, dead/detached monster denied");

    location.room[0]=43;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    location.room[0]=42;
    owner.rom_num=43;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    owner.rom_num=42;
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    roster.epoch[0]='0';
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    roster.epoch[0]='1';
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    puts("PASS: remote room and wrong character epoch fail closed");

    /* Monster removal and logout must clear the runtime token. */
    hd79_world_mount_unbind_creature(&impostor);
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    hd79_world_mount_unbind_creature(&horse);
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==1);
    hd79_world_mount_unbind_owner(&owner);
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==0);
    puts("PASS: explicit removal/logout invalidates attestation");

    /* Physical monster list and player membership both required. */
    world.first_ply=NULL;
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==0);
    world.first_ply=&tag_player;
    world.first_mon=NULL;
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==0);
    world.first_mon=&tag_horse;
    assert(hd79_world_mount_bind(&owner,&horse,1,&roster,&location)==1);
    assert(hd79_world_mount_present(&owner,1,&roster,&location)==1);
    puts("PASS: native room membership required for registration and verification");

    printf("ROUND79AC2: PRIVATE NATIVE MOUNT WORLD IDENTITY PASS\n");
    printf("GAMEPLAY BOARD/STABLE/RETRIEVE: NOT ENABLED\n");
    printf("PRODUCTION DEPLOYMENT: NONE\n");
    return 0;
}
