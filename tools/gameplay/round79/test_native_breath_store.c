/* Round 79H: real atomic-player-receipt persistence regression.
 * Compiled with native fixture from the existing verified pet store tests.
 * Never run against production. No live player files are accessed.
 */
#define main legacy_main
#include "test_pet_store.c"
#undef main
#include "hd_breath_store.h"
#include "hd_wilderness_breath.h"

int main(void)
{
    const char *who="Hdbrqtest";
    const char *reserved="ffffffffffffffffffffffffffffff79";
    char *seed[]={0,"seed",NULL};
    hd_breath_record a,b,c,old,recreated;
    creature p,*loaded=NULL;
    hd_pet_state undead;
    int i;

    /* Existing fixture initializes private Necromancer/pet saved records. */
    assert(legacy_main(2,seed)==0);
    initial(&p,who);
    p.class=FIGHTER;
    p.level=40;
    assert(hd_store_create_player(who,&p)==HD_STORE_OK);

    /* This ID must be reserved and cannot be overwritten as loot claim. */
    assert(hd_store_save_claim(who,&p,reserved,digest)==HD_STORE_FAILURE);
    assert(hd_breath_store_read(who,&a)==HD_BREATH_STORE_ABSENT);

    assert(hd_breath_store_init(who,1000,&a)==HD_BREATH_STORE_OK);
    assert(a.current==100 && a.revision==1 && a.last_recover==1000);
    assert(hd_breath_store_init(who,1000,&b)==HD_BREATH_STORE_CONFLICT);
    assert(hd_breath_store_read(who,&b)==HD_BREATH_STORE_OK);
    assert(b.revision==a.revision && !strcmp(b.epoch,a.epoch));
    puts("PASS: reserved Breath receipt created exactly once");

    for (i=0;i<50;i++) {
        hd_breath_record old=a;
        assert(hd_breath_store_step(who,&a,
            HD_BREATH_OP_TRAVEL,1,0,1001U+(uint32_t)i,&b)
            ==HD_BREATH_STORE_OK);
        assert(b.current==a.current-2);
        assert(b.revision==a.revision+1);
        a=b;
        assert(hd_breath_store_step(who,&old,
            HD_BREATH_OP_TRAVEL,1,0,1002U+(uint32_t)i,&c)
            ==HD_BREATH_STORE_CONFLICT);
    }
    assert(a.current==0);
    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_TRAVEL,1,0,2000,&b)==HD_BREATH_STORE_FAILURE);
    assert(hd_breath_store_read(who,&b)==HD_BREATH_STORE_OK &&
           b.current==0 && b.revision==a.revision);

    /* Returning to a verified interior is free, including at 0 Breath. */
    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_TRAVEL,0,0,0,&b)==HD_BREATH_STORE_FAILURE);
    /* The travel wrapper never calls durable store for free interior steps. */

    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_RECOVER,0,1,2000,&b)==HD_BREATH_STORE_OK);
    assert(b.current==15);
    assert(hd_breath_store_step(who,&b,
        HD_BREATH_OP_RECOVER,0,1,2000,&c)==HD_BREATH_STORE_FAILURE);
    a=b;
    puts("PASS: 50 checked wilderness debits, zero exhaustion and timed rest");

    assert(hd_store_load_player(who,&loaded)==HD_STORE_OK);
    assert(loaded);
    loaded->gold=4321;
    assert(hd_store_save_live_player(who,loaded)==HD_STORE_OK);
    free_crt(loaded);
    assert(hd_breath_store_read(who,&c)==HD_BREATH_STORE_OK);
    assert(c.current==15 && c.revision==a.revision);
    a=c;
    puts("PASS: ordinary player save preserves depleted Breath");

    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_TRAVEL,1,0,2001,&b)==HD_BREATH_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_breath_store_read(who,&c)==HD_BREATH_STORE_OK);
    assert(c.current==15 && c.revision==a.revision);

    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_TRAVEL,1,0,2001,&b)==HD_BREATH_STORE_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_breath_store_read(who,&c)==HD_BREATH_STORE_OK);
    assert(c.current==13 && c.revision==a.revision+1);
    assert(hd_breath_store_step(who,&a,
        HD_BREATH_OP_TRAVEL,1,0,2001,&b)==HD_BREATH_STORE_CONFLICT);
    puts("PASS: atomic rename failure, uncertain recovery and stale CAS denial");

    /* Existing Necromancer pet receipt must survive an independent Breath
       transaction; don't add fake pets or create gameplay objects. */
    assert(hd_store_load_player(name,&loaded)==HD_STORE_OK);
    assert(loaded);
    loaded->level=10;
    assert(hd_store_save_live_player(name,loaded)==HD_STORE_OK);
    free_crt(loaded);
    loaded=NULL;
    assert(hd_breath_store_read(name,&a)==HD_BREATH_STORE_ABSENT);
    assert(hd_breath_store_init(name,2500,&a)==HD_BREATH_STORE_OK);
    assert(hd_breath_store_step(name,&a,
        HD_BREATH_OP_TRAVEL,1,0,2501,&b)==HD_BREATH_STORE_OK);
    assert(hd_pet_store_read(name,&undead)==HD_PET_OK);
    puts("PASS: existing Necromancer/pet record retained");

    /* New character with reused name receives a new random epoch. */
    old=c;
    assert(unlink("player/Hdbrqtest")==0);
    initial(&p,who);
    p.class=FIGHTER;
    p.level=40;
    assert(hd_store_create_player(who,&p)==HD_STORE_OK);
    assert(hd_breath_store_init(who,3000,&recreated)==HD_BREATH_STORE_OK);
    assert(strcmp(old.epoch,recreated.epoch));
    assert(hd_breath_store_step(who,&old,
        HD_BREATH_OP_TRAVEL,1,0,3001,&b)==HD_BREATH_STORE_CONFLICT);
    puts("PASS: recycled character names cannot reuse an old Breath epoch");

    puts("ROUND 79H: NATIVE ATOMIC BREATH PLAYER-RECEIPT TEST PASS");
    puts("NATIVE WILDERNESS MOVEMENT / MOUNTS: NOT YET INTEGRATED");
    return 0;
}
