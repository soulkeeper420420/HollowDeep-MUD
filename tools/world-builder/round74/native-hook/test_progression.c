#include "hd74_progression.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static hd74_rules rules(void){
    hd74_rules r;
    r.level_cap=20;r.xp_base=1000;r.xp_growth=50;
    r.stat_base=10;r.stat_max=18;r.starting_points=20;
    r.remort_kills=3;r.remort_seconds=180;
    r.points_per_remort=2;r.legacy_points_cap=10;
    return r;
}
static void make_hex(char out[33],unsigned n){
    static const char hex[]="0123456789abcdef";
    unsigned i;
    for(i=0;i<32;i++) out[i]=hex[(i+n)%16];
    out[32]=0;
}
static void test_xp_levels(void){
    hd74_rules r=rules(),bad=r;
    hd74_player p;uint32_t top,prev;
    assert(hd74_valid_rules(&r)==0);
    assert(hd74_exp_threshold(&r,1,&prev)==0&&prev==0);
    assert(hd74_exp_threshold(&r,20,&top)==0&&top>prev);
    assert(hd74_exp_threshold(&r,21,&top)!=0);
    bad.level_cap=128;assert(hd74_valid_rules(&bad)!=0);
    bad=r;bad.xp_base=65000;bad.xp_growth=65000;bad.level_cap=100;
    assert(hd74_valid_rules(&bad)!=0);
    assert(hd74_new_player(&r,&p,"PlayerOne",4)==0);
    assert(hd74_award_xp(&r,&p,500)==HD74_DENIED);
    assert(hd74_allocate_stat(&r,&p,0,8)==0);
    assert(hd74_allocate_stat(&r,&p,1,8)==0);
    assert(hd74_allocate_stat(&r,&p,2,4)==0);
    assert(hd74_allocate_stat(&r,&p,2,1)==HD74_DENIED);
    assert(hd74_finalize_stats(&r,&p)==0);
    assert(hd74_allocate_stat(&r,&p,2,1)==HD74_DENIED);
    assert(hd74_award_xp(&r,&p,UINT32_MAX)==0);
    assert(p.level==20&&p.experience==top);
    assert(hd74_award_xp(&r,&p,UINT32_MAX)==0);
    assert(p.experience==top);
    puts("ROUND 74A: config XP/ELF32 cap/starting stat allocation PASS");
}
static void test_remort(void){
    hd74_rules r=rules();hd74_player p;
    hd74_legacy_request req;
    uint32_t top;char q[33],e[33],e2[33],e3[33];
    assert(hd74_new_player(&r,&p,"HeroOne",4)==0);
    assert(hd74_allocate_stat(&r,&p,0,8)==0);
    assert(hd74_allocate_stat(&r,&p,1,8)==0);
    assert(hd74_allocate_stat(&r,&p,2,4)==0);
    assert(hd74_finalize_stats(&r,&p)==0);
    assert(hd74_can_use_skill(&r,&p,4,10)==0);
    assert(hd74_can_use_skill(&r,&p,5,1)==0);
    assert(hd74_exp_threshold(&r,20,&top)==0);
    assert(hd74_award_xp(&r,&p,top)==0);
    assert(hd74_can_use_skill(&r,&p,4,20)==1);
    assert(hd74_can_use_skill(&r,&p,4,21)==0);
    make_hex(q,0);make_hex(e,1);make_hex(e2,2);make_hex(e3,3);
    assert(hd74_begin_remort(&r,&p,q,101,1000)==HD74_OK);
    assert(hd74_credit_kill(&r,&p,"SomeoneElse",101,e,1100)==HD74_DENIED);
    assert(hd74_credit_kill(&r,&p,"HeroOne",102,e,1100)==HD74_DENIED);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e,999)==HD74_DENIED);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e,1100)==HD74_OK);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e,1100)==HD74_ALREADY);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e2,1181)==HD74_EXPIRED);
    assert(hd74_finish_remort(&r,&p,5,1101)==HD74_DENIED);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e2,1102)==HD74_OK);
    assert(hd74_credit_kill(&r,&p,"HeroOne",101,e3,1103)==HD74_OK);
    assert(hd74_finish_remort(&r,&p,4,1104)==HD74_DENIED);
    assert(hd74_finish_remort(&r,&p,5,1181)==HD74_EXPIRED);
    assert(hd74_finish_remort(&r,&p,5,1104)==HD74_OK);
    assert(p.level==1&&p.experience==0&&p.remorts==1&&p.legacy_points==2);
    assert(hd74_can_use_skill(&r,&p,4,20)==1);
    assert(hd74_can_use_skill(&r,&p,5,2)==0);
    assert(hd74_can_use_skill(&r,&p,5,1)==1);
    assert(hd74_finish_remort(&r,&p,6,1105)==HD74_DENIED);
    memset(&req,0,sizeof req);strcpy(req.owner,"HeroOne");
    req.point_cost=1;req.bind_to_character=0;
    assert(hd74_buy_legacy(&p,&req)==HD74_DENIED);
    req.bind_to_character=1;req.point_cost=2;
    assert(hd74_buy_legacy(&p,&req)==HD74_OK);
    assert(hd74_buy_legacy(&p,&req)==HD74_DENIED);
    assert(p.legacy_points==0&&p.legacy_items==1&&p.divine_favor==0);
    puts("ROUND 74A: timed remort/unique kills/class inheritance/bound legacy PASS");
}
static void test_codec(void){
    hd74_rules r=rules();hd74_player p,q,before;
    unsigned char bytes[HD74_WIRE_BYTES],corrupt[HD74_WIRE_BYTES];
    char id[33];
    assert(hd74_new_player(&r,&p,"ArchiveHero",7)==0);
    assert(hd74_allocate_stat(&r,&p,0,8)==0);
    assert(hd74_allocate_stat(&r,&p,1,8)==0);
    assert(hd74_allocate_stat(&r,&p,2,4)==0);
    assert(hd74_finalize_stats(&r,&p)==0);
    assert(hd74_award_xp(&r,&p,UINT32_MAX)==0);
    make_hex(id,5);
    assert(hd74_begin_remort(&r,&p,id,777,100)==0);
    before=p;
    assert(hd74_encode(&r,&p,bytes)==0);
    assert(hd74_decode(&r,bytes,sizeof bytes,&q)==0);
    assert(!memcmp(&q,&p,sizeof p));
    memcpy(corrupt,bytes,sizeof bytes);corrupt[106]^=1;
    assert(hd74_decode(&r,corrupt,sizeof corrupt,&q)==HD74_CORRUPT);
    assert(hd74_decode(&r,bytes,sizeof bytes-1,&q)==HD74_CORRUPT);
    assert(!memcmp(&q,&before,sizeof q));
    assert(hd74_credit_kill(&r,&p,"ArchiveHero",777,id,101)==0);
    assert(hd74_encode(&r,&p,bytes)==0);
    assert(hd74_decode(&r,bytes,sizeof bytes,&q)==0);
    assert(q.quest_kills==1);
    puts("ROUND 74A: fixed-size native-safe progression receipt/CRC/reload PASS");
}
int main(void){test_xp_levels();test_remort();test_codec();puts("ROUND 74A: PRIVATE CORE PASS (NO NATIVE HOOKS/PRODUCTION)");return 0;}
