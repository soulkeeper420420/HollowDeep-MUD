/* Synthetic native players only, using the existing serializer fixtures. */
#include "travel_base.c"
#include "hd79_mount_store.h"

/* Any unresolved uncertain result must fail-stop instead of saving live state. */
void output_buf(void) {}
void disconnect(int fd) { (void)fd; assert(!"Unexpected failed reconciliation"); }

int hd79_wilderness_terrain(int id)
{
    return id==10003 ? '^':'.';
}

static creature *owner(const char *name, room *where)
{
    creature *player=NULL;
    assert(hd_store_load_player(name,&player)==HD_STORE_OK && player);
    player->parent_rom=where;
    return player;
}

int main(void)
{
    const char *name="Hdmountqa";
    hd79_mount_roster a,b,c,stale;
    hd_breath_record breath;
    creature seed,*player;
    object equipped={0};
    room town={0};
    hd_travel_plan plan;
    FILE *file;
    int i,status,successes=0,conflicts=0;
    pid_t children[4];

    assert(previous_travel_main()==0);
    assert(mkdir("rooms",0700)==0);
    file=fopen("rooms/stables.map","w");
    assert(file && fputs("HDSTABLE1\n2\n",file)>0 && fclose(file)==0);
    town.rom_num=2;
    initial(&seed,name); seed.class=FIGHTER; seed.level=40; seed.rom_num=2; seed.gold=20000;
    assert(hd_store_create_player(name,&seed)==HD_STORE_OK);
    assert(hd_breath_store_init(name,1000,&breath)==HD_BREATH_STORE_OK);
    player=owner(name,&town);
    assert(hd79_mount_read(name,&a)==HD79_MOUNT_ABSENT);
    assert(hd_store_save_claim(name,player,claim,digest)==HD_STORE_OK);
    strcpy(equipped.name,"Mount Test Blade");
    equipped.wearflag=WIELD;
    player->ready[WIELD-1]=&equipped;
    assert(hd_store_save_claim(name,player,"ffffffffffffffffffffffffffffff7a",digest)==HD_STORE_FAILURE);
    assert(hd_store_save_claim(name,player,"ffffffffffffffffffffffffffffff7b",digest)==HD_STORE_FAILURE);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BUY,1,2,0,NULL,&b)==HD79_MOUNT_OK);
    assert(b.count==1 && b.entries[0].endurance==120);
    stale=a;
    assert(hd79_mount_change(player,&stale,HD79_MOUNT_BUY,1,2,0,NULL,&c)==HD79_MOUNT_CONFLICT);
    player->ready[WIELD-1]=NULL;
    free_crt(player); player=owner(name,&town);
    assert(player->first_obj && !strcmp(player->first_obj->obj->name,"Mount Test Blade"));
    assert(hd_store_read_claim(name,claim,digest)==1);
    assert(player->gold==19900);
    a=b;
    {
        unsigned char packed[50000], raw[100000], altered[50000];
        size_t count,total;
        int length,encoded,k;
        hd_receipt_set receipts;
        FILE *save=fopen("player/Hdmountqa","rb");
        assert(save);
        count=fread(packed,1,sizeof packed,save);
        assert(count>0 && count<sizeof packed && fclose(save)==0);
        length=hd_uncompress_bounded((char *)packed,(char *)raw,count,sizeof raw);
        assert(length>0);
        assert(hd_receipt_decode(raw,length,sizeof(creature)+sizeof(int)+sizeof(object)+sizeof(int),&receipts)==0);
        for(k=0;k<(int)receipts.count;++k)
            if(!strcmp(receipts.entries[k].claim_id,"ffffffffffffffffffffffffffffff7b")) break;
        assert(k<(int)receipts.count);
        receipts.entries[k]=receipts.entries[--receipts.count];
        assert(hd_receipt_encode(raw,sizeof raw,sizeof(creature)+sizeof(int)+sizeof(object)+sizeof(int),&receipts,&total)==0);
        encoded=hd_compress_bounded((char *)raw,(char *)altered,total,sizeof altered);
        assert(encoded>0 && hd_atomic_player_snapshot("player",name,altered,encoded)==0);
        memset(&c,0x5a,sizeof c);
        stale=c;
        assert(hd79_mount_read(name,&c)==HD79_MOUNT_ERROR && !memcmp(&c,&stale,sizeof c));
        assert(hd_atomic_player_snapshot("player",name,packed,count)==0);
        assert(hd79_mount_read(name,&c)==0 && c.count==1);
        puts("PASS: valid outer native receipt with a missing mount fragment fails closed without output mutation");
    }
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BOARD,1,2,0,NULL,&c)==HD79_MOUNT_ERROR);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_read(name,&c)==HD79_MOUNT_OK && c.active_id==0 && c.revision==a.revision);
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BOARD,1,2,0,NULL,&b)==HD79_MOUNT_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_read(name,&c)==HD79_MOUNT_OK && c.active_id==1 && c.revision==b.revision);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BOARD,1,2,0,NULL,&c)==HD79_MOUNT_CONFLICT);
    a=b;
    assert(hd_mount_travel_preview(1,1,'^',100,120,&plan)==0);
    assert(hd_mount_travel_preview(1,1,'.',100,120,&plan)==1);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_MOVE,10001,0,1,&plan,&b)==HD79_MOUNT_OK);
    assert(b.entries[0].endurance==119);
    assert(hd_breath_store_read(name,&breath)==0 && breath.current==100);
    free_crt(player); town.rom_num=10001; player=owner(name,&town);
    assert(player->rom_num==10001 && player->gold==19900);
    assert(hd_store_save_live_player(name,player)==HD_STORE_OK);
    assert(hd79_mount_read(name,&a)==0 && a.entries[0].endurance==119);
    puts("PASS: native paired mount save, gold debit, fault recovery, room checkpoint and ordinary-save preservation");

    /* Four processes present the same expected roster. Exactly one can dismount. */
    for(i=0;i<4;++i) {
        children[i]=fork(); assert(children[i]>=0);
        if (!children[i]) {
            int rc=hd79_mount_change(player,&a,HD79_MOUNT_OFF,0,0,0,NULL,&b);
            _exit(rc==HD79_MOUNT_OK ? 10:rc==HD79_MOUNT_CONFLICT ? 11:12);
        }
    }
    for(i=0;i<4;++i) {
        assert(waitpid(children[i],&status,0)==children[i] && WIFEXITED(status));
        if(WEXITSTATUS(status)==10) ++successes;
        else if(WEXITSTATUS(status)==11) ++conflicts;
        else assert(0);
    }
    assert(successes==1 && conflicts==3);
    assert(hd79_mount_read(name,&a)==0 && !a.active_id);
    stale=a;
    strcpy(stale.epoch,"123456789012345678901234");
    assert(hd79_mount_change(player,&stale,HD79_MOUNT_BOARD,1,0,0,NULL,&b)==HD79_MOUNT_CONFLICT);
    /* Use the same mounted native checkpoint until exhausted, then retreat. */
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BOARD,1,0,0,NULL,&b)==0);
    a=b;
    for(i=0;i<119;++i) {
        unsigned target=player->rom_num==10001 ? 10002:10001;
        assert(hd_mount_travel_preview(1,1,'.',100,a.entries[0].endurance,&plan)==1);
        assert(hd79_mount_change(player,&a,HD79_MOUNT_MOVE,target,0,1,&plan,&b)==0);
        player->rom_num=(short)target;
        town.rom_num=(short)target;
        a=b;
    }
    assert(a.entries[0].endurance==0);
    assert(hd_mount_travel_preview(1,1,'.',100,0,&plan)==0);
    assert(hd_mount_travel_preview(1,0,0,100,0,&plan)==1);
    assert(hd79_mount_change(player,&a,HD79_MOUNT_MOVE,2,0,0,&plan,&b)==0);
    assert(b.entries[0].endurance==0);
    free_crt(player);
    puts("PASS: native Endurance exhausts exactly once per move and allows free indoor retreat");
    /* A recreated character receives a new authoritative Breath epoch. */
    assert(unlink("player/Hdmountqa")==0);
    assert(hd_store_create_player(name,&seed)==0);
    assert(hd_breath_store_init(name,2000,&breath)==0);
    town.rom_num=2;
    player=owner(name,&town);
    assert(hd79_mount_read(name,&b)==HD79_MOUNT_ABSENT);
    assert(strcmp(b.epoch,a.epoch));
    assert(hd79_mount_change(player,&a,HD79_MOUNT_BOARD,1,0,0,NULL,&c)==HD79_MOUNT_CONFLICT);
    /* Reserve every remaining receipt slot, leaving no room for half a pair. */
    for(i=0;i<HD_RECEIPT_MAX-2;++i) {
        char claim[33];
        snprintf(claim,sizeof claim,"%032x",1000+i);
        assert(hd_store_save_claim(name,player,claim,digest)==HD_STORE_OK);
    }
    assert(hd79_mount_change(player,&b,HD79_MOUNT_BUY,1,2,0,NULL,&c)==HD79_MOUNT_ERROR);
    assert(hd79_mount_read(name,&b)==HD79_MOUNT_ABSENT && b.count==0);
    free_crt(player);
    puts("PASS: recreated names reject old epochs and a full receipt set cannot publish half a mount pair");
    puts("PASS: native concurrent mount CAS grants one change, denies stale and forged epochs");
    puts("ROUND79T: NATIVE MOUNT ATOMIC STORE PASS");
    return 0;
}
