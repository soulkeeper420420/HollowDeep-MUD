/* Round 79F: strict 64-hex persistent Breath record unit regressions. */
#include "hd_breath_record.h"
#include "hd_wilderness_breath.h"
#include "hd_status_hud.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static const char *EPOCH="6a11bb22cc33dd44ee55ff66";
static int same_record(const hd_breath_record *a,const hd_breath_record *b)
{
    return !strcmp(a->epoch,b->epoch) && a->revision==b->revision &&
           a->last_recover==b->last_recover && a->current==b->current;
}

static void assert_serialization(const hd_breath_record *s)
{
    char data[65];
    hd_breath_record copy;
    assert(hd_breath_record_encode(s,data)==0);
    assert(strlen(data)==HD_BREATH_WIRE_HEX_LENGTH);
    assert(hd_breath_record_decode(data,&copy)==0);
    assert(!strcmp(copy.epoch,s->epoch));
    assert(copy.revision==s->revision);
    assert(copy.last_recover==s->last_recover);
    assert(copy.current==s->current);
}

int main(void)
{
    hd_breath_record init,now,next,decoded,untouched;
    hd_status_hud_values hud;
    char wire[65],bad[65],display[192];
    int i;

    assert(hd_breath_record_new(&init,EPOCH,1000)==0);
    assert(init.current==100 && init.revision==1);
    assert_serialization(&init);
    assert(hd_breath_record_new(&init,"bad",1000)==-1);
    assert(hd_breath_record_new(&init,EPOCH,0)==-1);
    assert(hd_breath_record_new(&init,EPOCH,1000)==0);

    now=init;
    for(i=0;i<50;i++) {
        assert(hd_breath_record_step(&now,&next,
            HD_BREATH_OP_TRAVEL,1,0,1001+(uint32_t)i)==0);
        assert(next.current==(unsigned)(98-2*i));
        assert(next.revision==now.revision+1);
        now=next;
    }
    assert(now.current==0);
    assert_serialization(&now);
    untouched=next;
    assert(hd_breath_record_step(&now,&next,
        HD_BREATH_OP_TRAVEL,1,0,2000)==-1);
    assert(same_record(&next,&untouched));

    /* No Breath penalty on successful move to an ordinary interior. */
    assert(hd_breath_record_step(&now,&next,
        HD_BREATH_OP_TRAVEL,0,0,2000)==0);
    assert(next.current==now.current && next.revision==now.revision);
    assert_serialization(&next);
    now=next;

    /* Native timer caller passes one verified callback per recovery tick. */
    assert(hd_breath_record_step(&now,&next,
        HD_BREATH_OP_RECOVER,0,1,2000)==0);
    assert(next.current==15);
    assert(next.last_recover==2000);
    now=next;
    untouched=next;
    assert(hd_breath_record_step(&now,&next,
        HD_BREATH_OP_RECOVER,0,1,2000)==-1);
    assert(same_record(&next,&untouched));
    assert(hd_breath_record_step(&now,&next,
        HD_BREATH_OP_RECOVER,0,0,2001)==0);
    assert(next.current==20);
    assert_serialization(&next);

    /* Exact save/load bytes survive an ordinary player-save roundtrip. */
    assert(hd_breath_record_encode(&next,wire)==0);
    assert(hd_breath_record_decode(wire,&decoded)==0);
    assert(decoded.current==20 && decoded.revision==next.revision);
    assert(decoded.last_recover==2001);

    memset(&hud,0,sizeof hud);
    hud.hp_current=14; hud.hp_max=25;
    hud.mp_current=5; hud.mp_max=10;
    hud.breath_available=1; hud.breath_current=decoded.current;
    hud.breath_max=100; hud.ansi_enabled=1;
    assert(hd_status_hud_format(display,sizeof display,&hud)>0);
    assert(strstr(display,"\033[1;31mBreath 20/100\033[0m"));

    memcpy(bad,wire,65);
    bad[0]='z';
    assert(hd_breath_record_decode(bad,&decoded)==-1);
    memcpy(bad,wire,65);
    bad[45]='1'; /* max corruption */
    assert(hd_breath_record_decode(bad,&decoded)==-1);
    memcpy(bad,wire,65);
    bad[62]='1'; /* reserved bits nonzero */
    assert(hd_breath_record_decode(bad,&decoded)==-1);
    memcpy(bad,wire,65);
    bad[44]='f'; /* max metadata corruption */
    assert(hd_breath_record_decode(bad,&decoded)==-1);
    memcpy(bad,wire,65);
    bad[64]=0; bad[41]='z';
    assert(hd_breath_record_decode(bad,&decoded)==-1);
    assert(hd_breath_record_decode("",&decoded)==-1);
    assert(hd_breath_record_decode(NULL,&decoded)==-1);
    assert(hd_breath_record_encode(NULL,bad)==-1);
    assert(hd_breath_record_encode(&now,NULL)==-1);

    next.revision=UINT32_MAX;
    /* Even when revisions are exhausted or the clock fails, a retreat
       to a non-wilderness room is still free and must remain possible. */
    assert(hd_breath_record_step(&next,&decoded,
        HD_BREATH_OP_TRAVEL,0,0,0)==0);
    assert(same_record(&decoded,&next));
    untouched=decoded;
    assert(hd_breath_record_step(&next,&decoded,
        HD_BREATH_OP_TRAVEL,1,0,2002)==-1);
    assert(same_record(&decoded,&untouched));
    assert(hd_breath_record_step(&now,&decoded,99,1,0,2002)==-1);
    assert(hd_breath_record_step(&now,&decoded,
        HD_BREATH_OP_TRAVEL,2,0,2002)==-1);

    puts("ROUND 79F: PERSISTENT BREATH WIRE / REVISION / HUD RULES PASS");
    puts("NATIVE ATOMIC PLAYER STORE AND MOVEMENT: NOT YET CONNECTED");
    return 0;
}
