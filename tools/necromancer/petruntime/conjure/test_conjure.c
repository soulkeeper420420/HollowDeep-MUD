#define main legacy_main
#include "test_pet_store.c"
#undef main
#include "hd_conjure.h"

#define APPLY(old,action,time,a,b,out) \
    hd_conjure_store_apply(who,old,action,time,a,b,out)

int main(void)
{
    const char *who="Hdconjq";
    const char *reserved="ffffffffffffffffffffffffffffff77";
    creature p,*loaded=NULL;
    hd_conjure_state a,b,c,old;
    hd_pet_state undead;
    unsigned gain1,gain2,i;
    uint32_t last=0;
    char *seed[]={0,"seed",NULL};

    for(i=1;i<=6;++i)
        assert(hd_conjure_get(i));

    assert(hd_conjure_threshold(10)==8100);
    assert(hd_conjure_threshold(60)==348100);

    assert(hd_conjure_drain(21,500,500,100,100,
                            100,&last,&gain1,&gain2)==0);

    assert(hd_conjure_drain(20,500,500,100,100,
                            100,&last,&gain1,&gain2)==50);
    assert(gain1==25 && gain2==25);

    assert(hd_conjure_drain(1,500,500,100,100,
                            102,&last,&gain1,&gain2)==0);

    assert(hd_conjure_drain(1,40,500,5,100,
                            103,&last,&gain1,&gain2)==40);
    assert(gain1==5 && gain2==20);

    puts("PASS: 20 percent mana drain and three-second cooldown");

    assert(legacy_main(2,seed)==0);

    initial(&p,who);
    p.class=FIGHTER;
    p.level=40;

    assert(hd_store_create_player(who,&p)==HD_STORE_OK);

    assert(hd_store_save_claim(who,&p,reserved,digest)
           ==HD_STORE_FAILURE);

    assert(hd_conjure_store_read(who,&a)==HD_PET_ABSENT);

    assert(APPLY(NULL,HD_CJ_INIT,0,0,0,&a)==HD_PET_OK);

    assert(APPLY(&a,HD_CJ_SUMMON,1000,6,0,&b)==HD_PET_ERROR);

    assert(APPLY(&a,HD_CJ_SUMMON,1000,5,0,&b)==HD_PET_OK);

    a=b;
    assert(a.active && a.species==5 && a.level==1);

    assert(APPLY(&a,HD_CJ_SUMMON,1300,1,0,&b)==HD_PET_ERROR);

    assert(APPLY(&a,HD_CJ_XP,1001,8100,0,&b)==HD_PET_OK);

    assert(b.level==10 && b.xp==8100);

    assert(APPLY(&a,HD_CJ_XP,1001,8100,0,&c)==HD_PET_CONFLICT);

    a=b;
    assert(APPLY(&a,HD_CJ_DISMISS,1002,0,0,&b)==HD_PET_OK);

    a=b;
    assert(!a.active && a.level==10 && a.xp==8100);
    assert(APPLY(&a,HD_CJ_RECALL,1299,0,0,&b)==HD_PET_ERROR);
    assert(APPLY(&a,HD_CJ_RECALL,1300,0,0,&b)==HD_PET_OK);

    puts("PASS: Fighter conjure, level gates, one companion, 300s timer");

    a=b;

    assert(hd_store_load_player(who,&loaded)==0);
    loaded->gold=4321;
    assert(hd_store_save_live_player(who,loaded)==0);
    free_crt(loaded);

    assert(hd_conjure_store_read(who,&b)==0);
    assert(b.xp==8100 && b.level==10 && b.active);

    {
        pid_t child=fork();
        int status;
        assert(child>=0);

        if(!child) {
            hd_conjure_state fresh;
            assert(hd_conjure_store_read(who,&fresh)==0);
            assert(fresh.level==10 && fresh.xp==8100);
            _exit(0);
        }

        assert(waitpid(child,&status,0)==child);
        assert(WIFEXITED(status) && WEXITSTATUS(status)==0);
    }

    puts("PASS: persistent pet XP, level and ordinary character saves");

    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(APPLY(&a,HD_CJ_XP,1301,100,0,&b)==HD_PET_ERROR);
    unsetenv("HD_ATOMIC_FAIL");

    assert(hd_conjure_store_read(who,&b)==0);
    assert(b.xp==8100 && b.revision==a.revision);

    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(APPLY(&a,HD_CJ_XP,1301,100,0,&b)==HD_PET_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");

    assert(hd_conjure_store_read(who,&c)==0);
    assert(c.xp==8200);

    assert(APPLY(&a,HD_CJ_XP,1301,100,0,&b)==HD_PET_CONFLICT);

    a=c;
    old=a;

    assert(APPLY(&a,HD_CJ_DEATH,1302,0,0,&b)==HD_PET_OK);
    assert(!b.species && !b.level && !b.xp && !b.active);

    assert(APPLY(&old,HD_CJ_XP,1303,100,0,&c)==HD_PET_CONFLICT);

    a=b;
    assert(APPLY(&a,HD_CJ_SUMMON,1599,1,0,&b)==HD_PET_ERROR);
    assert(APPLY(&a,HD_CJ_SUMMON,1600,1,0,&b)==HD_PET_OK);
    assert(b.level==1 && !b.xp);

    puts("PASS: atomic failures, stale writes and permanent pet death");

    assert(hd_store_load_player(who,&loaded)==0);
    assert(loaded->gold==4321);
    free_crt(loaded);

    assert(hd_store_load_player(name,&loaded)==0);
    loaded->level=10;
    assert(hd_store_save_live_player(name,loaded)==0);
    free_crt(loaded);

    assert(hd_conjure_store_apply(name,NULL,HD_CJ_INIT,
                                  0,0,0,&a)==HD_PET_OK);

    assert(hd_conjure_store_apply(name,&a,HD_CJ_SUMMON,
                                  1000,2,0,&c)==HD_PET_OK);

    assert(hd_pet_store_read(name,&undead)==HD_PET_OK);
    assert(undead.revision==1 && !undead.hpcur);

    puts("PASS: Necromancer and Conjure records are independent");

    assert(unlink("player/Hdconjq")==0);
    initial(&p,who);
    p.class=FIGHTER;
    p.level=40;
    assert(hd_store_create_player(who,&p)==HD_STORE_OK);

    assert(APPLY(NULL,HD_CJ_INIT,0,0,0,&a)==HD_PET_OK);
    assert(strcmp(a.epoch,b.epoch));

    assert(APPLY(&b,HD_CJ_DEATH,1700,0,0,&c)==HD_PET_CONFLICT);

    puts("PASS: deleted character cannot reclaim old companion");
    puts("ROUND 75B: NATIVE CONJURE STORAGE PASS");

    return 0;
}
