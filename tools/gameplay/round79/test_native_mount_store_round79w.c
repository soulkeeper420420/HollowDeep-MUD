/* Round79W: actual ELF32 native PLAYERPATH + atomic snapshot regression.
 * Runs ONLY in synthetic disposable world/player created by private runner.
 * Does not register movement, mount commands or any live world interaction.
 */
#define main legacy_main
#include "test_pet_store.c"
#undef main
#include "hd_breath_store.h"
#include "hd79_mount_store.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MT_A "ffffffffffffffffffffffffffffff80"
#define MT_B "ffffffffffffffffffffffffffffff81"

static void same(const hd79_mount_roster *a,const hd79_mount_roster *b)
{
    char a1[65],a2[65],b1[65],b2[65];
    assert(hd79_mount_wire_encode(a,a1,a2)==0);
    assert(hd79_mount_wire_encode(b,b1,b2)==0);
    assert(!strcmp(a1,b1) && !strcmp(a2,b2));
}
int main(void)
{
    const char *who="Hdmtwtest";
    char *seed[]={0,"seed",NULL};
    hd_breath_record breath,second_breath;
    hd79_mount_roster current,readback,next,committed,stale,untouched;
    creature person,*loaded=NULL;
    hd_pet_state undead;
    unsigned id;

    /* Reuse the verified pet-store fixture's private synthetic world. */
    assert(legacy_main(2,seed)==0);
    initial(&person,who);
    person.class=FIGHTER;
    person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,1000,&breath)==HD_BREATH_STORE_OK);

    memset(&readback,0x5a,sizeof readback);
    untouched=readback;
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_ABSENT);
    assert(!memcmp(&readback,&untouched,sizeof readback));
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_mount_store_init(who,&current)==HD79_MOUNT_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_ABSENT);
    puts("PASS: failed initialization leaves no partial mount receipt");

    assert(hd79_mount_store_init(who,&current)==HD79_MOUNT_STORE_OK);
    assert(current.count==0 && current.revision==1);
    assert(!strcmp(current.epoch,breath.epoch));
    assert(hd79_mount_store_init(who,&readback)==HD79_MOUNT_STORE_CONFLICT);
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&current,&readback);
    assert(hd_store_save_claim(who,&person,MT_A,digest)==HD_STORE_FAILURE);
    assert(hd_store_save_claim(who,&person,MT_B,digest)==HD_STORE_FAILURE);
    puts("PASS: paired receipt initialization and both reserved claim IDs");

    stale=current;
    assert(hd79_mount_award(&current,&next,current.epoch,
                             HD_MOUNT_HORSE,&id)==1 && id==1);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_OK);
    current=committed;
    assert(hd79_mount_store_commit(who,&stale,&next,&readback)
           ==HD79_MOUNT_STORE_CONFLICT);
    assert(hd79_mount_board(&current,&next,current.epoch,id,1)==1);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_OK);
    current=committed;
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&current,&readback);
    assert(readback.active_id==id);
    puts("PASS: award, mount, persistent one-rider state, stale CAS denial");

    /* Ordinary saves must preserve BOTH receipt fragments. */
    assert(hd_store_load_player(who,&loaded)==HD_STORE_OK && loaded);
    loaded->gold=4321;
    assert(hd_store_save_live_player(who,loaded)==HD_STORE_OK);
    free_crt(loaded);
    loaded=NULL;
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&current,&readback);
    assert(hd_breath_store_read(who,&second_breath)==HD_BREATH_STORE_OK);
    assert(!strcmp(second_breath.epoch,breath.epoch));
    puts("PASS: ordinary native save preserves both mounts and Breath");

    assert(hd79_mount_stable(&current,&next,current.epoch,id,42,1,1)==1);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&current,&readback);

    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&next,&readback);
    assert(readback.active_id==0 && readback.entries[0].stabled==1);
    assert(readback.entries[0].stable_room==42);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_CONFLICT);
    current=readback;
    puts("PASS: before-rename rollback; after-rename uncertainty reconciled");

    assert(hd79_mount_retrieve(&current,&next,current.epoch,id,42,1)==1);
    assert(hd79_mount_store_commit(who,&current,&next,&committed)
           ==HD79_MOUNT_STORE_OK);
    current=committed;
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_OK);
    same(&current,&readback);
    puts("PASS: same-stable retrieval persists without Endurance refill");

    /* Preserve private Necromancer pet data in independent fixture player. */
    assert(hd_store_load_player(name,&loaded)==HD_STORE_OK && loaded);
    loaded->level=10;
    assert(hd_store_save_live_player(name,loaded)==HD_STORE_OK);
    free_crt(loaded);
    loaded=NULL;
    assert(hd_breath_store_init(name,2500,&second_breath)
           ==HD_BREATH_STORE_OK);
    assert(hd79_mount_store_init(name,&readback)==HD79_MOUNT_STORE_OK);
    assert(hd_pet_store_read(name,&undead)==HD_PET_OK);
    puts("PASS: existing undead pet receipt retained in same snapshot");

    /* Re-creation under same character name must not inherit old mounts. */
    stale=current;
    assert(unlink("player/Hdmtwtest")==0);
    initial(&person,who);
    person.class=FIGHTER;
    person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,3000,&second_breath)
           ==HD_BREATH_STORE_OK);
    assert(strcmp(stale.epoch,second_breath.epoch));
    assert(hd79_mount_store_read(who,&readback)==HD79_MOUNT_STORE_ABSENT);
    assert(hd79_mount_board(&stale,&next,stale.epoch,id,1)==1);
    assert(hd79_mount_store_commit(who,&stale,&next,&committed)
           ==HD79_MOUNT_STORE_CONFLICT);
    puts("PASS: recycled name cannot replay old mount ownership epoch");

    puts("ROUND79W: PRIVATE ELF32 NATIVE ATOMIC MOUNT RECEIPT PASS");
    puts("MOUNT COMMANDS / RIDDEN MOVEMENT: NOT YET CONNECTED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
