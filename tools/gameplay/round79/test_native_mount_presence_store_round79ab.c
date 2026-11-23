/* Round79AB: native PLAYERPATH atomic 80/81/82 tests on disposable fixture.
 * This is NOT a player command or an authorization source for world entities.
 */
#define main legacy_main
#include "test_pet_store.c"
#undef main
#include "hd_breath_store.h"
#include "hd79_mount_store.h"
#include "hd79_mount_presence_store.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void equal_state(const hd79_mount_roster *r,
                        const hd79_mount_presence *p,
                        const hd79_mount_roster *expect,
                        const hd79_mount_presence *pos)
{
    char a[65],b[65],c[65],ea[65],eb[65],ec[65];
    assert(hd79_mount_wire_encode(r,a,b)==0);
    assert(hd79_mount_wire_encode(expect,ea,eb)==0);
    assert(hd79_presence_encode(r,p,c)==0);
    assert(hd79_presence_encode(expect,pos,ec)==0);
    assert(!strcmp(a,ea) && !strcmp(b,eb) && !strcmp(c,ec));
}
int main(void)
{
    const char *who="Hdmtabtest";
    char *seed[]={0,"seed",NULL};
    creature person,*loaded=NULL;
    hd_breath_record breath,saved_breath;
    hd_pet_state undead;
    hd79_mount_roster r,next,read,old,saved;
    hd79_mount_presence p,np,read_p,old_p,saved_p;
    unsigned id;
    assert(legacy_main(2,seed)==0);
    initial(&person,who);
    person.class=FIGHTER; person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,1000,&breath)==HD_BREATH_STORE_OK);

    memset(&read,0x5a,sizeof read);
    memset(&read_p,0x5a,sizeof read_p);
    old=read;old_p=read_p;
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_ABSENT);
    assert(!memcmp(&old,&read,sizeof old));
    assert(!memcmp(&old_p,&read_p,sizeof old_p));
    assert(hd79_mount_store_init(who,&read)==HD79_MOUNT_STORE_FAILURE);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_presence_store_init(who,&r,&p)==
           HD79_PRESENCE_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_ABSENT);
    puts("PASS: failed triple init writes nothing; legacy pair init refused");

    assert(hd79_presence_store_init(who,&r,&p)==HD79_PRESENCE_STORE_OK);
    assert(r.count==0 && p.count==0 && r.revision==1);
    assert(!strcmp(r.epoch,breath.epoch));
    assert(hd79_presence_store_init(who,&read,&read_p)==
           HD79_PRESENCE_STORE_CONFLICT);
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    equal_state(&read,&read_p,&r,&p);
    assert(hd_store_save_claim(who,&person,
          HD79_MOUNT_PRESENCE_ID,digest)==HD_STORE_FAILURE);
    puts("PASS: three receipts created once; ID 82 reserved as non-loot");

    /* Synthetic world-authenticated ownership grant is staged only in
     * the fixture, not exposed to MUD commands. Source room = 42.
     */
    old=r; old_p=p;
    assert(hd79_mount_award(&r,&next,r.epoch,HD_MOUNT_HORSE,&id)==1);
    assert(id==1);
    np=p;np.count=next.count;np.active_id=next.active_id;
    np.revision=next.revision;np.room[0]=42;
    assert(hd79_presence_valid(&next,&np));
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
             &saved,&saved_p)==HD79_PRESENCE_STORE_OK);
    r=saved;p=saved_p;
    assert(hd79_mount_store_commit(who,&old,&next,&read)==
           HD79_MOUNT_STORE_FAILURE);
    assert(hd79_presence_store_commit(who,&old,&old_p,&next,&np,
             &read,&read_p)==HD79_PRESENCE_STORE_CONFLICT);
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    equal_state(&read,&read_p,&r,&p);
    puts("PASS: synthetic award location commits all 3; old pair writer and stale CAS denied");

    /* A verified physical mount in room 42 allows boarding. */
    assert(hd79_mount_board(&r,&next,r.epoch,id,1)==1);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_BOARD,
                             id,43,1,0,&np)==0);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_BOARD,
                             id,42,1,0,&np)==1);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_OK);
    r=saved;p=saved_p;
    assert(r.active_id==id && p.room[0]==0);
    puts("PASS: physically same-room boarding; remote boarding denied");

    /* Character's ordinary native save preserves all three fragments. */
    assert(hd_store_load_player(who,&loaded)==HD_STORE_OK && loaded);
    loaded->gold=4321;
    assert(hd_store_save_live_player(who,loaded)==HD_STORE_OK);
    free_crt(loaded);loaded=NULL;
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    equal_state(&read,&read_p,&r,&p);
    assert(hd_breath_store_read(who,&saved_breath)==HD_BREATH_STORE_OK);
    assert(!strcmp(saved_breath.epoch,breath.epoch));
    puts("PASS: normal player save preserves location, roster and Breath");

    assert(hd79_mount_dismount(&r,&next,r.epoch)==1);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_DISMOUNT,
                             id,42,0,0,&np)==1);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    equal_state(&read,&read_p,&r,&p);
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    equal_state(&read,&read_p,&next,&np);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_CONFLICT);
    r=read;p=read_p;
    assert(r.active_id==0 && p.room[0]==42);
    puts("PASS: before-rename atomic rollback; after-rename full 3-record uncertain recovery");

    assert(hd79_mount_stable(&r,&next,r.epoch,id,42,1,1)==1);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_STABLE,
                             id,42,1,1,&np)==1);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_OK);
    r=saved;p=saved_p;
    assert(r.entries[0].stabled==1 && p.room[0]==0);
    assert(hd79_mount_retrieve(&r,&next,r.epoch,id,42,1)==1);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_RETRIEVE,
                             id,43,0,1,&np)==0);
    assert(hd79_presence_step(&r,&p,&next,HD79_PRESENCE_RETRIEVE,
                             id,42,0,1,&np)==1);
    assert(hd79_presence_store_commit(who,&r,&p,&next,&np,
           &saved,&saved_p)==HD79_PRESENCE_STORE_OK);
    assert(saved.entries[0].endurance==r.entries[0].endurance);
    r=saved;p=saved_p;
    assert(p.room[0]==42 && r.entries[0].stabled==0);
    puts("PASS: stored stable location, remote retrieval denial and no Endurance refill");

    assert(hd_store_load_player(name,&loaded)==HD_STORE_OK && loaded);
    loaded->level=10;
    assert(hd_store_save_live_player(name,loaded)==HD_STORE_OK);
    free_crt(loaded);loaded=NULL;
    assert(hd_breath_store_init(name,2500,&saved_breath)==HD_BREATH_STORE_OK);
    assert(hd79_presence_store_init(name,&read,&read_p)==
           HD79_PRESENCE_STORE_OK);
    assert(hd_pet_store_read(name,&undead)==HD_PET_OK);
    puts("PASS: Necromancer/pet receipt preserved alongside three mount claims");

    old=r;old_p=p;
    assert(unlink("player/Hdmtabtest")==0);
    initial(&person,who); person.class=FIGHTER; person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,3000,&saved_breath)==HD_BREATH_STORE_OK);
    assert(strcmp(old.epoch,saved_breath.epoch));
    assert(hd79_presence_store_read(who,&read,&read_p)==
           HD79_PRESENCE_STORE_ABSENT);
    assert(hd79_mount_board(&old,&next,old.epoch,id,1)==1);
    assert(hd79_presence_step(&old,&old_p,&next,HD79_PRESENCE_BOARD,
                             id,42,1,0,&np)==1);
    assert(hd79_presence_store_commit(who,&old,&old_p,&next,&np,
           &read,&read_p)==HD79_PRESENCE_STORE_CONFLICT);
    puts("PASS: same-name new character cannot reuse old triple owner epoch");
    puts("ROUND79AB: NATIVE THREE-RECEIPT ATOMIC PLAYER SAVE PASS");
    puts("NATIVE PRESENCE ENTITY, BOARD, STABLE, RETRIEVE, TRAVEL: DISABLED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
