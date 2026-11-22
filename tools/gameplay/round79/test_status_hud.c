/* Round 79B: display-only unit regressions; requires no MUD runtime. */
#include "hd_status_hud.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static hd_status_hud_values sample(void)
{
    hd_status_hud_values v;
    memset(&v,0,sizeof v);
    v.hp_current=14;
    v.hp_max=25;
    v.mp_current=5;
    v.mp_max=10;
    return v;
}

int main(void)
{
    char text[192], untouched[4]={'a','b','c',0};
    hd_status_hud_values v=sample();
    int rc;

    rc=hd_status_hud_format(text,sizeof text,&v);
    assert(rc>0 && rc==(int)strlen(text));
    assert(!strcmp(text,"HP 14/25 | MP 5/10 | Breath --"));
    assert(!strchr(text,27));

    v.breath_available=1;
    v.breath_current=80;
    v.breath_max=100;
    assert(hd_status_hud_format(text,sizeof text,&v)>0);
    assert(!strcmp(text,"HP 14/25 | MP 5/10 | Breath 80/100"));

    v.ansi_enabled=1;
    assert(hd_status_hud_format(text,sizeof text,&v)>0);
    assert(strstr(text,"\033[1;32mHP 14/25\033[0m"));
    assert(strstr(text,"\033[1;34mMP 5/10\033[0m"));
    assert(strstr(text,"\033[1;36mBreath 80/100\033[0m"));

    v.hp_current=2;
    v.breath_current=10;
    assert(hd_status_hud_format(text,sizeof text,&v)>0);
    assert(strstr(text,"\033[1;31mHP 2/25\033[0m"));
    assert(strstr(text,"\033[1;31mBreath 10/100\033[0m"));

    v.ansi_enabled=0;
    v.hp_current=-30;
    v.mp_current=900;
    assert(hd_status_hud_format(text,sizeof text,&v)>0);
    assert(!strcmp(text,"HP 0/25 | MP 10/10 | Breath 10/100"));

    assert(hd_status_hud_format(untouched,3,&v)==-1);
    assert(!strcmp(untouched,"abc"));
    assert(hd_status_hud_format(NULL,192,&v)==-1);
    assert(hd_status_hud_format(text,0,&v)==-1);
    assert(hd_status_hud_format(text,sizeof text,NULL)==-1);

    v.breath_max=0;
    assert(hd_status_hud_format(text,sizeof text,&v)==-1);
    v.breath_available=0;
    assert(hd_status_hud_format(text,sizeof text,&v)>0);
    assert(strstr(text,"Breath --"));
    v.ansi_enabled=2;
    assert(hd_status_hud_format(text,sizeof text,&v)==-1);

    puts("ROUND 79B: HP/MP/BREATH ANSI DISPLAY RULES PASS");
    puts("NATIVE STATUS PROMPT / CREATION ANSI: NOT YET INTEGRATED");
    return 0;
}
