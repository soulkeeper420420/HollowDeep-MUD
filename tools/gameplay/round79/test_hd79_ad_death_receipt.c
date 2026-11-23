/* Synthetic native-format death receipt tests; no native player writes. */
#include "hd79_ad_death_receipt.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static const char EPOCH[]="1234567890abcdef12345678";
int hd79_mount_roster_valid(const hd79_mount_roster *r)
{
    unsigned i;
    if(!r||!r->revision||strlen(r->epoch)!=24||r->count>6||
       r->active_id>r->count)return 0;
    for(i=0;i<r->count;i++)
       if(r->entries[i].id!=i+1||r->entries[i].species<1||
          r->entries[i].species>6)return 0;
    return 1;
}
static void init(hd79_mount_roster *r)
{
    memset(r,0,sizeof *r);
    memcpy(r->epoch,EPOCH,25);
    r->revision=1;
}
int main(void)
{
    hd79_mount_roster empty,one,two,forged;
    hd79_ad_death_receipt first,with_one,dead,decoded,next,sentinel;
    char hex[65],tampered[65];
    init(&empty);
    memset(&sentinel,0xa5,sizeof sentinel);
    assert(hd79_ad_death_new_empty(&empty,&first)==1);
    assert(first.count==0&&first.serial==1&&first.dead_mask==0);
    assert(hd79_ad_death_wire_encode(&empty,&first,hex)==0);
    assert(strlen(hex)==64);
    assert(hd79_ad_death_wire_decode(&empty,hex,&decoded)==0);
    assert(!memcmp(&decoded,&first,sizeof first));
    puts("PASS: empty roster death receipt canonical wire roundtrip");

    one=empty;one.revision=2;one.count=1;
    one.entries[0].id=1;one.entries[0].species=1;
    assert(hd79_ad_death_new_empty(&one,&sentinel)==-1);
    assert(hd79_ad_death_award_step(&empty,&first,&one,&with_one)==1);
    assert(with_one.count==1&&with_one.serial==2);
    assert(hd79_ad_death_action_eligible(&one,&with_one,1)==1);
    assert(hd79_ad_death_reconnect_allowed(&one,&with_one,1)==0);
    assert(hd79_ad_death_wire_encode(&one,&with_one,hex)==0);
    assert(hd79_ad_death_mark(&one,&with_one,1,&dead)==1);
    assert(dead.dead_mask==1 && dead.serial==3);
    assert(hd79_ad_death_action_eligible(&one,&dead,1)==0);
    assert(hd79_ad_death_reconnect_allowed(&one,&dead,1)==0);
    assert(hd79_ad_death_mark(&one,&dead,1,&sentinel)==0);
    assert(hd79_ad_death_wire_encode(&one,&dead,hex)==0);
    assert(hd79_ad_death_wire_decode(&one,hex,&decoded)==0);
    assert(decoded.dead_mask==1 && decoded.serial==3);
    puts("PASS: first owned mount death monotone, no dead resurrection or auto restore");

    two=one;two.count=2;two.revision=3;
    two.entries[1].id=2;two.entries[1].species=2;
    assert(hd79_ad_death_award_step(&one,&dead,&two,&next)==1);
    assert(next.dead_mask==1 && next.count==2);
    assert(hd79_ad_death_action_eligible(&two,&next,1)==0);
    assert(hd79_ad_death_action_eligible(&two,&next,2)==1);
    assert(hd79_ad_death_mark(&two,&next,2,&decoded)==1);
    assert(decoded.dead_mask==3);
    puts("PASS: award preserves earlier tombstones and isolates new mount ID");

    strcpy(tampered,hex);tampered[14]=(hex[14]=='a'?'b':'a');
    assert(hd79_ad_death_wire_decode(&one,tampered,&sentinel)==-1);
    strcpy(tampered,hex);tampered[0]='5';
    assert(hd79_ad_death_wire_decode(&one,tampered,&sentinel)==-1);
    strcpy(tampered,hex);tampered[8]='A';
    assert(hd79_ad_death_wire_decode(&one,tampered,&sentinel)==-1);
    strcpy(tampered,hex);tampered[64]='!';
    assert(hd79_ad_death_wire_decode(&one,tampered,&sentinel)==-1);
    forged=one;memcpy(forged.epoch,"aaaaaaaaaaaaaaaaaaaaaaaa",25);
    assert(hd79_ad_death_wire_decode(&forged,hex,&sentinel)==-1);
    assert(hd79_ad_death_action_eligible(&forged,&dead,1)==0);
    puts("PASS: corruption/epoch replay/magic/canonical length denied");

    assert(hd79_ad_death_mark(&one,&with_one,0,&sentinel)==-1);
    assert(hd79_ad_death_mark(&one,&with_one,2,&sentinel)==-1);
    assert(hd79_ad_death_action_eligible(&one,&with_one,0)==0);
    assert(hd79_ad_death_action_eligible(&one,&with_one,7)==0);
    assert(hd79_ad_death_award_step(&one,&with_one,&one,&sentinel)==-1);
    assert(hd79_ad_death_new_empty(&one,&sentinel)==-1);
    puts("PASS: forged IDs, populated migration, invalid transitions denied");
    puts("ROUND79AD: PRIVATE FOURTH DEATH RECEIPT POLICY PASS");
    return 0;
}
