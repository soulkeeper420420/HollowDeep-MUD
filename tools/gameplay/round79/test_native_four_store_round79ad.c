/* Round79AD R3: real native compressed PLAYERPATH four-claim save on a
 * disposable test player's fixture. Never operate on a live player. */
#define main hd79_ad_legacy_test_main
#include "test_pet_store.c"
#undef main
#include "hd_breath_store.h"
#include "hd79_mount_store.h"
#include "hd79_mount_presence_store.h"
#include "hd79_ad_four_store.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void canonical_equal(const hd79_mount_roster *a,
                             const hd79_mount_presence *ap,
                             const hd79_ad_death_receipt *ad,
                             const hd79_mount_roster *b,
                             const hd79_mount_presence *bp,
                             const hd79_ad_death_receipt *bd)
{
    char a0[65],a1[65],a2[65],a3[65];
    char b0[65],b1[65],b2[65],b3[65];
    assert(!hd79_mount_wire_encode(a,a0,a1));
    assert(!hd79_mount_wire_encode(b,b0,b1));
    assert(!hd79_presence_encode(a,ap,a2));
    assert(!hd79_presence_encode(b,bp,b2));
    assert(!hd79_ad_death_wire_encode(a,ad,a3));
    assert(!hd79_ad_death_wire_encode(b,bd,b3));
    assert(!strcmp(a0,b0)&&!strcmp(a1,b1)&&
           !strcmp(a2,b2)&&!strcmp(a3,b3));
}
int main(void)
{
    const char *who="Hdadfour";
    char *seed[]={0,"seed",NULL};
    creature person,*loaded=NULL;
    hd_breath_record breath,read_breath;
    hd79_mount_roster r,ro,old,got;
    hd79_mount_presence p,po,oldp,gotp;
    hd79_ad_death_receipt d,doo,oldd,gotd;
    int result;
    assert(hd79_ad_legacy_test_main(2,seed)==0);
    initial(&person,who);
    person.class=FIGHTER;person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,1000,&breath)==HD_BREATH_STORE_OK);

    memset(&r,0x5a,sizeof r);memset(&p,0x5a,sizeof p);
    memset(&d,0x5a,sizeof d);
    ro=r;po=p;doo=d;
    assert(hd79_ad_four_store_read(who,&r,&p,&d)==HD79_AD_FOUR_ABSENT);
    assert(!memcmp(&r,&ro,sizeof r)&&!memcmp(&p,&po,sizeof p)&&
           !memcmp(&d,&doo,sizeof d));
    assert(hd79_presence_store_init(who,&r,&p)==HD79_PRESENCE_STORE_FAILURE);
    assert(hd79_mount_store_init(who,&r)==HD79_MOUNT_STORE_FAILURE);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    result=hd79_ad_four_store_init_empty(who,&r,&p,&d);
    assert(result==HD79_AD_FOUR_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_ad_four_store_read(who,&r,&p,&d)==HD79_AD_FOUR_ABSENT);
    puts("PASS: old two/three writers denied; four-way failed init leaves no claims");

    assert(hd79_ad_four_store_init_empty(who,&r,&p,&d)==HD79_AD_FOUR_OK);
    assert(!strcmp(r.epoch,breath.epoch)&&!r.count&&!d.dead_mask&&d.serial==1);
    assert(hd79_ad_four_store_init_empty(who,&ro,&po,&doo)==HD79_AD_FOUR_CONFLICT);
    assert(hd79_ad_four_store_read(who,&ro,&po,&doo)==HD79_AD_FOUR_OK);
    canonical_equal(&r,&p,&d,&ro,&po,&doo);
    assert(hd_store_save_claim(who,&person,HD79_AD_DEATH_RECEIPT_ID,digest)==
           HD_STORE_FAILURE);
    puts("PASS: authentic epoch creates all four claims atomically; reserved #83 blocked for loot");

    /* Test-only award is ABSENT from the full game build. This synthetic
     * fixture generates one authenticated-looking location for death tests. */
    old=r;oldp=p;oldd=d;
    assert(hd79_ad_four_store_test_award(who,&r,&p,&d,HD_MOUNT_HORSE,
                                         42,&ro,&po,&doo)==HD79_AD_FOUR_OK);
    r=ro;p=po;d=doo;
    assert(r.count==1 && p.room[0]==42 && d.count==1 && d.serial==2);
    assert(hd79_ad_four_store_test_award(who,&old,&oldp,&oldd,
                                         HD_MOUNT_WARHORSE,42,
                                         &ro,&po,&doo)==HD79_AD_FOUR_CONFLICT);
    assert(hd79_presence_store_commit(who,&old,&oldp,&r,&p,
                                      &ro,&po)==HD79_PRESENCE_STORE_FAILURE);
    assert(hd79_ad_four_store_read(who,&ro,&po,&doo)==HD79_AD_FOUR_OK);
    canonical_equal(&r,&p,&d,&ro,&po,&doo);
    puts("PASS: test-only award, exact 4-receipt CAS and stale legacy-write denial");

    /* A write failure must preserve every receipt and the owner epoch. */
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_ad_four_store_mark_dead(who,&r,&p,&d,1,&gotd)==
           HD79_AD_FOUR_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_ad_four_store_read(who,&got,&gotp,&gotd)==HD79_AD_FOUR_OK);
    canonical_equal(&r,&p,&d,&got,&gotp,&gotd);
    assert(hd79_ad_death_action_eligible(&r,&gotd,1)==1);
    puts("PASS: native before-rename mount death preserves all 4 receipts");

    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_ad_four_store_mark_dead(who,&r,&p,&d,1,&gotd)==
           HD79_AD_FOUR_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_ad_four_store_read(who,&got,&gotp,&gotd)==HD79_AD_FOUR_OK);
    assert(gotd.dead_mask==1 && gotd.serial==3 &&
           hd79_ad_death_action_eligible(&got,&gotd,1)==0);
    assert(hd79_ad_death_reconnect_allowed(&got,&gotd,1)==0);
    assert(hd79_ad_four_store_mark_dead(who,&r,&p,&d,1,&doo)==
           HD79_AD_FOUR_CONFLICT);
    assert(hd79_ad_four_store_mark_dead(who,&got,&gotp,&gotd,1,&doo)==
           HD79_AD_FOUR_CONFLICT);
    puts("PASS: native after-rename death reconciles exact #83; no replay or resurrection");

    /* The ordinary player save must retain all four receipts, Breath,
     * other native inventory and standard player values. */
    assert(hd_store_load_player(who,&loaded)==HD_STORE_OK && loaded);
    loaded->gold=4321;
    assert(hd_store_save_live_player(who,loaded)==HD_STORE_OK);
    free_crt(loaded);loaded=NULL;
    assert(hd79_ad_four_store_read(who,&ro,&po,&doo)==HD79_AD_FOUR_OK);
    canonical_equal(&got,&gotp,&gotd,&ro,&po,&doo);
    assert(hd_breath_store_read(who,&read_breath)==HD_BREATH_STORE_OK);
    assert(!strcmp(read_breath.epoch,breath.epoch));
    puts("PASS: ordinary native character save preserves death tombstone, roster, location and Breath");

    /* Recreated same-name character receives a fresh Breath epoch.
     * Stale prior receipts must never be copied or reused. */
    assert(unlink("player/Hdadfour")==0);
    initial(&person,who);person.class=FIGHTER;person.level=40;
    assert(hd_store_create_player(who,&person)==HD_STORE_OK);
    assert(hd_breath_store_init(who,3000,&read_breath)==HD_BREATH_STORE_OK);
    assert(strcmp(read_breath.epoch,breath.epoch));
    assert(hd79_ad_four_store_mark_dead(who,&got,&gotp,&gotd,1,&doo)==
           HD79_AD_FOUR_CONFLICT);
    assert(hd79_ad_four_store_read(who,&ro,&po,&doo)==HD79_AD_FOUR_ABSENT);
    puts("PASS: recreated same-name owner cannot replay old epoch death receipt");

    puts("ROUND79AD R3: PRIVATE NATIVE FOUR-RECEIPT PLAYER STORE PASS");
    puts("COMBAT DEATH HOOK, LOGIN REHYDRATION, BOARD/STABLE/MOVE: DISABLED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
