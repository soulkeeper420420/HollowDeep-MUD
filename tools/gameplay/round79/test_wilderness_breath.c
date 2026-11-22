/* Round 79C deterministic Breath movement stamina acceptance rules. */
#include "hd_wilderness_breath.h"
#include "hd_status_hud.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    int breath=HD_BREATH_MAX;
    int i;
    hd_status_hud_values hud;
    char display[192];

    /* Only completed wilderness steps cost Breath. The caller must skip the
       commit function on blocked exits, look, inventory, and invalid moves. */
    for (i=0;i<50;i++) {
        assert(hd_breath_can_move(breath,1)==1);
        breath=hd_breath_after_move(breath,1);
        assert(breath==100-2*(i+1));
    }
    assert(breath==0);
    assert(hd_breath_can_move(breath,1)==0);
    assert(hd_breath_after_move(breath,1)==-1);

    /* Players can leave the wilderness even when exhausted. */
    assert(hd_breath_can_move(0,0)==1);
    assert(hd_breath_after_move(0,0)==0);

    /* Wilderness rest restores enough Breath to move again. */
    assert(hd_breath_recover(0,1)==15);
    assert(hd_breath_can_move(hd_breath_recover(0,1),1)==1);
    assert(hd_breath_recover(93,1)==100);
    assert(hd_breath_recover(98,0)==100);
    assert(hd_breath_recover(50,0)==55);

    /* Indoor travel and non-movement actions never drain the resource. */
    assert(hd_breath_after_move(56,0)==56);
    for(i=0;i<500;i++)
        assert(hd_breath_after_move(56,0)==56);

    /* Never permit negative/oversized gauges or ambiguous zone states. */
    assert(hd_breath_can_move(-1,1)==-1);
    assert(hd_breath_can_move(101,1)==-1);
    assert(hd_breath_can_move(100,2)==-1);
    assert(hd_breath_after_move(100,2)==-1);
    assert(hd_breath_recover(-1,1)==-1);
    assert(hd_breath_recover(50,2)==-1);

    /* The existing ANSI/plain formatter can display REAL numeric Breath. */
    memset(&hud,0,sizeof hud);
    hud.hp_current=14;
    hud.hp_max=25;
    hud.mp_current=5;
    hud.mp_max=10;
    hud.breath_current=hd_breath_recover(0,1);
    hud.breath_max=HD_BREATH_MAX;
    hud.breath_available=1;
    hud.ansi_enabled=0;
    assert(hd_status_hud_format(display,sizeof display,&hud)>0);
    assert(!strcmp(display,"HP 14/25 | MP 5/10 | Breath 15/100"));
    hud.ansi_enabled=1;
    assert(hd_status_hud_format(display,sizeof display,&hud)>0);
    assert(strstr(display,"\033[1;31mBreath 15/100\033[0m"));
    assert(strstr(display,"\033[1;32mHP 14/25\033[0m"));

    puts("ROUND 79C: WILDERNESS BREATH MOVEMENT / REGEN RULES PASS");
    puts("NATIVE MOVEMENT / PERSISTENCE: NOT YET INTEGRATED");
    return 0;
}
