/* Round 79J: actual native compressed character room and Breath receipt
 * share ONE atomic save transaction. Only synthetic player files exist.
 */
#define main legacy_main
#include "test_pet_store.c"
#undef main

#include "hd_breath_move_checkpoint.h"

int main(void)
{
    char *who="Hdbrmove";
    char *seed[]={0,"seed",NULL};
    hd_breath_record first,second,third,old;
    creature p,*live=NULL,*disk=NULL;
    int i,old_room;

    /* Reuse the established isolated native pet-store seed only. */
    assert(legacy_main(2,seed)==0);

    initial(&p,who);
    p.class=FIGHTER;
    p.level=40;
    p.rom_num=2;
    p.gold=7654;
    assert(hd_store_create_player(who,&p)==HD_STORE_OK);
    assert(hd_breath_store_init(who,1000,&first)==HD_BREATH_STORE_OK);
    assert(first.current==100);

    assert(hd_store_load_player(who,&live)==HD_STORE_OK);
    assert(live && live->rom_num==2);
    live->rom_num=10001;
    assert(hd_breath_store_checkpoint_move(
        who,live,2,&first,1,1100,&second)==HD_BREATH_STORE_OK);
    assert(second.current==98 && second.revision==first.revision+1);

    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==10001 && disk->gold==7654);
    free_crt(disk);
    disk=NULL;
    assert(hd_breath_store_read(who,&third)==HD_BREATH_STORE_OK);
    assert(third.current==98 && third.revision==second.revision);
    puts("PASS: atomic snapshot contains BOTH room 10001 and Breath 98");

    /* Refuse a stale prior room or stale Breath revision without
       changing either stored room or receipt. */
    live->rom_num=10002;
    assert(hd_breath_store_checkpoint_move(
        who,live,2,&second,1,1101,&third)
        ==HD_BREATH_STORE_CONFLICT);
    assert(hd_breath_store_checkpoint_move(
        who,live,10001,&first,1,1101,&third)
        ==HD_BREATH_STORE_CONFLICT);
    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==10001);
    free_crt(disk);disk=NULL;
    assert(hd_breath_store_read(who,&third)==HD_BREATH_STORE_OK);
    assert(third.current==98);
    puts("PASS: wrong old room and stale receipt cannot move player");

    /* A write denied before rename must keep BOTH durable values. */
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd_breath_store_checkpoint_move(
        who,live,10001,&second,1,1200,&third)
        ==HD_BREATH_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==10001);
    free_crt(disk);disk=NULL;
    assert(hd_breath_store_read(who,&third)==HD_BREATH_STORE_OK);
    assert(third.current==98 && third.revision==second.revision);
    puts("PASS: failed atomic rename saves NEITHER new room nor charge");

    /* Uncertain after rename must be resolved by disk read. Both
       values must be present, not room-only or Breath-only. */
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd_breath_store_checkpoint_move(
        who,live,10001,&second,1,1201,&third)
        ==HD_BREATH_STORE_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");

    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==10002 && disk->gold==7654);
    free_crt(disk);disk=NULL;
    assert(hd_breath_store_read(who,&third)==HD_BREATH_STORE_OK);
    assert(third.current==96 && third.revision==second.revision+1);
    assert(hd_breath_store_checkpoint_move(
        who,live,10001,&second,1,1202,&old)
        ==HD_BREATH_STORE_CONFLICT);
    puts("PASS: uncertain rename atomically commits room and Breath once");

    /* Exhaust Breath through the verified receipt-only storage, then
       verify room+receipt co-checkpoint fails closed for wilderness. */
    old=third;
    for (i=0;i<48;i++) {
        assert(hd_breath_store_step(
            who,&old,HD_BREATH_OP_TRAVEL,1,0,
            1300+(uint32_t)i,&third)==HD_BREATH_STORE_OK);
        old=third;
    }
    assert(third.current==0);
    old_room=live->rom_num;
    live->rom_num=10003;
    assert(hd_breath_store_checkpoint_move(
        who,live,old_room,&third,1,1400,&second)
        ==HD_BREATH_STORE_FAILURE);
    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==10002);
    free_crt(disk);disk=NULL;

    /* Exhaustion cannot trap player in the wilderness. Indoor retreat
       checkpoints a new room with ZERO Breath cost even at time zero. */
    live->rom_num=2;
    assert(hd_breath_store_checkpoint_move(
        who,live,10002,&third,0,0,&second)==HD_BREATH_STORE_OK);
    assert(second.current==0 && second.revision==third.revision);
    assert(hd_store_load_player(who,&disk)==HD_STORE_OK);
    assert(disk->rom_num==2);
    free_crt(disk);disk=NULL;
    assert(hd_breath_store_read(who,&old)==HD_BREATH_STORE_OK);
    assert(old.current==0 && old.revision==third.revision);
    free_crt(live);
    puts("PASS: exhausted wilderness step denied, indoor retreat free");
    puts("ROUND 79J: NATIVE ROOM+BREATH ATOMIC CHECKPOINT PASS");
    puts("NATIVE MOVE/GO HOOK, TIMER, MOUNTS: NOT YET ACTIVE");
    return 0;
}
