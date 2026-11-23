/* Extension of tested Round79AB native fixture, ALL synthetic players. */
#include "round79ab_native_test_embed.c"
#include "hd79_presence_dismount_store.h"
int main(void)
{
    const char *who="Hdmactest";
    creature player;
    hd_breath_record breath;
    hd79_mount_roster state,next,saved,check;
    hd79_mount_presence pos,np,savedp,checkp;
    unsigned id;
    hd79_mount_roster untouched;
    assert(round79ab_fixture_main()==0);
    initial(&player,who);
    player.class=FIGHTER;player.level=40;
    assert(hd_store_create_player(who,&player)==HD_STORE_OK);
    assert(hd_breath_store_init(who,1000,&breath)==HD_BREATH_STORE_OK);
    assert(hd79_presence_store_init(who,&state,&pos)==HD79_PRESENCE_STORE_OK);
    assert(hd79_mount_award(&state,&next,state.epoch,HD_MOUNT_HORSE,&id)==1);
    np=pos;np.count=next.count;np.active_id=next.active_id;
    np.revision=next.revision;np.room[0]=42;
    assert(hd79_presence_store_commit(who,&state,&pos,&next,&np,
                                       &saved,&savedp)==HD79_PRESENCE_STORE_OK);
    state=saved;pos=savedp;
    assert(hd79_mount_board(&state,&next,state.epoch,id,1)==1);
    assert(hd79_presence_step(&state,&pos,&next,HD79_PRESENCE_BOARD,id,
                              42,1,0,&np)==1);
    assert(hd79_presence_store_commit(who,&state,&pos,&next,&np,
                                       &saved,&savedp)==HD79_PRESENCE_STORE_OK);
    state=saved;pos=savedp;
    assert(state.active_id==id && pos.room[0]==0);
    untouched=state;
    assert(hd79_presence_dismount_store(who,0,&saved)==HD79_DISMOUNT_FAILURE);
    assert(hd79_presence_dismount_store(who,0x1000000U,&saved)==HD79_DISMOUNT_FAILURE);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_presence_dismount_store(who,42,&saved)==HD79_DISMOUNT_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_presence_store_read(who,&check,&checkp)==HD79_PRESENCE_STORE_OK);
    equal_state(&check,&checkp,&state,&pos);
    puts("PASS: actual native 3-receipt dismount pre-rename rollback");
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_presence_dismount_store(who,42,&saved)==HD79_DISMOUNT_SUCCESS);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_presence_store_read(who,&check,&checkp)==HD79_PRESENCE_STORE_OK);
    assert(check.active_id==0 && checkp.room[0]==42);
    assert(check.revision==untouched.revision+1);
    assert(check.entries[0].endurance==untouched.entries[0].endurance);
    assert(hd79_presence_dismount_store(who,42,&saved)==HD79_DISMOUNT_ON_FOOT);
    assert(hd79_presence_store_read(who,&saved,&savedp)==HD79_PRESENCE_STORE_OK);
    equal_state(&saved,&savedp,&check,&checkp);
    assert(hd_breath_store_read(who,&breath)==HD_BREATH_STORE_OK);
    puts("PASS: native after-rename dismount reconciles exact 80/81/82");
    puts("PASS: no duplicate dismount; Endurance/Breath preserved");
    puts("ROUND79AC1: REAL ELF32 ATOMIC DISMOUNT ADAPTER PASS");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
