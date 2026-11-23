/* Round79AC3C: exact ELF32 trusted template spawn backend mocks. */
#include "ac3c-mock/hd_player_store.h"
#include "ac3c-mock/mextern.h"
#include "hd79_mount_trusted_spawn.h"
#include "hd79_mount_world_identity.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define EPOCH "1234567890abcdef12345678"
static hd79_mount_roster saved,next;
static hd79_mount_presence position;
static room world={42,0,0};
static creature owner={"Player",PLAYER,100,100,42,&world,0,0,0};
static ctag owner_tag={0,&owner},monster_tag={0,0};
static unsigned loads,adds,deletes,frees,reads;
static int fake_type=MONSTER,broken_add,fail_load,invalid_save;
static creature *created;
static hd79_trusted_mount_catalog whitelist={{101,102,103,104,105,106}};

int hd79_presence_store_read(const char *name,hd79_mount_roster *roster,
                             hd79_mount_presence *location)
{
    reads++;
    if(invalid_save||strcmp(name,"Player"))return HD79_PRESENCE_STORE_FAILURE;
    *roster=saved;*location=position;
    return HD79_PRESENCE_STORE_OK;
}
int load_crt(int idx,creature **out)
{
    creature *crt;
    loads++;
    if(fail_load || idx!=101) return -1;
    crt=(creature*)calloc(1,sizeof *crt);
    assert(crt);
    memcpy(crt->name,"horse",6);
    crt->type=fake_type;
    crt->hpmax=100;crt->hpcur=100;
    created=crt;*out=crt;
    return 0;
}
void add_crt_rom(creature *crt,room *r,int count)
{
    assert(count==0);
    adds++;
    hd79_world_mount_unbind_creature(crt); /* AC3B hook */
    crt->parent_rom=r;crt->rom_num=r->rom_num;
    if(!broken_add){monster_tag.crt=crt;r->first_mon=&monster_tag;}
}
void del_crt_rom(creature *crt,room *r)
{
    deletes++;
    hd79_world_mount_unbind_creature(crt); /* AC3B hook */
    if(r->first_mon && r->first_mon->crt==crt)r->first_mon=0;
    crt->parent_rom=0;crt->rom_num=0;
}
void free_crt(creature *crt)
{
    frees++;
    hd79_world_mount_unbind_creature(crt);
    free(crt);created=0;
}
int main(void)
{
    creature *out=(creature*)0x1,*mounted;
    unsigned id=0;
    assert(hd79_mount_roster_new(&saved,EPOCH)==1);
    assert(hd79_mount_award(&saved,&next,EPOCH,HD_MOUNT_HORSE,&id)==1);
    saved=next;
    memset(&position,0,sizeof position);
    position.revision=saved.revision;
    position.count=saved.count;
    position.room[0]=42;
    assert(hd79_presence_valid(&saved,&position));
    world.first_ply=&owner_tag;
    assert(hd79_mount_spawn_trusted(&owner,0,&whitelist,&out)==0);
    assert(hd79_mount_spawn_trusted(&owner,1,0,&out)==0);
    assert(out==(creature*)0x1 && reads==0 && loads==0);
    puts("PASS: missing catalog and invalid ID denied without save read");

    whitelist.native_template_id[0]=0;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    whitelist.native_template_id[0]=101;
    whitelist.native_template_id[1]=101;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    whitelist.native_template_id[1]=102;
    assert(loads==0);
    invalid_save=1;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    invalid_save=0;
    world.first_ply=0;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    world.first_ply=&owner_tag;
    owner.rom_num=43;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    owner.rom_num=42;
    assert(loads==0 && adds==0);
    puts("PASS: invalid whitelist/save/owner live room fail closed");

    fail_load=1;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==-1);
    fail_load=0;
    fake_type=PLAYER;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    assert(frees==1 && adds==0 && out==(creature*)0x1);
    fake_type=MONSTER;
    puts("PASS: failed native template and non-monster load cannot spawn");

    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==1);
    assert(out==created && world.first_mon && world.first_mon->crt==out);
    assert(hd79_world_mount_present(&owner,1,&saved,&position));
    mounted=out;out=(creature*)0x1;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==0);
    assert(out==(creature*)0x1 && adds==1);
    puts("PASS: trusted native load, exact room insertion, ownership binding, no duplication");
    del_crt_rom(mounted,&world);free_crt(mounted);
    assert(!hd79_world_mount_present(&owner,1,&saved,&position));
    out=(creature*)0x1;
    broken_add=1;
    assert(hd79_mount_spawn_trusted(&owner,1,&whitelist,&out)==-1);
    assert(deletes==1 || deletes==2);
    assert(world.first_mon==0 && out==(creature*)0x1);
    broken_add=0;
    puts("PASS: native bind failure rolls back creature allocation and state");

    assert(loads==4 && adds==2 && frees==3);
    puts("ROUND79AC3C: PRIVATE TRUSTED NATIVE SPAWN BACKEND PASS");
    puts("BOARD/STABLE/RETRIEVE AND PUBLIC SPAWN: NOT ENABLED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
