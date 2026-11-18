#include "mstruct.h"
#include "hd_necro_creation.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned calls;

static int minimum(int low,int high)
{
    ++calls;
    return low;
}

static int maximum(int low,int high)
{
    ++calls;
    return high;
}

static int random_stat(int low,int high)
{
    ++calls;
    return low+rand()%(high-low+1);
}

int main(void)
{
    creature p={0},before;
    int i;

    hd_necro_creation_stats(&p,1,minimum);

    assert(calls==5);
    assert(p.strength==8);
    assert(p.dexterity==9);
    assert(p.constitution==10);
    assert(p.intelligence==14);
    assert(p.piety==14);

    hd_necro_creation_stats(&p,1,maximum);

    assert(calls==10);
    assert(p.strength==14);
    assert(p.dexterity==15);
    assert(p.constitution==16);
    assert(p.intelligence==18);
    assert(p.piety==18);

    puts("PASS: Exact Necromancer attribute boundaries");

    before=p;
    hd_necro_creation_stats(&p,0,minimum);

    assert(calls==10);
    assert(!memcmp(&before,&p,sizeof p));

    puts("PASS: Ordinary class attributes preserved");

    srand(7505);

    for(i=0;i<10000;++i) {
        hd_necro_creation_stats(&p,1,random_stat);

        assert(p.strength>=8 && p.strength<=14);
        assert(p.dexterity>=9 && p.dexterity<=15);
        assert(p.constitution>=10 && p.constitution<=16);
        assert(p.intelligence>=14 && p.intelligence<=18);
        assert(p.piety>=14 && p.piety<=18);
    }

    assert(calls==50010);

    puts("ROUND 75E: 10000 ATTRIBUTE ROLLS PASS");

    return 0;
}
