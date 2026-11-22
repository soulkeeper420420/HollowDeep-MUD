/* Round79K: stage-specific real native atomic pre-transfer movement policy.
 * Uses the synthetic native player-store fixture, not production data.
 * The native move()/go() command code is compiled separately with the
 * full private MUD; this fixture checks the precommit ordering contract.
 */
#define main legacy_main
#include "test_pet_store.c"
#undef main

#include "hd79_breath_travel_runtime.h"
#include "hd_breath_store.h"
#include "hd_breath_move_checkpoint.h"
#include <time.h>

int hd79_wilderness_tile(int id)
{
    if (id>=10000 && id<=10003) return 1;
    if (id>=10000) return -1;
    return 0;
}

static void expect_disk(const char *name,int roomid,unsigned breath)
{
    creature *disk=NULL;
    hd_breath_record resource;
    assert(hd_store_load_player(name,&disk)==HD_STORE_OK);
    assert(disk && disk->rom_num==roomid);
    free_crt(disk);
    assert(hd_breath_store_read(name,&resource)==HD_BREATH_STORE_OK);
    assert(resource.current==breath);
}

int main(void)
{
    char *seed[]={0,"seed",NULL};
    const char *name="Hdtravelq";
    room town={0},forest={0},plain={0},mountain={0};
    creature player,*live=NULL;
    hd_breath_record before,after;
    unsigned breath;
    int value,i;
    time_t now;

    assert(legacy_main(2,seed)==0);
    town.rom_num=2;
    forest.rom_num=10001;
    plain.rom_num=10002;
    mountain.rom_num=10003;

    initial(&player,name);
    player.class=FIGHTER;
    player.level=40;
    player.rom_num=2;
    assert(hd_store_create_player(name,&player)==HD_STORE_OK);
    assert(hd_store_load_player(name,&live)==HD_STORE_OK);
    assert(live);
    live->parent_rom=&town;

    /* First prompt may lazily migrate legacy player state ONCE.
     * It must never recreate a depleted record on reconnect.
     */
    value=-1;
    assert(hd79_breath_status(live,&value)==0);
    assert(value==100);
    assert(hd79_breath_status(live,&value)==0 && value==100);
    puts("PASS: first status initializes exact saved 100 Breath once");

    /* A successful native command will execute the real room transfer
     * AFTER this checkpoint returns, not before it. */
    assert(hd79_breath_precommit(live,&forest)==0);
    assert(live->rom_num==2 && live->parent_rom==&town);
    expect_disk(name,10001,98);
    live->rom_num=10001;live->parent_rom=&forest;
    puts("PASS: initial wilderness travel commits room+Breath before mutation");

    /* A native short write/rename error leaves the caller in old room
     * and leaves BOTH persisted values unchanged.
     */
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_breath_precommit(live,&plain)==-1);
    unsetenv("HD_ATOMIC_FAIL");
    assert(live->rom_num==10001 && live->parent_rom==&forest);
    expect_disk(name,10001,98);
    puts("PASS: refused write cannot move player or spend Breath");

    /* A rename-uncertain save may have committed. The hook must
     * reconcile both values before allowing the caller to move.
     */
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_breath_precommit(live,&plain)==0);
    unsetenv("HD_ATOMIC_FAIL");
    assert(live->rom_num==10001);
    expect_disk(name,10002,96);
    live->rom_num=10002;live->parent_rom=&plain;
    puts("PASS: uncertain rename reconciled; room and charge exactly once");

    /* Native callback pulse does not refill on command spam.
     * Resting acceleration is not yet connected to the real pose flag.
     */
    assert(hd_breath_store_read(name,&before)==HD_BREATH_STORE_OK);
    now=(time_t)before.last_recover;
    assert(hd79_breath_pulse(live,(long)(now+30))==0);
    expect_disk(name,10002,96);
    assert(hd79_breath_pulse(live,(long)(now+45))==0);
    expect_disk(name,10002,100);
    assert(hd79_breath_pulse(live,(long)(now+45))==0);
    expect_disk(name,10002,100);
    puts("PASS: native recovery callback applies max one timed +5 pulse");

    /* Deliberately exhaust player in the synthetic durable record
     * without replaying dozens of artificial room changes.
     */
    assert(hd_breath_store_read(name,&before)==HD_BREATH_STORE_OK);
    for (i=0;i<50;i++) {
        assert(hd_breath_store_step(name,&before,
            HD_BREATH_OP_TRAVEL,1,0,
            (uint32_t)(now+90+i),&after)==HD_BREATH_STORE_OK);
        before=after;
    }
    expect_disk(name,10002,0);
    value=-1;
    assert(hd79_breath_status(live,&value)==0 && value==0);

    assert(hd79_breath_precommit(live,&mountain)==-1);
    assert(live->rom_num==10002);
    expect_disk(name,10002,0);
    assert(hd79_breath_precommit(live,&town)==0);
    expect_disk(name,2,0);
    assert(live->rom_num==10002);
    live->rom_num=2;live->parent_rom=&town;
    puts("PASS: exhausted wilderness denied; indoor retreat free");

    assert(hd79_breath_status(live,&value)==0 && value==0);
    free_crt(live);
    puts("ROUND 79K: NATIVE PRETRANSFER BREATH MOVE/PULSE/HUD CONTRACT PASS");
    puts("REAL MOVE/GO SOCKET TESTS AND RESTING +15: NOT YET VERIFIED");
    return 0;
}
